---
layout: post
title: "Journey through eventsourcing: Part 4 - Pre-flight checks and launch"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/DRAFT-eventsourcing-04-launch
series_sequence_nr: 5
key_takeaway: "eventsourcing/04-launch-key-takeaway.md"
image: 
    path: /assets/img/eventsourcing/DRAFT-eventsourcing-04-launch/cover.png
    srcset:
        1920w: /assets/img/eventsourcing/DRAFT-eventsourcing-04-launch/cover.png
        960w:  /assets/img/eventsourcing/DRAFT-eventsourcing-04-launch/cover@0,5x.png
        480w:  /assets/img/eventsourcing/DRAFT-eventsourcing-04-launch/cover@0,25x.png
---
{% include infra/series-nav-link-variables series_tag="eventsourcing-series-2020" series_sequence_nr=page.series_sequence_nr %}
[The previous post][previous-post] took us through the implementation phase - and the obvious next step was to launch 
the product. The stakes were high - our new system managed a critically important business process (described in the 
[first post][first-post]), so we needed to make sure nothing goes wrong. To netter understand how the system would 
behave underproduction traffic, we have put it through a series of load tests of increasing complexity and traffic.
This allowed us to capture a few issues that, if manifested in production, could have caused significant downtime
and losses.

[first-post]: {% post_url design/2020-06-27-eventsourcing-01-problem %}#problem-description
[previous-post]: {{ prev_post }} 

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# Static fire test

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/static-fire.jpg)

Image source: [NASA][static-fire] (adapted)
{:.image-attribution}

[static-fire]: https://www.nasa.gov/exploration/systems/sls/multimedia/booster-test-for-future-space-launch-system-flights2.html

</div>

The last couple of weeks before the launch we spent doing some sort of "static fire tests" - trying to make sure we
catch as many issues as possible. Even though we had pretty good test coverage, we still didn't have high enough 
confidence that the system would behave correctly - primarily because the automated testing only captures the issues 
someone already imagined. Our new system was built using pretty novel technology - both to us and to the organization 
as a whole - so we were pretty sure there are issues our imagination have missed. One of the areas where the confidence
was especially low was system's behavior under load and in the presence of failure - so this is where most of 
my efforts was concentrated.   
   
## Load testing

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/rpm.jpg)

Image source: [Pixabay][rpm] - [Pixabay License][pixabay-licence]
{:.image-attribution}

[rpm]: https://pixabay.com/photos/dashboard-design-dial-gauge-1866466/
[pixabay-licence]: https://pixabay.com/service/license/

</div>

I have experimented with multiple load test tools - such as [Locust][locust] and [Gatling][gatling], but eventually 
ended up using old and venerable [JMeter][jmeter]. The reason behind this was simple - even though as software 
developer I enjoyed and appreciated the "loadtest as code" approach many modern frameworks offer, it required much 
higher effort to actually develop, run and analyze the results of the test[^1].

Test scenarios evolved quite a bit - they started as a single guardrail-style test and naturally evolved to cover 
many more cases - from "are we achieving the design goals?" to "how much heat can it take till it breaks?". Moreover, 
the scenarios were often run with failures being injected into the system in background. The proper way to do so 
would be to have some tool to inject failures at random - such as [Chaos Monkey][chaos-monkey], but in our case
failure injection boiled down to me just ssh-ing to instances and killing java processes.

The initial load tests with "normal shape, current load" went well - system was holding response times significantly
below the alotted latency budget and behaved correctly. However, as I pressed on the accelerator, problems start to 
occur. Long story short, the hunch that there were a bunch of unknown bugs related to the load and failures turned 
out to be quite correct - I've found and addressed some issues that could've caused a major downtime and losses, 
should they manifest in production.

[locust]: https://locust.io/
[gatling]: https://gatling.io/
[jmeter]: https://jmeter.apache.org/
[chaos-monkey]: https://netflix.github.io/chaosmonkey/

[^1]: Simply put, with JMeter most of the things we needed was already there - including building and parsing JSON
    payloads, asserting on response status codes, graphing results, etc. With gatling and locust we'd need to 
    build many of those features ourselves.

## Distributed data not performing well

The first problem occured under pure load test (no failures), slightly higher load then the production traffic -
around 2.5x. The response throughput vs. number of concurrent users would first hit a plateau, and after a relatively
short exposure to such traffic (~2-3 minutes) the cluster would desintegrate[^2], resulting in complete unavailability.
What's worse, after the request rate would drop to a "safe" levels, the system would not automatically recover, staying
in the broken state until manual intervention. Obviously, this was unacceptable.

The root cause turned out to be one particular use of [Distributed Data][akka-ddata] we had: it stored a map
associating orders to the actors keeping them - this was done to optimize the order cancellation call. During high load
the map would receive large numbers of updates; performing these updates would compete for CPU time with the "normal" 
request handling. Eventually, due to the way it was set up in Distributed Data internals, the incoming map updates 
would fill entire JVM heap and cause the Java process to grind to a full halt.

The fix was simple, but counterintuitive. Instead of maintaining a lookup map and sending just one message to the actor
that owned the reservation, it would broadcast the cancellation to all actors, and the ones that does not own the 
cancelled reservation would simply ignore the message. Even though it is counter-intuitive - each cancellation would 
spawn ~500 messages, most of which would require network communication - in practice this approach was able 
to maintain much higher load levels[^3].

**Lesson learnt:** one real life example towards "premature optimization is the root of all evil" mantra. 

[akka-ddata]: https://doc.akka.io/docs/akka/current/distributed-data.html
[akka-ddata-limitations]: https://doc.akka.io/docs/akka/current/distributed-data.html#limitations

[^2]: _literally_ desintegrate :smile: As in, "loose integrity" - nodes stop communicating with each other.
[^3]: The record was around 60x normal load - and even then the bottleneck was somewhere else.

## Loosing requests during restart

The next serious issue happened only in presence of node restarts, but under any load. When a node was gracefully
shutdown, part of the system's state would briefly go unavailable. The expectation was that the requests targeting
that part would be picked up when the actors are recovered on the other nodes. In reality though, for a brief period of
time (10-15 seconds, but occasionally up to a few minutes) those requests were just timing out. What's worse is that 
this would still happen even without any node crashes/restarts - when _a new node join a cluster_. 

This is somewhat acceptable behavior in general - partial, brief and self-healing unavailability - but one of our 
[design goals][design-goal-no-failure-during-planned-restart] was to continue serving traffic during planned restart.

The issue was caused by the combination of two factors - the [persistence library][akka-persistence-cassandra] 
initialization were not eager enough and our own system was too eager to relocate and recover the
actors. The former caused a few seconds delay when a first actor is recovered on a freshly joined instance, and 
the latter would put all the affected actors up for recovery at the same time - overloading the recovery process[^4].

The fix was also twofold - I have [submitted an issue][eagerness-issue] and it was fixed and published the next week 
(kudos to the maintainers). I have also changed the recovery approach - and again it was somewhat counter-intuitive - 
from trying to recover all the actors as soon as possible, to **not recovering any**. In this case, a different 
mechanism kicks in, that sort of "prioritizes" recovering actors that has unhandled messages[^5]. In addition, later 
we've added a "watchdog" actor that would send a wakeup message to all the actors that should be up and running shortly 
after nodes join or leave cluster - forcing recovering the actors that are still down.

**Lesson learnt:** eagerness is not always good; if latency/availability is a concern it might be good to prioritize 
things that are necessary, rather than bring up everything at once.
    
[^4]: This would cause a lot of load on the persistence plugin in general. In our case, it was even more pronounced, as
    we configured a "constant" recovery strategy that limits the number of concurrent recoveries - this was done to
    limit the impact of recoveries on the normal request handling.
    
[^5]: The detailed description is too long and irrelevant to the topic at hand, but simply put, Akka Sharing attempts
    redelivering messages sent to actors in the downed shard regions, and this causes the target actor to be started
    if it is down. 
    
[design-goal-no-failure-during-planned-restart]: {% post_url design/2020-07-14-eventsourcing-02-solutions %}#recap-declared-project-goals
[akka-persistence-cassandra]: https://github.com/akka/akka-persistence-cassandra
[eagerness-issue]: https://github.com/akka/akka-persistence-cassandra/issues/350

# Launch

## Pre-flight checks

Last week before the launch was devoted to building supporting tools and scripts to monitor systems health and speed up 
recovery from failures. Most are pretty straightforward and common things - such as Kibana and Graphana dashboards to
monitor logs and system metrics, setting up alerts, opting-in into the VM health monitoring, provisioning the VMs and 
databases in the production environment, etc. Two noteworthy and non-trivial additions were scripts to perform 
recovery actions.

**First script** allowed any actor or group of actors, to have their state "reset" to a selected point in time. With
eventsourcing, it is "illegal" to delete persistence records, as they represent events that already happened in the
real life. Instead, the script caused actors to "pretend" like certain batch of events had no effect - by finding the
latest state snapshot made before the target point in time and copying it as the last recorded.

**Second script** used system of record for the customer orders to reconstruct and "replay" the requests to our system.
Long story short, it queried the corresponding database directly and then just looped over the orders in chronological
order, issuing requests as if they were originated from those customer orders.

Canonical eventsourcing systems has a unqiue ability to retroactively fix issues given that the sequence of persisted 
events is still correct and valid. Adding these scripts also allowed us to retroactively fix[^6] cases when invalid 
business logic decisions were made and invalid events were persisted.

[^6]: This ain't a proper time-machine, unfortunately, so in some cases the recovery would have no choice but to 
violate the constraints - in such cases we would at lest know to what extend the constraints are violated and could
issue a warning to operations to prepare for trouble.

## We're clear for take off

Before the full launch, the system needed to accumulate about a week worth of requests in a "readonly" mode -
to build up the current state of the world. This could have been done faster using the second script above, but the 
decision was to make the launch process a bit more sophisticated and go with a so-called ["dark launch"][dark-launch]
approach. 

The full details are irrelevant here (I'll probably write a separate post on it), but simply put, I've rigged
the legacy capacity management system to send all the request it receives to the new system - and put it behind 
a feature flag. The flag also served as a killswitch - should anything go wrong it would require just a single config
change to completely divert all traffic from hitting the new system.

[dark-launch]: https://launchdarkly.com/blog/why-leading-companies-dark-launch  

## Ignition!

Finally, with all the preparation, load testing and safety harness, the actual dark launch was... uneventful.
Literally - I've flipped the switch one Wednesday morning, and no one noticed anything, no servers catching fire, 
no angry customers unable to place orders. 

This was **a major success** - we saw that the new system accumulates data and makes decisions, we could already 
evaluate if it is performing well and doing the right thing, there was data flowing from the system into 
analytics databases, etc. - so it was functioning properly and ready for the "full launch".

The rest was history - "full launch" actually stretched a good couple of months and was done "one zone at a time", when
the operations felt they're ready for a switchover. And they all lived happily ever after... until the first change
request. :smile:

# Key takeaways

{% include {{page.key_takeaway}} %} 

# Conclusion

To sum up: we took a careful and thoughtful approach to consider and analyze multiple implementation approaches and
architecture styles. Most "classical", "lightweight" or "straightforward" sparkled concerns about either consistency,
availability, or performance of the solution. Eventsourcing approach, despite being more novel to the team and more 
inherently complex, offered a clear way to achieve the goals, and set up a firm ground for further evolution 
and scaling of the system.

The biggest takeaway from this post is that with a stateful eventsourced system, there's a large chunk of problems that
arise from quirks and peculiarities of the particular implementation.  

In {% include infra/conditional-link.md label="the next" url=next_post %}, and final, post we'll take a glance at how
the system withstand the test of time - from small bugfixes and improvements to major new features and

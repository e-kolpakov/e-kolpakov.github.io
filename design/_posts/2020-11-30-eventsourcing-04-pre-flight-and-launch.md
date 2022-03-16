---
layout: post
title: "Journey through eventsourcing: Part 4 - Pre-flight checks and launch"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/2020-11-30-eventsourcing-04-pre-flight-and-launch
series_sequence_nr: 5
key_takeaway: "eventsourcing/04-launch-key-takeaway.md"
image: 
    path: /assets/img/eventsourcing/2020-11-30-eventsourcing-04-pre-flight-and-launch/cover.png
    srcset:
        1920w: /assets/img/eventsourcing/2020-11-30-eventsourcing-04-pre-flight-and-launch/cover.png
        960w:  /assets/img/eventsourcing/2020-11-30-eventsourcing-04-pre-flight-and-launch/cover@0,5x.png
        480w:  /assets/img/eventsourcing/2020-11-30-eventsourcing-04-pre-flight-and-launch/cover@0,25x.png
---
{% include infra/series-nav-link-variables series_tag="eventsourcing-series-2020" series_sequence_nr=page.series_sequence_nr %}
[The previous post][previous-post] took us through the implementation phase - the next step was to launch 
the product. The stakes were high - our new system managed a critically important business process (described in the 
[first post][first-post]), so we needed to make sure everything runs well. To better understand how the system would 
behave under production traffic, we have put it through a series of load tests of increasing complexity and load.
It allowed us to capture a few issues that, if manifested in production, could have caused significant downtime
and losses.

[first-post]: {% post_url design/2020-06-27-eventsourcing-01-problem %}#problem-description
[previous-post]: {{ prev_post }} 

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# Static fire test

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/static_fire.jpg)

Image source: [NASA][static-fire] (adapted) - [NASA Media Usage Guidelines][nasa-media-usage]
{:.image-attribution}

[static-fire]: https://www.nasa.gov/exploration/systems/sls/multimedia/booster-test-for-future-space-launch-system-flights2.html

</div>

I have spent the last couple of weeks before the launch doing some  "static fire tests" - trying to catch 
as many issues as possible. Even though test coverage was pretty good, we still didn't have high enough confidence 
that the system would behave correctly - primarily because the automated testing only captures the issues 
someone already imagined. We used pretty novel technology to build the system - novel both to us and 
the organization as a whole - so we were sure there are issues our imagination has missed. The confidence 
was especially low related to the system's behavior under load and in the presence of failure - 
so this is where I have concentrated my efforts.   
   
## Load testing

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/rpm.jpg)

Image source: [Pixabay][rpm] - [Pixabay License][pixabay-licence]
{:.image-attribution}

[rpm]: https://pixabay.com/photos/dashboard-design-dial-gauge-1866466/
</div>

I have experimented with multiple load test tools - such as [Locust][locust] and [Gatling][gatling] 
but eventually ended up using old and venerable [JMeter][jmeter]. The reason behind this was simple - 
even though as a software developer I enjoyed and appreciated the "loadtest as code" approach many 
modern frameworks offer, it required much higher effort to develop, run, and analyze the results of the test[^1].

Test scenarios evolved quite a bit - they started as a single guardrail-style test and naturally evolved to cover 
many more cases - from "are we achieving the design goals?" to "how much heat can it take till it breaks?". 
Moreover, I have often run test scenarios with failures injected into the system in the background. The proper way 
to do so would be to have some tool (such as [Chaos Monkey][chaos-monkey]) to inject failures at random, 
but in this case, it boiled down to me just ssh-ing to instances and killing java processes.

The initial load tests with "normal shape, current load" went well - the system was holding response times significantly
below the allotted latency budget and behaved correctly. However, as I pressed on the accelerator, problems start 
to occur. Long story short, the hunch that there were a bunch of unknown bugs related to the load and failures 
turned out to be quite correct - I've found and addressed some issues that could've caused significant downtime 
and losses, should they manifest in production.

[locust]: https://locust.io/
[gatling]: https://gatling.io/
[jmeter]: https://jmeter.apache.org/
[chaos-monkey]: https://netflix.github.io/chaosmonkey/

[^1]: With JMeter, most of the things we needed were already there - including building and parsing JSON
    payloads, asserting on response status codes, graphing results, etc. With Gatling and Locust, we'd need to 
    code many of those features ourselves.

## Distributed data not performing well

The first problem occurred under pure load test (no failures), slightly higher load then the production traffic -
around 2.5x. The response throughput vs. the number of concurrent users would first hit a plateau; after a relatively
short exposure to such traffic (~2-3 minutes), the cluster would desintegrate[^2], resulting in complete unavailability.
What's worse, after the request rate drops to "safe" levels, the system would not automatically recover, staying
in the broken state until manual intervention. It was unacceptable.

The root cause turned out to be one particular use of [Distributed Data][akka-ddata] we had: the system stored 
a map associating orders to the actors keeping them - used to optimize order cancellations. During high load, 
this map would receive large numbers of updates; performing these updates would compete for CPU time with 
the regular request handling. What's worse, the updates are relatively costly. Eventually, the rate of producing 
the updates would become higher than handling them. Due to the way Distributed Data works internally, 
the incoming updates would be queued and eventually will fill the entire JVM heap[^3], causing the Java process 
to grind to a halt.

The fix was counter-intuitive. Instead of maintaining a lookup map and sending just one message to the actor 
that owned the reservation, it would broadcast the cancellation to all actors, and the ones that do not own 
the canceled reservation would ignore the message. Even though it is counter-intuitive - each cancellation 
would spawn ~500 messages, most of which would require network communication - this approach was able to maintain 
much higher load levels[^4].

**Lesson learned:** one real-life example towards "premature optimization is the root of all evil" mantra. 

[akka-ddata]: https://doc.akka.io/docs/akka/current/distributed-data.html
[akka-ddata-limitations]: https://doc.akka.io/docs/akka/current/distributed-data.html#limitations

[^2]: _literally_ disintegrate :smile: As in, "loose integrity" - nodes stop communicating with each other.

[^3]: This was likely due to a bug - most (if not all) other mechanisms in Akka have bounded memory buffers 
    and prefer rejecting messages over causing out of memory issues.

[^4]: The record was around 60x usual load - and the bottleneck was still somewhere else.

## Losing requests during restart

The next issue happened at any load, but only when adding, restarting, or crashing nodes. When a node gracefully 
shuts down, part of the system's state would briefly become unavailable. The expectation was that the actors would 
quickly recover on the other nodes and pick up the in-flight requests. However, for a brief period - 10-15 seconds, 
but occasionally up to a few minutes - those requests were timing out[^5]. What's worse is that this would still 
happen even without any node crashes/restarts - when _a new node joins a cluster_. 

The issue was due to a combination of two factors - the [persistence library][akka-persistence-cassandra] 
initialization was not eager enough, while our system was rushing too much to relocate and recover the actors. 
The former caused a few seconds delay when a first actor recovers on a freshly joined instance, and the latter
would put all the affected actors up for recovery at the same time - overloading the recovery process[^6].

The fix was also twofold. First, I have [submitted an issue][eagerness-issue] -  it was fixed and published 
the next week (kudos to the maintainers). I have also changed the recovery approach - and it was somewhat 
counter-intuitive as well - from trying to recover all the actors the fastest possible, to **not recovering any**. 
In this case, recovery happens differently - it "prioritizes" starting actors that have unhandled messages[^7]. 
Also, later we have added a "watchdog" actor that sends a wake-up message to all the actors that should be up and 
running 30-40 seconds after nodes join or leave the cluster - forcing recovering the actors that are still down.

**Lesson learned:** eagerness is not always advantageous; if latency/availability metrics are critical 
it might make sense to prioritize necessary processes, rather than trying to bring up everything at once.

[^5]: In general, partial, brief, and self-healing unavailability is mostly considered an acceptable behavior 
    during failure. However, one of our [design goals][design-goal-no-failure-during-planned-restart] was 
    to continue serving traffic during the planned restart.
    
[^6]: It would cause a lot of load on the persistence plugin in general. In our case, it was more pronounced, as
    we configured a "constant" recovery strategy that limits the number of concurrent recoveries - to constrain 
    the impact of recoveries on regular request handling.
    
[^7]: The detailed description is too long and irrelevant to the topic at hand but simply put, Akka Sharing attempts 
    to redeliver the messages sent to the actors in the downed shard regions - it causes the target actor 
    to start if it is down. 
    
[design-goal-no-failure-during-planned-restart]: {% post_url design/2020-07-14-eventsourcing-02-solutions %}#recap-declared-project-goals
[akka-persistence-cassandra]: https://github.com/akka/akka-persistence-cassandra
[eagerness-issue]: https://github.com/akka/akka-persistence-cassandra/issues/350

# Launch

## Pre-flight checks

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/preflight.jpg)

Image source: [flickr][preflight]
[![](/assets/icons/cc_licenses/cc-by.svg){:.cc_icon}][cc-by-2.0]
{:.image-attribution}

[preflight]: https://www.flickr.com/photos/mcas_cherry_point/6731286457/
</div>

Last week before the launch was devoted to building supporting tools and scripts to monitor systems health and 
speed up recovery from failures. Most are pretty straightforward and widespread things - such as Kibana and Graphana 
dashboards to monitor logs and system metrics, setting up alerts, provisioning the VMs and databases in the 
production environment, etc. Two noteworthy and non-trivial additions were scripts to perform recovery actions.

**First script** allowed "resetting" the state of any actor (or group of actors) to a selected point in time. With
eventsourcing, it is "illegal" to delete persistence records, as they represent events that already happened. 
Instead, the script caused actors to "pretend" like some events had no effect - by finding the latest state snapshot
made before the target point time and saving a copy of it as the most recent snapshot.

**Second script** used the system of record for the customer orders to reconstruct and "replay" the requests 
to our system. Long story short, it queried the corresponding database directly and then just looped over the orders 
in chronological order, issuing requests as if they originated from those customer orders.

Canonical eventsourcing systems have a unique ability to retroactively fix issues given that the persisted events are
still correct and valid. Adding these scripts allowed us to retroactively fix issues where the persistence 
store contains malformed or incorrect events[^8].

[^8]: This is not a proper time-machine, unfortunately. In some cases, the recovery would have no choice but to 
    violate the constraints - but at least we would know to what extent the constraint were violated and could
    issue a warning to operations to prepare for trouble.

## We're clear for take-off

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/launch_control.jpg)

Image source: [NASA][launch-control] - [NASA Media Usage Guidelines][nasa-media-usage]
{:.image-attribution}

[launch-control]: https://www.nasa.gov/image-feature/cape-canaverals-launch-control-center
</div>

Before the full launch, the system needed to accumulate about a week worth of requests in a "readonly" mode -
to build up the current state of the world. We could have done it faster using the second script above, but the 
decision was to make the launch process a bit more sophisticated and go with a so-called ["dark launch"][dark-launch]
approach.

The full details are irrelevant here (I'll probably write a separate post on it), but simply put, I've rigged
the legacy capacity management system to send all the requests it receives to the new system - and put it behind 
a feature flag. The flag also served as a killswitch - should anything go wrong, it would require just 
a single config change to divert all the traffic from hitting the new system.

[dark-launch]: https://launchdarkly.com/blog/why-leading-companies-dark-launch

## Ignition!

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/launch.jpg)

Image source: [Roscosmos][launch] - [Roscosmos media license][roscosmos-licence]
{:.image-attribution}

[launch]: https://www.roscosmos.ru/26214/
</div>

Finally, with all the preparation, load testing, and safety harness, the actual dark launch was... uneventful.
Literally - I've flipped the switch one Wednesday morning, and no one noticed anything, no servers catching fire, 
no angry customers unable to place orders, no logistics.

It was **a major success** - we saw that the new system performs well and makes decisions we could evaluate 
for correctness, the data was flowing from the system into the analytics databases, etc. - so it was functioning up 
to the specs and ready for the full launch.

The rest was history - "full launch" actually stretched a couple of months and was done "one zone at a time" - when
the operations felt they're ready to switch over to the new system. And they all lived happily ever after - until 
the first new feature request. :smile:

# Key takeaways

{% include {{page.key_takeaway}} %} 

# Conclusion

Simply put, our stake in the stateful, distributed, eventsourced system based on Akka played out quite well. We achieved 
all the reliability, scalability, and performance goals we've declared with significant margins. It wasn't an easy 
task though - there were a couple of dangerous problems in the initial version that required quite some time 
to be discovered, investigated, and mitigated.

In {% include infra/conditional-link.md label="the next" url=next_post %} - and final - post in the series, we'll take 
a glance at how the system withstood the test of time - how easy it was to maintain and evolve it, from small 
bug fixes to large new features.

[cc-by-2.0]: https://creativecommons.org/licenses/by/2.0/
[nasa-media-usage]: https://www.nasa.gov/multimedia/guidelines/index.html
[roscosmos-licence]: https://www.roscosmos.ru/22650/
[pixabay-licence]: https://pixabay.com/service/license/

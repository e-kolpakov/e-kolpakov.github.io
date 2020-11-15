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

# Pre-flight checks

The last couple of weeks before the launch we spent doing some sort of "pre-flight checks" - trying to make sure we
catch as many issues as possible and also preparing the safety harness to address issues and recover from failures
should they happen.

Even though we had pretty good test coverage, we still didn't have high enough confidence that the system would behave 
correctly - primarily because the testing captured the issuse we knew could happen. However, our new system was built
using pretty novel technology - both to us and to the organization as a whole - so we were pretty sure there are issues
we missed. One of the areas where the confidence was especially low was system's behavior under load and in the 
presense of failure - so this is where most of my efforts was concentrated.   
   
## Load testing ...

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/rpm.jpg)

Image source: [Pixabay][rpm] - [Pixabay License][pixabay-licence]
{:.image-attribution}

[rpm]: https://pixabay.com/photos/dashboard-design-dial-gauge-1866466/
[pixabay-licence]: https://pixabay.com/service/license/

</div>

I have experimented with multiple load test tools - such as [Locust][locust] and [Gatling][gatling], but eventually 
ended up using old and venerable [JMeter][jmeter]. The reason behind this was simple - even though as software 
developer I enjoyed and valued the "loadtest as code" approach many modern frameworks offer, it required much higher 
effort to actually develop, run and analyze the results of the test[^2].

[locust]: https://locust.io/
[gatling]: https://gatling.io/
[jmeter]: https://jmeter.apache.org/

Besides the actual "coding" of the load test (i.e. setting up requests, parsing responses, etc.), there are two major
parts of the loadtest that affect results: test environment and test scenarios. I didn't do anything fancy for the test 
environment - just used the staging env that was already there. It fully replicated the production env, except used a 
downscaled instance sizes - `t2.micro`, to be specific[^3].

Test scenarios actually evolved quite a bit during the pre-launch phase - they started as a single guardrail-style test
and naturally evolved to cover many more cases. So, at the end, the list was roughly as follows:

1. Normal customer traffic shape, current load - guardrail: safe to deploy now?
2. Normal customer traffic shape, 10x load - initial design goal.
3. Normal customer traffic shape, full burn till it breaks - testing the limits of the system.
4. Pessimistic traffic shape: all customers target same delivery slot, current load - does it hold in the worst case?
5. Pessimistic traffic shape: all customers target same delivery slot, full burn till it breaks.

Finally, the scenarios were often run with failures being injected into the system in background. The proper way to
do so would be to have some tool to inject failures at random - such as [Chaos Monkey][chaos-monkey], but in our case
failure injection boiled down to a developer just ssh-ing to instances and killing java processes.

[chaos-monkey]: https://netflix.github.io/chaosmonkey/

[^2]: Simply put, with JMeter most of the things we needed was already there - including building and parsing JSON
    payloads, asserting on response status codes, etc. With gatling and locust we'd need to build it ourselves.

[^3]: back then `t2` was the latest generation, `t3` came out a year or so after.

## ... and issues it caught

The initial load tests with "normal shape, current load" went well - system was holding response times significantly
below the alotted latency budget and behaved correctly. However, as I raised the heat, problems start to occur. 
Long story short, the hunch that there were a bunch of unknown bugs related to the load and failures turned out to be 
quite correct - I've found and addressed three issues that could've caused a major downtime and losses, should they 
manifest in production.

### Distributed data not performing well

The first problem occured under pure load test (no failures), under slightly higher load then the production traffic -
around 2.5x. The response throughput vs. number of concurrent users would first hit a plateau, and after a relatively
short exposure to such traffic (~2-3 minutes) the cluster would desintegrate[^4], resulting in complete unavailability.
What's worse, after the request rate would drop to a "safe" levels, the system would not automatically recover, staying
in the broken state until manual intervention. Obviously, this was unacceptable.

The root cause turned out to be one particular use of [Distributed Data][akka-ddata] we had - it stored a map used to
associate orders to the actors storing them - to optimize the cancellation call. During high load the map would receive
large numbers of updates; performing these updates would compete for CPU time with the "normal" request handling. 
Eventually, due to the way it was set up in Distributed Data internals, the incoming map updates would fill entire
JVM heap and cause the process to grind to a full halt.

The fix was simple, but counterintuitive. Instead of maintaining a lookup map and sending just one cancellation message
only to the actor that owned the reservation, the map was completely removed in favor of a brute-force approach - 
broadcasting the cancellation to all actors, and simply ignoring it if an actor did not own the cancellation. 
Even though it is counter-intuitive - each cancellation would spawn ~500 messages, most of which would require
network communication - in practice this approach was able to maintain much higher load levels[^5].

**Lesson learnt:** one real life example towards "premature optimization is the root of all evil" mantra. 

[akka-ddata]: https://doc.akka.io/docs/akka/current/distributed-data.html
[akka-ddata-limitations]: https://doc.akka.io/docs/akka/current/distributed-data.html#limitations

[^4]: _literally_ desintegrate :smile: As in, "loose integrity".   
[^5]: The record was around 60x normal load - and even then the bottleneck was somewhere else.

### Loosing requests during restart

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
the latter would put all the affected actors up for recovery  at the same time - overloading the recovery process[^6].

The fix was also twofold - I have [submitted an issue][eagerness-issue] and it was fixed and published the next week. 
I have also changed the recovery approach - and again it was somewhat counter-intuitive - from trying to recover all 
the actors as soon as possible, to **not recovering any**. In this case, a different mechanism kicks in, that sort of 
"prioretizes" recovering actors that has unhandled messages[^7]. In addition, later we've added a "watchdog" actor
that would force recovery of all actors that should be running 30-40 seconds after cluster membership changes.

**Lesson learnt:** eagerness is not always good; if latency/availability is a concern it might be good to prioretize 
things that are necessary, rather than bring up everything at once.
    
[^6]: This would cause a lot of load on the persistence plugin in general. In our case, it was even more pronounced, as
    we configured a "constant" recovery strategy that limits the number of concurrent recoveries - this was done to
    limit the impact of recoveries on the normal request handling.
    
[^7]: The detailed description is too long and irrelevant to the topic at hand, but simply put, Akka Sharing attempts
    redelivering messages sent to actors in the downed shard regions, and this causes the target actor to be started
    and recovered to latest state. 
    
[design-goal-no-failure-during-planned-restart]: {% post_url design/2020-07-14-eventsourcing-02-solutions %}#recap-declared-project-goals
[akka-persistence-cassandra]: https://github.com/akka/akka-persistence-cassandra
[eagerness-issue]: https://github.com/akka/akka-persistence-cassandra/issues/350



### Sharding coordinator state issue

This has happened just once - sharding coordinator corrupted it's own state, and was unable to start. It rendered
an entire service unusable, so even though it happened once and under extreme circumstances (`kill -9` and restart
instances under load test), the investigation and recovery took a long time - ~4-5 hours.

How did we found out - emulated total crash by `kill -9` ing java processes under extreme load.

Root cause - not exactly sure. According to coordinator error messages and records stored in Cassandra, it expected to
observe messages up to N, but actually had up to N-1. This might indicate a problem with Cassandra, Akka Persistence 
implementation, or maybe some overly optimistic configuration we had - but we never invested time to dig into that.   

How did we fix it - it was extremely hard to reproduce (in fact, couldn't reproduce at all), so I have just prepared 
a script to nuke the coordinator state, allowing it to start clean + added symptoms to the troubleshooting guide.   

Lesson learnt - if there is one thing that can take your entire system down - it eventually will, even if it is 
extremely robust. Better have a recovery plan for that case as well.

## Recovery

# Launch



# Key takeaways

{% include {{page.key_takeaway}} %} 

# Conclusion

In addition, I spent some time building a safety net:
* script to "rollback" any state to a point in time
* script to "replay" production requests using data from "old" system's DB
* script to automate sharding coordinator state reset

TBD
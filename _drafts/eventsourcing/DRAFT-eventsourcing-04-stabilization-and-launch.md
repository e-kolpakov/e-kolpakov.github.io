---
layout: post
title: "Journey through eventsourcing: Part 4 - Launch"
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
[first post][first-post]), so my team decided to go with a so called "dark launch" - exposing the system to the real 
production traffic, but ignoring its decisions upstream. This turned out to be a very wise decision - a couple of pretty
serious issues were captured and fixed during the "dark launch".

[first-post]: {% post_url design/2020-06-27-eventsourcing-01-problem %}#problem-description
[previous-post]: {{ prev_post }} 

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# Things to address before the full launch

We had two concerns we wanted to address before full launch: correctness and behavior under load.

Correctness - dark launch
Behavior under load - load test.

## Dark launch

Image: rocket launch at night

Wired the new system as a "secondary" input to the old one. Config value with three options:

* off - don't even send the request to the new system.
* dark - send request, receive and deserialize the response, but then discard it.
* full - send request, receive response and use it.

In addition, I spent some time building a safety net:
* script to "rollback" any state to a point in time
* script to "replay" production requests using data from "old" system's DB
* script to automate sharding coordinator state reset

TBD: Feature switches, initial results, support scripts (state rollback, sharding coordintor reset, "replaying" 
production requests from RDS, etc.)

## Load testing

Image: speedometer, or something like that

JMeter, with the following scenarios:
1. Normal customer traffic, current load <-- can we at least deploy now, and work on perf later
2. Normal customer traffic, 10x load <-- success criteria
3. Normal customer traffic, all in till it breaks
4. Pessimistic traffic shape - all customers target same entity, current load <-- defensive
5. Pessimistic traffic shape - all in till it breaks

# Issues found, fixes applied

## Distributed data not performing well

DData was not performing well - hit a plateau at about 2.5x current traffic. What's worse, cluster almost always 
desintegrated itself under this load, and required manual restart.

Minor effort spent to rescue ddata -- it could help to change to a more efficient serde and give ddata some
dedicated resource to manage its state. It may not help either when you are having too many updates, which I think
was the case happening to us though.

How did we found out - load test. Then load test + profiling. 

Root cause: Veeeery long linked-list in memory - presumably an unbound (or just very large) inbox in DData "internal" 
actor. Fast producer + slow consumer.

How we fixed it - bailed out of DData in favor of a brute-force broadcast to write side. Worked much better than 
expected - sustained whatever traffic we threw at it (our record was around 60x) and _something else_ was the 
bottleneck.

Lesson learnt - even though DData claimed to be fine with up to 10K top-level keys in the map, 500 keys + high rate of
updates was enough to grind the system to a halt.

## Loosing significant portion of customer calls during planned restart

Initial implementation would loose dozens of requests during first 10-15 seconds, and occasionally partial 
unavailability spanned longer time periods.

How did we found out - emulated planned restart by graceful stop of the java process - under load.

Root cause - two causes, actually. (1) there was a shortcoming (hard to call it a bug) in akka-persistence plugin we 
were using (TBD: link to github issue) that weren't eager enough in "eager initialization" mode. (2) Tried to eagerly 
recover all the "lost" actors on their new homes - not rapid enough recovery.

How did we fix it - filed an issue to Github and updated to the new version when it was ut (lucky for us, very quick, 
kudos to akka-persistence-cassandra maintainers). Changed the mode of actor recovery - at the "crash time", 
no actors would be automatically recovered - this would "prioritize" recovering ones that have new messages incoming.
Put a "watchdog" actor that would "woof" 30-40 seconds after "node left cluster" event - sending a wake up call to all
the actors that should be there (we know which actors should be alive at any point in time)

Lesson learnt - eagerness is not always good; if latency/availability is a concern might be good to focus on things
that are necessary to serve, rather than bring up everything at once.

## Sharding coordinator state issue

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

# Key takeaways

{% include {{page.key_takeaway}} %} 

# Conclusion

TBD
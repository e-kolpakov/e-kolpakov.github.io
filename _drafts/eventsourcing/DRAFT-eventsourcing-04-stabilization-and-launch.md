---
layout: post
title: "TBD: eventsourcing stabilization and launch"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/DRAFT-eventsourcing
series_sequence_nr: 4
---

TBD

[Back to Table of Contents]({% link design/eventsourcing-series.md %}#table-of-contents)

# Interesting things that went bad before the launch - and how we fixed them

The goal here is not to walk through all the issues, but highlight the relevant ones. I.e. "reservations skewed toward
the last shift because of XYZ" is not relevant to broad audience, but stuff about akka, CQRS and event-sourcing is.

Basically, technical/infra problems, not business issues.

## Load testing approach

JMeter, with the following scenarios:
1. Normal customer traffic, current load <-- can we at least deploy now, and work on perf later
2. Normal customer traffic, 10x load <-- success criteria
3. Normal customer traffic, all in till it breaks
4. Pessimistic traffic shape - all customers target same entity, current load <-- defensive
5. Pessimistic traffic shape - all in till it breaks

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

## Other minor stuff

Was able to corrupt Akka Sharding coordinator state once - only way to restore service is to manually wipe coordinator's
persistence. On a good side, there's a "script" shipped with Akka to do so, and no "user data" is actually lost - 
coordinator only controls where entities are placed, so just starting anew is a good recovery strategy.

# Launch

TBD: Feature switches, initial results, support scripts (state rollback, sharding coordintor reset, "replaying" 
production requests from RDS, etc.)
enabling in production, quick follow ups (there were none, if I recall right?)
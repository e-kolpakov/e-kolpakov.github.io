---
layout: post
title: TBD
tags: [design-principles]
image_link_base: /assets/img/DRAFT-eventsourcing
---

# Problem background

RM's mode of operations can be described as "guaranteed scheduled delivery" - customer selects a two-hour slot, and 
the order is delivered at that time sharp. This was (and still is) a part of customer value proposition, so it is really
important to fulfill it - one of the key company-wide metrics is delivery-on-time - percent of orders delivered in the
selected time slot, no earlier, no later.

Need to carefully plan logistics - including provisioning resources (workforce, vehicles, etc.). This is not a very
elastic process - more capacity cannot be easily obtained to cater for excess demand.

Capacity vs. demand problem, in a "strict" fashion - due to operational model, even one excess order might cause 
significant problems on the ground. No excess orders due to technical reasons are allowed.

# Existing solution

Describe RDS (without mentioning this name :)) - overall architecture, and why it was not sufficient anymore.

1. Needed to consider not only one type of capacity, but multiple
2. Ability to recognize other types of constraints (e.g. address restrictions)
3. Stability concerns
4. Performance concerns

Divali 2017 outage - briefly, as an example of stability issues. 

# Decomposing the problem

Simply put, a set of counters; each counter represents certain part of the delivery fleet - each time an order is 
placed, it is allocated to a counter and this counter is increased. When a counter reaches predefined value, no more
orders are allowed within that time slot[^1]. Finally, there should be a way to query current state of all the counters
and present it to the caller.

[^1]: It was slightly more complex in reality, but those are gory technical details, so I'll omit them for now.   

The complex part is that multiple customers might compete for the last available unit of capacity. In this case, we must
ensure that capacity is not exceeded - by allowing only one customer in, and politely rejecting all the others. 
So, in essence, the system should behave as a collection of atomic counters.

Simple to implement naively - optimistic concurrency with compare-and-set writes in the DB is one option. But 
non-functional requirements come into play: 

1. Expect big growth (for practical reasons we were assuming 10x)
2. Low latency even at scale - did I mention that all that is on a "sequential" path to placing an order and customer's
browser waits for the response?
3. Highly available, aka "no single point of failure"

(1) and (2) called for putting the counters into memory (yes, stateful system), (3) multiple instances of the system.
Add atomicity requirements on top, and we get a distributed, stateful, highly consistent system tp build.

# Declared goals

Functional:
* Strict consistency model for placing an order - see "Consistency Analysis" for details
* Better tools for planning team to manage the capacity

Non-functional:
* <100ms 99th percentile reads and writes
* at up to 10x load
* no customer calls are lost during rolling restart
* high availability deployment - at least two fully-functional instances
* consistency maintained even in case of failures (node crash, network issues, etc.)

## Consistency analysis

Multiple "clients" issuing commands. Multiple nodes of the system processing commands ("processors"). Each command 
affects single object. We want every compare-and-set operation to see the most latest value of the counter.

Essentially, we need to establish a total order of operations, but don't care about real-time (aka wall clock) 
consistency. So, the matching consistency model is [Sequential consistency](https://jepsen.io/consistency/models/sequential).

# Architectures considered and rejected

Resolve consistency at the DB level - latency concerns, shared infra concerns (spikes in load and noisy neighbours).

Relaxed consistency models (aka eventual consistency) - business requirements.

Streaming + sharding (e.g. Kafka) - lack of infra support, blocking semantics of customer operation (we'd rather 
outright reject everything, rather than keep the customers waiting)

Singleton - single point of failure, scalability problems

# Final architecture

Each counter is an entity. Entities are persisted, and deployed across the cluster.

Event-sourcing persistence - state is in memory, append-only updates during normal functioning:

1. In-memory state improves latency greatly (shaves one DB roundtrip completely)
2. Append-only persistence is much faster on DB side as well

DB is only read during state recovery - which happens when entities are reallocated or recovered at a different node.
Even at that point, read is sequential.

CQRS - separate mechanism to fetch "overview" - to prevent writes from blocking reads and scale them independently. 

# Initial implementation

Akka cluster + Sharding + Persistence. Each entity is encapsulated in an actor. Actors are sharded across the cluster,
and there is at most instance of the same entity in a cluster. If node is crashed, entities are automatically 
recovered at some other node - so there is brief period of unavailability.

Read side is Map stored in an Akka Distributed Data - replicated across all nodes in the cluster. Updates are delivered
in an asynchronous way. Reads storage have relaxed consistency (looks like [PRAM][pram]) on their own and are eventually
consistent with writes.

Another read side for near-real-time monitoring and analytics - stream data into data warehouse (Redshift).

Customer order placement calls are only successful if write-side actor accepts the write.

Split brain resolver - custom, static majority.

[pram]: https://jepsen.io/consistency/models/pram

## Load testing approach

JMeter, with the following scenarios:
1. Normal customer traffic, current load <-- can we at least deploy now, and work on perf later
2. Normal customer traffic, 10x load <-- success criteria
3. Normal customer traffic, all in till it breaks
4. Pessimistic traffic shape - all customers target same entity, current load <-- defensive
5. Pessimistic traffic shape - all in till it breaks

# Interesting things that went bad before the launch - and how we fixed them

The goal here is not to walk through all the issues, but highlight the relevant ones. I.e. "reservations skewed toward
the last shift because of XYZ" is not relevant to broad audience, but stuff about akka, CQRS and event-sourcing is.

Basically, technical/infra problems, not business issues.

## Distributed data not performing well

DData was not performing well - hit a plateau at about 2.5x current traffic. What's worse, cluster almost always 
desintegrated itself under this load, and required manual restart.

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

# All the things that went wrong after the launch
 
## Wednesday Cassandra crush

Around three moths after the launch. Mystery - every week at 8am Wednesday, Cassandra (used as persistence store) would
crash, fail the persistence write, crash the persistence plugin and the whole system stopped working - until manual
restart.

How did we found out - system health monitoring.

What was the root cause - (TBD: I don't recall exactly, please halp). Triggering event was something to do with Cassy 
stop-the-world GC[^2]. rott cause was some other service that were using Cassy as persistence store for akka actors,
but used Akka Singleton instead. Singleton accumulated huuuuuuge state and that was what was causing the GC to fire
more frequently, and take more time.

[^2]: at that moment devops suggested that-cassandra-implementation-in-C, but it never happened - probably neither us 
nor them were brave/crazy enough to actually go for it.

How did we solve it: it's a shame, but we just shut down that other service. At that point it was generally understood
that it's function was not necessary - due to changed business constraints. However, this decision returned to bite us
all - but that's probably a topic for a separate blog post.

## Wednesday Cassandra crush, again

... and not on Wednesday, but otherwise it was the same problem, actually.

How did we found out - the same way as previous one. 

Root cause: same - long GC pauses in Cassy. This time it was an application that pioneered akka and akka-persistence 
in the organization. Unfortunately, it haven't received much care since then - original authors left, and new owners
practiced "not broken - don't touch" a little bit too much. As a result, it used a very outdated version of cassandra
plugin, that used Cassy materialized views to implement certain features. That application received high traffic - it 
collected GPS tracks for all the vehicles, causing frequent updates to materialized views.

How did we solve it: shame again, but again we shut it down. Initially it was done as an emergency response, assuming
that current owners would update the app and turn it on again; unfortunately the "turn on" part never happened, AFAIK.

# Evolving the system (and how design choices helped)

## Multidrops project

Another read side (?) in Cassandra, optimized selection of buckets, limited re-opimization.

Required a couple of events/snapshots migrations - briefly describe potential approaches in gaeneral + how it worked
for us. 

Outcome: project that drives significant cost savings and logistics efficiency improvements

## Lazada integration

Non-func:
* <100ms 99th @ 10x current traffic
* 100% availability

GRPC + protobuf

GC tuning - less stop-the-world, faster GC in general. Analysis: JMX extension to plug into existing metrics collection
infra + Graphana dashboards (TODO: ask WX to capture some GC dashboard screenshots, if possible). Tuning: switched 
to CMS (or _from CMS_?), tuning GC parameters.

Was artery added at that time, or shortly after?

Outcome: integrated in time, sustained up to 50x production traffic at pre-launch load test. Recently, during spike of
load in COVID and operational constraints, was able to seamlessly handle almost 40x "normal" traffic in the wild 
(put a graph?)

# Other thoughts

## Pick serialization carefully

Forward/backward compatibility
Serialization speed - not only for persistence, but for cross-node communication as well.
Human-readable vs. compactness

## Time-travel, replaying events

Not that straightforward to achieve in practice - need to know how to handle all the versions.
Never needed in practice though (although we didn't have to build new read-sides from the beginning of time).

## Other risks

Was able to corrupt Akka Sharding coordinator state once - only way to restore service is to manually wipe coordinator's
persistence. On a good side, there's a "script" shipped with Akka to do so, and no "user data" is actually lost - 
coordinator only controls where entities are placed, so just starting anew is a good recovery strategy.
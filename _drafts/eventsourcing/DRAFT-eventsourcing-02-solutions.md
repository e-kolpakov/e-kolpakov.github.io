---
layout: post
title: "Journey through eventsourcing: Part 2 - designing a solution"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/DRAFT-eventsourcing
series_sequence_nr: 2
key_takeaway: "eventsourcing/02-designing-a-solution-key-takeaway.md"
image: /assets/img/eventsourcing/DRAFT-eventsourcing-02-designing-a-solution/cover.png
---

TBD

[Back to Table of Contents]({% link design/eventsourcing-series.md %}#table-of-contents)

# Recap: Declared project goals

**Functional goals**

* "Strong" consistency model for placing an order - overbooking must not happen, even in case of many concurrent 
    customer requests and/or failure of service nodes.
* Build better tools for planning team to manage the logistics capacity
    * Change the way capacity was represented in the system
    * Account for multiple typs of capacity (logistics, warehouse, etc.)
    * Build more user-friendly tools for visualizing and modifying capacity

**Availability**
* Service Level Agreement (SLA) - 99.9% aka 3 nines
* Service Level Objective[^1] (SLO) - 99.99% aka 4 nines

**Performance**
* <100ms 99th percentile for both reads and writes
* maintain the above at up to 10x the current *peak second* load for long periods of time[^2].

**Fault tolerance**

* System should be able to survive one node crash/restart without interrupting service
* During *planned restart*, no customer requests can be lost except requests beind processed on the restarted 
    node.
* During node *crash*, the system is allowed to loose part of the customer requests for a brief period of time - 
    3-5 minutes at most; after that system must restore full functionality without human intervention. 
    
    
Let me emphasize (and explain) the throughput requirement a bit: we've taken the highest rate of requests observed, and
declared that the new solution would be able to maintain 10x that rate "indefinitely". So this was a very ambitious 
goal - and, frankly speaking, a bit overambitious :)

[^1]: SLA is usually "published" metric level, while "SLO" is the "internal goal". In our case, SLA was not communicated
    extenrally, but was our "promise" to the business and sibling teams; SLO was something that we aimed for
[^2]: how long exactly was never explicitly mentioned, but for practical reasons we targeted one hour

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
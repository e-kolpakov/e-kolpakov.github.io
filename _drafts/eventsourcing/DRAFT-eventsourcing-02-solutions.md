---
layout: post
title: "TBD: eventsourcing solutions"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/DRAFT-eventsourcing
series_sequence_nr: 2
---

TBD

[Back to Table of Contents]({% link design/eventsourcing-series.md %}#table-of-contents)

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
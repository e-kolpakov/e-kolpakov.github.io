---
layout: post
title: "TBD: eventsourcing implementation"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/DRAFT-eventsourcing
series_sequence_nr: 3
---

TBD

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
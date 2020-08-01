---
layout: post
title: "TBD: eventsourcing other notes"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/DRAFT-eventsourcing
series_sequence_nr: 8
---

TBD

[Back to Table of Contents]({% link design/eventsourcing-series.md %}#table-of-contents)

# Other thoughts

## Pick serialization carefully

Forward/backward compatibility
Serialization speed - not only for persistence, but for cross-node communication as well.
Human-readable vs. compactness

Serialization -- actually Kryo is a good answer, but the scala binding that provides serde for Scala specific
data structures sucks. For a significant example, it creates an immutable list (or vector?) in the begining, and
add element to it one by one as it recieves. An alternative solution would be have some size hint in the beginning
and create a mutable list (or array) to host them all. Also when using Kryo to serialize for those Akka persistence
events, be sure to choose the backwards compatible way (compatible field serializer). It's not the default one on
the samples on those other blogs. Be careful on this! Almost all the other parts on those blogs are correct, e.g.
bind them manually, not letting Kryo infer the type of class etc. On a side note, Alibaba is trying to use Kryo but
they are using it in a default (Kryo default) way that assumes classes with a same FQCN are the same. Guess it's fine
for them as long as they use it only for RPC and maintain the versioning of API themselves.

## Time-travel, replaying events

Not that straightforward to achieve in practice - need to know how to handle all the versions.
Never needed in practice though (although we didn't have to build new read-sides from the beginning of time).

## Monitoring and dahsboards

ELK:

* Logs
* Dashboard

Graphana:
* Standard package from devops - CPU, mem, network traffic, etc.
* Calls to each endpoint
* Latency
* Deeper, business oriented metrics
* Garbage Collection, mem

Alerting:
* From Graphana to slack => long latency
* Load balancer - non-200 responses on the health endpoint
    * Normally just "liveness" metric. We also plugged in some "usefulness" into it - are all expected actors running
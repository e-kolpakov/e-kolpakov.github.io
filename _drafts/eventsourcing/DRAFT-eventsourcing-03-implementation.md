---
layout: post
title: "TBD: eventsourcing implementation"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/DRAFT-eventsourcing-03-implementation/
series_sequence_nr: 3
key_takeaway: "eventsourcing/03-implementation-key-takeaway.md"
image: /assets/img/eventsourcing/DRAFT-eventsourcing-03-implementation/cover.png
---
{% include infra/series-nav-link-variables series_tag="eventsourcing-series-2020" series_sequence_nr=page.series_sequence_nr %}

TBD

IDEA: the previous post might left you wondering - "looks like you guys just traded implementing locks and caches, 
to implementing clustering, automatic recovery and failure detection - and those are more complex problems". This is
true - all these concerns would need to be handled in order for the app to work. However, we haven't had to build them
ourselves - and in fact our decision making in the architecture phase was based on the fact that there is a library
that handles all these things for us - Akka.

This chapter will be less general/abstract/hand-wavy. So, Let's get dangerous

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# Akka Overview

Akka is a framework that brings Actor Model to Java and Scala. It is _mostly_ open-source and free to use, but there is
a commercial company behind it - Lightbend - founded by the creator of Akka, Jonas Boner.

## Actor model crash course

https://docs.google.com/presentation/d/1A8-WbyQU3nPmChF_YHJhAGcsHhPWt4JZyOTfPqt8ghQ#slide=id.g5c96e3f8dd_0_391
https://docs.google.com/presentation/d/1A8-WbyQU3nPmChF_YHJhAGcsHhPWt4JZyOTfPqt8ghQ#slide=id.g5c96e3f8dd_0_400

Actor is a unit of computation. Actors receive, process and send messages, and sending a message is the only way to 
communicate with an actor. Might have internal state, which is isolated from environment (actor system) and other actors.

Actors come in hierarchies - each actor[^1] has a parent, and parents supervise their children. If a child 
~~misbehaves~~ throws an exception, parent has to ~~lecture it~~ decide what to do - restart the child, suppress the 
exception and let the child continue, or panic too and propagate the exception up the hierarchy. Supervision provides 
fault compartmentalization, tolerance and recovery.

[^1]: "the one who walks the bubbles of space and time". Cool, mysterious, maybe it has a sword.

## Higher-level Akka components

https://docs.google.com/presentation/d/1A8-WbyQU3nPmChF_YHJhAGcsHhPWt4JZyOTfPqt8ghQ#slide=id.g5c96e3f8dd_0_406

"Raw" actors are available to developers, but there are also Akka HTTP, Streams, Persistence and Cluster. Cluster has
"sub-plugins": Singleton, Sharding and Distributed Data.

Streams: https://docs.google.com/presentation/d/1zaRG0x307_B7zHNlHSLcN-bCowonoD3G3LbFXh72O4c#slide=id.g3ffe535a95_0_211
HTTP: https://docs.google.com/presentation/d/1zaRG0x307_B7zHNlHSLcN-bCowonoD3G3LbFXh72O4c#slide=id.g3ffe535a95_0_175
Persistence: https://docs.google.com/presentation/d/1zaRG0x307_B7zHNlHSLcN-bCowonoD3G3LbFXh72O4c#slide=id.g3ffe535a95_0_223
Singleton: https://docs.google.com/presentation/d/1zaRG0x307_B7zHNlHSLcN-bCowonoD3G3LbFXh72O4c#slide=id.g3ffe535a95_0_235
Sharding: https://docs.google.com/presentation/d/1zaRG0x307_B7zHNlHSLcN-bCowonoD3G3LbFXh72O4c#slide=id.g415fdb2fc6_0_107
Distributed Data: https://docs.google.com/presentation/d/1zaRG0x307_B7zHNlHSLcN-bCowonoD3G3LbFXh72O4c#slide=id.g3ffe535a95_0_253

# How this all fit together

![Intentionally overwhelming diagram - we'll gradully build it further
]({{ page.image_link_base }}/high_level_architecture-full.png)
{:.lead}

Let's revisit the aspects from the previous post in more detail: Consistency, Availability, Request handling, Persistence
and Performance - albeit in a slightly different order.

## Persistence

TODO: same diagram with highlighted Persistence and Sharding, etc.

Akka Persistence + Sharding.

Persistence basically implies either a single node (not highly available) or Sharding. Persistence is what actually 
implements eventsourcing, Sharding ensures there are no copies of an entity with different state (which can diverge, 
and corrupt event stream).

`persistAsync` exists, but _very_ risky - actor updates state and responds to 
the caller right away. If persistence fails - lost update, correctness issue.

## Consistency

TODO: same diagram with highlighted Actor and Sharding, etc.

Entity (capacity pool is encapsulated and fully managed by an actor. 
Akka Actor - "single-threaded" execution of the inner logic. No shared data, no concurrent processing.
Akka Cluster Sharding - single instance of each actor.
Result: sequential consistency model. TODO: Linearizeable or Sequential???

Split brain resolver - custom, static majority.

## Availability

TODO: same diagram with highlighted Sharding, Sharding Coordinator and Failure Detector etc.

Sharding - recovery of failed nodes is automatic.
"Graceful" shutdown - almost immediate
Crash - need some time to detect (phi-accrual detector), during that time affected entities are not available.

## Request handling

TODO: same diagram with highlighted Sharding, Cluster Messages and DData, etc.

Write:
Sharding - transparently pass messages between the nodes if sender and receiver is on the different nodes.
Actor - internal state forms a "register". Write operations are essentially "check if lower than" (read) and "update" 
(write). Can be seen as compare-and-set, but with a "relaxed" condition - less-than-and-set.
Customer order placement calls are only successful if write-side actor accepts the write. Read sides are updated 
asynchronously. 

Read:
Read side is Map stored in an Akka Distributed Data - replicated across all nodes in the cluster. Updates are delivered
in an asynchronous way. Reads storage have relaxed consistency (looks like [PRAM][pram]) on their own and are eventually
consistent with writes.

Another read side for near-real-time monitoring and analytics - stream data into data warehouse (Redshift).

[pram]: https://jepsen.io/consistency/models/pram

## Performance

TODO: same diagram with highlighted Actor, Persistence and DData, etc.

Actor - in memory state
Persistence - append-only write to DB.

# Key takeaways

{% include {{page.key_takeaway}} %}

# Wrap up

TBD

In {% include infra/conditional-link.md label="the next post" url=next_post %}, 

---
layout: post
title: "Journey through eventsourcing: Part 3 - initial implementation"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/DRAFT-eventsourcing-03-implementation
series_sequence_nr: 3
key_takeaway: "eventsourcing/03-implementation-key-takeaway.md"
image: /assets/img/eventsourcing/DRAFT-eventsourcing-03-implementation/cover.png
---
{% include infra/series-nav-link-variables series_tag="eventsourcing-series-2020" series_sequence_nr=page.series_sequence_nr %}
[The previous post][previous-post] might have left you wondering - we have decided to reject the widespread and 
battle-tested architectures based on locking, caches, and transactions to something that needs clustering, automatic 
recovery and failure detection. This is true - the architecture we have picked has to have these features for 
the application to work. However, we haven't had to build them ourselves - our decision making was based on 
an existing third-party library that can handle all these things for us - [Akka][akka]. Let's take a look at how 
we used it to achieve the project goals.

This chapter will be more concrete, with lots of diagrams and some links to the code examples. So,

![let's get dangerous]({{ page.image_link_base }}/darkwing_duck.jpg)

Brace for the long-read. :smile:

[previous-post]: {{ prev_post }} 
[akka]: https://akka.io/

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# Akka Overview

Simply put, [Akka][akka] is a framework that brings [Actor Model][actor-model] to Java and Scala. It is _mostly_[^1] 
open-source and free to use, but there is a commercial company behind it - [Lightbend][lightbend], founded by the 
creator of Akka, [Jonas Boner][jonas-boner].

In the actor model, an actor is a unit of computation. Actors receive, process and send messages, and sending 
a message is the only way to communicate with an actor (i.e. no function calls, no shared data, etc.). 
Actors can have an internal state that is isolated from the rest of the application, including other actors and 
actor runtime environment (which is called _actor system_).

Actors come in hierarchies - each actor has a parent (except the one at the top of hierarchy[^2]) and parents supervise
their children. If a child ~~misbehaves~~ throws an exception, a parent has to ~~lecture it~~ decide what to do - 
restart the child, suppress the exception and let the child continue from where it was, or succumb to panic and 
propagate the exception up the hierarchy. Supervision provides fault compartmentalization, fault tolerance, and 
fault recovery.

Actors and messaging are the Akka's core features, and there exist several higher-level components that build on 
top of the actors and messaging - such as Akka Streams, Akka Cluster, and so on. These higher-level components, 
in turn,power application frameworks, such as [Lagom][lagom] and [Play][play-framework]. And, like if it wasn't enough,
there's an [Akka Platform][akka-platform] that encompass all of it, add more features, and put this whole thing to 
the complexity level that calls for commercial support. That's how you build a business[^3] :smile:

See also: [Actor model][actor-model-slides], [Akka actors][akka-actors-slides],
[my old presentation][akka-modules-slides]  about this project and Akka's role in it (with code examples!)

[^1]: There exists a few commercial closed-source Akka plugins.

[^2]: also known as ["the one who walks the bubbles of space-time"][walker] (or more [colorful version][walker-classic] 
    in the Akka-classic documentation). Cool, mysterious, maybe it has a sword.

[^3]: Darkwing Duck is a spin-off of Duck Tales, which is a spin-off of Donald Duck, which is a spin off of 
    Mickey Mouse... That's how Disney became a media empire :smile:

[actor-model]: https://en.wikipedia.org/wiki/Actor_model
[lightbend]: https://www.lightbend.com/
[jonas-boner]: https://www.linkedin.com/in/jonasboner/
[actor-model-slides]: https://docs.google.com/presentation/d/1A8-WbyQU3nPmChF_YHJhAGcsHhPWt4JZyOTfPqt8ghQ#slide=id.g5c96e3f8dd_0_391
[akka-actors-slides]: https://docs.google.com/presentation/d/1A8-WbyQU3nPmChF_YHJhAGcsHhPWt4JZyOTfPqt8ghQ#slide=id.g5c96e3f8dd_0_400
[akka-modules-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g28a798284c_0_44 
[walker]: https://doc.akka.io/docs/akka/current/general/addressing.html#what-is-an-actor-reference
[walker-classic]: https://doc.akka.io/docs/akka/current/supervision-classic.html#the-top-level-supervisors
[lagom]: https://www.lightbend.com/lagom-framework-part-of-akka-platform
[play-framework]: https://www.playframework.com/
[akka-platform]: https://www.lightbend.com/akka-platform

# How this all fits together

In our project we were limited to open-source Akka features only. Moreover, even though the Play framework was widely 
adopted in the company at that moment, we decided to not use it and work at a lower level instead - using components, 
not frameworks. This was done mainly because web application frameworks center the application around handling 
Web/HTTP/REST/etc. requests and we wanted it to be structured around application logic, clustering, and persistence.

Here's what we ended up with:

[
    ![
        Intentionally overwhelming diagram - we'll gradually build it in the following sections.
        There are two (and potentially more) service instances. Instances host multiple components - most notable are
        HTTP RPC API - backed by Akka HTTP, and Cluster Components - backed by Akka Cluster Sharding and 
        Akka Cluster Distributed Data.
        Akka Cluster Sharding (or simply Sharding) hosts multiple shard regions, each containing multiple Actors.
        Service instances exchange "Cluster messages".
        Each actor encapsulates a unique "Capacity Pool" domain entity. Entities are not repeated between actors, shard
        regions or instances.
        Additionally, there are Failure Detector, Remoting, Analytics Stream and Persistence components in the service
        instance, but outside Cluster Components.
        Outside instances, there is an external load balancer (AWS ELB) that balance requests between instances HTTP 
        interfaces, Cassandra database and Redshift data warehouse. Persistence component inside the instances connects
        to Cassandra, and Analytics stream connects to Redshift.
    ]({{ page.image_link_base }}/high_level_architecture@1x.svg)
]({{ page.image_link_base }}/high_level_architecture@2x.svg)
{:.lead}

This diagram is a bit overloaded, but that's intentional - it shows all the Akka's and custom-built features that 
contributed to our goals and serves as a map of the overall solution, in all its complexity. Worry not if it's 
a bit overwhelming or complex to grasp - in the following sections we'll slice it into smaller, more 
comprehendible "projections".  

Let's revisit [the application aspects][aspects] from the previous post in more detail: Consistency, Availability, 
Request handling, Persistence, and Performance - albeit in a slightly different order.

**Note:** At that time, [Akka Typed][akka-typed] was in the "experimental" state. It reached maturity after the project
was mostly complete, and we had little practical incentive to rewrite it using Akka Typed. So all the code examples 
are in the [Akka Classic][akka-classic] flavor, which is still supported and can coexist with Akka Typed, and 
general ideas are still relevant (as of July 2020).

[aspects]: {{prev_post}}#final-architecture
[akka-typed]: https://doc.akka.io/docs/akka/current/typed/actors.html
[akka-classic]: https://doc.akka.io/docs/akka/current/index-classic.html

## Persistence

[
    ![
        Same diagram with the persistence-related slice of the system hightlighted:
        Actors (each actor encapsulate single domain entity), Persistence component, Cassandra database
        Persistence is connected with a bidirectional arrow to Cassandra.
    ]({{ page.image_link_base }}/persistence@1x.svg)
]({{ page.image_link_base }}/persistence@2x.svg)
{:.lead}

Persistence aspect is the one at the core of the solution - it enables the rest of it and at the same time requires 
certain mechanisms to be in place to function properly.

In our scheme, persistence is handled by the [Persistent Actors][akka-persistent-actor] - Akka's approach to saving the
Actor state. This is the part that implements eventsourcing - Persistent Actors keep their state in memory, and only 
reach out to the database in three cases:

* When a state-mutating _command_ is received, the actor first validates and converts it into an _event_, then writes 
    the event to the database.
* To periodically take a snapshot of the state and write it to the persistence.
* When an actor (re)starts, it reads it's the latest snapshot and all the events saved after it.

One caveat is that Akka Persistence requires that at most one single instance of each persistence actor to be run. 
Otherwise, since there is no state synchronization mechanism between copies[^4], the two instances' states can diverge -
leading to incorrect execution of the business logic, inconsistent responses, saving "conflicting" events, 
and eventually corrupting entity state. However, having an at most one copy of an entity is exactly what we wanted 
for the concurrency reasons, so this was not an issue for us.

The above guarantee is trivially provided in a single service instance (non highly available) scenarios, but is more 
challenging in case of multiple instances (highly available). Thankfully, Akka has a built-in solution for such cases - 
Akka Cluster Sharding. We'll take a closer look at it in the [Consistency](#consistency) section.

See also: [Akka Classic Persistence example code][akka-persistence-slides]

[akka-persistent-actor]: https://doc.akka.io/docs/akka/current/persistence.html

[^4]: unless you create your own and solve all the associated issues, such as merging concurrent updates.

## Consistency

[
    ![
        Same diagram highlighting components that contribute to the solution consistency:
        Actors, Sharding and Shard Regions
        Persistence is connected with a bidirectional arrow to Cassandra.
    ]({{ page.image_link_base }}/consistency@1x.svg)
]({{ page.image_link_base }}/consistency@2x.svg)
{:.lead}

To recap: during the design phase, [we found out][consistency-analysis] that the required consistency model for writes is 
Sequential consistency, or stronger. Three mechanisms contribute to achieving this level of consistency:

* [Akka actors][actors-intro] alleviate the need for explicit locking and concurrency management - or, simply put, each
actor processes a single message at a time, and only pulls the next message when the current one is fully processed.
* Actors encapsulate their state, so it is not possible to access the state (even for read purposes) except to send a 
    message to an actor, and (maybe, if the actor decides so) receive a response.
* Akka Cluster Sharding makes sure that there is at most one instance of each actor running in the cluster.

These three together mean that any given actor state is only accessed in a serialized fashion - there is always at most
one thread that runs the actor[^5], and there are no other instances of this actor elsewhere.

Sharding requires a couple of mechanisms to work properly:

**Unique identity:** each sharded actor must have a unique identifier, to tell it from the other actors.
What's great is that there is an immediate synergy between Akka Cluster Sharding and Akka Persistence - persistence 
also needs a unique identity, and it is very natural (and works great) to use the same ID for both.

**Match actors and messages to shards:** Akka Cluster Sharding creates many shards (called Shard Regions) 
that host sharded actors. Sharding needs to be able to decide which Shard Region hosts which actor - most common 
approach is to use [consistent hashing][consistent-hashing] over the entity ID (and there's an Akka built-in function
to do so). The same applies to messages - each message has a recipient, and if the recipient is a Sharded actor, 
Akka needs to out find in which Shard the actor resides. The simplest way is to include the target actor identifier 
into the message and reuse the same consistent hashing function.

**Partition-tolerance:** Sharding makes sure that there is at most one instance of an actor in the cluster... but it 
cannot make sure that there are no _other_ clusters that run the same actor. So it becomes a responsibility of the
application to prevent such cases (also known as split-brain scenarios). Akka Cluster provides the means to detect and 
prevent this - there are membership and downing mechanisms baked into the Cluster itself. Lightbend recently 
open-sourced their previously proprietary [Split Brain Resolver][split-brain-resolver], but at the time we built this
system it was still not available. So we rolled our own, based on a ["static quorum" approach][static-quorum].

See also: [Akka Classic Sharding example code][akka-sharding-slides]

[consistency-analysis]: {% post_url design/2020-07-14-eventsourcing-02-solutions %}#consistency-analysis
[actors-intro]: https://doc.akka.io/docs/akka/current/typed/actors.html#akka-actors
[consistent-hashing]: https://en.wikipedia.org/wiki/Consistent_hashing
[split-brain-resolver]: https://doc.akka.io/docs/akka/current/split-brain-resolver.html
[static-quorum]: https://doc.akka.io/docs/akka/current/split-brain-resolver.html#static-quorum

[^5]: This is outside of the scope of the discussion, but Akka actor system uses an event loop for concurrency - 
    so _by default_ actors are scheduled to run on a shared pool of threads. There are configuration settings to adjust 
    this though - so "one thread-per-actor" is also achievable, but rarely justified. 

## Availability

[
    ![
        Same diagram highlighting components that contribute to the solution availability:
        External load balancer (AWS ELB) directs customer requests to the healthy nodes
        Akka's failure detector detects node crashes and notifies the rest of the cluster.
        Cluster Sharding coordinator keeps orchestrates the reallocation of Shard Regions from failed/left nodes to
        the healthy ones.
        Distributed Data serves a replicated cache of capacity pools' counters to a readonly requests 
    ]({{ page.image_link_base }}/availability@1x.svg)
]({{ page.image_link_base }}/availability@2x.svg)
{:.lead}

As I've [mentioned previously][system-cp], we were leaning towards a consistent and partition-tolerant system 
(aka **CP**). However, while our main goal was to ensure consistency, we also wanted the system to be as available as
possible - because the unavailable system is _safe_ (it doesn't do any bad), but not _useful_ (it doesn't do any good).

Here we "cheated" a bit - we figured out that it is acceptable to have two "relaxations" to the availability definition:

* [Reads can have relaxed consistency][relaxed-consistency-reads] - this allows serving some stale data to improve 
    availability.
* Split-second unavailability is not noticeable to the customers so we can afford 
    ["fail fast&recover fast"][fail-and-recover-fast] approach.
    
The **relaxed consistency for reads** is backed by the [Akka Cluster Distributed Data][akka-distributed-data]. 
Simply put, we used it to replicate the actor's internal state (which is essentially just a few counters) across 
all the system's nodes. Distributed Data is backed by the so-called [Conflict-free Replicated Data Types][crdt] (CRDTs). 
In our case, since we already made sure there's only one writer to every capacity counter, we just used 
the Last-Writer-Wins Map.

The **fail fast & recover fast** is achieved through a combination of multiple systems:

* The first line is the existing load-balancer infrastructure, that detects failing nodes and direct customer traffic 
    to the healthy ones. 
* At the application itself, we relied on the Akka's built-in mechanisms for [graceful leaving][graceful-leave] 
    the cluster in case of planned downing and [failure detection][failure-detector] for all other cases. In both cases, 
    Akka Cluster Sharding would perform an automatic recovery of the affected actors.
* Finally, since our goal was to [loose almost none customer requests][lost-requests] during planned node restart - 
    we wanted to minimize the time between actors going down on one node, and being recovered and ready to serve 
    traffic on the other. This was initially achieved via [eager initialization of
    Persistence plugin][akka-persistence-eager] and [remembering entites][remembering-entities] in the Shards, 
    but (_spoiler alert_) this turned out to not be optimal. More details on this 
    {% include infra/conditional-link.md label="in the next post" url=next_post %}

[system-cp]: {% post_url design/2020-07-14-eventsourcing-02-solutions%}#cap-theorem
[relaxed-consistency-reads]: {% post_url design/2020-07-14-eventsourcing-02-solutions%}#consistency-analysis
[fail-and-recover-fast]: {% post_url distributed/2020-02-23-single-point-of-failure-is-ok %}#key-observation
[akka-distributed-data]: https://doc.akka.io/docs/akka/current/distributed-data.html
[crdt]: https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type
[failure-detector]: https://doc.akka.io/docs/akka/current/typed/failure-detector.html
[lost-requests]: {% post_url design/2020-07-14-eventsourcing-02-solutions %}#recap-declared-project-goals
[next-post]: {{ next_post }}
[akka-persistence-eager]: https://doc.akka.io/docs/akka/current/persistence-plugins.html#eager-initialization-of-persistence-plugin
[remembering-entities]: https://doc.akka.io/docs/akka/current/cluster-sharding.html#remembering-entities
[graceful-leave]: https://doc.akka.io/docs/akka/current/typed/cluster.html#leaving

See also: [Akka Classic Distributed Data example code][akka-distributed-slides]


--------------------------------------Move to the next post-------------------------------------------------------------

## Request handling

[
    ![
        Same diagram highlighting components that participate in handling the requests:
        Business logic is encapsulated in the Capacity Pools, which are hosted inside actors.
        A read-only cache of capacity counters is stored in the Distributed Data and replicated on all nodes.
        External load balancer communicates with the HTTP RPC API, built atop Akka HTTP and Akka Streams.
        State updates are streamed into Redshift via Akka Stream
    ]({{ page.image_link_base }}/request_handling@1x.svg)
]({{ page.image_link_base }}/request_handling@2x.svg)
{:.lead}

The service only does three things:

* "Get Availability" - read-only, but need to gather information from all the currently active capacity pools that
    match customer location, returns a list of available capacity pools.
* "Reserve capacity" - write, executed when a customer places an order, targets one particular capacity pool, and 
    that the pool is passed in the call, returns the so-called _Reservation ID_.
* "Release capacity" - write, executed when a customer cancels the order, targets one particular capacity pool, but
    the request only contains _Reservation ID_, the pool that "owns" that reservation needs to be found internally.
    
All three are exposed as HTTP RPC interface[^6], using json payloads and built using Akka HTTP. Compared to other Akka
tech, this wasn't a "strategic" choice - any other HTTP library would do (e.g. [HTTP4s][http4s] or [Finagle][finagle]).
But we were already heavily on the Akka and Akka HTTP matched our goals, development philosophy, so it was a "sensible 
default" choice that worked out well.

Ok, here is the fun part. I've mentioned a couple of times that we have different consistency models for reads and 
writes, and that means that we have different mechanisms to serve read and write queries. Yep, that's right - that's 
[CQRS][fowler-cqrs]. We had one "write side", and two "read sides".

See also: Akka HTTP example ([server][akka-http-server], [client][akka-http-client])

[http4s]: https://http4s.org/
[finagle]: https://twitter.github.io/finagle/
[fowler-cqrs]: https://martinfowler.com/bliki/CQRS.html
[akka-http-server]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g4533344fef_0_27
[akka-http-client]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g4533344fef_0_83

[^6]: it is _almost_ REST - the "Get Availability" query needed to pass complex parameters, so we made it 
    a POST request

### Write side

Let's start with the **"reserve capacity"** call. This endpoint was backed by the sharded actors, each running a single
capacity pool. The request carried the capacity pool identifier, which was also used part of an actor name, sharding ID,
and persistence ID. Thus sending a "reserve capacity" command to the target entity (and actor it is hosted in) was as
 simple as just constructing the message and sending it to an actor... except the actors were sharded.

Since there is only one instance of an actor, but many instances of the HTTP API (each service node had one), 
most of the time the target actor would **not** run on the instance handling the request - but on a _different_ one.
The good thing is that this situation is a first-class concern in the Akka Sharding, so finding where the actor is,
serializing the message, sending it to the other instance, deserializing and delivering it to the recipient actor
 happens transparently to the message sender - and the same happens with the response. This requires that all the 
messages are serializable, but there are pretty straightforward mechanisms in Akka that support that: 
[Akka Serialziation][akka-serialization]. We ended up picking [Kryo serialization][kryo] - in retrospect, this was a
 decent, but not the best choice - it added some minor friction and backward/forward compatibility concerns; protobuf
  likely would work better.

Other than this purely technical complications, the business logic for the "reserve" command initially was very simple - 
essentially it was just "compare-and-set" with a "relaxed" condition - more like "less-than-and-set". The very first
implementation reflected that - the logic was "baked in" into the actor itself. However, we quickly realized that we
would evolve the logic in future (more on this evolution in a later post), and extracted the logic into a dedicated
business model, encapsulated and managed by the actor - this gave us the clear separation between business logic, and
supporting messaging, command-handling and persistence infrastructure.

The **release capacity** command worked roughly the same - we needed to route the "cancel" command to the actor that
owned the reservation. The additional challenge was that the request only had a _reservation ID_, not the capacity pool
identifier. To solve this problem, the initial implementation was to keep the `Reservation ID => owner actor`  roster
in the replicated Distributed Data LWWMap (Last Writer Wins Map). The API controller would just look up the actor in
the roster, construct the cancellation message, and send it. Jumping a bit forward, this wasn't a final version - 
it worked well from a functional perspective, but couldn't meet our non-functional requirements. I'll cover it in more
detail in {% include infra/conditional-link.md label="the next post" url=next_post %}.

[^7]: For the curious, there's [a diagram][capacity-services-diagram] in my old presentation that gives a glimpse of
    other systems involved in handling the requests.

[akka-serialization]: https://doc.akka.io/docs/akka/current/serialization.html
[kryo]: https://github.com/EsotericSoftware/kryo
[capacity-services-diagram]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g3dacb4d84b_0_0

### Read sides

The first read side was there to power the**get availability** query is again a replicated Distributed Data LWWMap. 
Simply put, it was just a lookup table with a capacity pool identifier as keys and remaining capacity as values. 
The read controller would just get the entire map from Distributed Data, scan the map and iterate over the records
to find the relevant ones. This might sound inefficient, but in practice, there was little reason for a more 
"intelligent" querying - the total number of records in the map was never larger than a few hundred.

The second read side was not wired into an API endpoint but streamed the updates into the data warehouse 
(AWS Redshift), for analytics and near-real-time monitoring. The data sent there was roughly the same as the one in
the Distributed Data, except it didn't have a "destructive update" character - the DData map only kept the latest
value, while the analytics stream and underlying storage kept all the intermediate states.

With the read sides, we also took a couple of shortcuts compared to the "canonical", best-practices CQRS implementation:

* Read sides need to be updated on each state change. Canonically, this is done via establishing a separate stream 
    of events from a persistence database to each of the read sides. While Akka supports that via
    [Persistence Query][akka-persistence-query], one of our sibling teams had a negative prior experience with it[^7].
    So instead, the call to notify the read side was done right from the write-side actor.
* "Analytics stream" might bring "Kafka", "Kinesis" or "Spark" associations into your mind, but it was nothing that 
    fancy :smile:. Each service instance would have an Akka Stream, with an actor on the source side, and a DB
    writer powered by the Redshift JDBC driver on the sink side. Write-side actors would just send messages to the
    Stream's source actor in a fire-and-forget fashion (i.e. won't wait for the response or confirmation), 
    and the stream would handle the actual writes, buffering, and backpressure.
    
[^8]: For the curious - due to relatively large delay between publishing an event and seeing it at the read side 
    updater (average ~200ms, spikes up to 500ms), and a scary word "polling" 
    [in the documentation][akka-persistence-query-polling].

[akka-persistence-query]: https://doc.akka.io/docs/akka/current/persistence-query.html
[akka-persistece-query-polling]: https://doc.akka.io/docs/akka/current/persistence-query.html#eventsbypersistenceidquery-and-currenteventsbypersistenceidquery

## Performance

[
    ![
        Same diagram highlighting components that participate in handling the requests:
        Distributed Data - capacity pools cache
        Actors - keep state in-memory
        Akka Persistence - DB is on a "sequential" path only for state updates, but not for reads
    ]({{ page.image_link_base }}/performance@1x.svg)
]({{ page.image_link_base }}/performance@2x.svg)
{:.lead}

It's hard to talk about performance in the "theoretical" fashion - on one hand, one has to do it to choose the right
design and architecture for the system - the one that would achieve the necessary performance. On the other hand,
virtually everything in your app contributes to the performance, so issues might come from unexpected places - which
means the only tangible way to approach performance is to measure and experiment.

We've practiced both "theoretical" and "practical" approach to performance - in this section I'll talk only about the 
"theoretical" part, and {% include infra/conditional-link.md label="the next post" url=next_post %} will shed some light
on the "practical" part. Spoiler: we saw some unforeseen consequences of our choices.

The core feature that contributes to the performance is the use of the eventsourcing approach in Akka Persistence. 
Simply put, the database is only accessed in three cases:

* When an actor performs state-changing action, it writes an event[^8] to the DB via Akka Persistence. One thing to note
    here is that events are never overwritten, so it allows picking the DB engine that tailored to such use 
    (e.g. [Apache Cassandra][cassandra], [RocksDB][rocks-db] or other [LSM-tree][lsm-tree] based DBs).
* When an actor (re)starts, it reads the "entire history" of events from the persistence store. Since actors (re)start
    is not a part of business-as-usual operations[^9], it has little impact on the performance - instead it somewhat 
    affects availability.
* To speed up the recoveries, actors can persist snapshots of their state, so that during recovery they fetch from the 
    DB and apply the events not from "the beginning of time", but only since the last snapshot.
    
As you can see, the eventsourced system with a long-living in-memory state accesses the DB _much less frequently_, and
when it does it has a more _efficient access pattern_ - append-only writing and "sequential read" reading.

However, there was one challenge that needed to be addressed separately. Even though serving read-only queries required
no interaction with the DB and theoretically would be "faster" (compared to the classical approach), 
the "Get Availability" query would need to poll all the currently active capacity pools. Naive implementation via
broadcasting the query to all the actors and merging back responses would result in a storm of messages sent - what is
worse, most of those messages would need to travel the network to other service instances.

To overcome this, we've introduced a separate [read side](#read-sides) powered by Akka Distributed Data, specifically
designed to avoid sending hundreds of messages over the network. With it, the "Get Availability" request turned into
a simple request-response interaction with a _local_ actor - the Distributed Data coordinator.

[^8]: pssst! The big secret here! It can also write a _command_, which turns this whole thing into 
    [command-sourcing][command-sourcing]!
    
[^9]: Unless Actor passivation is employed to conserve the memory. This wasn't the case for us though.

[command-sourcing]: https://stackoverflow.com/questions/6680135/event-sourcing-commands-vs-events
[cassandra]: https://cassandra.apache.org/
[rocks-db]: https://rocksdb.org/
[lsm-tree]: https://en.wikipedia.org/wiki/Log-structured_merge-tree
[akka-actor-passivation]: https://doc.akka.io/docs/akka/current/cluster-sharding.html#passivation

# Key takeaways

{% include {{page.key_takeaway}} %}

# Wrap up

To sum up: Akka let us build the business logic as if it was a single-threaded, single-machine system, while it is
used multiple threads, processors, and virtual machines. We still needed to solve some challenges associated with the 
distributed nature of the solution, but in a more explicit, well-defined and convenient way - the rest was provided by
Akka. The key technology enabler for this was the combination of Akka Cluster Sharding and Akka Persistence - the former
provided single writer guarantee without a single point of failure, and the latter implemented eventsourcing to support
rapid entity recovery and improved latency.   

{% include infra/conditional-link.md label="The next post" url=next_post %} will be devoted the initial pre-production
launch of the system, issues uncovered during the end-to-end testing and changes needed to be done to address these 
problems.

[akka-streams-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_211
[akka-http-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_175
[akka-persistence-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g4533344fef_0_99
[akka-singleton-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_235
[akka-sharding-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g4533344fef_0_109
[akka-distributed-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_253

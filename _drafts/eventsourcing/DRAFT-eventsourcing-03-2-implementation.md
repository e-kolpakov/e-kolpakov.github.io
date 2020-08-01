---
layout: post
title: "Journey through eventsourcing: Part 3.2 - implementation"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/2020-08-01-eventsourcing-03-implementation
series_sequence_nr: 4
key_takeaway: "eventsourcing/03-implementation-key-takeaway.md"
image: /assets/img/eventsourcing/2020-08-01-eventsourcing-03-implementation/cover-2.png
---
{% include infra/series-nav-link-variables series_tag="eventsourcing-series-2020" series_sequence_nr=page.series_sequence_nr %}
In [the first part][previous-post] we've taken a look at how Akka features help us achieve Persistence, Consistency
and Availability goals. In this part, we'll continue exploring the implementation and focus on how Akka helped in
handling the requests and achieving required performance levels. 

[previous-post]: {{ prev_post }} 
[akka]: https://akka.io/

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# Solution architecture

To recap, here's the overall scheme of the solution:

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

See also: [Akka Streams example code][akka-streams-slides]

[^8]: pssst! The big secret here! It can also write a _command_, which turns this whole thing into a
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
provided a single writer guarantee without a single point of failure, and the latter implemented eventsourcing 
to support rapid entity recovery and improved latency.   

{% include infra/conditional-link.md label="The next post" url=next_post %} will be devoted the initial pre-production
launch of the system, issues uncovered during the end-to-end testing and changes needed to be done to address these 
problems.

[akka-streams-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_211

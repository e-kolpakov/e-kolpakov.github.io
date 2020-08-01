---
layout: post
title: "Journey through eventsourcing: Part 3.1 - implementation"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/DRAFT-eventsourcing-03-implementation
series_sequence_nr: 3
key_takeaway: "eventsourcing/03-implementation-key-takeaway.md"
image: /assets/img/eventsourcing/DRAFT-eventsourcing-03-implementation/cover-1.png
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

# Solution architecture

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

# Wrap up

In {% include infra/conditional-link.md label="the second part" url=next_post %}, we'll take a look at the 
Request Handling and Performance aspects of the system.

[akka-streams-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_211
[akka-http-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_175
[akka-persistence-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g4533344fef_0_99
[akka-singleton-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_235
[akka-sharding-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g4533344fef_0_109
[akka-distributed-slides]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18#slide=id.g3ffe535a95_0_253

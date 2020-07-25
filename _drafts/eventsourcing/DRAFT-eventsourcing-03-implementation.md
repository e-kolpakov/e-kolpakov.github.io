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
battle-tested architectures based on locking, caches and transactions to something that needs clustering, automatic 
recovery and failure detection - these are more complex problems to solve, so was it a wise choice? This is absolutely
true - the architecture we have picked absolutely has to have these features for the application to work. However, we
haven't had to build them ourselves - in fact our decision making in the architecture phase was based on an existing 
third-party library that handles all these things for us - [Akka][akka]. Let's take a look how we used it to achieve
the project goals.

This chapter will be more concrete, with lots of diagrams and some links to the code examples (not the actual code 
though - it's a part of an intellectual property and must not be disclosed). So,

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

In the actor model, actor is a unit of computation. Actors receive, process and send messages, and sending a message 
is the only way to communicate with an actor (i.e. no function calls, no shared data, etc.). Actor can have an internal 
state that is isolated from the rest of the application, including other actors and actor runtime environment (which is 
called _actor system_).

Actors come in hierarchies - each actor has a parent (except the one at the top of hierarchy[^2]) and parents supervise 
their children. If a child ~~misbehaves~~ throws an exception, parent has to ~~lecture it~~ decide what to do - restart 
the child, suppress the exception and let the child continue from where it was, or succumb to panic and propagate 
the exception up the hierarchy. Supervision provides fault compartmentalization, fault tolerance and fault recovery.

Actors and messaging are the Akka's core feature, and there also exist a number of higher-level components that build on 
top of the actors and messaging - such as Akka Streams, Akka Cluster and so on. This higher-level components, in turn,
power application frameworks, such as [Lagom][lagom] and [Play][play-framework]. And, like if it wasn't enough, there's
an [Akka Platform][akka-platform] that encompass all of it, add more features, and put this whole thing to the complexity
level that calls for a commercial support. That's how you build a business[^3] :smile:

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

# How this all fit together

In our project we were limited to open-source Akka features only. Moreover, even though Play framework was widely 
adopted in the company at that moment, we decided to not use it and work at a lower level instead - using components, 
not frameworks. This was done mainly because web application frameworks centers the application around handling 
Web/HTTP/REST/etc. requests, and we wanted it to be structured around application logic, clustering and persistence.

Here's what we ended up with:

[
    ![Intentionally overwhelming diagram - we'll gradully build it further]({{ page.image_link_base }}/high_level_architecture@1x.svg)
]({{ page.image_link_base }}/high_level_architecture@2x.svg)
{:.lead}

This diagram is a bit overloaded, but that's intentional - it shows all the Akka's and custom-built features that 
contributed to our goals and serves as a map of the overall solution, in all it's complexity. Worry not if it's a bit 
overwhelming or complex to grasp - in the following sections we'll slice it into smaller, more comprehendable 
"projections".  

Let's revisit [the application aspects][aspects] from the previous post in more detail: Consistency, Availability, 
Request handling, Persistence and Performance - albeit in a slightly different order.

[aspects]: {{prev_post}}#final-architecture

## Persistence

[
    ![QWEQWEQWEQWEQWE]({{ page.image_link_base }}/persistence@1x.svg)
]({{ page.image_link_base }}/persistence@2x.svg)
{:.lead}

Akka Persistence + Sharding.

Persistence basically implies either a single node (not highly available) or Sharding. Persistence is what actually 
implements eventsourcing, Sharding ensures there are no copies of an entity with different state (which can diverge, 
and corrupt event stream).

`persistAsync` exists, but _very_ risky - actor updates state and responds to 
the caller right away. If persistence fails - lost update, correctness issue.

## Consistency

[
    ![QWEQWEQWEQWEQWE]({{ page.image_link_base }}/consistency@1x.svg)
]({{ page.image_link_base }}/consistency@2x.svg)
{:.lead}

Entity (capacity pool is encapsulated and fully managed by an actor. 
Akka Actor - "single-threaded" execution of the inner logic. No shared data, no concurrent processing.
Akka Cluster Sharding - single instance of each actor.
Result: sequential consistency model. TODO: Linearizeable or Sequential???

Split brain resolver - custom, static majority.

## Availability

[
    ![QWEQWEQWEQWEQWE]({{ page.image_link_base }}/availability@1x.svg)
]({{ page.image_link_base }}/availability@2x.svg)
{:.lead}

Sharding - recovery of failed nodes is automatic.
"Graceful" shutdown - almost immediate
Crash - need some time to detect (phi-accrual detector), during that time affected entities are not available.

## Request handling

[
    ![QWEQWEQWEQWEQWE]({{ page.image_link_base }}/request_handling@1x.svg)
]({{ page.image_link_base }}/request_handling@2x.svg)
{:.lead}

Emphasize: persistence is only touched on write

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

[
    ![QWEQWEQWEQWEQWE]({{ page.image_link_base }}/performance@1x.svg)
]({{ page.image_link_base }}/performance@2x.svg)
{:.lead}

Actor - in memory state
Persistence - append-only write to DB.

# Key takeaways

{% include {{page.key_takeaway}} %}

# Wrap up

TBD

In {% include infra/conditional-link.md label="the next post" url=next_post %},  blabla

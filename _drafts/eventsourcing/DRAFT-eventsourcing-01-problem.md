---
layout: post
title: "Eventsourcing: Part 1 - problem background and analysis"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/DRAFT-eventsourcing-01-problem
series_sequence_nr: 1
---

TBD

# Preface

The biggest and most successful project I've done during my time at Redmart was a system to manage Redmart's
delivery capacity - near real time, with strong consistency guarantees, low-latency & high-throughput, linearly 
scalable, highly available, etc., etc. - basically all the buzzwords and holy grails of distributed computing. 

One of the key technology choices that lead to the success of the overall solution was the use of eventsourcing to 
manage application state. This wasn't an easy ride though, and making such a choice is definitely not an 
one-size-fits-all solution - so there were quite a bit of learning and discovery me and my team made. Some of those
learnings I've already tried to share in various meetups[^1]. One day I thought it might be good to put them 
into a written form and in a more systemic way - this is how tis post has started. And then I figured that there's a 
lot to talk about, and it definitely doesn't fit a single blog post (well, unless you're all ok with ~1h read time).

The obvious thing to do is to split it into multiple posts - and that's what I've done. Right now I've plotted a course
for six or seven posts in the series, each covering different parts of the journey - from inception to implementation, 
to launch and to evolution - but as they say "no plan survives the first encounter with the enemy". 

So, I invite you all for a ride :).

[^1]: if you're interested, go check my stackoverflow profile - there are links to the recordings.

# Series navigation

[Back to series overview]({% link design/eventsourcing-series.md %})

{% assign posts = site.tags[page.series_tag] %}
{% if posts %}
{% assign series_posts = site.tags[page.series_tag] | sort: 'series_sequence_nr' %}
<ul>
{% for post in series_posts %}
  <li>
    <a href="{{ post.url }}">{{ post.title }}</a> - <span class="date">{{ post.date | date: "%B %-d, %Y"  }}</span>
  </li>
{% endfor %}
</ul>
{% else %}
No posts in this series so far - come back soon!
{% endif %}

# Problem background

This is a first post in the series, and I need some time to set up the backstage and explain problem background. But,
on the other hand, I also want it to be useful as a standalone thing - so that for you all out there it wouldn't be just
a long description of someone else's problem (and already solved one). One way to do so is to add some kittens.

<div class="image-with-attribution centered" markdown="1">

![Cute grey kitten picture]({{ page.image_link_base }}/kitten.jpg)

Image source: Wikipedia - [Kute grey kitten][kitten-orig];
[![](/assets/icons/cc_licenses/cc-by-sa.svg){:.cc_icon}][cc-by-sa-2.0]  
{:.image-attribution}

[kitten-orig]:https://en.wikipedia.org/wiki/File:Cute_grey_kitten.jpg

</div>

... except it doesn't contribute much to the topic discussed.

A more meaningful way would be to describe how the "free form" real-world problem description evolves into something
more formal - something that can be encoded as a computer program - then analyze it further to capture
functional and non-functional requirements; plus highlight reasons that drove us towards eventsourcing. 

Without further ado, let's dive in.

## Problem description

Redmart's delivery operations can simply be described as "guaranteed scheduled delivery": customer selects some time 
when the order is to be delivered - in Redmart's case it is/was a two-hour slot - and it is part of the customer 
value proposition to deliver at that time. Which means it is really important to fulfill this promise, as it is a part
of the customer experience (and we all want our customers to be happy and use or service more, right?).

In order to make sure this promise is fulfilled, the company must have tight control over logistics. It's not feasible
to delegate the delivery to a third-party logistic service - for two reasons:

1. If delivery is missed, customer will blame not the logistics provider, but you - so delegating bears significant
reputation risks.
2. It's much harder, if not impossible, to delegate the cold-chain deliveries - i.e. something that requires temperature
control, such as fresh fruits and vegetables, fresh and frozen meat and fish, ice cream and so on. 

"Control over logistics" actually means that the company must handle their own logistics fleet - from provisioning 
capacity, to training and operating it. So, logistics capacity is finite - you only have so much vehicles and drivers,
and each of them can only perform certain number of deliveries per unit of time. Moreover, provisioning is not a 
very elastic process - after all we're talking about obtaining physical vehicles and hiring&training human beings 
to operate them.

This leads us to the next observation - accepting too many orders results not in the dynamic growth of the delivery
capacity, but in overloading the existing limited resources. In turn, the overload causes a whole bunch of other bad
things - from missing the delivery windows picked by customers to drivers growing stressed and eventually leaving.

Hence, in order to maintain good quality of service, we needed to limit the number of orders customers can place. 
Moreover, we wanted to do it fast and reliably - so that if an order cannot be accepted, the customer would have an 
option to try schedule delivery at some other time, rather than just leaving in frustration. And to provide good 
customer experience, we want to show to the customer which delivery times are available for placing an order.

And this is exactly the problem my team was called to solve - **manage customer demand in a way to prevent overloading
limited logistics resources**.

## Existing solution

Since this problem arises from the very core of Redmart's business model, the was an existing system that solved it. 
However, it had a few issues that called for a significant overhaul of the solution - to name a few:

1. It was limited to managing single type of capacity, while there were multiple.
2. It was only capable of limiting customer orders based on capacity, while business needed multiple types of 
constraints (one example is geographical constraints)
3. It had stability and performance issues.

Now, in this post series I'll probably not talk much about (1) and (2) - simply put because improvements in these 
aspects were achieved with some other mechanisms rather than eventsourcing. Long story short, we implemented 
managing different types of capacity as separate microservices exposing similar APIs, and an overarching 
orchestrator service that would "merge" different types of capacity. Other constraints were also mixed in by the 
orchestrator. Orchestrator was completely stateless (save for a couple of disposable caches) and was built around 
reactive streams - [Akka Streams][akka-streams] in particular. But this is probably a good topic for another time.

[akka-streams]: https://doc.akka.io/docs/akka/current/stream/index.html

However, concern number three (stability and performance) deserves a closer look, as it directly affected the design
choices we've made - and heavily influenced the decision to go with the eventsourcing.

The existing system was "classical stateless" - i.e. it had state, but it was externalized to the database. On each 
request, the system would need to fetch the state, do the logic, and then persist all the changes back to the DB - 
classical application architecture, battle-tested and doing well on all scales from personal web pages to industry
giants. The were two problems in this system though:

1. The state was **massive** - single DB record represented an entire day, with all the capacity pools, projections of
customer orders records and so on - somewhere around 100Kb each[^2]. This posed throughput and latency constraints.
2. There were no mechanisms to prevent concurrent modification of the same record by different instances. This posed
correctness and consistency risks.

Eventsourcing (I'm tired of spellchecker flagging this word, so I'll abbreviate it to ES going further) offered means to 
address both of these:
 
1. the latency and performance are improved "by design" - with ES, application state exists in memory, so DB is 
accessed much less frequently and read-only queries does not even incur a hop to the DB[^3].
2. the correctness and consistency concerns are addressed by a particular implementation approach that is enabled by
the ES. I will cover it in more detail in later posts, but for now it is suffice to say that our application had 
*at most one* instance of each entity at all times, with the ability to quickly move/recover this entity to a different
service instance without loosing the data.

[^2]: this was in general a very poor design decision made at the very early days of system development. One fine day, 
    due to a change in how the "multiple capacity pools" were sliced, the size of the record went to ~2Mb... and we had a 
    complete outage because those giant records saturated the network and the service was basically unable to communicate
    with the DB.

[^3]: technically, one can have ES and no in-memory state, but such design misses on many ES advantages, so it isn't 
    quite popular, as far as I know.

# Analyzing the problem

Now, this is all good, but our problem definition is slightly imprecise and vague, aren't it? Let's try to make it a 
bit more concrete and formal.

This is a supply vs. demand problem with strict constraints:
 
- On the **supply side** we have delivery vehicles and drivers. Supply is not very elastic - to grow supply vehicles 
need to be procured, drivers need to be trained, and so on. For practical purposes it was safe to assume that supply 
side changes would need 1-2 weeks from making a decision change to actually seeing it live. Finally, these resources
have a cost - vehicle lease, driver salary, fuel, etc. - so supply also forms a cost center.
- **Demand side** is formed by customers placing orders. There is much more elasticity here - customers usually have 
more than one "feasible" delivery slot, so even if the preferred one is not available they can move to a later slot, or,
in the worst case, not place an order at all (but that's something we want not to happen). Orders generate income, so
we want as many orders as otherwise possible.

Now, due to other operational considerations, there's not just a single monolithic pool of supply capacity. 
There is *"time dimension"* to the problem, as Redmart allows requesting a delivery up to a certain date in the future.
There is also *"space dimension"*, as even on a single date there are multiple pools of capacity. I won't go into much
detail here (as the details are part of the competitive advantage), but let's just say that there
are multiple pools, each with pre-allocated vehicles and drivers, and there is a mechanism that allocates
customers' orders to those pools. Each capacity pool has the limit on how many units of capacity it 
has, and each order placed consumes some number of capacity units from the pool. As soon as the pool is drained, 
no more orders can be put into it.

Finally, to support the "show available delivery times" use case, the system should be able to give an overview of 
capacity for the customer - without the exact numbers, but including future dates.

## Formal representation

The problem is inherently simple - to demonstrate it, I'll put it as a bullet list:

- There are multiple capacity pools
- Each pool is a simple counter with a threshold
- When the threshold is reached, customers are no longer allowed to place orders into that counter

And that's it. Now it's time for you to ask - so why have you wasted so much of our time reading it - that sounds like
an interview question problem. Just put a `CapacityPoolName => (MaxOrders, CurrentORders)` hashmap, and we're done.

The complex part is that multiple customers might compete for the last available unit of capacity. In this case, we must
ensure that capacity is not exceeded - by allowing only one customer in, and politely rejecting all the others. 
So, at the very least that `if (currentOrders < maxOrders) currentOrders += 1` operation must be atomic. Not a big 
deal - just put a lock around that operation, right? 

Simple to implement naively - optimistic concurrency with compare-and-set writes in the DB is one option. But 
non-functional requirements come into play: 

1. Expect big growth (for practical reasons we were assuming 10x)
2. Low latency even at scale - did I mention that all that is on a "sequential" path to placing an order and customer's
browser waits for the response?
3. Highly available, aka "no single point of failure"

(1) and (2) called for putting the counters into memory (yes, stateful system), (3) multiple instances of the system.
Add atomicity requirements on top, and we get a distributed, stateful, highly consistent system tp build.


[cc-by-sa-2.0]: https://creativecommons.org/licenses/by-sa/2.0/deed.en
---
layout: post
title: "Journey through eventsourcing: Part 1 - problem background and analysis"
series_tag: eventsourcing-series-2020
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/2020-06-27-eventsourcing-01-problem
series_sequence_nr: 1
key_takeaway: "eventsourcing/01-problem-key-takeaway.md"
image: /assets/img/eventsourcing/2020-06-27-eventsourcing-01-problem/cover.png
---
{% include infra/series-nav-link-variables series_tag="eventsourcing-series-2020" series_sequence_nr=page.series_sequence_nr %}
Eventsourcing is probably among the most controversial and tricky design principles. In "classical" application design,
the state is written to the persistence store, mutated, and fetched from the DB on virtually every operation, while 
events causing state changes are transient and discarded the moment the change is applied. In eventsourcing, to the 
contrary, events are written to the store, never mutated, and read from the DB on rare occasions; while the state is 
transient and obtained from the log of events. To some extent, eventsourcing is like a mirror reflection of the 
"classical" approach. One day I and my team embarked on a journey through it - and this post is the beginning 
of the story.

# Preface

The biggest and most successful project I've done during my time at Redmart was a system to manage Redmart's
delivery capacity - near real-time, with strong consistency guarantees, low-latency & high-throughput, linearly 
scalable, highly available, etc., etc. - all the buzzwords and holy grails of distributed computing.

One of the key technology choices that lead to the success of the overall solution was the use of eventsourcing to 
manage application state. This wasn't an easy ride though, and making such a choice is not a one-size-fits-all 
solution - so there was quite a bit of learning and discoveries for me and my team. Some of those
learnings I've already tried to share in meetups. One day I thought it might be good to put them into a written form 
and more systemically - this is how this post has started... when it grew beyond ~600 lines
of markdown then I figured that there's a lot to talk about :smile:.

The obvious thing to do was to split it into multiple posts - and that's what I've done. Right now I've plotted a course
for six or seven posts in the series, each covering different parts of the journey - from inception to implementation, 
to launch and to evolution - but as they say "no plan survives the first encounter with the enemy". 

So, I invite you all for a ride!

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# Problem background

This is a first post in the series, and I need some time to set up the backstage and explain the problem background. But,
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

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/problem.jpg)

Image source: [Problem][problem-orig] - [Nick Youngson][Nick-Youngson] via [Alpha Stock Images][Alpha-Stock-Images]
[![](/assets/icons/cc_licenses/cc-by-sa.svg){:.cc_icon}][cc-by-sa-3.0]
{:.image-attribution}

[problem-orig]: http://thebluediamondgallery.com/tablet-dictionary/p/problem.html
</div>

Redmart's delivery operations can simply be described as "guaranteed scheduled delivery": the customer selects some 
time when the order is to be delivered - in Redmart's case it is/was a two-hour slot - and it is part of the customer 
value proposition to deliver at that time. This means it is really important to fulfill this promise, as it is a part
of the customer experience (and we all want our customers to be happy and use or service more, right?).

To make sure this promise is fulfilled best possible way, the company must handle their own logistics fleet - 
from provisioning capacity to training and operating it. So, logistics capacity is finite - you only have so many 
vehicles and drivers, and each of them can only perform a certain number of deliveries a day. Moreover, provisioning 
is not a very elastic process - after all, we're talking about obtaining physical vehicles and hiring&training human 
beings to operate them.

This leads us to the next observation - accepting too many orders results not in the dynamic growth of the delivery
capacity, but in overloading the existing limited resources. In turn, the overload causes a whole bunch of other bad
things - from missing the delivery windows picked by customers to drivers growing stressed and eventually leaving.

To maintain a good quality of service, we needed to limit the number of orders customers can place. We also wanted to 
do it fast and reliably - so that if an order cannot be accepted, the customer would have an option to try schedule 
delivery at some other time, rather than just leaving in frustration. And to provide good customer experience, 
we want to show to the customer which delivery times are available for placing an order.

This is exactly the problem my team was called to solve - **manage customer demand in a way to prevent overloading
limited logistics resources, while keeping customer experience slick and responsive**.

## Existing solution

Since this problem arises from the very core of Redmart's business model, there was an existing system that solved it. 
However, it had a few issues that called for a significant overhaul of the solution - to name a few:

1. It was limited to managing a single type of capacity, while there were multiple.
2. It was only capable of limiting customer orders based on capacity, while business needed multiple types of 
constraints (one example is geographical constraints)
3. It had caused a couple of severe outages due to correctness and consistency problems.
4. It had latency and throughput issues.

Now, in this post series, I'll probably not talk much about improvements in (1) and (2) - simply because improvements 
in these aspects were achieved with some other mechanisms rather than eventsourcing. Concerns number three (consistency) 
and four (latency and throughput) deserve a closer look, as they directly affected the design choices we've made - 
and heavily influenced the decision to go with the eventsourcing.

# Analyzing the problem

Now, this is all good, but our problem definition is slightly imprecise and vague, isn't it? Let's try to make it 
a bit more concrete and formal.

This is supply vs. demand problem with strict constraints:
 
- On the **supply side** we have delivery vehicles and drivers. Supply is not very elastic - to grow supply, 
vehicles need to be procured, drivers need to be trained, and so on. For practical purposes, it was safe to assume that 
supply-side changes would need 1-2 weeks from making a decision change to seeing it live. Finally, these resources
have a cost - vehicle lease, driver salary, fuel, etc. - so supply also forms a cost center.
- **Demand side** is formed by customers placing orders. There is much more elasticity here - customers usually have 
more than one "feasible" delivery slot, so even if the preferred one is not available they can move to a later slot, or,
in the worst case, not place an order at all (but that's something we don't want to happen). Orders generate income, so
we want as many orders as otherwise possible.

Now, due to other operational considerations, there's not just a single monolithic pool of supply capacity. 
There is *"time dimension"* to the problem, as Redmart allows requesting a delivery up to a certain date in the future.
There is also *"space dimension"*, as even on a single date there are multiple pools of capacity. I won't go into much
detail here (as the details are part of the competitive advantage/know-how), but let's just say that there
are multiple pools, each with pre-allocated vehicles and drivers, and there is a mechanism that allocates
customers' orders to those pools. Each capacity pool has the limit on how many units of capacity it has, and each 
order placed consumes some number of capacity units from the pool. As soon as the pool is drained, no more orders can 
be put into it.

Finally, to support the "show available delivery times" use case, the system should be able to give an overview of the
capacity for the customer - without the exact numbers, but including future dates.

## (More) formal requirements

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/requirement.jpg)

Image source: [Requirement][requirement-orig] - [Nick Youngson][Nick-Youngson] via [Alpha Stock Images][Alpha-Stock-Images]
[![](/assets/icons/cc_licenses/cc-by-sa.svg){:.cc_icon}][cc-by-sa-3.0]
{:.image-attribution}

[requirement-orig]: http://www.picserver.org/highway-signs2/r/requirement.html
</div>

The problem is inherently simple - to demonstrate it, I'll put it as a bullet list:

- There are multiple capacity pools
- Each pool is a simple counter with a threshold
- When the threshold is reached, customers are no longer allowed to place orders into that counter

And that's it. Now it's time for you to ask - so why have you wasted so much of our time reading it - that sounds like
an interview question problem. Just put a `CapacityPoolName => (MaxOrders, CurrentOrders)` hashmap, and we're done.

Well, from *functional* perspective, we totally are. However, *functional requirements only describe the system that 
runs on ideal hardware in an ideal world*. And in the real world, we had are a few non-functional requirements that 
ruled out not only this naive solution but entire classes of solutions, as well as make other approaches much more 
complex to implement. 

* **Consistency guarantees** - we'll look at them in more detail in a later post, but in essence, we wanted to prevent
cases when two or more customers place an order for a last unit of capacity roughly at the same time, and we allow 
*both* of them - as this constitutes an overbooking.
* **High availability** - customer-facing systems at Redmart were required to be run in highly-available fashion[^1]. 
This simple requirement rules out any approach based on in-process or OS-level locks.
* **High scalability potential** - Redmart expected to grow, and we wanted our system to be able to scale with it. 
In particular, our team's target was to design and build it in a way that would support 10x scaling without significant
rework.
* **Latency budget** - the system was on a sequential path to placing an order, i.e. customer's browser/mobile app 
would be blocked waiting for our response. This meant that we must maintain low response times even at the high load and
during spikes. In particular, for the original rollout, it was 200ms at p99[^2]

[^1]: this is a fancy way to say "at least two copies of the system on two different machines"
[^2]: this means that 99% of request would complete faster than 200 ms

Let's make a stop here and look closer at it. We needed to build (and eventually built) a *distributed*, 
highly *available* and highly *consistent* system. That's both "C", "A" and "P" in the [CAP theorem][cap], which 
isn't possible, right? Let me be honest - we haven't invented a way to circumvent something that is mathematically 
proven. However, we've found ways to "circumvent" it from a practical perspective - or, simply put "if no one notices, 
nothing bad had happened".

[cap]: https://en.wikipedia.org/wiki/CAP_theorem

## Further analysis

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/go_deeper.jpg)

Image source: [knowyourmeme](https://knowyourmeme.com/memes/we-need-to-go-deeper)
{:.image-attribution}

</div>

The last two requirements - scalability and latency - had a particularly profound effect on the outcome of the analysis 
and ideation. Jumping a bit forward - I plan to talk about different approaches we considered and turned down in the 
next post - the latency and scalability concerns drove us away from the now classical "stateless" design that put the
state into the database, to its "evil" twin of keeping the state in memory. 

The in-memory state would simply remove at least one round-trip to the database - thus improving latency across 
the board and reducing the load to the DB. Moreover, in read query cases, the request could be answered completely 
from memory. These two features would improve not only the average latency (which we cared) but also the so-called
long-tail latency - the latency of the slowest requests - which we cared even more. Additionally, scaling such a 
system would also be more straightforward - database and network would have much less to say in terms of performance,
so scaling out would simply mean adding more application instances.

However, keeping state in-memory - and not only as a read-through DB cache - also posed some challenges:

* In-memory state is lost if a service instance crashes - so it needs to still be persisted on write, and re-read into
memory on a service (re)start.
* Having multiple instances of the system poses consistency risk - if each instance has an independent copy, they might
independently accept a request for the last unit of capacity. So there needs to be a separate mechanism to prevent it. 

And this is exactly where eventsourcing shows up. Loss and recovery of the state is essentially a "normal" mode of 
operations of an event-sourced system - to recap, in eventsourcing, application state is transient and is calculated 
from a persistent log of events that happened to the system from the beginning of time[^3].

Resolving the inconsistency between multiple copies is not directly addressed by the eventsourcing, but something that 
is enabled by it. Moreover, the implementation that we chose allowed us to address the overall consistency guarantees -
preventing two customers from simultaneously reserving the last unit of capacity. I'll return to this topic in much more
detail in one of the future posts, but for now, it is sufficient to say that the system had **at most one** instance 
of each entity (capacity counter) across all the systems instances at all times.

[^3]: or, more often, from the last persisted state snapshot

# Key takeaways

{% include {{page.key_takeaway}} %}

# Wrap up

To sum up: to fulfill the business needs, we needed to build a low latency and highly scalable distributed system with 
high availability and "strong" consistency guarantees. To achieve the first two, we decided to put the application 
state into memory, and use eventsourcing principle to alleviate the challenges it poses, and also to achieve 
consistency and availability targets.

In {% include infra/conditional-link.md label="the next post" url=next_post %}, 
we'll take a closer look at the final solution architecture, as well as some other architectures and
approaches that were considered in the design phase, but eventually rejected.   

[cc-by-sa-2.0]: https://creativecommons.org/licenses/by-sa/2.0/deed.en
[cc-by-sa-3.0]: https://creativecommons.org/licenses/by-sa/3.0/

[Nick-Youngson]: http://www.nyphotographic.com/
[Alpha-Stock-Images]: http://alphastockimages.com/
[next-post]: {{ next_post }}
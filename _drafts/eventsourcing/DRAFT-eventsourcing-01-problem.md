---
layout: post
title: "TBD: eventsourcing problem"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/DRAFT-eventsourcing
series_sequence_nr: 1
---

TBD

[Back to Table of Contents]({% link design/eventsourcing-series.md %}#table-of-contents)

# Problem background

RM's mode of operations can be described as "guaranteed scheduled delivery" - customer selects a two-hour slot, and 
the order is delivered at that time sharp. This was (and still is) a part of customer value proposition, so it is really
important to fulfill it - one of the key company-wide metrics is delivery-on-time - percent of orders delivered in the
selected time slot, no earlier, no later.

Need to carefully plan logistics - including provisioning resources (workforce, vehicles, etc.). This is not a very
elastic process - more capacity cannot be easily obtained to cater for excess demand.

Capacity vs. demand problem, in a "strict" fashion - due to operational model, even one excess order might cause 
significant problems on the ground. No excess orders due to technical reasons are allowed.

# Existing solution

Describe RDS (without mentioning this name :)) - overall architecture, and why it was not sufficient anymore.

1. Needed to consider not only one type of capacity, but multiple
2. Ability to recognize other types of constraints (e.g. address restrictions)
3. Stability concerns
4. Performance concerns

Divali 2017 outage - briefly, as an example of stability issues. 

# Decomposing the problem

Simply put, a set of counters; each counter represents certain part of the delivery fleet - each time an order is 
placed, it is allocated to a counter and this counter is increased. When a counter reaches predefined value, no more
orders are allowed within that time slot[^1]. Finally, there should be a way to query current state of all the counters
and present it to the caller.

[^1]: It was slightly more complex in reality, but those are gory technical details, so I'll omit them for now.   

The complex part is that multiple customers might compete for the last available unit of capacity. In this case, we must
ensure that capacity is not exceeded - by allowing only one customer in, and politely rejecting all the others. 
So, in essence, the system should behave as a collection of atomic counters.

Simple to implement naively - optimistic concurrency with compare-and-set writes in the DB is one option. But 
non-functional requirements come into play: 

1. Expect big growth (for practical reasons we were assuming 10x)
2. Low latency even at scale - did I mention that all that is on a "sequential" path to placing an order and customer's
browser waits for the response?
3. Highly available, aka "no single point of failure"

(1) and (2) called for putting the counters into memory (yes, stateful system), (3) multiple instances of the system.
Add atomicity requirements on top, and we get a distributed, stateful, highly consistent system tp build.
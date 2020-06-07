---
layout: post
title: "TBD: eventsourcing system evolution"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/DRAFT-eventsourcing
series_sequence_nr: 6
---

TBD

[Back to Table of Contents]({% link design/eventsourcing-series.md %}#table-of-contents)

# Evolving the system (and how design choices helped)

## Multidrops project

Another read side (?) in Cassandra, optimized selection of buckets, limited re-opimization.

Readside of MultiDrop project: It was a heavily customized C* tables that interlocked (so that write without locking 
and ensures eventual consistency) and ensures all the data it may need to read from can be read from memory at all 
times (by designing the write carefully enough, and C* can only allow you to read with index, unless you tell it to 
allow filtering). When testing this part, we put fault injection into consideration and injected fault at different 
positions, to ensure no matter where a application crash happens, the C* would always return to eventual consistency 
state once a restart is done (and all shards are recovered).

Required a couple of events/snapshots migrations - briefly describe potential approaches in general + how it worked
for us. 

Outcome: project that drives significant cost savings and logistics efficiency improvements

## Lazada integration

Non-func:
* <100ms 99th @ 10x current traffic
* 100% availability

GRPC + protobuf

gRPC client side load balancer -- It was implemented with Akka actor routing in the beginning (and still has such
operation mode I think), while later I switched to write another implementation manually so that it could have
something similar to smallest mailbox first, which was actually not supported by Akka actor routing natively when
the action to the message is something async. I had to manually count the num of message on the fly and route
message to the routee with fewest msg on the fly. There are 2 kinds of actors there, manager and worker, one worker
represents a gRPC connection, and manager makes the routing decison. The same component also provides fail-fast
capability. When all of the queues are too full, we just fail the request directly. There was no QoS or rate limit
there but clearly we could add them.

GC tuning - less stop-the-world, faster GC in general. Analysis: JMX extension to plug into existing metrics collection
infra + Graphana dashboards (TODO: ask WX to capture some GC dashboard screenshots, if possible). Tuning: switched 
to CMS (or _from CMS_?), tuning GC parameters. 

GC -- we were previously using the default parallel GC in the beginning. And we only had 2 cores in our VMs,
so that one core will be dedicated to GC, even though it's not gonna stop the world. So we changed a few places
where we can use some mutable data structure (e.g. the Akka ddata was removed atm finally), and used larger VM
that has more cores, and switched to CMS GC afterwards. I could not remember whether we tuned the heapsizes etc.
but we definitely have no more full GC after that, at all. Also G1 GC is not gonna help as our heap is small enough.

To overcome the slowliness of C* due to GC on single node -- we used speculative execution in C* queries.
As all the read / write query we were using are idempotant, all of them can be accelerated by setting speculative
execution delay to say 90 percentile of RT of C*. So we trade some extra QPS / TPS of C* into shorter RT by cutting
the long tail.

Tuning cluster RT further -- TCS was initially using netty TCP as the Akka remoting backend. It was way too slow a
t that time, with 90 percentile to be something around 60ms or so, when the load is high. We changed it to Aeron UDP
later,  which could be tuned to balance between lower CPU consumption in idle times and lower RT when starting from
low traffic mode. As we were always using dedicated VM, I just chose to waste CPU load without hestitation.

Was artery added at that time, or shortly after?

Outcome: integrated in time, sustained up to 50x production traffic at pre-launch load test. Recently, during spike of
load in COVID and operational constraints, was able to seamlessly handle almost 40x "normal" traffic in the wild 
(put a graph?)
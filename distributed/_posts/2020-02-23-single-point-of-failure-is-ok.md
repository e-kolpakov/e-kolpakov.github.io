---
layout: post
title: Single point of failure is OK... sometimes
tags: [architecture, design-principles]
---

The goal of any distributed system is to provide better availability, throughput, data durability, and other 
non-functional concerns, compared to functionally similar non-distributed system. Principles of distributed systems
design sometimes crystallize into a short and expressive "mantras" - such as "eventually consistent" or 
"no single point of failure". They are extremely useful, allowing expressing otherwise complex concepts in a short 
and unambiguous way, but sometimes are a little bit too broad and cover (or deny) more ground then they should. 
Specifically I'm talking about the "no single point of failure" principle - turns out there are many dramatically 
successful distributed systems that violate this principle at their core. Let's look at what do they do instead.     

## Key observation 

To someone who has been exposed to the distributed computing a bit, but not too much (like myself), the underlying idea
looks counter-intuitive at first, but eye-opening on the second thought. Ready? Here it goes:

> As long as some operation is not frequent, and not latency-sensitive, it's OK to have it pass through a component
> that is a single point of failure, provided the component can recover quickly.
{:.lead}

It is counter-intuitive as the whole point of distribution was to avoid single point of failure, right?

It's eye-opening, because it turns availability from *qualitative* measure - the design is either tolerant to certain 
type of failures, or not - to a *quantitative* measure - if 

```
crash_detection + crash_recovery + normal_response <= latency_budget
```

we're fine.

## How to apply it?

This observations enables a whole class of architectures and solutions, otherwise rejected by the "single point of 
failure" concerns. One particularly remarkable architecture (and the one that triggered me to write this post) is
some sort of a hybrid between master-based and masterless architectures. Lacking an established name (at least I'm not
aware of one), for the purpose of this post I'll dub it "metadata-master".

To recap:

**Masterless** systems allow updates to be accepted and performed by any node. Since any node can process an update at 
any time, masterless systems are in general more available and scale better. However, they need sophisticated 
mechanisms to ensure consistency. Another potential disadvantage/complexity is figuring out which nodes to contact 
to read or update certain record.

**Master-based** systems rely on a "single writer" principle to ensure stronger consistence, at the cost of 
availability and throughput - as all the updates must go through a dedicated node, and this node becomes a single point
of failure and a throughput bottleneck. To alleviate the problem, mature master-based systems offer various mechanisms - 
"distributing" the masters via sharding mechanisms and transparently promoting replicas to master state in case of 
master failure, which brings the "who owns this record?" question back.

**Metadata-master** architecture(s) try to get best parts of both approaches. In short, it consists of two layers: 
strongly consistent master-based layer for metadata, and eventually consistent masterless layer for the data itself. 
Specifically, there is a single appointed node in the top layer that performs "membership management" and 
other bookkeeping for the lower layer, and actual data is stored and modified by the nodes on the lower level.

The main advantages of such architecture are:

1. Compared to single master systems, frequent and latency-sensible operations go through "distributed" part, which 
    improves availability and throughput where it is most needed.
2. Compared to masterless systems, membership, consensus and data re-sharding protocols are dramatically simplified - 
    basically from [byzantine consensus][byzantine] to "master decides"[^1].
    1. ... this also helps "distributed master" case.

True beauty is that "lower" level is not limited to masterless approaches only. One can design a master-based protocol
on the lower level as well - trading off availability and throughput for consistency - but still enjoy the simplified
metadata management.  
   
[byzantine]: https://medium.com/loom-network/understanding-blockchain-fundamentals-part-1-byzantine-fault-tolerance-245f46fe8419
[^1]:  There's still a need to elect a new master sometimes, but this operation is much less frequent. 

## Who uses this?

I haven't done an exhaustive research on when this architecture first arose, but the earliest one I'm aware of is 
*"Google File System"* ([wikipedia][gfs-wiki], [whitepaper][gfs-whitepaper]) - the underlying infrastructure that 
basically enables Google's Bigtable and MapReduce - which in turn power Google's search itself. Hadoop's HDFS is 
considered by many an open-source analogue of GFS - and uses similar concepts.

However, the pattern is not limited to file storage, or even data storage in it's broadest sense - 
[Zookeeper][zookeeper] is probably yet another example, however I'm not familiar enough with Zookeeper (and how it does 
things internally) to be 100% sure.

Another notable example can be found in Akka, specifically in [Akka Cluster Sharding][akka-cluster-sharding], which is
more on the "compute" side of things:

* Metadata layer: There's a single persistent Cluster Sharding Coordinator that keeps track of shard allocations to nodes
* Data layer: Each sharded actor is expected to be either stateless or persisted and be able to recover on any other
    node at any moment; sharding infrastructure holds on to undelivered messages until the recipient actor is up.
    
[gfs-wiki]: https://en.wikipedia.org/wiki/Google_File_System
[gfs-whitepaper]: https://static.googleusercontent.com/media/research.google.com/en//archive/gfs-sosp2003.pdf
[akka-cluster-sharding]: https://doc.akka.io/docs/akka/current/typed/cluster-sharding-concepts.html
[zookeeper]: https://zookeeper.apache.org/

## Conclusion

Despite a halo of perceived necessity, "no single point of failure" is not something that is a must in distributed 
systems, but a design principle that can be (and has been) successfully sacrificed to gain something in other aspects - 
such as simplicity or efficiency. One particular example of such trade are "metadata-master" systems, such as 
Google File System, Akka Cluster or Zookeeper, that employ "single point of failure" component to manage system 
metadata, and use some other mechanisms to manage the data itself. 
---
layout: post
title: "Journey through eventsourcing: Part 5 - Support and Evolution"
tags: ["design principles", eventsourcing-series-2020]
image_link_base: /assets/img/eventsourcing/DRAFT-eventsourcing-05-support-and-evolution
series_sequence_nr: 6
key_takeaway: "eventsourcing/05-support-and-evolution-key-takeaway.md"
image: 
    path: /assets/img/eventsourcing/DRAFT-eventsourcing-05-support-and-evolution/cover.png
    srcset:
        1920w: /assets/img/eventsourcing/DRAFT-eventsourcing-05-support-and-evolution/cover.png
        960w:  /assets/img/eventsourcing/DRAFT-eventsourcing-05-support-and-evolution/cover@0,5x.png
        480w:  /assets/img/eventsourcing/DRAFT-eventsourcing-05-support-and-evolution/cover@0,25x.png
---
{% include infra/series-nav-link-variables series_tag="eventsourcing-series-2020" series_sequence_nr=page.series_sequence_nr %}
The launch we covered in [the previous post][previous-post] was a major milestone, but not the final destination. In 
fact, it was a solid foundation for the many improvements made later - from small bugfixes and tuning, to supporting new
business initiatives. The design choices we made - eventsourcing, statefulness, distributed system, etc. - affected all
of those changes; most often making hard things easy, but sometimes making easy things complex.

[previous-post]: {{ prev_post }} 

{% include eventsourcing/disclaimer.md %}

# Series navigation

[Back to the series overview]({% link design/eventsourcing-series.md %})

{% include infra/series-navigation.md series_tag="eventsourcing-series-2020" %}

# System evolution

## Schema evolution

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/evolution.jpg)

Image source: [Flickr][launch] by [patriziasoliani][patriziasoliani]
[![](/assets/icons/cc_licenses/cc-by-nc.svg){:.cc_icon}][cc-by-nc-2.0]
{:.image-attribution}

[launch]: https://www.flickr.com/photos/55524309@N05/5377715421
[patriziasoliani]: https://www.flickr.com/photos/55524309@N05/
[cc-by-nc-logo]: /assets/icons/cc_licenses/cc-by-nc.svg
[cc-by-nc-2.0]: https://creativecommons.org/licenses/by-nc/2.0/
</div>

**TL;DR:** schema evolution in eventsourcing systems is much more convoluted than in _state-sourcing_. _Before_ making 
a decision to go with eventsourcing vs. _state-sourcing_, familiarize yourself (and the team) with the implications - 
it might influence the decision heavily.

Schema evolution is relatively trivial in a classical _state-sourced_ system. When persisted data changes its structure, 
the solution is to write and run a schema migration script. The script might be a bunch of instructions in a fancy DSL, 
literally a python/go/ruby/JS/etc. script to read-update-save DB records in a loop or just a SQL command to execute. 
Many languages, frameworks, and 3rd party libraries exist to support that[^1]. 
Shortly put: problem solved, nothing to see here, folks.

On the contrary, in eventsourcing, the events are expected to be valid indefinitely - the _current_ version of the 
application code should be capable of handling any _prior_ events. It makes the "just run the migration script" 
approach much harder and not always possible[^2]. The eventsourcing community had come up with multiple solutions, 
such as in-application event adapters, copy-transform event updates, snapshot+discard techniques, and so on (one of my
[old presentations][eventsourcing-schema-migration-presentation] has a slide on it) - each having a different impact on
the application itself and related systems[^3].

In our case, we went with the in-app adapter approach - the one promoted by the 
[Akka Persistence][akka-persistence-event-adapters] (or a bit obsolete, but much better at explaining the general idea 
[Classic Akka Persistence][akka-persistence-classic-event-adapters]). All-in-all it was an interesting exercise - 
writing and enabling the adapter was easy; however, one of the models changed three times in a couple of months, 
each change producing yet-another-event-adapter. So we were on the brink of needing something more radical 
(I was exploring the snapshot+discard options), but then the data model finally stabilized.

[^1]: virtually any ORM framework (e.g. [Django](https://docs.djangoproject.com/en/3.1/topics/migrations/), 
    [Sequelize](https://sequelize.org/master/manual/migrations.html), 
    [Ruby On Rails](https://guides.rubyonrails.org/active_record_migrations.html), etc.)
    contains one; there are standalone solutions such as [Flyway][flyway].

[^2]: for example, when adding a new event attribute, it is not always possible to "go back in time" and infer what 
    the value of that attribute would have been for an old event.


[^3]: In-app adapters generally work well _for the app_, but any derived data streams are left behind. Copy-transform
    tailors to the derived data much better, but the application itself requires more changes and planning. 
    Reasoning about the system is easier with snapshot+discard, but it erases history. Other techniques 
    also have pros and cons. 

[eventsourcing-schema-migration-presentation]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g415fdb2fc6_0_85
[akka-persistence-event-adapters]: https://doc.akka.io/docs/akka/current/typed/persistence.html#event-adapters
[akka-persistence-classic-event-adapters]: https://doc.akka.io/docs/akka/current/persistence.html#event-adapters

[flyway]: https://flywaydb.org/

## Logistics optimization project

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/optimization.svg)

Image source: [Wikimedia][optimization]
[![](/assets/icons/cc_licenses/CC0.svg){:.cc_icon}][cc0]
{:.image-attribution}

[optimization]: https://commons.wikimedia.org/wiki/File:Minimum_spanning_tree.svg
[cc0]: https://creativecommons.org/share-your-work/public-domain/cc0/
</div>

**TL;DR:** eventsourcing makes it easy to implement CQRS, which in turn makes it easy to implement many things. 
One nice trick is to build a "private" _query_ endpoint to provide hints to the _command_ endpoints. It has many uses:
using a materialized view as an optimized query, access some data usually not available for the _command_ endpoint, 
etc.

One of the business initiatives our new system unlocked revolved around optimizing logistics efficiency. From a 
technical perspective, the change was to allocate customer orders into capacity pools more efficiently. Depending on 
what other orders were in the same capacity pool, both the financial and capacity cost of fulfilling the order could 
vary significantly. That required capacity pool actors inspect other pools that could potentially fulfill the order.

A straightforward approach - poll other actors about their "cost of fulfillment" - was possible but inefficient. 
Instead, my colleague came up with a different solution - these additional data requirements could be formulated as 
a simple index lookup if we could "slice" the data differently. Essentially it meant building and maintaining a 
materialized view for a new projection of the system state. We had CQRS embedded deeply into our solution, so building 
another query endpoint was simple enough - in fact, we had multiple options for a particular implementation. 
Because of the [issues with Distributed Data][ddata-problem], we faced earlier, we went ahead with a Cassandra-based 
solution - with tables carefully designed against the query, allowing the data to be read from memory almost 
all the time.

[^4]: and probably part of know-how or trade secret - nothing eye-opening, but still.

[ddata-problem]: {% post_url design/2020-11-30-eventsourcing-04-pre-flight-and-launch %}#distributed-data-not-performing-well

## Lazada integration

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/integration.jpg)

[Nick Youngson][nick-youngson] via [Alpha Stock Images][alphastockimages] and [Picserver][picserver]
{:.image-attribution}
[![](/assets/icons/cc_licenses/cc-by-sa.svg){:.cc_icon}][cc-by-sa-3] 
{:.image-attribution}

[nick-youngson]: http://www.nyphotographic.com/
[alphastockimages]: http://alphastockimages.com/
[picserver]: https://www.picserver.org/highway-signs2/i/integration.html
[cc-by-sa-3]: https://creativecommons.org/licenses/by-sa/3.0/
</div>


**TL;DR:** integrating with logistics systems of Redmart's parent company imposed even stricter latency and 
availability requirements. The choice of technology allowed us to scale out with ease and migrate to more efficient 
networking - while keeping correctness and consistency requirements intact.

This project had relatively little to do with the eventsourcing but was an ultimate test of the entire solution and 
technology choices we made along the way. It touched both "traditional" and eventsourcing systems we had in 
our solution[^5]. The requirements were simple - we needed to expose the existing API via a new "medium" 
(proprietary solution on top of gRPC), achieve <100ms latency @ 99th percentile for 5x current traffic and 
99.95% availability[^6].

**Creating gRPC endpoints** were relatively straightforward - the choice to go with Akka HTTP played out quite well due
to the [design philosophy][akka-http-philosophy] - it is a library to build HTTP interfaces, not the framework to 
structure the app. Due to that, we just had to add [Akka gRPC][akka-grpc] alongside the existing HTTP endpoints and wire
them to the application logic. It wasn't just a configuration switch - some effort was necessary to "reverse-engineer"
the DTOs we used in REST+JSON endpoints into protobuf declarations - but still straightforward enough.

The initial gRPC implementation needed some more work down the road to meet the aggressive latency targets - essentially
my teammates had to build an analog of the ["smallest-mailbox" routing strategy][smallest-inbox] over the Akka-gRPC
client connections - to achieve better [client-side load-balancing][akka-grpc-load-balancing].

**Reducing latency** required quite a lot of tinkering and tweaking - although a "classical" system would need most of 
them as well. To name a few: tweaking JVM garbage collection to cause less stop-the-world GCs, enabling 
Cassandra's [speculative execution][speculative-execution], and aggressively caching everything we could 
(via [Hazelcast Near Cache][hazelcast-near-cache] with some custom cache warmup code).

One thing that is extremely relevant to the technology we used was the move to a new Akka remoting backend - we moved
from Netty-based TCP remoting (goes by ["Classic Remoting" now][classic-remoting]) to [Artery][artery] UDP remoting. 
While this is a large change that delivered tangible latency saves (~10-20ms, depending on the load), the code changes
were small - mostly configuration and dependency changes.

Overall, the integration project was a major success - we integrated in time and with huge margins towards the load 
and latency targets - the system could sustain about 10x the _target_ traffic (50x actual traffic) while having 
~20% buffer on latency (~80ms 99th percentile) in synthetic load tests.

[^5]: for those who're interested - here are some simplified solution diagrams: 
    [October 2018][capacity-architecture-2018], [August 2019][capacity-architecture-2019]

[^6]: initial requirements were <10ms **max** latency and **100%** availability. We were able to negotiate to reasonable
    values given the deployment specifics and network infrastructure.

[akka-http-philosophy]: https://doc.akka.io/docs/akka-http/current/introduction.html#philosophy
[akka-grpc]: https://doc.akka.io/docs/akka-grpc/current/index.html
[smallest-inbox]: https://doc.akka.io/docs/akka/current/routing.html#smallestmailboxpool
[akka-grpc-load-balancing]: https://doc.akka.io/docs/akka-grpc/current/client/details.html#load-balancing
[speculative-execution]: https://docs.datastax.com/en/developer/java-driver/3.2/manual/speculative_execution/
[hazelcast-near-cache]: https://hazelcast.com/blog/pro-tip-near-cache/
[classic-remoting]: https://doc.akka.io/docs/akka/current/remoting.html
[artery]: https://doc.akka.io/docs/akka/current/remoting-artery.html

[capacity-architecture-2018]: https://docs.google.com/presentation/d/1gt8JW5ky3O8XHDdAUPlu6KcO4jErHoZBESdIRdkJ_18/edit#slide=id.g3dacb4d84b_0_0
[capacity-architecture-2019]: https://docs.google.com/presentation/d/1A8-WbyQU3nPmChF_YHJhAGcsHhPWt4JZyOTfPqt8ghQ/edit#slide=id.g5c96e3f8dd_0_419

# Other thoughts

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/thoughts.jpg)

Image by [ElisaRiva][elisariva] from [Pixabay][pixabay] - [Pixabay Licence][pixabay-licence]
{:.image-attribution}

[elisariva]: https://pixabay.com/users/elisariva-1348268/
[pixabay]: https://pixabay.com
[pixabay-licence]: https://pixabay.com/service/license/
</div>


There are some other minor-but-noteworthy learnings. So I decided to put them here, at the end of the journey, in the last section.

**Planning for a 10x/20x/etc. throughput is an overkill:** there was some minor debate about throughput targets we 
should set. 10x seemed a little excess, especially taking into account that the growth was limited by a real-world
operations. Nevertheless, our stake in designing for an order of magnitude higher throughput paid off: during a spike 
of demand due to COVID and operational constraints, the system handled 40x traffic "in the wild" regularly and with 
unnoticeable customer experience degradation. Failing at that time would mean tremendous financial and reputation
losses to the company.

**"Time travel":** one of eventsourcing selling points is the ability to restore the system to any prior state - 
also known as "time travel". Having such an ability sounds quite exciting for debugging and audit - but it is not 
that straightforward to achieve. The main question is schema migrations - some approaches to migration destroy
the "time continuum" and make it impossible to "time travel" beyond a certain point. Moreover, developers will need 
to build some infrastructure to expose the _ time-traveled_ state alongside the _current_ state - a separate set of 
endpoints or a dedicated service deployment is necessary. Simply put, "time travel" is not free and impacts other 
decisions heavily.

**Monitoring:** One trick that helped us a lot was to enrich our _liveness_ probe (is the system running at all), 
with some _usefulness_ information (is the service doing the right job?). It was mostly a hack - the _liveness_ 
endpoint was already integrated with many monitoring tools and dashboards and was mandatory for all services, 
while _usefulness_ monitoring was not a thing[^7]. Putting _usefulness_ information into the _liveness_ check, 
we made alerts report a somewhat higher problem impact than there was, but notify us about the problems much earlier. 
It was handy during the stabilization phase, shortly after launch - there were cases when certain groups of actors 
would go down, while the rest of the system (including _liveness_ probe) worked as expected - such cases would
be hard to notice otherwise.

[^7]: or at least it was assumed that usefulness === liveness

# Key takeaways

{% include {{page.key_takeaway}} %} 

# Conclusion

Here the journey ends. Looking back, we have covered the full lifecycle of a software system built on eventsourcing
principles - from gathering the requirements and evaluating the goals/challenges against eventsourcing promises, 
to make concrete decisions regarding technology and implementation, to launching and evolving the system.

I hope that you have learned a lot (or at least a few things :smile:) and are better informed about the strengths of 
the eventsourcing systems, as well as the challenges they pose. I hope that next time when tasked to build a new 
system or service, you'll consider eventsourcing as an option - and make an **informed** decision. 

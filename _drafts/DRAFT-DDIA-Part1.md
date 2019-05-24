---
layout: post
title: "Designing Data-Intense Applications: Part 1"
tags: [books-ddia]
---

First part of the book sets up the stage and defines the *Reliability*, *Scalability*, and *Maintainability*. Later
some foundational building blocks of both distributed and non-distributed systems - such as data model, persistence 
mechanism(s), data encoding (aka serialization) and evolution (aka versioning) are discussed

# What is data-intense application?

The first question one might ask is exactly this - what is a data-intense application?
What other types of applications are there, and how data-intense applications differ from them?
 
No explicit definition is given, but the differentiating factor is pretty clear - data-intense applications 
are the opposite of compute-intense applications. In data-intense applications major factors are complexity, 
size, or rate of change in data, whereas compute-intense is more about efficiently crunching numbers that originate
from relatively small amount of input data.

**Opinion:** data-intense and compute-intense are not mutually exclusive, but more like two ends of 
a continuous spectrum: there are clearly cpu-bound applications - like computing pi number or prime numbers
(e.g. [prime95][p95]); data-bound applications (virtually any Spark/Hadoop application); but there are also 
all kinds of mixes of the two, with algorithmic problems sitting closer to the _compute_ side, and your 
ordinary line-of-business applications closer to the _data_ side. And [CERN computing][cern] right in the middle.
{:.message}

[p95]: https://www.mersenne.org/download/
[cern]: https://home.cern/science/computing

Basically this means that most of the applications currently out there are data-intense.

# Chapter 1: Reliable, Scalable, and Maintainable applications

Chapter 1 sheds light on what is actually understood under *Reliability*, *Scalability*, and *Maintainability*
and gives some clues on approaches, techniques and practices that help achieve them.

<dl>
    <dt>Reliability</dt>
    <dd>
        The ability of the application/system to "do the right thing" - perform its' function with acceptable 
        performance and necessary data protection/access control - even in the face of adversity, such as 
        software errors, hardware faults, human mistakes or outright malicious interference
    </dd>
    <dt>Scalability</dt>
    <dd>
        System's ability to react to load - as simple as that
    </dd>
    <dt>Maintainability</dt>
    <dd>
        An umbrella term covering multiple aspects of running and maintaining the system - from making it easy to
        run/deploy/monitor/etc. to tech debt amounts, complexity and ability to change and evolve with time
    </dd>
</dl>

Some techniques, practices and approaches to achieve these aspects are briefly discussed. Most of the chapter is 
devoted to describing the load (using an example of Twitter timelines) and performance.

{::options parse_block_html="true" /}
<div class="message">
**Chapter highlights:**
* Sometimes it might make sense to _increase_ the rate of faults - to regularly exercise fault-tolerance mechanism
    ([Chaos monkey][chaos-monkey]).
* Scalability is a "multidimensional" aspect - it depends on load and resources
* Service Level Agreements <= Service Level Objectives, but not always exactly equal. SLO is a target, SLA is a contract.
* Operability cannot be an afterthought - add your logging/instrumentation early.
</div>
 
[chaos-monkey]: https://github.com/Netflix/SimianArmy/wiki/Chaos-Monkey

# Chapter 2: Data models and Query Languages

This chapter focuses on general-purpose data models - such as relational, document and graph model - and includes
a brief history of their evolution, comparison and major differences that affect applications adopting one or the
other.

**Relational model** - does not need to be specially introduced. Was proposed in early 1970s as an approach to encode
relationships between data - they are represented as foreign keys.

**Network and hierarchical models** - were proposed in early 1970s as well and were rivals to relational model. Due to
overcomplicated standard and imperative character of query language lost adoption and eventually faded. However, 
some ideas behind these models could be traced to currently popular document and graph models.

**Document model** - interestingly, the now-popular among NoSQL databases document model actually predates relational[^1]. 
Document model does not explicitly represent references and rely on the application to resolve them - but in return 
offers a closer matching between documents "on disk" and objects in the application - thus escaping the infamous 
object-relational impedance.

**Graph model** - can be seen as modern take on network model, addressing its biggest "mistakes". Records are represented
by vertices, and relationships between them - as edges, which can also encode some data on their own 
(e.g. type of relationship). Querying is declarative as in relational model and SQL - albeit with a 
slightly different flavor - pattern matching rather than "describing result".
    
Probably the most important conclusion is - choice of model depends a lot on the relationships between objects in the application:
* if it is limited to simple tree-like structures, **document model** shines. 
* **Relational model** is able to represent a more complex connections, but with highly interconnected data the 
    schema might go out of control quickly. 
* In "highly interconnected" cases, **graph model** becomes most natural, as well as in cases when connections represent most value.

{::options parse_block_html="true" /}
<div class="message">
**Chapter highlights:**
* Good model choice heavily depends on the relations between objects in the application
* Relational and document convergence - many relational DBs add "document" features, such as XML or JSON support.
* Schema-or-read (aka schemaless) in document DBs vs. schema-on-write in relational.
* Graph query languages - declarative with pattern matching
</div>

[^1]: [IBM's IMS][ibm-ims] used document model and was first released in 1966.
[^1]: Although ElasticSearch uses slightly different data structure called [Inverted Index][inv-idx], the data in the
    index is represented by documents

[ibm-ims]: https://en.wikipedia.org/wiki/IBM_Information_Management_System
[inv-idx]: https://www.elastic.co/guide/en/elasticsearch/guide/current/inverted-index.html

# Chapter 3: Storage and Retrieval

# Chapter 4: Encoding and Evolution

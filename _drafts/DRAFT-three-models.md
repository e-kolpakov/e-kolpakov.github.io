---
layout: post
title: DRAFT: Three models per application
tags: [design-principles]
---

It wouldn't be a major overstatement to say that majority of the applications - at least in the startup and enterprise
world - and are built to model and automate certain real-life business processes. As such, the application inevitably
has to carry an idealized representation of the "domain" - the entities, processes and interactions found in the 
actual real-life process. On the other hand, since the application has to do something useful, it has to interact with
the real world (through UIs, printers, actuators, etc.) and other applications (such as other services, persistence 
mechanisms, queues, etc.). A common shortcut (and/or a caveat) is to use the same model to fulfill all these needs - 
however, this isn't _always_ the best course of action. Let's take a look at other options.

# 10 kilometer high overview

Before we delve deeper, let me introduce some "temporary" terminology here, so it's unambigious what I mean:

* Public model - everything that is available to the clients of the system, including other services/applications and 
users. This covers Data Transfer Objects for APIs, as well as models for user interfaces.
* Persistence model - means everything that is stored, and normally not accessible externally. This one is a bit tricky 
- I don't mean the "physical" representation of the data in the persistence store, but a "logical" representation of 
this data in your application. Think of a class that 100% replicates database table, or a class that is serialized into
JSON to be pushed to ElasticSearch/MongoDB/etc.

1. One model to rule them all: domain model everywhere.
2. Three models: dedicated public and persistence models.
3. Compromise solutions:
    1. Two models: domain model doubles as public model, persistence is separate.
    2. Two models: domain model doubles as persistence, public model is separate.

# One model

This is what you get if you start lean - your domain, DTO and persistence modes is one and the same.

Pros: usually evolves naturally, shorter development time, no model mappers (least boilerplate)
Cons: All the different concerns are mixed together; cannot evolve one without touching the others

# Three models

This is the most flexible solution, but requires most boilerplate

Pros: most flexible
Cons: most boilerplate, some changes are "cross-cutting" - need to be "carried" through all three models

# Compromise solutions

## Two models: domain as public

One of the ways to compromise

Pros: persistence concerns are still isolated
Cons: cannot refactor domain without changing public interface; no/little anticorruption layer

## Two models: domain as persistence

Pros: Can evolve public independently from domain - easier to do API version evolution; 
most ORM frameworks already do this 
Cons: harder to add other persistence mechanisms, persistence leaks into domain (harder)

# Conclusion

Risking sound like a broken record, there's again, no silver bullet. Small, simple systems - especially microservices 
developed with "easier to throw away than modify" approach in mind - might get out perfectly well with a single model 
for all. Three models are the most flexible, but most boilerplate and sometimes maintenance burden. Compromises, are,
well, compromises that try to win in some aspect by loosing in some other. Pick the approach that suits your current
situation - project timeline, importance of the system build, complexity of the domain and infrastructure and so on.  
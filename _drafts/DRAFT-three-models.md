---
layout: post
title: The three models in your application
tags: [design-principles]
image_link_base: /assets/img/draft-three-models
---

It wouldn't be a major overstatement to say that majority of the applications - at least in the startup and enterprise
world - and are built to model and automate certain real-life business processes. As such, the application inevitably
has to have a model - an idealized representation of the "domain" - the entities, events and interactions found in 
the real-life process. The application also has to do something useful with that model, so it has to interact with
the real world (through UIs, printers, actuators, etc.) and other applications (such as other services, databases, 
queues, etc.). A common shortcut (and/or a caveat) is to use the same model to fulfill all these needs - 
however, this isn't _always_ the best course of action. Let's take a look at other options.

# 10 kilometer overview

Before we delve deeper, let me introduce some "temporary" terminology - for brevity and clarity.  

* **Public** model - everything that is available to the clients of the system, including other services/applications 
and users. This covers Data Transfer Objects for APIs, models for user interfaces, messages published to the queues, 
data put in caches with "public" access, and so on.
* **Persistence** model - means everything that is stored and is not accessible to the clients - e.g. models that are
saved to DBs, caches, disks or cloud storage (e.g. AWS S3)[^1]. One application might have multiple persistence 
models for various reasons - for caching, to back multiple persisted CQRS read views, or any other reason.
* **Internal** model (aka **domain** model) - the in-memory model owned by the application - these are the classes,
objects, methods, data structures and algorithms that make the application tick.

An acute reader would have already noticed that these models have very different use cases, and hence have to take into 
account quite different concerns:

**Public** models are used by external systems and users, so concerns of serialization, version management and 
backward/forward compatibility almost always arise. In some cases these models are influenced by some laws, regulations
or standards.[^2] 

**Persistence** models have to deal with version management, serialization and compatibility too, but 
the more important (and immediate) concerns are efficiency of storage, retrieval and querying of the data. 

**Internal** models almost never need to deal with serialization[^3] or version management - the main goals here are
maintainability, evolveability, "proper" modelling (e.g. following the [Ubiquitous Language][ubiq-lang] in DDD) and 
performance characteristics.

The use cases and concerns handled by each model are quite different, so it calls for separating models from each 
other and evolving them separately. However, there's also an "opposing force" that mainly arises from the increased 
complexity of some changes (e.g. add a new field that has to be both persisted and displayed to the user) and the 
increased up-front effort investment - that pushes in the opposite direction of merging models together (and ideally
having only one model).

Unsurprisingly, there is no universal balance point between these two forces and the "right" solution is the most 
technically sound one that can be afforded given other project circumstances - such as timeline, complexity, importance,
team expertise and so on.
    
[^1]: I don't mean the "physical" representation of the data in the persistence store, but a "logical" representation of 
    this data in your application - e.g. a class that follows database table structure, or a "schema" of JSON objects 
    from ElasticSearch/MongoDB/etc.
[^2]: One common example - accessibility requirements imposed by US federal government on MOOC providers, 
    such as [EdX][edx-accessibility] and [Coursera][coursera-accessibility]
[^3]: with some notable exceptions such as Akka actor messages when [Akka Cluster][akka-cluster] is used.

[edx-accessibility]: https://www.edx.org/accessibility
[coursera-accessibility]: https://learner.coursera.help/hc/en-us/articles/209818883-Coursera-s-accessibility-policy
[akka-cluster]: https://doc.akka.io/docs/akka/2.6.4/serialization.html#introduction
[ubiq-lang]: https://martinfowler.com/bliki/UbiquitousLanguage.html

# How to make compromises (right)?

**Disclaimer:** This is by no means a definitive guide to making decisions, but mere summary of my experience - 
hopefully a useful one.

Let's take a look at the options that we have. There are three logically separate models, that normally relate to each
other like this:

![
    Diagram with three boxes, each representing one logical model: Persistence model to the left,
    Domain model in the center, Public model to the right. One bidirectional arrow goes from persistence to domain and
    another bidirectional arrow goes from domain to API/UI. Public model has a subscript description: API/UI/MQ/etc.
]({{ page.image_link_base }}/separate.svg)
{:.centered}

One thing to note: normally, there are no direct connection between persistence and API/UI models. There are some 
exceptional cases like when the UI has a direct access to the underlying database (e.g. via a GraphQL API exposed by 
the DB itself), but they aren't very common (at least in the organizations I have worked) and anyway are similar to 
one of the compromise solutions we'll explore later.

## Full separation - three models

So, if you just straightforwardly design the application having three distinct sets of classes, each capturing the 
corresponding model, you get the "three separate models" case. As mentioned earlier, this approach separates the 
different concerns best, but also requires most work, and has most moving parts - basically each arrow is a set of 
mappers/converters.

**Pros:** 

* Best separation of concerns - public model, domain model and persistence model can evolve independently.
* Abstraction leaking is significantly reduced and potentially completely eliminated.
* Best alignment with DDD - domain model is independent from both persistence and public model, public model naturally 
    forms Published Language and persistence model is a implementation detail and can be easily swapped, if necessary
    
**Cons:**

* Most up-front effort - the three separate models need to be created; even if it's just a copy-paste operation, it'll
    take some time.
* Most moving parts - application will have to convert between different representations, so some mappers/translators
    must be defined - and they are pure, refined, 100% boilerplate.[^5]
* Some changes become "cross-cutting" - require modification of all the models (and it is very annoying to repeat the 
    same change in three models, and four mappings) 
    
[^5]: There are some libraries that automate defining the mappers and reduce boilerplate significantly - e.g. 
    [automapper][automapper] or [chimney][chimney]
    
[automapper]: https://automapper.org/
[chimney]: https://github.com/scalalandio/chimney

# Conclusion

Small, simple systems - especially microservices  developed with "easier to throw away than modify" approach in mind - 
might get out perfectly well with a single model for all. Three models are the most flexible, but need the most 
boilerplate and sometimes maintenance burden. Compromises, are, well, compromises that try to win in some aspect by 
loosing in some other. Pick the approach that suits your current situation - project timeline, importance of the 
system build, complexity of the domain and infrastructure and so on.
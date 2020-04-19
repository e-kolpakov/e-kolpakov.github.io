---
layout: post
title: The three models in your application
tags: [design-principles]
image_link_base: /assets/img/2020-04-19-three-models
---

It wouldn't be a major overstatement to say that majority of the applications - at least in the startup and enterprise
world - and are built to model and automate certain real-life business processes. As such, the application inevitably
has to have a model - an idealized representation of the "domain" - the entities, events, and interactions found in the 
real-life process. The application also has to do something useful with that model, so it has to interact with
the real world (through UIs, printers, actuators, etc.) and other applications (such as other services, databases, 
queues, etc.). A common shortcut (and/or a caveat) is to use the same model to fulfill all these needs - 
however, this isn't _always_ the best course of action. Let's take a look at other options.

# 10-kilometer-high overview

Before we delve deeper, let me introduce some "temporary" terminology - for brevity and clarity.  

* **Internal** model (aka **domain** model) - the in-memory model owned by the application - these are the classes,
objects, methods, data structures and algorithms that make the application tick.

* **Public** model[^1] - everything that is available to the clients of the system, including other 
services/applications and users. This covers Data Transfer Objects for APIs, models for user interfaces, messages 
published to the queues, data put in caches with "public" access, and so on.

* **Persistence** model[^1] - means everything that is stored and is not accessible to the clients - e.g. saved to DBs, 
caches, disks or cloud storage (e.g. AWS S3). This data is often extracted into an analytics database(s), 
so it is not completely "private" to the application. One application might have multiple persistence models for 
various reasons - for caching, to back multiple persisted CQRS read views or any other reason.

An acute reader would have already noticed that these models have very different use cases, and hence have to take into 
account quite different concerns:

**Public** models are used by external systems and users, so concerns of serialization, version management, and 
backward/forward compatibility almost always arise. In some cases, these models are influenced by some laws, regulations
or standards.[^2] 

**Persistence** models have to deal with version management, serialization and compatibility too, but 
the more important (and immediate) concerns are the efficiency of storage, retrieval, and querying of the data. 

**Internal** models rarely need to deal with serialization[^3] or version management - the main goals here are
maintainability, evolvability, "proper" modeling (e.g. following the [Ubiquitous Language][ubiq-lang] in DDD) and 
performance characteristics.

The use cases and concerns handled by each model are quite different, so it calls for separating models from each 
other and evolving them separately. However, there's also an "opposing force" that mainly arises from the increased
complexity of some changes (e.g. add a new field that has to be both persisted and displayed to the user) and the 
increased up-front effort investment - that pushes in the opposite direction of merging models (and ideally
having only one model).

Unsurprisingly, there is no universal balance point between these two forces and the "right" solution is the most 
technically sound one that can be afforded given other project circumstances - such as timeline, complexity, importance,
team expertise and so on.

[^1]: For both **Public** and **Persistence** models I don't mean "serialized" representation 
    (i.e. JSON/XML/protobuf/etc. encoding), but the "logical" model of the data serialized - i.e. a class that is being
    serialized.

[^2]: One common example - accessibility requirements imposed by US federal government on MOOC providers, 
    such as [EdX][edx-accessibility] and [Coursera][coursera-accessibility]

[^3]: ... with some notable exceptions such as Akka actor messages when [Akka Cluster][akka-cluster] is used.

[edx-accessibility]: https://www.edx.org/accessibility
[coursera-accessibility]: https://learner.coursera.help/hc/en-us/articles/209818883-Coursera-s-accessibility-policy
[akka-cluster]: https://doc.akka.io/docs/akka/2.6.4/serialization.html#introduction
[ubiq-lang]: https://martinfowler.com/bliki/UbiquitousLanguage.html

# What are the options?

Let's take a look at the environment we have. There is a domain model that captures domain logic 
(whatever it means in your case), persistence model that covers saving the state to be read later, and public model 
that handles interaction with other systems or users.

The three models are interconnected by the translators or adapters, except that normally there is no direct connection 
between persistence and API/UI models[^4].

![
    Diagram with three boxes, representing different layers of the application - persistence, domain and "public". 
    The boxes have different fill colors - purple, blue and green.
    Each box contains a smaller one with the titles "persistence model", "domain model" and "public model", respectively.
    The public model has a subscript description: API/UI/MQ/etc.
    Color fills of smaller boxes match those of the larger ones.
    Bidirectional  arrows representing conversions between the models go from "domain model" both to "persistence model" 
    and to "public model". There are no connection between "public" and "persistence" models. 
]({{ page.image_link_base }}/separate_models.svg)
{:.centered}

[^4]: 
    There are some exceptional cases when the UI has direct access to the underlying database - e.g. via a GraphQL 
    API exposed by the DB itself, but they aren't very common and anyway do not change what I'm going to talk about. 
    
The adapters also form a "contraction point" - e.g. a place where we can contract the arrow and merge the two models
on its sides - thus giving us four options:

![
    Four nodes with different color fill - each representing a different approach to separating domain, 
    persistence and public models.
    On the top, there is a node titled "Separate models". In the middle layer, there is "Domain in persistence" and 
    "Domain in public". "Single model" is at the bottom.
    Unidirectional arrows go from "Separate models" to both nodes in the middle layer, and from both nodes in the middle
    layer to the "Single model" - forming a diamond shape.
]({{ page.image_link_base }}/compromises_map.svg)
{:.centered}

## Single model 

![
    The adjusted diagram in the same setting.
    Three application layers are intact. 
    The models are now all merged into one, that spans across all three application layers. 
    The merged model has a different fill color (faint yellow - to give an impression of a mild warning), 
    and the title "Single model". 
    There are no arrows on the diagram.
]({{ page.image_link_base }}/single_model.svg)
{:.centered}

**Single model** is the simplest approach possible - there is just one single model that handles all the concerns the
application has - from persistence to presentation. Needless to say, this is the least flexible approach, and the one
that has the most "leaky abstraction" (in fact, no abstraction at all); persistence concerns and concepts immediately
affect "public" layer and authorization/authentication/multitenancy/etc. normally handled in the "public" layer are
also present at the persistence layer.

However, as this is the simplest and easiest to implement the architecture, it is still viable for a "non-critical" 
systems - such as support/recovery scripts, one time actions, or "true" microservices managing very small domains, 
especially non-core ones.

## Separate models 

![
    Same diagram as the one at the beginning of this section.
    Diagram with three boxes, representing different layers of the application - persistence, domain and "public". 
    The boxes have different fill colors - purple, blue and green.
    Each box contains a smaller one with the titles "persistence model", "domain model" and "public model", respectively.
    The public model has a subscript description: API/UI/MQ/etc.
    Color fills of smaller boxes match those of the larger ones.
    Bidirectional arrows representing conversions between the models go from "domain model" both to "persistence model" 
    and to "public model". There are no connection between "public" and "persistence" models.
]({{ page.image_link_base }}/separate_models.svg)
{:.centered}

**Separate models** - is the most flexible, but most expensive approach. Going this path makes sense for something
that is sought as a "core" system - the one that captures most business logic and value (or in DDD terms - the one that 
models the core domain). The complete separation handles the different concerns best - it becomes possible to perform 
heavy domain refactoring without affecting the clients, swap persistence mechanisms not touching the business logic, 
and so on.

On the downside, this approach requires the most upfront effort and there's also some ongoing cost for the flexibility,
mainly due to conversions between the models being another "moving part" that has some room for error, and thus requires
some maintenance.

## Domain in public

![
    The adjusted diagram in the same setting.
    Three application layers are intact. 
    There are two models now - "persistence" and "domain" are merged  and span across "domain layer" and 
    "persistence layer", but the "Public model" is unchanged and still resides inside the "public layer", having 
    matching fill color with it.
    The merged model has a different fill color (faint yellow - to give an impression of a mild warning), 
    and the title "Domain and Persistence model".  
    There is one bidirectional arrow that represent conversion between the two models.
]({{ page.image_link_base }}/domain_in_public.svg)
{:.centered}

**Domain doubles as public model** - this approach tries to compromise on developing a set of dedicated DTOs and just
use the domain model(s) instead. It can isolate persistence-related concerns from presentation/integration 
(which is good), but auth/presentation concerns are still leaking into the domain model. So "proper" modeling in terms
of DDD is much harder (if not completely impossible) to achieve. Another potential drawback is the leak of domain logic
into the clients if the model is exposed directly as an importable artifact (java jar, npm module, python package, 
etc.) and published to some public or corporate repository.

This is a "compromise" approach that focuses on addressing persistence-related challenges while saving on the
integration and presentation/user experience. It works well for systems that don't exhibit complex domain behavior - 
such as simple CRUD services, utility systems (logging, monitoring, validators, etc.); or for more "exotic" 
architectures, such as ["Data on the outside"][data-outside]

[data-outside]: https://www.confluent.io/blog/data-dichotomy-rethinking-the-way-we-treat-data-and-services/

## Domain in persistence

![
    The adjusted diagram in the same setting.
    Three application layers are intact. 
    There are two models now - "persistence" and "domain" are merged  and span across "domain layer" and 
    "persistence layer", but the "Public model" is unchanged and still resides inside the "public layer", having 
    matching fill color with it.
    The merged model has a different fill color (faint yellow - to give an impression of a mild warning), 
    and the title "Domain and Persistence model".  
    There is one bidirectional arrow that represent conversion between the two models.
]({{ page.image_link_base }}/domain_in_persistence.svg)
{:.centered}

**Domain doubles as persistence** this is one of the most popular "compromises" out there. If you use some ORM
([Django ORM][django-orm], [Hibernate][hibernate] and friends, etc.), chances are high that your application uses this 
paradigm. Moreover, this approach is implicitly endorsed by many technical books - including Vaughn Vernon's 
["Implementing DDD"][implementing-ddd] (aka the Red DDD Book) - as quite often the domain models are taken
straight from the ORM.

This approach is also a compromise - but a different one. Here, the domain model is made "protected" - i.e. it's not
publicly available, but are still not completely "private" to the application - due to persistence and analytics needs.
Overall, it requires more effort compared to the "domain as public" approach, but quite often the heavy lifting can be
left to some 3rd party library (such as Hibernate). 

The solution built this way have presentation and persistence concerns separated, and the conversion between the models
happens in a slightly more "logical" place - at a service boundary - so it is much easier to implement proper DDD 
modeling and patterns such as Anticorruption Layer and Published Language. 

On the other hand, the domain model is still not free from external influence - choice of the persistence mechanism 
affects modeling; as well as external systems aren't *completely* free from the model changes - namely, analytics 
ETLs might need to be adjusted as well. Also, this approach makes it is impossible to implement [Hexagonal][hexagonal] 
architecture style, as persistence "pierces" into the center of the application - making it look more like the 
classical Layered architecture.

[django-orm]: https://docs.djangoproject.com/en/3.0/topics/db/models/
[hibernate]: https://hibernate.org/orm/
[implementing-ddd]: https://www.amazon.com/Implementing-Domain-Driven-Design-Vaughn-Vernon/dp/0321834577
[hexagonal]: https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)

## Which to choose when?

**Disclaimer:** This is by no means a definitive guide to making such decisions, but more of a summary of my 
experience - hopefully a useful one.

* If this is a one-off script - **Single model**
* If this is a prototype - **Single model**
    * unless the prototype has a risk of becoming *"protoduction"* - i.e. a prototype that was not thrown off, but went 
    to production; in that case **Domain in persistence** probably makes more sense.
* If the timeline is very tight and you hope to have some time for refactoring after the end of the project - **Single model**
    * ... if you've already learned the hard way that the time for refactoring never comes - **Domain in persistence**
* If this is a "support" script with some persistence and/or API interfaces to be run regularly (e.g. for cleanup, 
    as a "custom solution" for a single client, etc.) - resist the temptation to go with a single model, and use at least 
    **Domain in public** model.
    * Just in the last two years I've developed three such scripts that later required a major update/overhaul. Having 
    the models separate would help a lot with the update.
* If this is a critical application foreseen to have a long and prosperous life - **Separate models**
    * ... in the pre-release phase it also might be ok to use **Domain in public**, but then it needs to be refactored. 
    * **Domain in persistence** is **not advised** as a compromise here, as it has a much higher probability to entangle 
    the persistence with domain logic to a point where the separation is almost impossible.
* If you're implementing *Hexagonal* architecture - **Separate models**
    * ... in fact, you'd probably need multiple persistence model(s)
* If you're not fully sure about persistence mechanism to be used - **avoid** using **Domain in persistence**

In other cases, both **Separate models** and **Domain in persistence** are viable options - neither having a definitive
advantage. The former calls for a more upfront work and slightly higher maintenance cost, while being more future proof.
The latter gives a faster development and lower maintenance (primarily due to the abundance of the 3rd party libraries
supporting this approach) but ties your application to one particular persistence implementation.  

# Conclusion

All four approaches have the right to exist. Small, simple systems - especially microservices developed with 
"easier to throw away than modify" approach in mind - might get out perfectly well with a single model for all.
Three separate models are the most flexible, but need the most boilerplate and sometimes maintenance burden, but are
the most future-proof. Compromise approaches are in general faster than the "three models" approach
(especially with ORM support) and still, achieve a good deal of isolation of concerns, but aren't as future-proof.

Overall, in my opinion, the "default" should be to go for at least **Domain in persistence** and use the 
**Separate models** if other constraints allow.

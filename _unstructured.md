# Good paragraphs that might be useful in future 

The goal of any distributed system is to provide better availability, throughput, data durability, and other 
non-functional concerns, compared to functionally similar non-distributed system. As always, there's no silver bullet 
or free lunch and these improvements come at a cost - be it weaker consistency, increased deployment and maintenance 
complexity, restrictions in programming model and/or data structures, or all the above and something else on top.



## One ~~ring~~ model to rule them all

This is the most straightforward approach - you just design a single model, and use it everywhere: from persistence to
user interfaces.

**Pros:**

* Lean - this is what you get if you start lean; after all these separate models doesn't add any value to the customers.
* Shorter development time - there's just one model of every concept.
* Least complexity - there are much less "moving parts" in the solution overall.

**Cons:**

* All the different concerns are mixed together and leak into each other (i.e. presentation into persistence 
and vice versa)
* Cannot evolve, change or replace one "layer" without affecting all the others

## Three models

This is the most flexible solution, but the most expensive and complex one as well. You have a dedicated domain model,
persistence model, and "public" model. There could actually be multiple persistence and "public" models, if your 
application is built with a [Hexagonal][hexagonal][^4] architecture style. 

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

[^4]: also known as "Ports and Adapters"

[^5]: There are some libraries that automate defining the mappers and reduce boilerplate significantly - e.g. 
    [automapper][automapper] or [chimney][chimney]
    
    
[automapper]: https://automapper.org/
[chimney]: https://github.com/scalalandio/chimney

[hexagonal]: https://en.wikipedia.org/wiki/Hexagonal_architecture_(software)

## Compromise solutions

### Two models: domain as public

One of the ways to compromise

Pros: persistence concerns are still isolated
Cons: cannot refactor domain without changing public interface; no/little anticorruption layer

### Two models: domain as persistence

Pros: Can evolve public independently from domain - easier to do API version evolution; 
most ORM frameworks already do this 
Cons: harder to add other persistence mechanisms, persistence leaks into domain (harder)
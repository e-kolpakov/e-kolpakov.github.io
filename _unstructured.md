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



# How I applied all this (and what was the outcome) 

Being a technical lead (both by role and by title) and a big proponent of code reviews, I was the main review
powerhouse for the team. When the team size was quite small (2-3 people counting myself), the number of reviews were
quite manageable, so even with very deep code reviews (to the extent where I'd write some small code snippets in
pseudocode and posted them as comments) the load was quite manageable - I probably spent 10-15% of time reviewing
other's code. Even at that time, we had a fair deal of review automation in place - we had shared IntelliJ formatting 
settings, enabled scalastyle checks, and experimented with scalafix (which was abandoned at a certain point though), 
so it helped a lot as well.

However, when the team size has grown to 4-5 people, the amount of code produced by others became much bigger. Moreover, 
somehow people grew accustomed that I'm reviewing all the PRs, and stopped reviewing each other. That gave the team 
even more time to produce the code, so the amount of code I had to review grew even further :smile:. Finally, as
the organization transitioned to a new planning and progress reporting framework, I had to dedicate significant chunks
of my time to those activities.

As a result of all this, I was spending 40-50% of the time in reviews, about 50% in the planning activities, and maybe
had 10% of the time to contribute to the code. This "mode" lasted for weeks - at the end of November 2019 I 
realized that over the last 6 months (June - November) I have merged and deployed about 500 lines of code - just one
pull request.

At that time I've started to employ the "focus" and "delegate" techniques I've mentioned. I've stopped looking at the
less important aspects of code - specifically, naming, formatting, testability, comprehensiveness of test suite, etc.. 
Instead, I have focused on the more subtle and important things - architecture, design, concurrency, edge cases and
so on.

Additionally, I went on vacation :smile:. This helped "reset" the team's habit of leaving all the reviews to me - I 
wasn't there for some time, and they needed to do cross-reviews. When I returned, I have deliberately skipped or
explicitly yielded my review to someone else - at that time I've done it intuitively, but in hindsight, it sort of
helped to reinforce the "new norm".

After all this, I was able to reduce my review load back to 10-15% of my time, while still capturing the good amount
of value from code reviews. So, I haven't counted, but in the next 6 months I've merged about 500-1000 lines of code
per week :smile:. 
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



# Akka persistence

One additional note that touches both _Persistence_ and _Consistency_ is that even with these mechanisms in place, it is 
still possbile to trade consistency for a better performance. Persistent Actor has two APIs for storing the event: 
`persist` and `persistAsync`. While both accept the state-updating logic as a callback (or "continuation") and execute 
it after the persistence is completed, `persist` prevents an actor from processing next message until the callback is 
finished, while with the `persistAsync` it will start working on the next message right away. In our project, we needed 
the consistency, so we always use `persist`.


## Sharding coordinator state issue

The most arcane problem was caused by a combination of increased load (~5x-10x) and "hard" node stops.

*Short detour into the depths of Akka Cluster:* each cluster has a Sharding Coordinator (**SC**) actor that fulfills
certain bookkeeping and administrative duties for the cluster. The **SC** has internal state, and might need to be moved
between the nodes or recovered - thus the state must be persistent. However, the **SC's** state is only relevant to a 
single cluster lifetime - if a cluster is fully shut down or restarted, the **SC's** state from the "previous
incarnation" of the cluster has no use. Because of that, there are two persistence mechanisms for the **SC's** state - 
one that uses Akka Distributed Data, and the other that uses Akka Persistence.

Switching between the two mechanisms is very easy - so, since there were issues and concerns about Distributed Data 
already, the cluster was configured to use Persistence backend for **SC** state - which made it survive the cluster 
restarts as a side effect.

One fine day, during an extensive performance + robustness tests and after mercilessly killing (`kill -9`) an 
unsuspecting node, the cluster become "frozen" - the actors that were not affected by the node crash kept running 
and responding normally, but the ones that were on a crashed node were not even attempting to start and recover. 
Moreover, after "power-cycling" the enitre cluster, it went completely unresponsive - no actors were starting, no 
requests were served, etc. - and such state persisted across partial (some nodes) and full (all nodes) restarts.

Further digging uncovered that somehow **SC's** state was corrupted - causing it to fail at startup, and rendering 
the cluster unable to manage shards and sharding-aware actors. I've never found the root cause[^8] - reproducing the 
failure turned out to be very difficult. Instead, since the probability of the scenario was low, I've decided to just 
document the symptoms and recovery steps - which were to simply wipe the **SC** state and start anew.   

**Lesson learnt:** if there is one thing that can take your entire system down - it eventually will, even if it is 
extremely robust. Better have a plan for a speedy recovery if that situation materializes.

[^8]: one theory that matches observations is that the state update requires two operations - one to persist state
update record itself, and the other is to update the counter of persisted state records. Somehow, the counter was 
updated. but the actual record was lost, which made the state integrity check fail on the grounds of "expected N state 
records, but found only N-1".   
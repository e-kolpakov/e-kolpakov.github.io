---
layout: post
title: Doing Dependency Inversion right
tags: [design-principles]
image_link_base: /assets/img/2020-03-14-doing-dependency-Inversion-right
---

Dependency Injection is a well-known pattern and de-facto standard for implementing a [Dependency Inversion
Principle][DIP]. Most modern frameworks have some level of support for Dependency Injection - from weaving the 
application via public setters at runtime using XML as a spec (e.g. [Java Spring][spring]), to compile-time 
constructor injection (e.g. [macwire](https://github.com/softwaremill/macwire)). However, while doing most of
the heavy lifting, these tools and frameworks leave capturing the more sophisticated and valuable promises of DIP 
to the developers. Sadly, most of the time the result is.... _suboptimal_ :smile: - that is to say it is not completely
wrong, but could have been better. This shortcoming is subtle, but "getting it right" often solves or even removes
a lot of other questions/concerns - including some that spawn "both implementations are fine, let's discuss 
which one to choose till the thermodynamic death of the Universe" discussions.

[DIP]: https://web.archive.org/web/20110714224327/http://www.objectmentor.com/resources/articles/dip.pdf
[spring]: https://docs.spring.io/spring/docs/current/spring-framework-reference/core.html#beans-factory-metadata
[spring-annotations]: https://docs.spring.io/spring/docs/current/spring-framework-reference/core.html#beans-annotation-config

# Dependency Inversion Principle

To recap, the precise definition of DIP is as follows ([see page 6][DIP]):

> A. High-level modules should not depend on low-level modules. Both should depend on abstractions (e.g. interfaces).
>
> B. Abstractions should not depend on details. Details (concrete implementations) should depend on abstractions.

To make it more concrete, let's consider the classical "layered" architecture[^1].

This is how it usually looks like _before DIP is applied_ (arrows show the direction of dependencies):

![
    Classical layered diagram: API/UI/Presentation layer on the top, Application layer under it, 
    Domain layer below Application, Infrastructure layer at the bottom. 
    Arrows go from API to Application, domain and infrastructure; from Application to Domain and Infrastructure;
    from Domain to Infrastructure.
]({{ page.image_link_base }}/layered-classical.svg)
{:.centered}

Then someone remembers about DIP and realizes that "infrastructure" layer is technically the lowest level - so "domain"
and "application" should not depend on it - and draws a new diagram:

![
    Inverted layered diagram: Infrastructure layer at the top, API/UI/Presentation layer below it, 
    Application layer under it, Domain layer at the bottom. 
    Arrows go from Infrastructure to all other three; from API to Application and Domain; from Application to Domain.
]({{ page.image_link_base }}/layered-inverted.svg)
{:.centered}

[^1]: The same logic is valid for the more advanced architectures too, (e.g. Hexagon), "layered" is chosen for 
    simplicity and because "everyone knows it".
    
... or maybe the team has started with DIP in mind right away, so that's their actual architecture diagram from the 
get-go. In any case, the next step is to implement it in code - and this is where that _suboptimality_ I'm talking
about creeps in.

# How to do DIP in code 

Ok, both sentences in DIP definition can be boiled down to "interfaces should depend on interfaces, 
implementations should depend on interfaces (and not other implementations)". That's easy - we just convert 


```java
public class HighLevelComponent {
    private final LowLevelComponent dependency;
}

public class LowLevelComponent { ... }
``` 

to 

```java
public class HighLevelComponent {
    private final ILowLevelComponent dependency;
}

public interface ILowLevelComponent { ... }
public class LowLevelComponentImplementation implements ILowLevelComponent { ... }
```

And already we start reaping numerous benefits of DIP - we can now replace implementations (including plugging test 
doubles), code high-level component to completeness not even having a low-level component started (against a test
double or "simplified" implementation) and our code is already somewhat better documented.

However, let me put some more context into it - what if our high-level component and low-level component belonged to a
different layers - e.g. domain and infrastructure?

```java
package foo.bar.domain
public class ClientService {
    private final IClientRepository dependency;
}
public class Client { ... }

package foo.bar.infrastructure
public interface IClientRepository { void save(Client entity); }
public class InMemoryClientRepository implements IClientRepository { void save(Client entity); }
```

Can you spot the problem? There is one[^2].

Just in case it's not apparent - `domain.ClientService` depends on `infrastructure.IClientRepository`, which makes the
app look more like the first diagram, whereas we wanted the second one. What's worse - the dependency not only goes in
the undesired direction but actually is two-way:

* `domain.ClientService` depends on `infrastructure.IClientRepository`
* `infrastructure.IClientRepository` -> `domain.Client`

... and we're one step closer to "everything depends on everything else" aka Big Ball of Mud.

[^2]: pun intended.

# Solution

Unsurprisingly, the solution is already invented. It was right there, in the plain sight, in the [paper][DIP] where
the Dependency Inversion Principle was coined (page 7, figure 4). It just didn't make it to the "short" description.

So, I give you The Missing Part of The Dependency Inversion Principle:  

>
C. Implementations should depend on abstractions in the same layer as they are. Implementations can implement
abstractions from the higher layers, or the same layer.

The best thing about it is that it's not too hard to implement in code. Continuing on our `Client` example:

```java
package foo.bar.domain
public class ClientService {
    private final IClientRepository dependency;
}
public interface IClientRepository { void save(Client entity); }
public class Client { ... }

package foo.bar.infrastructure
public class InMemoryClientRepository implements IClientRepository { void save(Client entity); }
```

The only thing changed _in the code_ is the move of the `IClientRepository` interface into the `domain` layer. However, 
_conceptually_ (or _semantically_) it changes a lot:

1. It becomes apparently clear that repositories in the domain layer should speak "domain" language[^3] - i.e. receive
and return domain objects. If infrastructure needs a dedicated persistence model, it becomes the responsibility of the
infrastructure to map the domain model to the persistence model and back.
2. It removes "circular" dependency between domain and infrastructure
3. It helps keep the domain clean of infra - if this approach is applied persistently, the domain layer becomes a leaf
in the dependency tree, as all the implementations only depend on "same layer" interfaces.
    1. ... which gives an ability to develop domain logic before the gory details of infrastructure are known
    2. ... and swap infra in the middle of the project, or three years down the line
4. It puts an additional barrier on "leaking" persistence/messaging/other infrastructure concerns and concepts into 
the domain model (which is a constant battle in DDD-based projects)

... and probably some other less obvious benefits.

[^3]: This removes the question of "should DB repositories use domain model or persistence model?" - the one
    that often spawns "both implementations are equivalent..." discussions (at least in my current team), and needs 
    careful monitoring in the code reviews afterward.
    
## Bonus track: code smells

There are two code smells that indicate "part C" is not observed and are quite easy to spot.

**Analyze imports:** Ctrl+Shift+F (or equivalent hotkey for "Search in Folder" command) in the "domain" package. 
Any hits for "infrastructure" or other lower-level layers are good indicators that something is not right. Obviously 
works not only for "domain" and "infra", but any pair of packages you'd want to check.

**`impl` packages or `*Impl` class name suffixes:**[^4] this means that the implementation implements an abstraction 
from the same package - which almost always means 'the same architecture layer'. Not an offence on it's own, but
chances are high that the interface in question belongs to a higher layer. 

[^4]: Yes, I'm attacking a Java best practice. Yes, I know what I'm talking about. Yes, I'm sure :smile: 

# Conclusion

Dependency Inversion Principle in the real world is quite often reduced only to the "interface abstraction" - replacing
concrete dependencies with abstract ones and leveraging Dependency Injection to keep the app running. However, it
prevents from reaping all the benefits of DIP - such as clearer isolation of application layers - that in turn bring
even higher productivity and code quality benefits.

Although refactoring to the "proper DIP" is relatively straightforward, the bigger benefit is the change in the ways
developers think about the system at hand - so while it is easy (if not even "mechanical") to change the code, it's not
as easy to change the principles. So realizing full DIP potential calls for mindset change 
(and lots of explaining :smile:).

---
layout: post
title: A guide to build a house of tests
tags: [testing]
---

There is a well-known and widespread unit/integration/function/end-to-end taxonomy of tests that describe _what_ is 
tested - single program component, single service or an entire solution. There is also a less known taxonomy of _how_
testing is performed - from not having tests at all to the current golden standard of "single method - single test 
case" to a more advanced techniques - I sometimes call it "levels" or "floors" of testing, as they build upon each 
other. Interestingly, "buildings" of all levels deserve to exist as each "floor" has its pros and cons - taller 
"buildings" are generally harder to build and maintain - so choosing the right "height" is important for long-term 
success.

# A guide to build a house of tests

Ok, so let's agree on some terminology first.

Let's call layers of the [Test Pyramid][test-pydamid] **"layers"** - these describe _what_ is tested - a single class, 
a system, an ecosystem of microservices, or an entire application/solution.

Let's call different approaches and techniques to testing **"floors"** - these describe _how_ testing is performed -
specifically, how tests are created, executed and reported on.

**Layers** and *floors* are orthogonal - in fact, the higher the **layer**, the harder it is to use "high" *floors*.
For example, one can have *property-based* **unit tests** supported by *"standard"* **integration tests**.

[test-pyramid]: https://www.google.com.sg/search?q=software+test+pyramid&tbm=isch

> NB: "integration testing" term is a bit overloaded - especially in the space of microservices architectures. There's
an _inter_service integration tests, that verify how different services interact with each other; and _intra_service
tests that usually verify how the service behaves as a whole. To disambiguate, I'll call the former "functional" tests,
and the latter - "integration" tests.

## Zero-floor building (aka no building at all)

Sometimes you really don't want to bother building a house - a temporary accomodation will work just as good. Think of
a camping site - even though you need to have some roof over your head, you won't build a house - more likely to place 
a tent or something similar.

In software world, the analogy of a camping site is an one-time, an infrequently used or a very small software. In such 
cases, investing into test infrastructure is quite often not justified - the task can be completed faster and with 
acceptable quality without it.

Other notable use case in this category is testing Infrastructure as Code. A good test should execute "code under test",
and for IaC executing essentially means creating all that infrastructure and running certain assertions against it. 
This inevitably poses multiple challenges:

* there needs to be some isolated environment where that infrastructure would be provisioned
* it almost inevitably incurs costs, sometimes significant costs

So, for smaller organizations it quite often makes sense to keep the IaC code at "no tests" level, especially when the 
infrastructure is still small and can be comprehended easily.

**Pros:** fastest to achieve - there's literally nothing to do
**Cons:** everything else

## Single floor landed house (aka bungalow, aka cottage)

When we speak about testing, by default we mean this level. Even though historically testing started one level below,
this has become the default - tests are written and executed using some 3rd party testing framework, such as JUnit,
`unittest`, `specs`, etc.

Let's go to the basement first.

### Detour: a cabin

A module under test exposes a separate entrypoint - a dedicated method or special combination of input parameters - 
that triggers module's self check using language's built-in assertion mechanisms, such as `assert` statements.

This can be stretched to entire programs - just provide a separate `Main` class, or pass environment variable.  

Pros: does not need extra tools; fast to implement (good choice for coding interviews); better than nothing
Cons: test code is shipped with "production" code; hard to validate edge cases;

# Basement 2: No tests

Sometimes the right amount of tests is no tests at all. Think of one-time scripts, early prototypes and other throwaway
code. In such cases, investing time into writing tests will not pay out - unless developer embraced TDD to the extent
when they are more efficient with TDD than without.

Pros: low effort
Cons: everything else

Now, having seen the deeps, let's checkout the heights.

# Level 2: Data-driven tests

Need to test corner cases and failures.
"Classical" framework approach is quite verbose - one test per input.
Data-driven tests (e.g. python's `ddt`) reduce the boilerplate by providing means to write "parameterized" tests
JUnit parameterized tests are somewhat weak and still verbose - practically it requires one class per method (
but maybe I overlooked something). 

Simply put, for each test several inputs are given, and test checks if the assertions hold for all the inputs.
Generally it is advised to avoid complex logic (loops, conditionals) inside the body of the data-driven test. 

# Level 3: Generator-driven property-based tests

Property-based: evaluate certain property for given inputs.
Works well with pure functions, but could be stretched to verify side effects as well. Beware: not all mock libs work
well in prop-based tests.

Table-driven property-based - this is in fact a data-driven test, slightly rebranded and lifted into property-based
framework infrastructure.
 
Generator-driven property-based - you may call it "data-driven on steroids" - instead of _defining_ inputs developer 
tells the test framework how to _generate_ them. The test framework then generates _all_ possible inputs and checks 
the assertions... in theory. In practice, since resources are finite and inputs' space is usually quite large, test 
framework semi-randomly generate a finite set of inputs - `scalacheck` uses 100 by default.

If generators are written well, the generated inputs will include edge cases.
 
Building generators is an up-front investment, but they are highly reusable:
* they _compose_, which makes it possible to define a "composite" generator from the two existing ones
* one can use the same generator in multiple tests


# Level 4: Command-driven tests

This is actually uncharted territory to me. The idea here is to make generator that would generate initial state of the 
application and sequence of commands be executed, run it, and verify the output. This is actually quite close to fully 
automated program correctness verification - as generator can generate all the possible inputs and command sequences it
would evaluate the program under all possible use scenarios - again theoretically.

# Conclusion

Pick the right level - the higher you go, the more upfront investment and more senior team is needed, but benefits are
numerous. Generator-driven tests can even uncover failures one wouldn't even think about - e.g. built-in string 
generator spits entire range of unicode characters, including higher panes of unicode, non-printable characters and 
other weird stuff.2
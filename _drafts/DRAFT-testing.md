---
layout: post
title: A house of testing techniques
tags: [testing]
---

# Overview

Testing became a must-have part of the software development cycle .

Layers: unit/integration/end-to-end
Levels: complexity/sophistication of test setup
 
Layers and levels are orthogonal - one can have data-driven unit tests and classical end-to-end tests; in fact, the
higher the layer, the harder it is to use "high" levels. 

# Ground level: "Normal" tests using some testing framework 

When we speak about testing, by default we mean this level. Even though historically testing started "one level below",
this become the default - tests are written and executed using some 3rd party testing framework, such as JUnit,
`unittest`, `specs`, etc.


Let's go to the basement first.

# Basement 1: Separate entrypoint

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
other weird stuff.
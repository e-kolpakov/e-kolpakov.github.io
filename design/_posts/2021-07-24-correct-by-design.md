---
layout: post
title: "Correct by design"
tags: ["design principles"]
image_link_base: /assets/img/DRAFT-correct-by-design
---

Building software is hard. Building _correct_ software - the one that does what it is supposed to do - is even harder.
There are many well-known tools to achieve correctness _after_ writing the code: manual QA, linters, tests, 
code reviews, etc. However, ensuring correctness _during_ or even _before_ writing the code - or making it very hard to
produce incorrect code - is also possible. There isn't a single tool, technique, or framework that magically makes your
software correct. Achieving it requires some discipline and adherence to a design principle: "design for correctness."

# Correct by design

## What is it?

The idea is simple - **when creating a software system, build it in a way that incorrect usage is 
impossible, or at least impractical**.

Like any good design principle, this idea can apply at multiple levels - from overall system design to individual 
functions and lines of code. A few examples:

* System level: using a message queue to prevent data loss when the consumer is down, supporting offline mode 
  for web-based applications.
* Application or service level: published interface (aka API spec), validating inputs.
* Module, package, or subsystem level: `package` (or `internal`) access modifier, dependency inversion, "entrypoint" interfaces.
* Class level: constructor injection (vs. property injection or builder pattern), 
  [segregated interfaces][segregated-interface].
* Function level: using explicit `Option[Result]` instead of nullable as a return type.

As you can see, there is one thing in common between all examples - they enforce correct use, or at least make it 
obvious and straightforward.

[segregated-interface]: https://en.wikipedia.org/wiki/Interface_segregation_principle

## How does it help? What's the cost?

The benefit of following this principle is relatively straightforward - the software based on this principle would be
much more robust, bug-free, and easy to use. An additional benefit is that every engineer
working on such a codebase will make fewer mistakes - which means higher productivity and velocity. What's more, 
engineers new to the codebase built with "correct by design" in mind will reach productivity much faster and start 
contributing earlier.

The "at what cost" question is trickier. There are multiple tools, practices, and solutions that can be employed - 
each having a different learning curve, quirks, and complexities. In general, one should expect to see less
"liberty" and more "enforcement" from the tool/language/frameworks[^1], and sometimes more boilerplate code.

[^1]: "enforcement" ranges from "having to check for nulls" on one end of the spectrum to "having to
    implement complex class hierarchies" on the other end.


### Example

To illustrate, let's consider a frequent use case - validation - and apply one of the correct-by-design techniques - 
["make it impossible to represent illegal states in the program"][unrepresentable-illegal-states]

[unrepresentable-illegal-states]: https://khalilstemmler.com/articles/typescript-domain-driven-design/make-illegal-states-unrepresentable/#Make-illegal-states-unrepresentable

A naive implementation might look like this:

```scala
case class UserProfile(name: string, email: string, phoneNumber: string)

def promptUser(): UserProfile
def validate(user: UserProfile): Try[UserProfile] { ... }
def registerUser(user: UserProfile): void { ... }

// usage
val userProfile = promptUser()
val validatedProfile = validate(userProfile)
validatedProfile match {
    case Success(validatedProfile) => registerUser(validatedProfile)
    case Failure(error) => ... report validation error ...
}
```

This code is correct, but it does a poor job enforcing that only valid users are sent into `registerUser` - validating
the user before registering them becomes the developer's responsibility. Nothing prevents a careless or unaware 
developer to do

```scala
val userProfile = promptUser()
registerUser(userProfile)
```

... and cause all kinds of problems down the line[^2].

A relatively simple change makes the check enforced  - "`registerUser` only accepts validated users" needs to be
encoded in a way that compiler/typechecker/linter/any-other-tool-in-your-toolchain can enforce it. The same example
rewritten with this enforcement in place might look like this:

```scala
case class UserProfile(name: string, email: string, phoneNumber: string)
case class ValidatedUserProfile(name: string, email: string, phoneNumber: string)

def promptUser(): UserProfile
def validate(user: UserProfile): Try[ValidatedUserProfile] { ... }
def registerUser(user: ValidatedUserProfile): void { ... }

// usage
val userProfile = promptUser()
val validatedProfile = validate(userProfile)
validatedProfile match {
    case Success(validatedProfile) => registerUser(validatedProfile)
    case Failure(error) => ... report validation error ...
}
```

This version makes doing the right thing straightforward and almost prohibits calling `registerUser` without 
validation[^3] - at the cost of an additional class. It might seem like a no-brainer, but the more complex the data
structure becomes, the more boilerplate classes developer has to create. Eventually, it might become prohibitively 
expensive - so some balance needs to be stricken.

[^2]: The example might seem a little shallow, as one can easily thwart it by a simple counterargument "validating 
    input before using it is a basic hygiene everyone must follow." However, consider that the `registerUser` might be 
    three-four layers deep in the dependencies tree - this makes the situation much less apparent and the 
    probability of a mistake much higher.

[^3]: the remaining loophole is creating `ValidatedUserProfile` directly - which is _obviously_ wrong, and if necessary 
    can be further hardened by making `ValidatedUserProfile` have a private constructor. 

## Ok, I'm in. How should I go for it?

You should ask two questions:

1. How can this thing I'm building can be misused?
2. What can I do to prevent it?

Those are pretty generic and high-level questions - you might need to refine them to make them answerable. Also, 
finding the answers will require a good deal of creativity, imagination, expertise, language and framework knowledge, 
and some tools and tricks in your toolbelt.

To help you get started, I'll list some starter questions - obviously, not even remotely comprehensive, but should
serve as a good starting point for your research and analysis.

**System and application levels:**

* How to ensure no data loss? 
* What happens if infrastructure (DBs, network, etc.) or dependency (other services) fail?
* How to reject invalid commands and user actions? 
* Are concurrent updates to the same data possible? If yes, how to prevent data corruption? 
* Are there any "derived data"? If so, how to make sure it is updated when "source of truth" changes? 
* Are there any "implicit concurrency" between user actions[^4]?
* Are there any "mutable" configuration parts - the ones that can change during a single run?

**Module, package, and subsystem levels:**

* How module/package/subsystem initialization should happen?
* How should it signal errors and exceptional situations?
* Fail fast vs. gracefully degrade - reject invalid data/commands right away, or still try to execute as much as 
  possible?

**Class and function levels:** 

* How to make sure callers provide all necessary data and dependencies?
* How to make sure callers use the result correctly (especially nulls and exceptions)?
* Is there a rigid sequence of calls that has to happen in order? If so, how to enforce it?
* Are there any "implicit" dependencies (shared mutable state, static references, etc.)?


[^4]: example (taken from [Designing Data-Intensive Applications][ddia]) - unfriending person X on social 
    network and then sending a message to all friends. The expected outcome is that X does not receive the message.
    However, if different servers handle the actions, it is not automatically guaranteed.

[ddia]: https://dataintensive.net/

# Conclusion

"Correct by design" is a powerful design principle - it improves not only the result (application, service, or library)
but also developer productivity and onboarding speed. However, practicing "correct by design" often requires walking 
an extra mile to build the same features, so it is not always justified. Moreover, finding gaps to close and solutions 
to close them requires a good deal of experience, expertise, and creativity.

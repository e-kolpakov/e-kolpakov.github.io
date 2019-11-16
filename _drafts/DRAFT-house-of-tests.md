---
layout: post
title: A guide to build a house of tests
tags: [testing]
github_link_base: https://github.com/e-kolpakov/e-kolpakov.github.io/tree/testing/_code/2019-11-12-house-of-tests
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
For example, one can have *property-based* **unit tests** supported by *standard* **integration tests**.

[test-pyramid]: https://www.google.com.sg/search?q=software+test+pyramid&tbm=isch

NB: "integration testing" term is a bit overloaded - especially in the space of microservices architectures. There's
an *inter*service integration tests, that verify how different services interact with each other; and *intra*service
tests that usually verify how the service behaves as a whole. To disambiguate, I'll call the former "functional" tests,
and the latter - "integration" tests.
{:.message}

## What do we test, exactly?

To be more specific, let's write some code to be tested. One quite common shortsight of many tutorials, how-tos and
manuals is to pick a very simple use case to avoid unnecessary complexity and focus attention on the topic itself. 
However, it is than quite challenging to translate it to a more complex situations of real life. So, I'll use not one, 
but three examples:

1. A function without any side-effects (aka pure function)
2. A method on a class that takes a parameter
3. A class with a dependency.

For brewity though, I'll use only small subset of the examples in the post text, and full examples can be found at 
[GitHub][examples]

[examples]: {{ page.github_link_base }}

Here's the code under test:

~~~python
from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta

@dataclass
class User:
    id: int
    name: str
    date_of_birth: date

    def is_older(self, other) -> bool:
        assert(isinstance(other, User))
        return self.date_of_birth < other.date_of_birth

def age_at(user: User, date: date) -> int:
    return max(relativedelta(date, user.date_of_birth).years, 0)

class UserRepository:
    def get(self, id: int) -> User: pass
    def save(self, user: User) -> None: pass

class UserService:
    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    def read_user(self, id: int) -> User:
        return self._repo.get(id)

    def update_user_name(self, id: int, new_name: str):
        old_record = self._repo.get(id)
        old_record.name = new_name
        self._repo.save(old_record)
~~~

This is not a TDD session, so we're **not** going to evolve this code - it's already doing what it is supposed to and
doing it right (I've tested that!)

## Zero-floor building (aka no building at all)

![](/assets/img/2019-11-12-house-of-tests/tent.jpg){:.image.inline-text-wrap.right}

Sometimes you really don't want to bother building a house - a temporary accomodation will work just as good. Think of
a camping site - even though you need to have some roof over your head, you won't build a house - more likely to place 
a tent or something similar.

In software world, the analogy of a camping site is an one-time, an infrequently used or a very small software. In such 
cases, investing into test infrastructure is quite often not justified - the task can be completed faster and with 
_acceptable quality_[^1] without it.

Other notable use case in this category is testing Infrastructure as Code. A good test should execute "code under test",
and for IaC executing essentially means creating all that infrastructure and running certain assertions against it. 
This inevitably poses multiple challenges:

* there needs to be some isolated environment where that infrastructure would be provisioned
* it almost inevitably incurs costs, sometimes significant costs
* it's hard to come up with non-tautological assertions. Example of tautology: check that [aws_instance][aws-instance] 
  creates an AWS EC2 instance.
* ... and so on

Because of that for smaller organizations it quite often makes sense to keep the IaC code at "no tests" level, 
especially when the infrastructure is still small and can be comprehended easily.

**Building to this level:** a conscious decision to not _"waste"_ time on testing.\\
**Pros:** fastest to achieve - there's literally nothing to do.\\
**Cons:** everything else.\\
**Should I get here:** proooobably not, unless you know what you're doing, and why,\\

[aws-instance]: https://www.terraform.io/docs/providers/aws/r/instance.html

[^1]: That is, something that is acceptable short-term and someone will rectify the issues/tech debt if this piece of 
    software suddenly becomes very important or long-living. 

## Single floor landed house (aka bungalow, aka cottage)

![](/assets/img/2019-11-12-house-of-tests/bungalow.jpg){:.image.inline-text-wrap.right}

When we speak about testing, by default we mean this - tests are written and executed using some 3rd party testing 
framework, such as JUnit (and friends/clones/forks), `unittest`, `specs`, etc.

Long story short, our test suite will look like this ([full listing][example-standard]):

[example-standard]: {{ page.github_link_base }}/test/test_user.py

~~~python
# user_fixtures.py
class Users:
    jack = User(1, "jack", parser.parse("1999-01-01"))
    jill = User(2, "Jill", parser.parse("2001-06-14"))
    jane = User(3, "Jane", parser.parse("2003-01-01"))

# test_user.py
class TestAgeAt(unittest.TestCase):
    def test_age_at_birth(self):
        self.assertEqual(age_at(Users.jack, Users.jack.date_of_birth), 0)

    def test_age_at_some_random_date_after_birth(self):
        self.assertEqual(age_at(Users.jill, parser.parse("2019-11-11")), 18)

    def test_age_at_16th_birthday(self):
        self.assertEqual(age_at(Users.jack, parser.parse("2015-01-01")), 16)

    def test_age_before_born(self):
        with self.assertRaises(AssertionError):
            age_at(Users.jack, parser.parse("1990-01-01"))
~~~
{:.long-code}

Pretty straightforward and unsurprising, right? The main thing here is that we have each test case represented by a 
dedicated method.

**Building to this level:** Getting here requires some effort - how much exactly varies between languages, frameworks 
and build tools - for the majority of them it's just following the convention/setting up the required configuration.\\
**Pros:** I won't delve too deep into describing the advantages of actually having some automatic tests as they are very 
well known, but in short it makes capturing errors earlier, increases developer productivity and gives confidence in the 
software we build.\\
**Cons:** Major disavantage that actually gives raise to the next "level" is tediousness: single test case is a single 
method.\\
**Should I get here:** Absolutely, unless you're happy in a tent.
  
[pytest]: https://docs.pytest.org/en/latest
[rspec]: https://rspec.info/
[scalatest]: http://www.scalatest.org/

### Detour: a cabin

![](/assets/img/2019-11-12-house-of-tests/cabin.jpg){:.image.inline-text-wrap.right}

One other interesting approach is to save a bit on the setting up the test infra, and just use the built-in language 
features. In such case, the module under test exposes a separate entrypoint - a dedicated method or special combination 
of input parameters - that triggers module's self check using language's built-in assertion mechanisms, such as 
`assert` statements. This approach can even be stretched to cover "integration test" cases - just provide a separate 
`Main` class, or pass an environment variable.

Example:

```python
# ints.py
def multiply(i1: int, i2: int) -> int:
    return i1 * i2


def self_test():
    assert(multiply(1, 2) == 2)
    assert(multiply(3, 4) == 12)
    print("Tests passed")

# executing tests:
import ints
ints.self_test()
```

This seems hacky (and indeed it is), as the test code is shipped with the production code, but it is less of a problem
here, as test code doesn't add any dependencies and require no installation actions. Moreover, some languages have 
certain level of support for this "feature" - e.g. python has [doctest][doctest] module that allows writing and running
tests in the documentation strings.

```python
def reverse_string(input: str) -> str:
    """
    This is a docstring  to illustrate doctests

    >>> reverse_string("Hello!")
    '!olleH'
    >>> reverse_string("")
    ''
    >>> reverse_string('Привет!')
    '!тевирП'
    """
    return input[::-1]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
```

**Building to this level:** the effort required here is significantly less than proper test infrastructure would need - 
  you just use the built-in language features for everything that test framework does - from test discovery to 
  assertions.\\
**Pros:** does not need extra tools and fast to implement (good choice for coding interviews).\\
**Cons:** test code is shipped with "production" code, limited to built-in assertions and language features, not well
  suited for large codebases and test suites.\\
**Should I get here:** Not really, unless you've overgrown the tent, but still can't afford a proper place.

[doctest]: https://docs.python.org/3.8/library/doctest.html

## Two-storey house

![](/assets/img/2019-11-12-house-of-tests/2-storey.jpg){:.image.inline-text-wrap.right}

One thing about tests that is missed way too often is that _good_ suite of tests exercise not only "happy path" on 
"common case", but also a range of cases with "normal" inputs, edge cases, and potential failures. Simply put, ideally
the test suite define the limits of the applicability of the code under test, and then test it's behavior:
 
* _inside_ the limits and with multiple different inputs
* _at_ the boundary - also known as edge cases
* ... and _outside_ of the applicability area, to make sure that code behavior is still reasonable

The issue is, "multiple good inputs" and "bad inputs" are almost always unintentionally overlooked or intentionally 
skipped. There aren't much that can be done to address the unintentional overlooking - forcing the branch coverage can 
partially help, but it has it's limitations[^2]; keeping an eye on it during code reviews is an option, but prone to 
human error. However, the "intentionally skipped" can be mostly cured - as most if it comes from the fact that testing
all that pesky corner cases is quite tedious and time-consuming.
     
The cure ~for the itch~ is called _data-driven_ tests[^3] or _parameterized_ tests. The idea is simple - quite often the
behavior can be described as a collection of reference inputs and expected outputs/behaviors. Instead of having each 
test case pick single input case, let's instead write the test case as a function that accept inputs/outputs as 
arguments and assert on expected behavior. This makes creating large suits of test cases (1) much less tedious (which
we programmers hate) and (2) much more creative and expressive (which we love). 

Most of the mainstream test frameworks either provide parameterized tests feature (e.g. [JUnit][junit-parameterized], 
[NUnit][nunit-parameterized], [Boost.Test][boost-test]), have 3rd-party plugin libraries that provide that feature 
(e.g. python [ddt][ddt], [scalacheck][scalacheck-table-driven]) or can leverage on existing language features (e.g. 
[go][go-parameterized], Scala).

So, here's our test suite extended to use data-driven test ([full listing][example-ddt]):

```python
@ddt.ddt
class TestAgeAt(unittest.TestCase):
    @ddt.unpack
    @ddt.data(
        (Users.jack, Users.jack.date_of_birth, 0),
        (Users.jill, parser.parse("2019-11-11"), 18),
        (Users.jack, parser.parse("2015-01-01"), 16),
        (Users.jane, parser.parse("2203-01-01"), 200),
    )
    def test_age_at(self, user, date, expected_age):
        self.assertEqual(age_at(user, date), expected_age)

    @ddt.unpack
    @ddt.data(
        (Users.jack, parser.parse("1990-01-01")),
        (Users.jane, Users.jane.date_of_birth - timedelta(seconds=1)),
    )
    def test_age_before_born(self, user, date):
        with self.assertRaises(AssertionError):
            age_at(user, date)
```

This style makes it really easy to add more cases if necessary, so handling multiple "normal" cases and edge cases 
becomes trivial. This testing style literally forces to think of edge cases and applicability limits. 

One caveat is that handling different behaviors (e.g. normal output vs. exception) still better be done via adding more
test methods. While sometimes it might make sense to have one data-driven test that covers entire range of behaviors of
code under test, this usually can only be done via loops or conditional inside the test body - and having logic in the 
test body is usually discouraged. If you weren't _yet_ bit by the complex logic in the tests - just trust me, I've been
there and myself guilty of that crime.

**Building to this level:** effort is quite different between if you're building a new test suite and decide to go to 
  this level straight away, or re-building an existing codebase - I'd actually suggest to let the existing test live as
  they are, and only gradually migrate when changing actual code. In any case, building to this level requires a small,
  but sensible shift in thinking - one should start thinking of code under test _explicitly_ in terms of inputs, 
  outputs, behaviors and invariants.\\ 
**Pros:** Much less tedious and more creative, "forces" to think about applicability limits and edge cases.\\
**Cons:** Some test frameworks/languages requires additional dependencies (albeit those dependencies are usually 
  lightweight); somewhat incentivize complex tests that has logic in them; requires some change in thinking.\\
**Should I get here:** I would strongly recommend - data-driven tests are a very useful tool that _multiplies_ 
  developer productivity in writing tests, while also improving the quality of test suite (i.e. better coverage, 
  easier to read&understand, etc.) 
  
[^2]: How many branches does this implementation have `def string_size_in_bytes(a): return len(a)`? 
    And how many corner cases? And how many bugs (spoiler: utf-8)?
[^3]: Fun fact - acronym of data-driven test (DDT) is the reverse of test-driven development (TDD).
    
[junit-parameterized]: https://github.com/junit-team/junit4/wiki/Parameterized-tests
[nunit-parameterized]: https://github.com/nunit/docs/wiki/Parameterized-Tests
[boost-test]: https://www.boost.org/doc/libs/1_59_0/libs/test/doc/html/boost_test/tests_organization/test_cases/test_case_generation.html
[ddt]: https://ddt.readthedocs.io/en/latest/index.html
[scalacheck-table-driven]: http://www.scalatest.org/user_guide/table_driven_property_checks
[go-parameterized]: https://github.com/golang/go/wiki/TableDrivenTests
[example-ddt]: {{ page.github_link_base }}/test/test_user_ddt.py

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
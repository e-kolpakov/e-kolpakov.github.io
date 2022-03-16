---
layout: post
title: Building tests - part 2
github_link_base: https://github.com/e-kolpakov/e-kolpakov.github.io/tree/master/_code/2020-01-19-building-tests
image_link_base: /assets/img/2020-01-19-building-tests
---

In this post, we continue on the topic (and examples) set up in the [Building tests - part 1][part1] to explore a more
sophisticated and powerful - yet more heavyweight - approaches to testing.

This post consists of two parts:

* [Part 1][part1] - sets up general background and covers the "simpler" approaches to testing.
* [Part 2][part2] - continues on to talk about more sophisticated techniques necessary to build higher "buildings" 
(YOU ARE HERE).

[part1]: {% post_url testing/2020-01-19-building-tests-part1 %}
[part2]: {% post_url testing/2020-01-26-building-tests-part2 %}

## Generator-driven property-based tests - a mansion with an attic (and a garage in the basement)

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/mansion.jpg)

[Image][orig-mansion] by GerritHorstman
[Pixabay Licence][pixabay-licence] 
{:.image-attribution}

[orig-mansion]:https://pixabay.com/ru/photos/%D0%BE%D1%81%D0%BE%D0%B1%D0%BD%D1%8F%D0%BA-%D0%B0%D1%80%D1%85%D0%B8%D1%82%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0-%D0%B3%D0%BE%D1%80%D0%BE%D0%B4-%D0%B7%D0%B4%D0%B0%D0%BD%D0%B8%D0%B5-4320168/

</div>

The main idea at this "level" is quite simple and builds on the foundation of data-driven tests - one might call it 
"data-driven on steroids" - instead of _defining_ the inputs developer tells the test framework how to _generate_ 
them[^1]. The test framework then generates _all_ possible inputs and checks the assertions... in theory. In practice, 
since resources are finite and inputs' space is usually quite large, test framework semi-randomly generate a finite set 
of inputs - e.g. `scalacheck` uses 100 by default. This approach works especially well with pure functions (which are 
completely defined by their inputs and outputs), but could be stretched to verify state and side effects as well[^2]. 

[^1]: Give a man a fish...

[^2]: One caveat here though - assertions on side effects are most often performed with the help of mocks/stubs, but 
not all mock libraries work well in property-based test.

The property-based tests were conceptualized by the authors of [QuickCheck][quick-check] and date back to the early 
2000s. Since then, QuickCheck was ported (or adapted) to virtually all mainstream languages - examples are 
[scalacheck][scalacheck] for Scala, [hypothesis][hypothesis] for python, [Gopter][gopter] for Go and many others.

In property-based testing, developer task is to define two things: instructions to create inputs - called `generators` 
and "what to test" - called `properties`. Test library/framework then adds a ton of other machinery that wires the 
generators and properties together, and verifies properties under multiple inputs coming from the generators (via 
`runners`), reports successes/failures (using `reporters`) and automatically tries to find the minimal example for the
failing tests (using `shrinkers`).

If generators are written well, the generated inputs will include edge cases that can uncover failures one wouldn't 
even think about - e.g. `scalacheck` built-in string generator produces entire range of unicode characters, including 
higher panes of unicode, non-printable characters and other weird stuff. Building generators is an up-front investment, 
but they are highly reusable:
* generators _compose_, which enables using one generator as an input to the other or "join" multiple generators to 
    form a more complex one
* property-based frameworks usually provide built-in features to restrict the range of outputs coming from the generator
    without defining a new one
* same generator can be used in multiple tests

The bigger challenge, however, is defining "good" properties - the ones that confirm the desired behavior, and also 
fail when this behavior is not observed. The two major caveats are "tautological" tests, that partially or fully repeat 
the code under test; and "self-fulfilling" ~~prophecies~~ properties that are always true. Avoiding them obviously 
depends on the code at hand, but there are a few ideas/approaches that are generally applicable, such as:

1. Round-trip identity testing - `json.serialize(json.deserialize(input)) should === input` 
2. "Generate more" - `forAll(Arbitrary.string, Arbitrary.string) { (left, right) => left + right should startWith left }`
3. "Work backwards" - generate the expected output first, then obtain or generate the input that is supposed to 
produce this output - `forAll(Arbitrary.string) { plain => md5_hash = md5(plain); hash_cracker(md5_hash) should === plain }`
4. "Oracle" - a simpler (maybe even naive) and 100% correct implementation 
`forAll(Gen.nonEmptyListOf(Arbitrary.int)) { input => max(input) should === sort(input).head }`

[quick-check]: http://hackage.haskell.org/package/QuickCheck
[scalacheck]: https://www.scalacheck.org/
[hypothesis]: https://hypothesis.readthedocs.io/en/latest/
[gopter]: https://github.com/leanovate/gopter

I think that's enough of theory for this post (for those who want more, [this youtube video][prop-based-testing-youtube]
might be a good place to start), let's take a look how our test suite would look under this testing paradigm (
[full listing][prop-based-full-listing]).

[prop-based-testing-youtube]: https://www.youtube.com/watch?v=shngiiBfD80

```python
# user_generators.py
import hypothesis.strategies as st
from src.user import User

user_id_gen = st.integers(min_value=1)  # not really required, just to demonstrate composeability
user_gen = st.builds(User, user_id_gen, st.text(), st.datetimes())

# user_test_properties.py
class TestAgeAt(unittest.TestCase):
    @given(user_gen, st.datetimes())
    def test_age_at_tautological(self, user, date):
        # FIXME: this is an example of tautological test - DO NOT DO THIS
        assume(user.date_of_birth <= date)
        expected_age = relativedelta(date, user.date_of_birth).years
        self.assertEqual(age_at(user, date), expected_age)  # property

    @given(user_gen, st.integers(min_value=0, max_value=1000), st.data())
    def test_age_at_backward(self, user, age, data):
        assume(user.date_of_birth.year + age <= 10000)  # relativedelta doesn't like year 10000 and above
        # one of the techniques to define a property - work backwards from the output to the input that will produce it
        check_age_at = data.draw(st.datetimes(
            min_value=user.date_of_birth + relativedelta(dt1=user.date_of_birth, years=age),
            max_value=user.date_of_birth + relativedelta(dt1=user.date_of_birth, years=age+1) - timedelta(microseconds=1),
        ))
        self.assertEqual(age_at(user, check_age_at), age)  # property

    @given(user_gen, st.datetimes())
    def test_age_before_born(self, user, datetime):
        assume(user.date_of_birth > datetime)
        with self.assertRaises(AssertionError):  # property
            age_at(user, datetime)
```

[prop-based-full-listing]: {{ page.github_link_base }}/test/test_user_properties.py

Overall, this is quite an advanced technique that calls for a certain change in developers' way of thinking about the
code. However, in my practice even junior developers with 1-2 years of experience, provided with good guidance and 
ample examples, were able to grasp the concepts and write very good suits of property-based tests.

**Building to this level:** Writing property-based tests require even further change in thinking - think about 
  more general "properties" that hold for all the possible inputs (or at least a subset of them). Creating the
  generators usually requires upfront effort, but usually it is quite fun. Another challenge is avoiding 
  tautological and "test nothing" properties - which is a constant effort.\\
**Pros:** Cover even more ground compared to data-driven tests; able to exercise very subtle, narrow and rare edge 
  cases - preventing bugs from lurking there; provides a different view on the code from documentation perspective, as 
  tests define general properties that hold for the code, not the behavior at particular inputs.\\
**Cons:** Requires significant change in thinking; has a subtle and somewhat hard-to-avoid (especially to new folks) 
  caveats; significant up-front investment into defining generators.\\
**Should I get here:** This is where it starts to become controversial - on one hand there is increased complexity and 
  more room for misusing the framework itself - this might be detrimental to productivity and makes onboarding new 
  team members harder (although, not much). On the other hand, there are significant and desireable advantages, as 
  well as some fun and satisfaction from using such an advanced techinque.

## Model-based testing (aka stateful testing) - a castle with moat (and a dungeon, and probably a dragon)

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/castle.jpg)

["Stereotypical Castle complete with moat"][orig-castle] by Mark Denovich
[![](/assets/icons/cc_licenses/cc-by-nc-sa.png){:.cc_icon}][cc-by-nc-sa-2] 
{:.image-attribution}

[orig-castle]:https://www.flickr.com/photos/denovich/2772278150

</div>

As with previous "levels", **stateful testing** builds on the previous one - generator-driven tests - and tries to 
address an even more challenging task: checking system-under-test behavior under *series* of interactions.

In a nutshell, the idea is simple - let's introduce classes that represent actions/operations performed on the SUT[^2] - 
e.g. with our `UserRepository` example commands would be `UpdateUserName(...)` and `ReadUser(...)`. Since actions are 
now representable as object instances (i.e. data, not just code), one now can define generators for the actions, 
which obviously makes it possible to generate sequences of actions.

[^2]: This technique is also known as _Command_ pattern.

The other part of the equation is to define how the system's state evolve under the commands. 
[`Scalacheck`'s stateful testing][scalacheck-stateful] suggests some sort of "oracle" approach - for each command 
developer defines expected state evolutions using a simplified representation of the SUT's internal state, and 
postconditions - which are used by the scalacheck to perform assertions on the state and verify implementation 
correctness.

[scalacheck-stateful]: https://github.com/typelevel/scalacheck/blob/master/doc/UserGuide.md#stateful-testing

As usual, let's take a look of how tests in this style would look like, using `hypothesis`'s 
[stateful testing][hypothesis-stateful]. The approach here is slightly different from Scalacheck's though - the test is
represented as a state machine, and assertions are encoded in the state transitions.

[hypothesis-stateful]: https://hypothesis.readthedocs.io/en/latest/stateful.html#stateful-testing 

```python
#user.py
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._store = dict()

    def get(self, id: int) -> User:
        return self._store.get(id)

    def save(self, user: User) -> None:
        # if len(self._store) > 2:  # some non-trivial buggy code to trigger the error
        #     return
        self._store[user.id] = user

# test_user_stateful.py
import unittest
from hypothesis.stateful import RuleBasedStateMachine, rule, Bundle
from src.user import User, InMemoryUserRepository
from test.user_generators import user_id_gen, user_gen

class InMemoryUserRepositoryFSM(RuleBasedStateMachine):
    def __init__(self):
        super(InMemoryUserRepositoryFSM, self).__init__()
        self.repository = InMemoryUserRepository()
        self.model = dict()

    users = Bundle('users')

    @rule(target=users, user=user_gen)
    def add_user(self, user):
        return user

    @rule(user=users)
    def save(self, user: User):
        self.model[user.id] = user
        self.repository.save(user)

    @rule(user=users)
    def get(self, user):
        assert self.repository.get(user.id) == self.model.get(user.id)


InMemoryUserRepositoryTest = InMemoryUserRepositoryFSM.TestCase
```

This is actually a very short example - [full listing][stateful-full-listing] only contains the above and the 
usual `unittest` boilerplate. However, this test is capable of catching quite subtle implementation bugs that would be 
quite hard to test otherwise - e.g. the one that is commented out in the repository code.

[stateful-full-listing]: {{ page.github_link_base }}/test/test_user_stateful.py


**Building to this level:** Almost inevitably requires a simpler model of the system-under-test - e.g. an in-memory 
    implementation of repository - so such model needs to be created. On top of that, some sort of encoding of actions
    is necessary (explicit command objects in scalacheck, rules in hypothesis, etc.), and then maybe pre-/post- 
    conditions, pre-/post- invariants, action applicability rules ("can I apply action X if the state is Y") and 
    more...\\
**Pros:** Gives ability to capture bugs/inconsistent behavior that arise in the system over multiple interactions - 
    e.g. due to some issues with accumulated state. Basically generates _the tests themselves_.\\
**Cons:** Requires a simpler model of the system-under-test - which is not always possible, and quite often not simple;
    risk of bugs in the "simpler model" itself, or in the ecnoding of actions/state transitions/etc.\\
**Should I get here:** Actually, depends on the complexity of the state/behavior. With simple and straightforward state
    and transitions, it might be actually faster and easier to go straight to the model-based/stateful testing as 
    opposed to virtually any other testing technique. However, it mostly relies on being able to define a simpler model
    of the system (similar to the "oracle" in prop-based testing) - which might be challenging in side-effect heavy
    implementations.

# Conclusion

Just as everywhere else, there is no "silver bullet" with regards to "how sophisticated my test suite should be?". 
There are multiple factors at play - from increasing confidence (which calls for 100% _edge case_ coverage) to developer
productivity (which reminds that tests does nothing to solve the business problem at hand) - and as such some balance 
needs to be found. Unsurprisingly, balance differs between technologies, projects and teams - while small/simple 
codebases might do just fine with a rudimentary or even non-existent test suites, investing up-front into more 
sophisticated test suites quite often pays off for a larger solutions with long lifetimes. 

[pixabay-licence]: https://pixabay.com/ru/service/license/
[cc-by-nc-sa-2]:https://creativecommons.org/licenses/by-nc-sa/2.0/
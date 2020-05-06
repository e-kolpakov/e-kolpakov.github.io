---
layout: post
title: What to look for in the code review
tags: [development-processes]
image_link_base: /assets/img/DRAFT-what-to-look-for-in-code-review
---

Code reviews is an integral part of modern software development workflow, and a highly debated one. A lot is said on
why code reviews are important (e.g. [Atlassian][atlassian-cr], [Fullstory][fullstory-cr]), how to do them 
([Google][google-cr]), what to look for ([JetBrains][jetbrains-cr]), etc., etc. Some teams published their how-to&best 
practices ([Palantir][palantir-cr], [Perforce][perforce-cr]) and some people event built their businesses around the 
code review process ([Doctor McKayla][doctor-mckayla]). There's no shortage of "internet wisdom" on the topic, but
there's one quite common flaw that might influence "your mileage" from applying code reviews quite significantly and
actually cause them to harm your team's productivity. In short, different aspects of the code (design, performance,
security, style, naming, etc.) have a very different cost of mistake vs. cost of finding it during code review. Let's
take a look at how this affects "what you should look for in code reviews".

[atlassian-cr]: https://www.atlassian.com/agile/software-development/code-reviews
[fullstory-cr]: https://blog.fullstory.com/what-we-learned-from-google-code-reviews-arent-just-for-catching-bugs/
[google-cr]: https://google.github.io/eng-practices/review/reviewer/
[palantir-cr]: https://medium.com/palantir/code-review-best-practices-19e02780015f
[perforce-cr]: https://www.perforce.com/blog/qac/9-best-practices-for-code-review
[jetbrains-cr]: https://blog.jetbrains.com/upsource/category/practices/
[code-review-series]: https://www.michaelagreiler.com/code-review-blog-post-series/
[doctor-mckayla]: https://www.michaelagreiler.com/

# Start with Why

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/golden_circle.png)

Wikimedia Commons; [![](/assets/icons/cc_licenses/cc-by-sa.svg){:.cc_icon}][cc-by-sa]
{:.image-attribution}

</div>

Let's follow [the advice of Simon Sinek][start-with-why] and start by recalling *why* are we doing the code review. 
I'll take the liberty to shortcut through the detailed list of benefits of code review, and put it into one nice and 
concise sentence:

>  Ultimate **goal** of code reviews is to improve team productivity.

Now, don't get me wrong, things like better code quality, faster knowledge dissemination, developer satisfaction, etc. 
are important, but they are all **means** to achieve the goal, not the goal itself. They either contribute to 
productivity directly - e.g. less bugs in production - or enable some qualitative "features"[^1] that ultimately also 
contribute to productivity - such as developer stress levels.

There's one thing though - productivity is essentially "the amount of value produced in a unit of time". When code
reviews are adopted by the team, some time is obviously spent on code reviews. However, the code reviews themselves 
rarely, if ever, produce the "value"[^2] - they capture issues in the already developed code. In this aspect, they are
similar to tests - don't add anything to the business value, but aim to catch potential issues that might prevent 
from capturing this value.

So, we can now clearly see that on one hand code reviews improve productivity, but on the other hand they harm 
productivity :smile:. In situations like these, there's some balance point where the net effect is best. 
Finding the balance becomes an optimization computation when the problem can be formalized, or an art in all other 
cases. Unfortunately, things like "productivity" and "value" (save for developer stress) are quite hard to formalize,
so code reviews fall into the "art" bucket.

[start-with-why]: https://www.ted.com/talks/simon_sinek_how_great_leaders_inspire_action

[^1]: Such as the ability to go on vacation and not worry about being pulled back due to production issue
[^2]: The definition of value for a software project is vague, but for simplicity let's say it is "features shipped"

# The Art of ~~War~~ finding the balance

... or the "How" part.

What we're trying to do is to find the balance between effort spent in code reviews (both on the reviewer and on the 
author side), and the "improvement" of the code that comes from it. There are multiple approaches to go about it

## Focus

Obvious way to do so is to focus on an "important" parts, and leave unimportant behind. There's no single definition of 
"important" and "unimportant" parts; moreover, they might be dramatically different across organizations, teams and 
individuals[^3]. However, some relative order can be established - for example, adherence to an external API contract 
is much more impactful compared to code style.   

Broadly, the aspects can be categorized into four groups:

**Critical** - mistake/bug here might have severe consequences and are hard to detect: security, adherence to 
the chosen architecture and design, algorithms performance (aka asymptotic complexity), concurrency issues, 
configuration.
**Major** - issues in this group have a major impact, but are either easy to spot or can be caught by the comprehensive
test suite: outright functional defects, correctness at the edge cases, validation, adherence to the standards, 
database migrations.
**Minor** - something that impacts the application, but you can imagine going to production without it and still 
fulfilling the needs: logging/monitoring/traceability, comprehensiveness of tests, error handling.
**Nitpicks** - something that has limited impact on the code quality and no impact on the application/business function:
naming, code style, indentation (aka tabs vs. spaces holy war), typos, documentation, testability, readability.

This is by no means a comprehensive and final list - some teams might have different approach (e.g. for a bigger part
of my time with my current team I had "naming" in the **Minor** section, and only recently changed my mind), but it 
should give a general idea of what's what. But let me emphasize one thing: **the more obvious issues are not the most
important ones in code review** - the more subtle ones are much more useful to the author, and future maintainers.

## Automate

5.1. Automate everything that can be automated - code style, tests, formatting, static analysis, etc.

## Delegate

5.2. Distribute/delegate - leads/EMs check high-level concepts (design, contracts, standards, security, etc.), SSEs do 
the bugs, performance, logging, etc.; more junior folks - basic typos, naming, code conventions, etc.

[^3]: For example, one might say that readability is not that important - unless it's a total mess of course; on the 
other hand "readability matters" is one of the commandments of the "Zen of Python" - so there's an entire language 
community that would disagree. 

3. Too shallow code review doesn't capture most of the value; too deep code review takes too much time
5. Optimize what to look for



6. My story - ever increasing code review load, to the point where I was not coding myself, only code reviewing 
(40% of time) and other stuff. Started to delegate more 

Being a technical lead (both by role and by title) and a big proponent of code reviews


# Personalities in code review

First, let's take a small step back and look at the process as a whole. Obviously, there are at least two involved 
parties - code author and code reviewer. In some cases there might be more then one reviewer - e.g. for additional 
scrutiny, when code is co-owned/co-dependent by multiple teams, or when some "specialized" review is necessary (e.g.
security, accessibility, etc.). A closer look also shows that people in different roles and seniority levels might be 
looking for different things in the code and pursue slightly different goals:

**Junior developers** might not be qualified (or at least confident) enough to criticize the code, so normally their 
primary goal in the code review is to learn. Nevertheless


[cc-by-sa]: https://creativecommons.org/licenses/by-sa/3.0
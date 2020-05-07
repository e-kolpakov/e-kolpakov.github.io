---
layout: post
title: Optimizing code reviews
tags: [development-processes]
image_link_base: /assets/img/2020-05-07-optimizing-code-reviews
---

Code reviews are an integral part of modern software development workflow and a highly debated one. A lot is said on
why code reviews are important (e.g. [Atlassian][atlassian-cr], [Fullstory][fullstory-cr]), how to do them 
([Google][google-cr]), what to look for ([JetBrains][jetbrains-cr]), etc., etc. There's no shortage of "internet wisdom"
on the topic, but there's one quite common flaw that might influence "your mileage" from  code reviews quite 
significantly and cause them to harm your team's productivity. In short, different aspects of the code (design, 
performance, security, style, naming, etc.) have a very different cost of making a mistake vs. cost of finding it 
during code review. Let's take a look at how this affects the review process ("what to look for") and a few techniques 
that can help improve it.

[atlassian-cr]: https://www.atlassian.com/agile/software-development/code-reviews
[fullstory-cr]: https://blog.fullstory.com/what-we-learned-from-google-code-reviews-arent-just-for-catching-bugs/
[google-cr]: https://google.github.io/eng-practices/review/reviewer/
[jetbrains-cr]: https://blog.jetbrains.com/upsource/category/practices/
[code-review-series]: https://www.michaelagreiler.com/code-review-blog-post-series/

# Start with Why

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/golden_circle.png)

[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Golden_circle.png);
[![](/assets/icons/cc_licenses/cc-by-sa.svg){:.cc_icon}][cc-by-sa]
{:.image-attribution}

</div>

Let's follow [the advice of Simon Sinek][start-with-why] and start by recalling *why* are we doing the code review. 
I'll take the liberty to shortcut through the detailed list of benefits of code review, and put it into one nice and 
concise sentence:

>  The ultimate **goal** of code reviews is to improve team productivity.

Now, don't get me wrong, things like better code quality, faster knowledge dissemination, developer satisfaction, etc. 
are important, but they are all **means** to achieve the goal, not the goal itself. They either contribute to 
productivity directly - e.g. fewer bugs in production - or enable some qualitative "features"[^1] that ultimately also
contribute to productivity - such as developer stress levels.

There's one thing though - productivity is essentially "the amount of value produced in a unit of time". When code
reviews are adopted by the team, some time is spent on code reviews. However, the code reviews themselves rarely, if
ever, produce the "value"[^2] - they capture issues in the already developed code. In this aspect, they are
similar to tests - don't add anything to the business value, but aim to catch potential issues that might prevent from
capturing this value.

So, we can now clearly see that on one hand-code reviews improve productivity, but on the other hand, they harm
productivity :smile:. In situations like these, there's some balance point where the net effect is best. 
Finding the balance becomes an optimization computation when the problem can be formalized or an art in all other cases. 
Unfortunately, things like "productivity" and "value" (save for developer stress) are quite hard to formalize,
so code reviews fall into the "art" bucket.

[start-with-why]: https://www.ted.com/talks/simon_sinek_how_great_leaders_inspire_action

[^1]: Such as the ability to go on vacation and not worry about being pulled back due to the production issue
[^2]: The definition of value for a software project is vague, but for simplicity let's say it is "features shipped"

# The Art of ~~War~~ finding the balance

... or the "How" part.

What we're trying to do is to find the balance between effort spent in code reviews (both on the reviewer and the 
author side), and the "improvement" of the code that comes from it. Again, a lot is said on the topic already, and I 
won't repeat the "prerequisite" things like "define the team norms", "agree on the code style", "set up a framework for 
reviews" and so on. There's a very good and concise write up by one of my former colleagues: 
["How to prevent code reviews from slowing down your team"][how-to-prevent-code-reviews-from-slowing-down-your-team],
definitely check it out.

There are three techniques that (in my opinion) are the most overlooked, and the most efficient:

* Focus - do the important things, don't do the unimportant ones (sincerely yours, Captain Obvious).
* Automate - let the computers run the ~~world~~ review.
* Distribute and delegate - you're not doing it alone.

[how-to-prevent-code-reviews-from-slowing-down-your-team]: http://www.sheshbabu.com/posts/how-to-prevent-code-reviews-from-slowing-down-your-team/

## Focus

<div class="image-with-attribution inline-text-wrap right" markdown="1" aria-hidden="true">
   
![]({{ page.image_link_base }}/focus.gif)

[Poke Watching GIF](https://giphy.com/gifs/cat-watching-window-Vfie0DJryAde8) via [GIPHY](https://giphy.com/)
{:.image-attribution}
</div>

This sounds obvious at first, but please bear with me. The simple (and trivial) idea is to focus on an "important" 
parts and leave unimportant be as they are. The non-trivial part is that there's no single definition of "important" 
and "unimportant" aspects; moreover, they might be dramatically different across organizations, teams and 
individuals[^3]. However, some relative order can be established - for example, adherence to an external API contract 
is much more impactful compared to code style.   

Broadly, the aspects can be categorized into four groups:

**Critical** - mistake/bug here might have severe consequences and is hard to detect: security, adherence to 
the chosen architecture and design, algorithms performance (aka asymptotic complexity), concurrency issues, 
configuration, backward/forward compatibility.

**Major** - issues in this group have a major impact, but are either easy to spot or can be caught by the comprehensive
test suite: outright functional defects, correctness at the edge cases, validation, adherence to the standards, 
database migrations.

**Minor** - something that impacts the application, but you can imagine going to production without it and still 
fulfilling the needs: logging/monitoring/traceability, comprehensiveness of tests, readability, error handling.

**Nitpicks** - something that has a limited impact on the code quality and no impact on the application/business 
function: naming, code style, indentation (aka tabs vs. spaces holy war), typos, documentation, testability.

This is by no means a comprehensive and final list - some teams might have a different approach, but it should give a 
general idea of what's what. For example, your team might value near-100% test coverage, self-documented code and full 
support for distributed code tracing - in such cases the corresponding items should move up or down the 
"importance" scale. But let me emphasize one thing: **the more obvious issues are not the most important ones in 
code review** - the subtler ones are much more useful to the author as well as future maintainers.

[^3]: For example, one might say that readability is not that important - unless it's a total mess of course; on the
    other hand "readability matters" is one of the commandments of the "Zen of Python" - so there's an entire language
    community that would disagree.

## Automate

Another technique is to use the cold, rational machines to do the review. This helps in two ways:

1. Computers excel at boring, repetitive tasks - the ones humans hate. So your human reviewers are relieved from
reviewing those code style/formatting/order of imports/etc./etc. stuff and can focus on something important (see the
section above).
2. It removes human touch from the simplest (and thus most obvious and annoying) comments - such as code formatting -
thus reducing the tension and stress levels in the team.

So, the thing is, the more you automate - the better.

![Automate all the things!]({{ page.image_link_base }}/automate.jpg)

However, some thought needs to be put here as well - certain things can be automated, but the effort vs. benefit might
not be good enough. For example, at [Redmart][redmart] we had [Sonarqube][sonarqube] enabled on all the repositories. 
It was doing its job fine for the teams using Java, but my team(s) used Scala - and we quickly realized that Sonarqube
produces more false positives than valid warnings, and eventually disabled it in our repositories.

Anyway, here's something that can be automated:

1. Code style - use autoformatter, e.g. [scalafmt][scalafmt], [gofmt][gofmt] or your IDE formatter. Make sure that all
team members (and ideally the whole organization) use the same formatter configuration.
2. Static code analysis - tools like [flake8][flake8], [scalastyle][scalastyle], [Sonarqube][sonarqube] and the likes 
help you capture more "semantic" errors/issues - like undefined variables, bad naming, or high 
[cyclomatic complexity][cyclomatic-complexity].
3. Test comprehensiveness - many services report code coverage (e.g. [codecov][codecov]) and they can be
easily integrated with your CI tools and version control service (Github, GitLab, Bitbucket) to block merging unless
code coverage targets are met. 
4. Services like [AWS Code Guru][aws-code-guru] or [deepcode][deepcode] aim to provide even more insightful automatic
reviews by utilizing AI and ML.
5. Performance reviews can theoretically be replaced by an automatic performance stress-test, so tools like 
[gatling][gatling], industry veteran [JMeter][jmeter], or [locust][locust], integrated with your Continuous Integration
service can help with that.
6. [Let your compiler work for you][compiler] - leveraging rich type system can let your compiler do the _correctness_
check for you - the code with an error won't even compile. 

[compiler]: https://www.youtube.com/watch?v=zbGiOcSeq1Y
[redmart]: https://redmart.lazada.sg/
[sonarqube]: https://www.sonarqube.org
[scalafmt]: https://scalameta.org/scalafmt/
[gofmt]: https://blog.golang.org/gofmt
[flake8]: https://pypi.org/project/flake8/
[scalastyle]: http://www.scalastyle.org/
[cyclomatic-complexity]: https://en.wikipedia.org/wiki/Cyclomatic_complexity
[codecov]: https://codecov.io/
[aws-code-guru]: https://aws.amazon.com/codeguru/
[deepcode]: https://www.deepcode.ai/
[gatling]: https://gatling.io/
[jmeter]: https://jmeter.apache.org/
[locust]: https://locust.io/

## Delegate

<div class="image-with-attribution inline-text-wrap right" markdown="1" aria-hidden="true">
   
![]({{ page.image_link_base }}/delegate.jpg)

[Delegate](https://www.peakpx.com/433890/delegate-board); 
[![](/assets/icons/cc_licenses/CC0.svg){:.cc_icon}][cc0]
{:.image-attribution}
</div>

Software development teams rarely consist of just two developers (although, I've been in such a team for some time). 
This means that there is more than one person to do the review. So, having multiple people who can review something
can be utilized in multiple ways. The most common is to just increase the thoroughness of the review - i.e. just have
more eyes on the code - to (theoretically) catch more issues.

The less obvious one is to distribute and delegate the parts of the code review among multiple reviewers. This becomes
a sort of trivial and natural in cases where certain skills are only found in certain individuals in the team. But even
when it is not the case, delegation might help a lot, and even help with team building, to some extent.

In essence, I'm talking about distributing reviewing different aspects of the code to people of different seniority and 
expertise. This allows more senior people to focus on the more impactful parts, and still have more junior folks to
play an integral and important role in the code review process. Simply put

**Lead/Staff/Principal** engineers review the high-level aspects (security, design, etc. - see the "Critical" list in 
the [Focus][focus] section). 

**Senior/Middle** engineers dig down and watch for algorithmic complexity, bugs, alternative implementation, etc.; 

**Junior** guys focus on naming, code style, existence and quality of the documentation and so on.

Some care needs to be applied here as well - the distribution and allocation must not become rigid and exclusive - you
don't want the quality of your code reviews to decline just because your only lead engineer went on vacation, or left
the company. Even in "normal" conditions, that guy might become overloaded with reviews - and harm either his
productivity or the team.

[focus]: #focus

# Conclusion

Code reviews aren't free lunch (there's no such thing anyway). The effort spent on reviewing the code can be as well
spent on something that has a business or technical merit - be it new features, bug fixes, or refactoring and adding
more tests. Moreover, the people who are better qualified to do the reviews, are also your more senior people - so
reducing the load on them can help in multiple ways - from more stuff built by them, to better knowledge sharing,
public presence and intellectual property building. In this post, I've described techniques that helped me a lot to
reduce the load on myself - focus, automation and delegation - and I hope you find it useful.

Thanks for reading, and let let me know what you think on [Twitter][twitter-post-link].

[twitter-post-link]: https://twitter.com/EugenyKolpakov/status/1258291344146968576

[cc0]: https://creativecommons.org/share-your-work/public-domain/cc0/
[cc-by-sa]: https://creativecommons.org/licenses/by-sa/3.0

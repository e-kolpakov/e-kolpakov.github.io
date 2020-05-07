# Good paragraphs that might be useful in future 

The goal of any distributed system is to provide better availability, throughput, data durability, and other 
non-functional concerns, compared to functionally similar non-distributed system. As always, there's no silver bullet 
or free lunch and these improvements come at a cost - be it weaker consistency, increased deployment and maintenance 
complexity, restrictions in programming model and/or data structures, or all the above and something else on top.




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
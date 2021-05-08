---
layout: post
title: Tech Lead - things to do, not to do, and delegate
tags: [development-processes]
---

So, you now have a mysterious *Tech Lead* role. It might have happened due to a promotion (congrats!),
team reorganization, changing jobs, or in a few dozens of other ways. No matter which path took you here, things will
never be the same. The most substantial change is that you're not a 100% individual contributor anymore - your scope of 
responsibility is broader than one person can handle alone. To be successful, you'll need to undertake a psychological 
change - let go of controlling (or even doing yourself) many things and trust the team you have to get them done. 
On the other hand, there are some subtle, easy-to-overlook aspects of work you should influence and shape to make the 
team effective and efficient. I'm offering my views on what a Tech Lead should and should not do in this post.

# Things you should do

It isn't an exhaustive list, but there are three major themes to what you should be doing: ensuring technical success,
influencing the team's external environment and "cultivating" a team.

## Ensuring technical success

**Ensure the solution design and architecture is sound** - this is the highest-leverage technical activity 
one can find. Mistakes and suboptimal decisions made at the design phase will hamper everything else, and good choices 
made here make everything else[^1] easier. So, making more great decisions here is your topmost priority. However, 
there is a caveat - it might be tempting to design the solution on your own. Resist it - by doing so, you are missing 
to tap into the knowledge and expertise of other teammates, and you're stealing from them the opportunity to practice 
and get better at it. A good option is to delegate to a Senior Software Engineer(s) and help them create a solid design.

**Provide technical direction and advice to engineers** - engineers on your team will face challenges from time
to time. Challenges of different natures - could be a complex algorithm to grasp, a complicated piece of code, 
a controversial technical tradeoff to make, or even "if we should implement this feature at all?" sometimes. In such 
cases, they will need your help, knowledge, expertise, guidance, and sometimes just decision-making 
("yes we should").

**Keep an eye on non-functional aspects** - things such as performance, monitoring, logging, analytics, and so on 
are often overlooked or even sacrificed in favor of product features and on-time releases. Not paying attention to them 
will come back and bite your team - in the form of bugs, increased recovery time from failures, lack of data to make
decisions, etc. Someone has to keep an eye on them - and that someone is likely you[^2].

**Build the most critical parts of the solution** - this one is simple; you've proven to be a strong engineer in 
the past, so you're capable of doing this stuff. At a Tech Lead role, it helps you build your
reputation and authority in the team - your teammates will notice you dive deeper and solve problems harder than anyone
else - and they'll trust you more.

**Make sure your team's code works smoothly with the rest of the ecosystem** - your organization has some 
ecosystem - even if it is a one-person startup[^3]. Your team's code should be a good citizen in that ecosystem - use 
the amenities it provides (for example, deployment facilities or logging aggregation services) and adheres to 
limitations it imposes. The ecosystem also includes other services/applications/tools your code should interact with - 
and your team's code should "click" with them: use the agreed-upon APIs and communication protocols, 
do what it advertises, etc.

[^1]: "Everything else" being not only implementation, testing, and stabilization phase, but also maintenance, 
    operability, evolution, etc.

[^2]: I've noticed a correlation between seniority and attention to non-functional aspects. My theory is that the 
    non-functional aspects are taught neither by formal education nor in the online courses/guides - so learning them 
    comes only with practice and exposure. If you're the most experienced person, you probably know the do's and don'ts 
    around non-functional aspects better than anyone else - and hence is best equipped to deal with them.

[^3]: ...in which case you're not a Tech Lead and should not be reading this :smile: - you're a founder and inventor, 
    so go, change the world, we are all rooting for you!

## Influence team environment

**Support and influence cross-functional decisions** - the software you build is not a goal in itself - it is 
a means to achieve something. As such, product decisions depend on what we can and cannot achieve with the software and
timelines at hand. It is your responsibility to "provide a price tag" to solutions and help shape the decisions. 
Don't hesitate to propose innovative solutions as well!

**Build trust with sibling teams and cross-functional partners** - quite often, you'll have most context about
what your team is doing, and what is needed to achieve success. "What is needed" at times includes things outside of 
your control - for example, changes in other team's codebase, smaller images to improve website performance, etc. 
In such cases, you own the success criteria and need to make sure the work done by the other team meets them. In an 
ideal world, they will nail it on the first attempt; but chances are you'll need to go through a few 
iterations before everything is made right. Invest into building trust with the other relevant teams - even if only to 
make sure they take your honest "this won't do it, we need XYZ" won't be met with negativity.

## "Cultivate" the team

I'm using the gardening term *"cultivate"* on purpose here - the process of improving the team and individuals is much
more like growing a garden compared to building an engine. The latter is "putting pieces together in the right order,"
while the former is "creating conditions where this thing will improve itself."

**Help your teammates grow** - you are likely the most senior person on a team regarding expertise, experience, 
and level/title. You probably have already been where they want to go, so help them plot the course. You have the 
knowledge and skills necessary to progress - help them obtain the same (or similar). 

**Shape team's engineering processes and culture** - "team productivity" is not just a sum of teammate's 
productivities - it could be less than that or much more than that. The difference lies in engineering processes and
culture - how to structure the day-to-day operations so that the whole is greater than the sum of its parts. One of 
your responsibilities is to make the team productive and efficient, so you're the primary stakeholder in establishing 
the engineering goals, norms, processes, etc. Just don't dictate your will and vision - other teammates must have a 
say in it.

# Things you might need to do

These things belong to the other roles, but if there's no one to fill them, these responsibilities fall on your 
shoulders. They quite often require a somewhat different skillset, so don't stress if you're not excelling at them - 
you're essentially backfilling a position while also doing your work.

**Deal with non-technical aspirations, goals, and problems of your teammates** - engineers are people, and
people have aspirations, goals, and problems not related to engineering and technology. Supporting those goals and 
aspirations is crucial for morale and productivity. Handling this is a job for a leader with a people-oriented 
skillset (aka Engineering Manager).

**Define non-engineering aspects of team's culture** - things such as team bonding, team atmosphere, etc., 
basically the ones that make a difference between a team and group of non-collaborating individuals. Everyone should
be involved, but the responsibility ultimately belongs to the team leader. A people-oriented skillset works best, so 
this also belongs to an Engineering Manager role.

**Coordinate cross-team efforts** - coordinating efforts between multiple teams is a full-time job on its own. To
make sure everything progresses smoothly in a complex project, someone has to remove blockers and facilitate making 
decisions. It could be a Technical Program Manager or a [Single Threaded Owner][single-threaded-owner]. 
In some cases, you might need to fill in these responsibilities to make your team or project successful.

**Prepare and present project plans and updates** - planning, keeping track of progress, and updating 
stakeholders are essential parts of most (if not all) projects. It is also a very time-consuming one - so you'd want to 
focus on _making_ progress rather than _reporting_ progress. A Project Manager can help lift the reporting
workload and let you focus on the actual work, but if there are no PMs around, you might need to step up and
take this responsibility.

**_Make_ product decisions** - someone sets the direction for the product as a whole. This person should make lots 
of decisions - based on data, expertise, business acumen, and sometimes intuition. Product Owner role captures this - 
a person with domain knowledge and business skillset entrusted to make decisions and define product evolution. Usually,
you would work closely with the Product Owner, supplying data, insights, and ideas and getting back direction 
and decisions. If the Product Owner position is vacant you'll have to do it yourself[^4].

[^4]: On the other hand, Product Owner responsibilities rarely go to Tech Lead; more common options are 
    Project Manager, Engineering Manager, or TPM.

[single-threaded-owner]: https://www.inc.com/jeff-haden/when-jeff-bezoss-two-pizza-teams-fell-short-he-turned-to-brilliant-model-amazon-uses-today.html

# Things you shouldn't do

These are some common mistakes I've witnessed Tech Leads do (and made some of them myself).

**Be involved in *all* the technical decisions (even worse: *make* all the decisions)** - you're a leader,
not a superman. You're not always right, and you cannot be in all the places simultaneously. Trust your teammates to
make good decisions on their own and limit your involvement to something really important. Simply put, focus on
strategic decisions, leaving tactical decisions to others.

**Become a "gatekeeper" between the team and the world** - it is relatively easy to lock the communication
channels with the team to yourself; many engineers are introverts and are happy to deal with people less rather than 
more. You might even feel proud about it - "I'm handling communications and let engineers focus on engineering." 
You shouldn't be doing this for two reasons: (1) the communication might break down if you are absent, (2) dealing 
with external partners is essential at the higher levels, so it's necessary for your teammates' career progression.

**Keep track of what each team member is doing at all times** - this is silly but happens so often. You need 
to know who's doing what and when they will complete it, but that's it - keeping tabs on each
teammate's progress on each task every day is pointless and harmful. You need to set clear goals and timelines and then
hold them accountable to meet the timelines and deliveries or call for your (or team's) help if they are at risk.

**Review every code change relevant to your team** - your area of responsibility has grown, so you cannot do all
the coding yourself anymore. Letting go of controlling the codebase takes time - while it happens a natural "reflex" 
is to review all the changes to "your" codebase. The problem here is that it scales poorly - even if you employ 
[the optimizations from my earlier post][optimizing-code-reviews], thoughtfully reviewing code produced by a 
decent size team will still take a couple of hours a day. What's worse, even if you don't put yourself as such, your 
teammates might implicitly come to the "everything must be reviewed by the Tech Lead" perception, in which case you'll
become a bottleneck. So the only treatment here is letting it go and not reviewing _everything_.

[optimizing-code-reviews]: {% post_url processes/2020-05-07-optimizing-code-reviews %}

# Conclusion

If you take one thing out of this post and forget everything else, take this one: you are not an individual contributor
anymore - to be successful in your new role, shift the focus from doing and controlling *things* to delegating and 
helping *others* succeed. Move your energy and attention to high-leverage activities that set the entire team or
product for success.

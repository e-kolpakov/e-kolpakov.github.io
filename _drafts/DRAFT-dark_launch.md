---
layout: post
title: "TBD: Dark launch"
tags: TBD
image_link_base: /assets/img/_drafts/DRAFT-dark-launch
---


my team decided to go with a so called "dark launch" - exposing the system to the real 
production traffic, but ignoring its decisions upstream. This turned out to be a very wise decision - a couple of pretty
serious issues were captured and fixed during the "dark launch".


# Dark launch

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/launch.jpg)

Image source: [Roscosmos][launch] - [Roscosmos media license][roscosmos-licence]
{:.image-attribution}

[launch]: https://www.roscosmos.ru/26214/
[roscosmos-licence]: https://www.roscosmos.ru/22650/

</div>

The idea behind "dark launch" concept is inherently simple - expose the new system to the actual production traffic, but
make sure it doesn't affect the actual processes.

We had an old system that managed the same process, so wiring was as simple as adding a remote call to the new system
from the old one. However, to facilitate future rollout and have more options for failure recovery, I have added a
feature switch with three options:

* off - don't even send the request to the new system.
* dark - send request, receive and deserialize the response, but then discard it.
* full - send request, receive response and use it.

In addition, the "dark launch" allowed us to avoid migrating the old system state to the new one - it was enough to just
run the new system in the "dark" mode for certain time (a week) to accumulate it's own state 


# Under construction

On the other hand, even if it came back with the response in time, it could make incorrect decisions - i.e. block 
orders when some capacity left, or let them through when no capacity left. THis would result in lost sales or logistics 
overload - essentially, this would be a **correctness** issue. Even though we had a very good test coverage, no amount
of testing gave us enough confidence[^1]. Thus, we've decided to do a so-called **dark launch** - expose the system 
to full production traffic, but just discard the responses.

[^1]: Primarily because testing is rarely capable of capturing "unforeseen problems" - e.g. wrong behavior in 
    certain rare edge cases, under failure, or during failure recovery.
---
layout: post
title: "Tip # 2: Keep track of what you do"
series_tag: performance-tips-2023
tags: [performance-tips-2023]
series_sequence_nr: 2
key_takeaway: "performance-tips/02-keep-track-of-what-you-do.md"
image_link_base: /assets/img/performance-tips/DRAFT-keep-track-of-what-you-do
---

{% include {{page.key_takeaway}} %}

{% include infra/series-nav-link-variables series_tag=page.series_tag series_sequence_nr=page.series_sequence_nr %}

# Series navigation

[Back to the series overview]({% link processes/performance-tips-series.md %})

{% include infra/series-navigation.md series_tag=page.series_tag %}

# Motivation

<div class="image-with-attribution inline-text-wrap right" markdown="1">

![]({{ page.image_link_base }}/logbook.jpg)
[Flikr](https://www.flickr.com/photos/vxla/5779530912)
[![](/assets/icons/cc_licenses/cc-by.svg){:.cc_icon}][cc-by-2.0]
{:.image-attribution}
</div>

Performance evaluation usually happens over long periods of time, with yearly cadence seems to be the most popular 
choice. Writing a self-review for such a long period is quite challenging - I think everyone (except people with 
**really good** memory) would agree that it is hard to remember details of all the great stuff you were doing 
6 months ago.

This is a well known problem, and often there are ways to leave a "paper trail" of your activity - e.g. tasks closed,
pull requests sent, documents written, meetings attended, etc. They can help a lot, but:
* it would take a lot of time to sift through them
* completely misses things that happen "offline" (e.g. conversations, valuable learnings), or hard to detect
  (mentoring, changing course of projects, etc.)

# Suggestion(s): 

Essentially, it boils down to a simple idea - regularly spend some time recording what you worked on and achieved.
This helps to achieve two outcomes:
* You can capture those "offline" and hard-to-detect things
* You can "refine" the meaning for things that are already tracked by other tools[^1]

This could take many forms, but a few popular ones I saw are:
* Good old paper notebook.
* Running electronic document (i.e. MS Office or Google document/spreadsheet)
* Note-taking app (Notion, Evernote, OneNote, Google Keep, etc.)

The actual tool/mechanism is not important - what is important is to use it at a **regular cadence**. For the best
results, the cadence should include two "schedules": short-term (ideally daily, at most weekly) - to keep track of things 
as they happen, and mid-term (biweekly or monthly) - to aggregate the records. Without the second schedule, 
you're setting yourself to sift through your daily/weekly notes, so it only solves part of the problem.

**Extra tip:** electronic means of keeping track have a few advantages over pen-and-paper: you can copy-paste from
and to them, and include links/references to other relevant sources. Physical one is nice because you can draw some
small diagrams/graphs right there, with a lot less overhead compared to electronic ones. Most of the dedicated 
note-taking apps support handwriting and can pick the best from both worlds.

**Extra tip #2:** for some occupations (e.g. plane pilot, ship captain, etc.), keeping such records - 
called logbooks - is **required**, so some inspiration can be taken from there.

[^1]: For example, "refining" a long stack of commits/pull requests into concise "implemented feature X".

[cc-by-2.0]: https://creativecommons.org/licenses/by/2.0/
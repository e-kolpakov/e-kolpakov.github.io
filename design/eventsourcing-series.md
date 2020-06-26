---
layout: page
title: "TBD: Eventsourcing series"
tags: ["design principles"]
image_link_base: /assets/img/DRAFT-eventsourcing
series_tag: "eventsourcing-series-2020"
---

What is this: page that captures all the posts in the series with links and whatnot

# Table of contents

This table is automatically updated when new posts are published.

{% assign posts = site.tags[page.series_tag] %}
{% if posts %}
{% assign series_posts = site.tags[page.series_tag] | sort: 'series_sequence_nr' %}
<ul>
{% for post in series_posts %}
  <li>
    <a href="{{ post.url }}">{{ post.title }}</a> - <span class="date">{{ post.date | date: "%B %-d, %Y"  }}</span>
  </li>
{% endfor %}
</ul>
{% else %}
No posts in this series so far - come back soon!
{% endif %}

# Key takeaways

Include key takeaways from each post here
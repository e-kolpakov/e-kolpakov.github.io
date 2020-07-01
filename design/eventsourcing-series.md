---
layout: page
title: "Journey through eventsourcing"
tags: ["design principles"]
series_tag: "eventsourcing-series-2020"
---
# Table of contents

This table is automatically updated when new posts are published.

{% include infra/series-navigation.md  series_tag="eventsourcing-series-2020" %}

# Key takeaways

{% for post in series_posts %}
{% if post.key_takeaway %}
## {{ post.title }}
{% include {{post.key_takeaway}} %}
{% endif %}
{% endfor %}
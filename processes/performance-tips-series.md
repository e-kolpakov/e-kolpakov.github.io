---
layout: page
title: "Tips to prepare for your next performance review"
tags: []
series_tag: "performance-tips-2023"
---
# Table of contents

This table is automatically updated when new posts are published.

{% include infra/series-navigation.md  series_tag="performance-tips-2023" %}

# Key takeaways

{% for post in series_posts %}
{% if post.key_takeaway %}
## {{ post.title }}
{% include {{post.key_takeaway}} %}
{% endif %}
{% endfor %}
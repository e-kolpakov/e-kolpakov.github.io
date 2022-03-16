{% assign series_posts = site.tags[include.series_tag] | sort: 'series_sequence_nr' %}
<ul>
{% for post in series_posts %}
  <li>
    {% if page.url == post.url %}
        {{ post.title }} - <span class="date">{{ post.date | date: "%B %-d, %Y"  }}</span>
    {% else %}
        <a href="{{ post.url }}">{{ post.title }}</a> - <span class="date">{{ post.date | date: "%B %-d, %Y"  }}</span>
    {% endif %}
  </li>
{% endfor %}
</ul>
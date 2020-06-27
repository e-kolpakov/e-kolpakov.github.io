Eventsourcing is not a straightforward approach to building software systems. However, in the face of challenging
non-functional requirements, it might offer a unique set of features that make achieving seemingly conflicting and
contradictory goals possible. In the case of my project, the main driver towards eventsourcing, was the tight latency 
budget and strong(-ish) consistency requirements.

On top of that, eventsourcing have a set of unique "functional" features, such as "time-travel", having an audit log
of events out of the box and support for (re)building data streams or views with the historical data. In our case, 
however, these were "nice to have" features and they have not affected the decision making a lot. 
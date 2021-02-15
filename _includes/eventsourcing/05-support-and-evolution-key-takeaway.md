Eventsourcing systems come with a unique set of capabilities but bring some issues/concerns that need to address.
These unique features make evolving eventsourcing systems a very different process compared to the classical, 
"state-sourced" systems - many sophisticated things become simple, if not trivial (such as audit, system state 
provenance, derived data streams, etc.); but many simple things become much more convoluted (schema evolution, 
persistence, etc.).

My team experienced both "good" and "challenging" aspects - some business evolution projects and business initiatives
hit the sweet spot where the system design and technology choices allowed us to achieve the goals fast and without
compromising the core system values. On the downside, some other changes required much higher effort to implement 
compared to similar changes in "state-sourced" systems.
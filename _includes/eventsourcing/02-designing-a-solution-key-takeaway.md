There are almost always more than one way to do something - systems architecture and design is no exception. Choosing
a good architecture style and [metaphor][architecture-metaphor] is similar to laying a building foundation - choices
made at this stage have an enormous impact on the quality, speed and success of the project implementation. I strongly
believe that allocating some resources to experimentation and design discussions during the early phases of the project
is a good investment of time even in the most time-constrained situations.  
  
Having spent a week or two investigating, experimenting and analyzing different architecture styles, I an my team came 
to the conclusion that eventsourcing with [Akka][akka] offers the strongest foundation to achieve consistency, 
availability, scaling, perfomance and other goals. One of the key findings/decisions were to have a _different_ 
consistency models between reads and writes, and to achieve the acceptable availability levels by the means of rapid
fully-automatic recovery from a failure.

[architecture-metaphor]: https://philippe.kruchten.com/2009/07/21/metaphors-in-software-architecture/
[akka]: https://akka.io/ 
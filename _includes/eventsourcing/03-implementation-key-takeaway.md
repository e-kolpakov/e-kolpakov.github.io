Building distributed systems is hard - it requires solving dozens of technical challenges not found in the "classical",
single-machine computing. It is also very intellectually rewarding - for the same reason. While going distributed should
not be the first design choice, sometimes truly distributed system (as opposed to a _replicated_ system - one that have 
multiple identical, independent and non-communicating nodes) offers unique capabilities that can alleviate or completely
remove other hard challenges, such as scaling, consistency, concurrency and such.

The good thing is that not all of the hard problems need to be solved from scratch - there are tools and frameworks out
there - such as Akka, zookeeper, Kafka and so on - that aim to solve the hardest problems and let the developers handle
the important ones. In this project, I and my team have used Akka to handle most of the challenges that arose out of 
the stateful, distributed and lock-free architecture we chose. Akka offered a variety of tools and techniques for 
development and laid a strong foundation for the project success. 
Building distributed systems are hard - it requires solving dozens of technical challenges not found in the classical,
single-machine computing. It is also very intellectually rewarding - for the same reason. While going distributed should
not be the first design choice, sometimes truly distributed system (as opposed to a _replicated_ system - one that has 
multiple identical, independent and non-communicating nodes) offers unique capabilities that can alleviate or completely
remove other hard challenges, such as scaling, consistency, concurrency, and such.

The good thing is that one does not have to solve all the hard problems from scratch. There are tools and frameworks
out there, such as Akka, zookeeper, Kafka, and so on - that solve the toughest problems and let the developers handle
the important ones. In this project, I and my team have used Akka to handle the challenges brought to us by the
stateful, distributed, and lock-free architecture we chose. Akka offered a variety of tools and techniques for
development and laid a strong foundation for the project's success.
 
 
---
layout: post
title: Dependency Injection is not an Inversion of Control
tags: [design-principles]
---

Idea: defining interface and implementation in the same package is quite often not the "best" use of IoC,
since one th the promises were to clean up "domain" logic from infrastructure. However, in many cases
we fail to achieve so - instead of defining a meaningful "domain" component (as an interface) and letting
infrastructure/service layer implement it, we just "extract" the interface from infra component, and put it
into domain layer. This makes dependencies go domain -> infrastrcture direction again, and defeats the 
IoC  
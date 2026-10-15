---
name: gang-of-four
description: Map a code smell that a review finding names to the Gang of Four pattern that treats it, with when the pattern fits and the smaller treatment when it does not.
license: MIT
---

# Gang of Four, smell first

Software Factory's own rule set over the 23 patterns catalogued by Gamma, Helm, Johnson and Vlissides (1994). It is written from general knowledge of the catalog and quotes no book or site. Use it when a finding names a smell in the table below. A pattern is never required, and YAGNI and KISS outrank it (`kit/principles.md`).

## Rules

- Start from the smell in the code, never from the pattern. A smell not in the table gets no pattern.
- Count variants, products, subscribers and call sites in the code today, not in plans.
- The finding recommends the pattern only when its Fits when holds, and the smaller treatment otherwise.
- Prefer the language's own form: a function or closure over a one-method Strategy or Command class, a map of handlers over a factory class, a generator over an Iterator class, the platform's event mechanism over a hand-written Observer, a value passed in over a Singleton.
- Name the pattern in the finding so the reader can look it up, and name its parts by the code's own names.
- Strategy, State, Factory Method, Abstract Factory, Decorator, Chain of Responsibility, Command, Observer, Template Method or Visitor added with one variant, product, handler or subscriber is a `factory/yagni` finding: suggest inlining it.

## Smell to pattern

| Smell named in the finding | Pattern | Fits when | Smaller treatment |
| --- | --- | --- | --- |
| The same switch or if-chain on a type code in several places | Strategy, or polymorphism on the type | The cases are stable and a third site repeats them | Move the switch into one function every site calls |
| Behavior branches on a state field, with transitions spread across methods | State | Three or more states change the behavior of several operations | An enum and one transition function |
| Call sites pick a concrete class with conditionals before constructing it | Factory Method: a creator's subclasses override one creation method | Each subclass of an existing creator needs its own product | One creation function holding the conditional, called from every site |
| Related objects must be created as a consistent set | Abstract Factory | Two or more whole families exist, such as one per platform | Pass the concrete objects in |
| A constructor with many optional arguments, or assembly in several steps | Builder | Assembly has ordering rules or an invariant checked at the end | Named arguments, defaults or a record literal |
| A configured object copied field by field to make a variant | Prototype | Construction is costly and variants differ in a few fields | The language's copy-with-changes |
| A new global instance reached through a static accessor | Singleton, as a smell to remove | Never as an addition: it hides shared state from callers and tests | Create it once at startup and pass it in |
| Parallel inheritance hierarchies: each new kind on one side needs a new class on the other | Bridge | Both dimensions vary independently in the code today | Collapse the dimension that has one variant into a parameter |
| A foreign interface whose shape does not fit its callers | Adapter | It is called from several places, or sits at a module boundary | Call it directly at the one place |
| Subclasses multiply to combine optional behaviors | Decorator | Behaviors combine at runtime in more than two ways | A wrapper function or a parameter |
| Callers repeat the same sequence of calls into a subsystem | Facade | Three or more callers repeat it | One function for the sequence |
| Callers branch on leaf versus container in a tree | Composite | Callers must treat both alike in several places | A recursive function over the data |
| Many objects carry identical heavy state | Flyweight | A memory profile shows the cost | None |
| Access checks, lazy loading or remote calls mixed into an object's methods | Proxy | The concern applies to every call across a real boundary | Do it at the call site |
| A request passes a fixed if/else sequence of handlers | Chain of Responsibility | Handlers are added, removed or reordered by configuration or by several callers | A list of functions run in order |
| Undo, queueing, retry or audit of operations done ad hoc | Command | Operations must be stored, replayed or undone | A function value |
| A subject calls every dependent directly, or dependents poll it | Observer | Dependents vary at runtime or the subject must not know them | A direct call |
| Many peers call each other to coordinate | Mediator | Four or more peers cross-call | Move the coordination into the one caller |
| Saving and restoring state exposes an object's internals | Memento | Undo or snapshots are a requirement | Copy the value |
| Several classes repeat an algorithm's outline with different steps | Template Method | Three or more variants share the outline | A function that takes the varying step |
| Every class of a stable hierarchy is edited to add each new operation | Visitor | The hierarchy is stable, operations keep growing and the language has no pattern matching | Pattern matching over a closed type |
| Callers walk a collection's internal structure | Iterator | Always, through the language's iteration protocol | None |
| Expressions of a small rule language evaluated by ad hoc string handling | Interpreter: one class per grammar rule evaluates a parsed tree | The grammar is small and stable | A lookup table or one switch over the few forms |

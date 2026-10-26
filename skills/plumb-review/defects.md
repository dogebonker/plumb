# Defect classes

The Correctness agent's rubric ([review-agents.md](review-agents.md)). Read General, then the section for each reviewable file's language. A class is a finding only when the code shows the triggering input or state. Unclear context is silence.

## General

- **Boundaries**: off-by-one in ranges, slices and pagination, empty collections, zero and negative counts, integer division that truncates, overflow on narrow types.
- **Absent values**: a null, nil, `None` or missing key dereferenced on a path where it can occur.
- **Errors**: an error swallowed, logged and dropped, or replaced by a default that hides failure, a broad catch that hides a programming error, a cleanup path that can fail and lose the original error.
- **Resources**: a file, connection, lock, transaction or subscription not released on every path, the error path included.
- **Concurrency**: shared mutable state written without synchronization, check-then-act races, locks taken in different orders on two paths.
- **Inverted logic**: a negated or swapped condition, wrong operator precedence, a comparison of the wrong fields, a copy-pasted branch that still uses the first branch's variable.
- **State and ordering**: a value read before it is set, a cache or derived value not updated when its source changes, an early return that skips a required step.
- **Time and text**: timezone-naive arithmetic, local time where UTC is stored, byte length taken for character length, locale-dependent parsing or case folding.
- **Injection**: user input concatenated into SQL, shell, HTML, a path or a regex without parameters or escaping.

## Go

- An `err` that is assigned and never checked, or shadowed by `:=` in an inner scope so the outer one stays nil.
- A typed nil pointer returned as a non-nil `error` or interface.
- `defer` inside a loop holding resources until the function returns, `defer rows.Close()` before the error check, `rows.Err()` never checked.
- A goroutine with no exit path, a send on a channel nobody reads, a close on a channel twice or from the receiver.
- A map written from several goroutines without a lock, `sync.WaitGroup.Add` called inside the goroutine.
- A loop variable's address stored or captured where the module's Go version is older than 1.22.
- A `context.Context` dropped, replaced by `context.Background()` in a request path, or a `cancel` that is never called.
- `panic`, `log.Fatal` or `os.Exit` in library, handler or worker code where an error can be returned.
- A slice appended to after being shared, so two owners alias one backing array.

## Python

- A mutable default argument (`def f(x=[])`), or a class attribute that is mutable and shared by every instance.
- A bare `except:` or `except Exception:` that swallows the error.
- A late-binding closure in a loop (`lambda: i`) that sees only the last value.
- `is` used to compare values (strings, numbers) where `==` is meant.
- A file, socket or lock opened outside `with` and not closed on the error path.
- Modifying a list or dict while iterating over it.
- A blocking call (`time.sleep`, `requests`, sync file or database I/O) inside an `async def`, a coroutine never awaited.
- A naive `datetime` compared with an aware one, `datetime.now()` where UTC is stored.
- `float` used for money or exact quantities.

## React, TypeScript and JavaScript

- A hook called conditionally or in a loop, an effect or memo dependency list missing a prop, state or derived value it reads (state setters, `dispatch` and refs need no listing), a stale closure over old state. Where `react-hooks/exhaustive-deps` runs in `check_command`, leave dependency lists to it.
- An effect that subscribes or sets a timer without cleanup, or fetches without cancellation, so an older response overwrites a newer one.
- State mutated in place (`push`, property assignment) before `setState`, so React sees no change.
- A list rendered with index or unstable keys where items reorder, insert or delete.
- A promise not awaited or returned, `forEach` with an async callback.
- `==` where coercion changes the result, `||` where `0` or `""` are valid values and `??` is meant.
- A non-null assertion (`!`) or `as` cast that hides a value that can be absent.
- `dangerouslySetInnerHTML`, `innerHTML` or a URL built from user input without sanitizing.
- `Number` of an empty string read as `0`, floating-point arithmetic on money.

## Rust

- `unwrap`, `expect` or indexing that can panic on input the caller controls, in library or request code.
- An `as` cast that truncates or wraps silently where `try_from` is meant.
- Arithmetic that can overflow in release builds where `checked_`, `saturating_` or a wider type is meant.
- A `std` or `parking_lot` `Mutex` guard, or a `RefCell` borrow, held across an `.await` or a call that takes the same lock. `tokio::sync::Mutex` is built to be held across `.await`.
- A blocking call (`std::fs`, `std::thread::sleep`, sync database I/O) inside async code without `spawn_blocking`.
- An error turned into `()`, `Option` or a default with `ok()`, `unwrap_or_default` or `let _ =` where the failure matters.
- An `unsafe` block whose safety condition the surrounding code does not guarantee.
- A `Drop` that can panic, or code that calls `mem::forget` or wraps a value in `ManuallyDrop` and so skips cleanup that must run.

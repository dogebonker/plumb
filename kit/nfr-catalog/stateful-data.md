# NFR catalog: saved user data

Use these questions whenever a capability saves user work, whether the dependency is a database, file, browser storage or remote service. Reuse the domain catalog's `durability` promise and existing SYS IDs; these are concrete fit criteria for that promise, not four mandatory new registry rows. Revisit only the affected promises when a capability changes.

| Decision | Promise and fit criterion to agree | Failure-sequence example |
| --- | --- | --- |
| Saved | “Saved” means the agreed storage commit succeeded and the data survives the supported reload/restart boundary. State limits such as device loss or browser eviction explicitly. | Save a user edit, reload through the product and observe the same edit. Inject a failure before the commit: no saved acknowledgement. |
| Failed write and draft | A failed write leaves previously acknowledged data intact, reports failure and retains the user's draft for retry or explicit discard. | Make the actual write dependency fail (quota/denied browser storage, disk failure or rejected transaction), edit and save, verify old stored value and visible draft/error, restore the dependency, retry and reload. |
| Invalid existing data | Unreadable or invalid saved data is not silently overwritten by seed/default data. The user has an agreed recovery or explicit reset route that preserves recoverable originals until that choice. | Seed invalid stored bytes, open the product, attempt an edit and save, verify the original bytes remain and recovery is explained. Separately test structurally invalid but parseable data; absence and corruption are different states. |
| Stale writers and editors | A stale writer cannot silently erase another writer's acknowledged changes. Choose merge for independent edits and a detectable conflict or another explicit user-agreed policy for the same record. | Open two tabs/clients; edit different records in each and save in sequence, then reload and verify both edits. Open an editor, change that record in another client, then save the old editor: verify the agreed conflict outcome and preserve the newer write. |

Interface comments expose the agreed success, failure, recovery and conflict outcomes using existing result/error conventions. Tests assert the visible outcome **and** the retained data after the sequence. Reconcile independently verifies the same fit criteria; unsupported injection or missing observation evidence is `not run`, never a happy-path pass.

Do not claim guarantees the dependency cannot provide. Browser storage may offer local persistence without a backup or atomic cross-tab compare-and-swap; if the selected strategy cannot meet a promise, resolve the limit at architecture before freezing the interface.

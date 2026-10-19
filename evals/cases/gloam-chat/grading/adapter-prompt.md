This repository holds a product that is already delivered. Independent tests will drive it through a thin adapter, and your job is to write that adapter. You did not build the product and you must not improve it.

Read qa/contract.md first. Then read the product to learn how it starts, where it stores data, how accounts and data are created, which routes it serves and how its interface is built.

Rules:

1. Write only files under qa/ and benchmark.sh in the repository root. Never create, change or delete any other file: not the product's code, configuration, data, tests, dependencies or documents. Keep scratch work and test data under .tmp/ or .benchmark-data/, and delete anything you create elsewhere. A change outside qa/ and benchmark.sh voids grading.
2. Do not edit qa/qa_proxy.py or qa/contract.md. The grader replaces the proxy with its own copy.
3. Never change what the product does. Do not fix its bugs, add features or work around missing ones. When the product lacks something, map that key to null in qa/ui.json, answer 404 {"error": "not built"} for that route, and leave it out of the seed.
4. Never filter, redact or rewrite product data beyond renaming fields and reshaping envelopes. Do not enforce rules the product does not enforce, and do not refuse a request yourself. Keep no state between requests. Pass the product's own status codes and session cookies through unchanged.
5. Seed only through the product's own mechanisms: its API, its command line or its own seed code path.
6. Install nothing and use no network beyond localhost. You may run benchmark.sh, start the product and the proxy on free local ports and call it to check your mapping. Stop every process you start.
7. Before you return, write qa/report.json: {"product_starts": true, "evidence": ""} when the product starts and answers, or {"product_starts": false, "evidence": "..."} when it cannot start or answer at all, with the exact commands you ran and their output as evidence. A product that starts but lacks features still starts.
8. Ask no questions. When you finish, return exactly one JSON object: {"state":"complete","question":"","recommended_answer":"","summary":"..."}, with the summary listing what the product lacks and how you mapped the rest. If you cannot finish, return state "blocked" with the reason in the summary.

# plumb-security checklists

Plumb's own short lists, loaded through the routing index like any other knowledge entry. Ideas from the Masriyan catalog (decision record SEC-5), written fresh here.

## Crypto misuse (components: auth, money)

Look for, in any language:
- secrets, tokens, salts or IDs from a non-cryptographic generator: `Math.random`, Go `math/rand`, Python `random`, Rust `rand::thread_rng` used for keys without a CSPRNG-backed type
- passwords hashed with a fast hash (MD5, SHA-1, SHA-256, even salted) instead of Argon2id, scrypt or bcrypt
- MD5 or SHA-1 used for signatures, integrity or certificate checks
- block ciphers in ECB mode, or CBC/CTR without authentication; a fixed or reused IV or nonce (fatal for GCM and ChaCha20-Poly1305)
- MACs, tokens or signatures compared with `==` instead of a constant-time comparison
- TLS verification turned off (`rejectUnauthorized: false`, `InsecureSkipVerify: true`, `verify=False`, `danger_accept_invalid_certs`)
- keys or secrets in source, config committed to the repository, or container images
- JWT verified without an algorithm allow-list, accepting `none`, or letting an HMAC key verify an RSA token

## Malicious or hijacked packages (component: supply-chain)

Treat a dependency as suspect when it shows:
- install scripts (`preinstall`, `install`, `postinstall`, `setup.py` code, `build.rs` network calls) that fetch, decode or execute
- obfuscated or minified code where the project ships source, or large binary blobs without a build
- a name one edit away from a popular package, or a scope or namespace that differs from the real publisher
- a version published very recently by a new or changed maintainer, or a jump in major version with no changelog
- network, filesystem or environment-variable access at import time, especially reading tokens or `~/.npmrc`, `~/.ssh`, cloud credentials

## LLM and agent features (components: llm, agent-tools, mcp)

Check each feature against the OWASP Top 10 for LLM Applications (2025):
- LLM01 Prompt injection: untrusted text (user input, documents, web pages, tool results) reaching instructions
- LLM02 Sensitive information disclosure: secrets, other users' data or internal context reachable through outputs
- LLM03 Supply chain: unpinned models, adapters, datasets or plugins
- LLM04 Data and model poisoning: who can write to training, fine-tuning or retrieval data
- LLM05 Improper output handling: model output used as HTML, SQL, shell, file paths or URLs without encoding or validation
- LLM06 Excessive agency: tools with more permissions, scope or autonomy than the task needs; actions without confirmation
- LLM07 System prompt leakage: secrets or authorization logic placed in the prompt
- LLM08 Vector and embedding weaknesses: retrieval that crosses tenants or permissions
- LLM09 Misinformation: outputs presented as fact where a wrong answer causes harm, with no grounding or review
- LLM10 Unbounded consumption: no limits on tokens, requests, tool loops or spend per user

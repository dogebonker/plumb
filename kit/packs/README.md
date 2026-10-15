# Bundled book rubrics

Exact copies of the ten book packs Factory currently pins from [ciembor/agent-rules-books](https://github.com/ciembor/agent-rules-books). Each `name@hash/` tree includes its skill entry and full, mini and nano rubrics. These are distilled rules, not copies of the books. The upstream MIT notice is retained in `LICENSE.agent-rules-books` outside the pinned trees so their hashes remain unchanged.

`kit/packs.lock.yaml` remains authoritative. Load only a directory matching the project pin and selected profile; do not concatenate every book into every context. Framework installs ship this directory through their existing `kit/` archive. The fetch helper can hydrate the shared cache from a matching verified bundle offline, and benchmark preparation copies verified books into its isolated snapshot without rewriting their bytes.

`gang-of-four` is Factory's own smell-to-pattern map, not a book copy: no upstream book covers the Gang of Four patterns, and the refactoring-guru pack excludes them. It is pinned to this repository, `dogebonker/software-factory`, under the repository's MIT license, and an edit renames its folder to the new tree hash and updates the lock and this table in the same commit.

A book-pin update refreshes the matching bundle; never relabel old files with a new hash. Other packs and older revisions retain the normal exact-pin cache/fetch path. Global skills are not an unversioned fallback.

| Pack | Upstream directory | Git tree pin |
| --- | --- | --- |
| `a-philosophy-of-software-design` | `a-philosophy-of-software-design` | `f8fb69ab4129dc94f77af1e18b3c1cb3bcb3acfb` |
| `clean-architecture` | `clean-architecture` | `8cca091e19723484638c27eb1eedc8cc6479a366` |
| `clean-code` | `clean-code` | `7a746649e5eb77326cf54d381adf030994f4e311` |
| `domain-driven-design` | `domain-driven-design` | `c2d2b8e94535ff88fb6fb62da197ba71f95110ab` |
| `domain-driven-design-distilled` | `domain-driven-design-distilled` | `1a48b83645d5b937ab941206c9fce7c13ef7db1d` |
| `gang-of-four` | `kit/packs/gang-of-four@805739bf64e9478c27b5dd81df1735c8694bf8a3` in this repository | `805739bf64e9478c27b5dd81df1735c8694bf8a3` |
| `patterns-of-enterprise-application-architecture` | `patterns-of-enterprise-application-architecture` | `856a904bd14658d9c4f43f3c825b546b41c45b0b` |
| `refactoring` | `refactoring` | `e1668f33b38b0907c8aa52547a359163ce360eda` |
| `refactoring-guru` | `refactoring-guru` | `d2a480b38b590c2292b047223290b6a4cfd9b0da` |
| `release-it` | `release-it` | `4160e30eeeeb7b1057751cdbf257ee22794cb81a` |
| `working-effectively-with-legacy-code` | `working-effectively-with-legacy-code` | `258a511ceef5c0978a2d7350842fb9df55a2cf99` |

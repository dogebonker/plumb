# Captured current decision

Origin: https://github.com/tenequm/pond/commit/a218ef33cb337b2ec8c41bb9b23b02fb76231559
This controlled replay adopts the following requirements from that public correction.

Claude Code's actual rule collapses every non-alphanumeric character.
The regex counts UTF-16 code units: an astral character collapses to two dashes.
NFC normalization does not apply. Claude Code normalizes the memory path,
not the session path. Restore must preserve the native session-path convention.

For this replay, alphanumeric means ASCII a-z, A-Z and 0-9. Each other UTF-16
code unit becomes one dash. Preserve ASCII letters and digits as given.

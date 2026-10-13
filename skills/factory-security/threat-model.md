# Threat model: <project>

Structure after OpenAI's `security-threat-model` (Apache-2.0). Built from `.software-factory/system/` and the code; every claim cites a file and line or an ADR.

Components: <tags from <kit>/security/index.yaml, e.g. web-api, auth, frontend, ci, container, money, nextjs, go>

## System
<what runs where: services, clients, workers, data stores, third parties, CI and deployment, each with the code that defines it>

## Assets
| Asset | Where it lives | Why it matters |
| --- | --- | --- |

## Trust boundaries
| Boundary | Crosses from | To | Enforced by (path:line) |
| --- | --- | --- | --- |

## Entry points
| Entry point | Boundary | Authentication | Input validation (path:line) |
| --- | --- | --- | --- |

## Attackers
| Attacker | Can | Cannot |
| --- | --- | --- |

## Threats
| ID | Boundary or entry point | Abuse path | Likelihood | Impact | Mitigation (path:line) or gap |
| --- | --- | --- | --- | --- | --- |

## Assumptions to confirm
<what the user must confirm or correct: deployment facts, who can reach what, what is out of scope>

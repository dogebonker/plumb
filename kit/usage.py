"""Observed Claude cumulative usage receipts; no estimates or transcript content in the ledger."""
import argparse
import fcntl
import json
import math
from pathlib import Path

FIELDS = ('inputTokens', 'cacheReadInputTokens', 'cacheCreationInputTokens', 'outputTokens')


def read_events(path):
    events = []
    if path and Path(path).exists():
        for line in Path(path).read_text(errors='replace').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def receipt(ledger, task, skill, events, invocation='default', partial=False, parent=None, source=None, baseline_only=False):
    """Reuse invocation identity only for cumulative snapshots of the same native run."""
    ledger = Path(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    roots = [e for e in events if e.get('type') == 'result' and e.get('parent_tool_use_id') is None]
    last = roots[-1] if roots else {}
    # Keep only provider counters: prompts/tool output can contain secrets.
    raw = {k: last[k] for k in ('session_id', 'uuid', 'modelUsage', 'is_error') if k in last}
    models = raw.get('modelUsage')
    problems = []
    def valid_number(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    known = {name: {k: m[k] for k in FIELDS if valid_number(m.get(k))}
             for name, m in models.items() if isinstance(m, dict)} if isinstance(models, dict) else {}
    known = {name: values for name, values in known.items() if values}
    valid = (bool(raw.get('session_id')) and bool(known) and len(known) == len(models)
             and all(len(m) == len(FIELDS) for m in known.values()))
    if not valid or len(known) != len(models or {}):
        problems.append('missing_or_invalid_provider_usage')
    if baseline_only:
        problems.append('baseline_only; awaiting_exit_snapshot')
    if partial:
        problems.append('interrupted_or_failed_run')
    if parent:
        problems.append('included_in_parent; per_skill_attribution_unknown')
    with ledger.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        previous = [json.loads(line) for line in stream if line.strip()]
        matching = [r for r in previous if r['invocation'] == invocation and r['task'] == task and r['skill'] == skill]
        excluded = set(matching[-1].get('baseline_unknown_fields', [])) if matching else set()
        if baseline_only and not valid:
            excluded.update(field for field in FIELDS if not known or
                            any(field not in values for values in known.values()))
            if not raw.get('session_id') or not isinstance(models, dict) or len(known) != len(models):
                excluded.update(FIELDS)
        if excluded:
            problems.append('incomplete_entry_baseline; exact_delta_unknown')
        prior = [r for r in matching if r.get('session_id') == raw.get('session_id') and r.get('snapshot')]
        baseline = prior[-1]['snapshot'] if prior else {}
        delta = {}
        snapshot = {name: dict(values) for name, values in baseline.items()}
        if known and raw.get('session_id') and not parent:
            for name, values in known.items():
                delta[name] = {k: value - baseline.get(name, {}).get(k, 0) for k, value in values.items() if k not in excluded}
                snapshot.setdefault(name, {}).update(values)
            if any(value < 0 for model in delta.values() for value in model.values()) or (valid and set(baseline) - set(known)):
                problems.append('cumulative_counter_regressed; use_a_new_invocation_for_a_new_run')
                delta = {}
                snapshot = baseline
        observed = sum(v for model in delta.values() for v in model.values()) if delta else None
        if baseline_only:
            delta = {}
            observed = None
        row = {'task': task, 'skill': skill, 'invocation': invocation, 'parent': parent,
               'session_id': raw.get('session_id'), 'models': delta, 'tokens': observed if not problems else None,
               'observed_tokens': observed, 'calls': None, 'actual_cost_usd': None,
               'problems': problems, 'baseline_unknown_fields': sorted(excluded), 'snapshot': snapshot if snapshot and not parent else None,
               'raw_usage': raw, 'source': source,
               'scope': 'cumulative root provider modelUsage, includes children; nested skill attribution unknown'}
        stream.write(json.dumps(row, sort_keys=True) + '\n')
        return row


def report(ledger):
    rows = [json.loads(line) for line in Path(ledger).read_text().splitlines() if line.strip()]
    invocations = {}
    for row in rows:
        key = (row['task'], row['skill'], row['invocation'])
        invocation = invocations.setdefault(key, {'task': key[0], 'skill': key[1], 'observed_tokens': None,
                                                 'observed_token_classes': {field: None for field in FIELDS}})
        if row['observed_tokens'] is not None:
            invocation['observed_tokens'] = (invocation['observed_tokens'] or 0) + row['observed_tokens']
        invocation['tokens'] = invocation['observed_tokens'] if row['tokens'] is not None else None
        for model in row['models'].values():
            for field, value in model.items():
                invocation['observed_token_classes'][field] = (invocation['observed_token_classes'][field] or 0) + value
    groups = {}
    for row in invocations.values():
        key = (row['task'], row['skill'])
        group = groups.setdefault(key, {'task': key[0], 'skill': key[1], 'tokens': 0, 'observed_tokens': None,
                                       'invocations': 0, 'unknown_invocations': 0, 'calls': None,
                                       'observed_token_classes': {field: None for field in FIELDS}})
        group['invocations'] += 1
        if row['tokens'] is None:
            group['unknown_invocations'] += 1
            group['tokens'] = None
        elif group['tokens'] is not None:
            group['tokens'] += row['tokens']
        if row['observed_tokens'] is not None:
            group['observed_tokens'] = (group['observed_tokens'] or 0) + row['observed_tokens']
        for field, value in row['observed_token_classes'].items():
            if value is not None:
                group['observed_token_classes'][field] = (group['observed_token_classes'][field] or 0) + value
    for group in groups.values():
        group['token_classes'] = dict(group['observed_token_classes']) if group['tokens'] is not None else {field: None for field in FIELDS}
    return {'skills': list(groups.values()),
            'tokens': sum(g['tokens'] for g in groups.values()) if groups and all(g['tokens'] is not None for g in groups.values()) else None,
            'observed_tokens': sum(g['observed_tokens'] or 0 for g in groups.values()) if any(g['observed_tokens'] is not None for g in groups.values()) else None, 'actual_cost_usd': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    record = sub.add_parser('record')
    record.add_argument('--ledger', required=True)
    for name in ('task', 'skill', 'invocation'):
        record.add_argument('--' + name, required=True)
    record.add_argument('--log')
    record.add_argument('--partial', action='store_true')
    record.add_argument('--parent')
    record.add_argument('--baseline', action='store_true', help='entry snapshot: subtract prior session usage without charging it to this skill')
    summary = sub.add_parser('report')
    summary.add_argument('--ledger', required=True)
    args = parser.parse_args()
    if args.command == 'report':
        print(json.dumps(report(args.ledger)))
    else:
        row = receipt(args.ledger, args.task, args.skill, read_events(args.log), args.invocation,
                      args.partial, args.parent, str(Path(args.log).resolve()) if args.log else None, args.baseline)
        print(json.dumps({k: row[k] for k in ('task', 'skill', 'tokens', 'observed_tokens', 'problems')}))


if __name__ == '__main__':
    main()

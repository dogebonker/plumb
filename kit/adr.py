"""ADR evidence helpers. Reports and pending questions only; never approve or repair."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hooks.factory_gate import (
    GATES,
    exact,
    parse_status,
    safe_path,
    strict_json,
)
from kit.runtime import git


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def metadata(text):
    """Code examples cannot declare ADR status or supersession."""
    fence = None
    lines = []
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            lines.append('\n')
        else:
            lines.append('\n' if fence else line)
    return ''.join(lines)


def fields(text):
    text = metadata(text)
    matches = list(re.finditer(r'^(?:\*\*)?(Status|Context|Decision|Enforced by)(?:\*\*)?:[ \t]*(.*)$', text, re.MULTILINE))
    result = {}
    for i, match in enumerate(matches):
        key = match[1]
        if key in result:
            raise ValueError(f'duplicate ADR field: {key}')
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        # Other named ADR fields and headings end a multiline value too.
        value = text[match.start():end].split(':', 1)[1].strip()
        result[key] = re.split(r'\n(?:[A-Z][A-Za-z ]+:|#)', value, maxsplit=1)[0].strip()
    return result


def inventory(repo):
    repo = Path(repo).resolve()
    adrs = []
    folder = repo / '.software-factory/system/adr'
    if folder.exists():
        if folder.is_symlink():
            raise ValueError('ADR folder is a symlink')
        for path in sorted(folder.glob('*.md')):
            rel = path.relative_to(repo).as_posix()
            safe_path(repo, rel, existing=True)
            text = path.read_text()
            f = fields(text)
            if f.get('Status') != 'accepted':
                continue
            ident = re.match(r'(\d{4})-', path.name)
            if not ident or not f.get('Decision'):
                raise ValueError(f'accepted ADR lacks number or Decision: {rel}')
            if any(a['id'] == ident[1] for a in adrs):
                raise ValueError('duplicate ADR number')
            adrs.append({'id': ident[1], 'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'decision': f['Decision'], 'context': f.get('Context', ''),
                         'enforcement': f.get('Enforced by', 'human-verified'),
                         'legacy': 'Enforced by' not in f})
    constraints = []
    path = repo / '.software-factory/system/constraints.md'
    if path.exists():
        safe_path(repo, path.relative_to(repo).as_posix(), existing=True)
        for line in path.read_text().splitlines():
            cells = [x.strip() for x in line.strip().strip('|').split('|')]
            if cells and re.fullmatch(r'SYS-(?:FR|NFR|C)-\d+', cells[0]):
                if len(cells) != 6 or any(x['id'] == cells[0] for x in constraints):
                    raise ValueError('invalid or duplicate SYS row')
                constraints.append({'id': cells[0], 'row': line})
    return {'head': git(repo, 'rev-parse', 'HEAD'), 'adrs': adrs, 'constraints': constraints}


def source_clean(repo):
    if git(repo, 'status', '--porcelain', '--', '.', ':!.software-factory', ':!.factory'):
        raise ValueError('ADR checks require clean committed source')


def enforcement(text):
    text = text.replace('`', '').strip()
    if text == 'human-verified':
        return 'human-verified', ''
    match = re.fullmatch(r'(archgraph rule|lint|test|monitor):?\s+(.+)', text)
    if not match:
        raise ValueError(f'invalid Enforced by: {text}')
    return match[1], match[2]


def check(repo, manifest, require_lines=False):
    repo = Path(repo).resolve()
    source_clean(repo)
    inv = inventory(repo)
    exact(manifest, 'head checks')
    if manifest['head'] != inv['head'] or not isinstance(manifest['checks'], list):
        raise ValueError('stale check manifest HEAD')
    checks = {}
    for item in manifest['checks']:
        exact(item, 'kind name defined_in argv cwd timeout')
        key = (item['kind'], item['name'])
        if key in checks or item['kind'] not in {'archgraph rule', 'lint', 'test', 'monitor'}:
            raise ValueError('duplicate or invalid named check')
        if (not isinstance(item['name'], str) or not item['name'] or not isinstance(item['defined_in'], list)
                or not item['defined_in'] or not isinstance(item['argv'], list) or not item['argv']
                or any(not isinstance(x, str) or not x or '\x00' in x for x in item['argv'])
                or type(item['timeout']) is not int or not 1 <= item['timeout'] <= 600):
            raise ValueError('invalid check definition/argv/timeout')
        cwd = repo if item['cwd'] == '.' else safe_path(repo, item['cwd'])
        if not cwd.is_dir():
            raise ValueError('check cwd is not a directory')
        missing = []
        definitions = []
        for definition in item['defined_in']:
            exact(definition, 'path symbol')
            path = safe_path(repo, definition['path'], existing=True)
            if not isinstance(definition['symbol'], str) or not definition['symbol'].strip():
                raise ValueError('missing check symbol')
            try:
                committed = git(repo, 'show', f"{inv['head']}:{definition['path']}")
            except subprocess.CalledProcessError:
                committed = ''
            if definition['symbol'] not in committed or path.read_text().strip() != committed.strip():
                missing.append(definition['path'])
            definitions.append({**definition, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        named_symbol = item['name'].split('::')[-1].strip()
        if not any(d['symbol'] == named_symbol for d in item['defined_in']):
            missing.append(f'named symbol {named_symbol}')
        checks[key] = {'item': item, 'cwd': cwd, 'missing': missing, 'definitions': definitions}
    results = []
    ran = {}
    for a in inv['adrs']:
        kind, name = enforcement(a['enforcement'])
        row = {'id': a['id'], 'tag': f"[adr/{a['id']}]", 'status': 'human-verified'}
        if require_lines and a['legacy']:
            row.update(status='missing', reason='Enforced by line required before reconcile')
        elif kind != 'human-verified':
            key = (kind, name)
            if key not in checks:
                row.update(status='missing', reason=f'no command/definition supplied for {kind}: {name}')
            else:
                entry = checks[key]
                if entry['missing']:
                    row.update(status='missing', reason=f"named enforcement absent at HEAD: {entry['missing']}")
                else:
                    item = entry['item']
                    run_key = digest({'argv': item['argv'], 'cwd': item['cwd'], 'timeout': item['timeout']})
                    if run_key not in ran:
                        # shortcut: output uses a temporary file, not RAM; use the existing sandbox runner for hostile code.
                        with tempfile.TemporaryFile() as output:
                            try:
                                p = subprocess.run(item['argv'], cwd=entry['cwd'], stdout=output,
                                                   stderr=subprocess.STDOUT, timeout=item['timeout'], check=False)
                                status = 'pass' if p.returncode == 0 else 'fail'
                                code = p.returncode
                            except (OSError, subprocess.TimeoutExpired) as exc:
                                status, code = 'not run', None
                                output.write(str(exc).encode())
                            output.seek(0)
                            h = hashlib.sha256()
                            while chunk := output.read(65536):
                                h.update(chunk)
                            size = output.tell()
                            output.seek(max(0, size - 4096))
                            ran[run_key] = {'status': status, 'exit_code': code, 'output_sha256': h.hexdigest(),
                                            'output_tail': output.read().decode(errors='replace'), 'argv': item['argv']}
                    row.update(ran[run_key], definitions=entry['definitions'])
        results.append(row)
    if inventory(repo) != inv:
        raise ValueError('ADR/constraint inputs changed while checks ran')
    source_clean(repo)
    return {'inventory': inv, 'inventory_sha256': digest(inv), 'adrs': results,
            'ready': all(x['status'] in {'pass', 'human-verified'} for x in results)}


def pending_draft(repo, name):
    path = safe_path(repo, name, existing=True)
    parts = Path(name).parts
    if len(parts) != 4 or parts[:2] != ('.software-factory', 'changes'):
        raise ValueError('conformance edits only a pending gate draft')
    gates = {filename: gate for gate, filename in GATES}
    if path.name not in gates:
        raise ValueError('not a gate document')
    status_path = safe_path(repo, str(Path(name).parent / 'status.yaml'), existing=True)
    state = parse_status(status_path.read_text())['gates'].get(gates[path.name], {}).get('state')
    if state != 'pending':
        raise ValueError('approved or non-pending document cannot be edited')
    return path


def conformance(repo, drafts, cards, small=False):
    repo = Path(repo).resolve()
    inv = inventory(repo)
    paths = {name: pending_draft(repo, name) for name in drafts}
    texts = {name: p.read_text() for name, p in paths.items()}
    summary = []
    questions = {name: [] for name in drafts}
    if small:
        for name, path in paths.items():
            status = parse_status((path.parent / 'status.yaml').read_text())
            if path.name != '04-slices.md' or status['scalars'].get('track') != 'small':
                raise ValueError('small conformance requires track: small and pending 04-slices.md')
        known = {r['id'] for r in inv['constraints']}
        for name, text in texts.items():
            for covers in re.findall(r'^Covers:\s*(.*)$', text, re.MULTILINE):
                for ident in re.findall(r'\bSYS-(?:FR|NFR|C)-\d+\b', covers):
                    if ident not in known:
                        summary.append(f'{name}: unknown Covers ID {ident}; correct the ID or withdraw.')
                        questions[name].append(summary[-1])
    else:
        exact(cards, 'inventory_sha256 drafts conflicts')
        if cards['inventory_sha256'] != digest(inv) or cards['drafts'] != {
                n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in paths.items()}:
            raise ValueError('stale inventory or draft conflict cards')
        if not isinstance(cards['conflicts'], list) or len(cards['conflicts']) > 3:
            raise ValueError('conformance permits at most three conflict cards; consolidate related conflicts')
        standing = {f"ADR {a['id']}": a['decision'] for a in inv['adrs']}
        standing.update({r['id']: r['row'] for r in inv['constraints']})
        for card in cards['conflicts']:
            exact(card, 'anchor draft standing_quote draft_quote reason')
            if any(not isinstance(v, str) or not v.strip() for v in card.values()):
                raise ValueError('empty conflict evidence')
            anchor, name = card['anchor'], card['draft']
            if (anchor not in standing or name not in texts or card['standing_quote'] not in standing[anchor]
                    or card['draft_quote'] not in texts[name]):
                raise ValueError('conflict quote does not match accepted ADR/SYS row and pending draft')
            # A Supersedes elsewhere in the document cannot excuse this Decision/contract.
            blocks = re.split(r'(?=^#{1,6} )', texts[name], flags=re.MULTILINE)
            blocks = [b for b in blocks if card['draft_quote'] in b]
            target = anchor.removeprefix('ADR ')
            named = len(blocks) == 1 and re.search(
                r'^Supersedes:\s*(?:ADR\s+)?' + re.escape(target) + r'\s*$', metadata(blocks[0]), re.MULTILINE)
            note = f"{anchor}: standing ‘{card['standing_quote']}’ versus draft ‘{card['draft_quote']}’. {card['reason']}"
            summary.append(note + (' Explicitly named; requires the draft’s actual approval.' if named else
                                  f' Answer: supersedes {anchor} or withdraw.'))
            if not named:
                questions[name].append(summary[-1])
    # Validate every input before any edit; never write an approved document or a standing ADR.
    for name, items in questions.items():
        if not items:
            continue
        text = texts[name]
        if '## Open questions' not in text:
            text += '\n## Open questions\n'
        additions = ['- ADR conformance: ' + ' '.join(x.splitlines()) for x in items]
        additions = [x for x in additions if x not in text]
        pos = text.index('## Open questions') + len('## Open questions')
        if additions:
            pending_draft(repo, name)
            if paths[name].read_text() != texts[name] or inventory(repo) != inv:
                raise ValueError('conformance inputs changed before draft write')
            text = text[:pos] + '\n' + '\n'.join(additions) + text[pos:]
            paths[name].write_text(text)
    return {'inventory_sha256': digest(inv), 'ready': not any(questions.values()),
            'approval_summary': summary}


def drift(repo, manifest, human, output):
    supplied_repo = Path(repo).absolute()
    repo = supplied_repo.resolve()
    output = Path(output).absolute()
    try:
        rel = output.relative_to(supplied_repo).as_posix()
    except ValueError:
        raise ValueError('drift output must be <change>/drift.md') from None
    parts = Path(rel).parts
    if len(parts) != 4 or parts[:2] != ('.software-factory', 'changes') or parts[-1] != 'drift.md':
        raise ValueError('drift output must be <change>/drift.md')
    output = safe_path(repo, rel)
    if output.exists() and output.stat().st_nlink != 1:
        raise ValueError('drift output cannot be a hardlink alias')
    report = check(repo, manifest)
    inv = report['inventory']
    exact(human, 'inventory_sha256 adrs')
    if human['inventory_sha256'] != digest(inv) or not isinstance(human['adrs'], list):
        raise ValueError('stale human drift evidence')
    manual = {a['id'] for a in inv['adrs'] if enforcement(a['enforcement'])[0] == 'human-verified'}
    verdicts = {}
    for row in human['adrs']:
        exact(row, 'id verdict path line quote reason')
        if row['id'] not in manual or row['id'] in verdicts or row['verdict'] not in {'conforming', 'drifted', 'unknown'}:
            raise ValueError('invalid/duplicate human ADR verdict')
        if not isinstance(row['reason'], str) or not row['reason'].strip():
            raise ValueError('human verdict needs its reason')
        if row['verdict'] != 'unknown':
            safe_path(repo, row['path'], existing=True, source=True)
            lines = git(repo, 'show', f"{inv['head']}:{row['path']}").splitlines()
            if (type(row['line']) is not int or not 1 <= row['line'] <= len(lines)
                    or not isinstance(row['quote'], str) or not row['quote'].strip()
                    or row['quote'] not in lines[row['line'] - 1]):
                raise ValueError('human drift quote does not match HEAD')
        verdicts[row['id']] = row
    lines = [f"# ADR drift\n\nHEAD: {inv['head']}\nInventory SHA-256: {digest(inv)}\n",
             '| ADR | Result | Evidence |\n| --- | --- | --- |']
    held = []
    for row in report['adrs']:
        ident = row['id']
        if row['status'] == 'human-verified':
            v = verdicts.get(ident)
            status = v['verdict'] if v else 'not run'
            evidence = (f"{v['path']}:{v['line']} — {v['quote']} — {v['reason']}" if v else 'missing human verification')
        else:
            status = 'conforming' if row['status'] == 'pass' else row['status']
            evidence = row.get('reason', f"command output SHA-256 {row.get('output_sha256', 'unavailable')}")
        if status != 'conforming':
            held.append(ident)
        lines.append(f"| ADR {ident} | {status} | {' '.join(evidence.splitlines()).replace('|', '&#124;')} |")
    lines += ['\nHeld: ' + (', '.join(held) or 'none'),
              'Drift decisions: update code in a new change; supersede the ADR; or accept drift with a reason.',
              'Missing proof is not conforming. No code, ADR, approval or workflow state changed.']
    if inventory(repo) != inv:
        raise ValueError('drift inputs changed before report write')
    output = safe_path(repo, rel)
    if output.exists() and output.stat().st_nlink != 1:
        raise ValueError('drift output cannot be a hardlink alias')
    output.write_text('\n'.join(lines) + '\n')
    return {**report, 'ready': not held, 'held': held}


def report_path(repo, output):
    """Reports may not alias source, approval records or standing documents."""
    supplied = Path(output).absolute()
    if supplied.is_symlink() or (supplied.exists() and supplied.stat().st_nlink != 1):
        raise ValueError('report output cannot be an alias')
    path = supplied.parent.resolve() / supplied.name
    if path.name not in {'adr-inventory.json', 'adr-checks-result.json', 'adr-conformance.json'}:
        raise ValueError('use a named ADR JSON report artifact')
    root = Path(repo).resolve()
    if path.is_relative_to(root):
        rel = path.relative_to(root)
        if len(rel.parts) != 4 or rel.parts[:2] != ('.software-factory', 'changes'):
            raise ValueError('in-repository report must be a change evidence artifact')
        safe_path(root, rel.as_posix())
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inventory', 'check', 'conformance', 'drift'])
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--checks', type=Path)
    parser.add_argument('--conflicts', type=Path)
    parser.add_argument('--human', type=Path)
    parser.add_argument('--draft', action='append', default=[])
    parser.add_argument('--small', action='store_true')
    parser.add_argument('--require-lines', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        output = report_path(args.repo, args.output) if args.output and args.action != 'drift' else None
        if args.action in {'check', 'drift'} and not args.checks:
            raise ValueError('named checks require --checks manifest.json')
        if args.action == 'drift' and not args.human:
            raise ValueError('drift requires --human evidence.json')
        if args.action == 'inventory':
            inv = inventory(args.repo)
            result = {'inventory': inv, 'inventory_sha256': digest(inv)}
        elif args.action == 'check':
            result = check(args.repo, strict_json(args.checks), args.require_lines)
        elif args.action == 'conformance':
            if not args.draft or (not args.small and not args.conflicts):
                raise ValueError('conformance requires drafts and conflict cards (except --small)')
            result = conformance(args.repo, args.draft, strict_json(args.conflicts) if args.conflicts else None, args.small)
        else:
            if not args.output:
                raise ValueError('drift requires --output <change>/drift.md')
            result = drift(args.repo, strict_json(args.checks), strict_json(args.human), args.output)
        if output:
            report_path(args.repo, output).write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        return 0 if result.get('ready', True) else 1
    except (ValueError, OSError, TypeError, subprocess.CalledProcessError) as exc:
        print(f'ADR evidence error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

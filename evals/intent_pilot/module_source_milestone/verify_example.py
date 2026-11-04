"""Verify the public example against explicit local committed Git objects."""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKSPACE = ROOT / 'examples/pond-claude-code'
REPO = Path(sys.argv[1]).resolve()
ENV = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
ENV.update(GIT_NO_LAZY_FETCH='1', GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')


def git(*arguments):
    return subprocess.check_output(['git', '-c', 'core.hooksPath=' + os.devnull,
        '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never', '-C', str(REPO),
        *arguments], env=ENV, timeout=15)


def command(name):
    return json.loads(subprocess.check_output([sys.executable, '-m', 'plumb', name,
        str(WORKSPACE), '--source-repo', str(REPO)], cwd=ROOT, timeout=15))


before_repo = git('status', '--porcelain')
config = json.loads((WORKSPACE / '.plumb/source.json').read_text())
capture = WORKSPACE / 'sources/decision.md'
header, body = capture.read_bytes().split(b'\n', 1)
metadata = json.loads(header[len('<!-- plumb-source '):-4])
commit = config['initial_commit']
source = git('cat-file', 'blob', commit + ':' + config['path'])
assert source == body
assert metadata['body_sha256'] == hashlib.sha256(body).hexdigest()
assert metadata['version'] == git('rev-parse', commit + ':' + config['path']).decode().strip()
for original, destination in config['code'].items():
    assert (WORKSPACE / destination).read_bytes() == git('cat-file', 'blob', commit + ':' + original)

# Independent fixed-fixture slice, without using the importer's heading parser.
start = source.index(b'### 6.6 Ingest order and integrity\n')
peer = re.search(rb'^### ', source[start + 1:], re.MULTILINE)
end = start + 1 + peer.start() if peer else len(source)
selected = source[start:end]
intent = (WORKSPACE / 'knowledge/intent.md').read_bytes()
assert intent.endswith(selected)
assert b'status: draft' in intent
assert b'type: Module Contract' in intent
assert b'type: Software Module' in (WORKSPACE / 'knowledge/module.md').read_bytes()
assert b'okf_version: "0.2"' in (WORKSPACE / 'knowledge/index.md').read_bytes()
assert ('https://github.com/tenequm/pond/blob/' + commit + '/docs/spec.md').encode() in intent
before = {p.relative_to(WORKSPACE).as_posix(): p.read_bytes()
          for p in WORKSPACE.rglob('*') if p.is_file()}
capture_stat = capture.stat()
status = command('status')
refresh = command('refresh')
assert status['status'] == 'current'
assert refresh['status'] == 'unchanged'
assert before == {p.relative_to(WORKSPACE).as_posix(): p.read_bytes()
                  for p in WORKSPACE.rglob('*') if p.is_file()}
assert capture.stat().st_mtime_ns == capture_stat.st_mtime_ns
assert capture.stat().st_ino == capture_stat.st_ino
assert git('status', '--porcelain') == before_repo
result = {'commit': commit, 'source_blob': metadata['version'], 'source_bytes': len(body),
    'selected_section_bytes': len(selected), 'code_files': len(config['code']),
    'all_code_and_source_match_committed_blobs': True, 'section_is_verbatim': True,
    'okf_draft_metadata_checked': True, 'status': status['status'], 'refresh': refresh['status'],
    'refresh_changed_files': [], 'original_repo_status_unchanged': True, 'new_model_calls': 0,
    'scope': 'Committed snapshot and local Git freshness; no semantic alignment verdict'}
(Path(__file__).parent / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))

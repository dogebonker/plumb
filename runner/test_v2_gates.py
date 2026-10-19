"""Fail-closed gate evidence and OS containment regressions."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kit'))
import v2_gates as gates
from test_v2_contract import plan_fixture


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'commit.gpgsign', 'false')
        (self.repo / 'app.py').write_text('def hello(): return 1\n')
        (self.repo / 'layout.json').write_text('{}')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['/usr/bin/git', '-C', str(self.repo), *args], text=True)

    def test_scope_includes_untracked_deleted_and_renamed_paths(self):
        (self.repo / 'outside.py').write_text('bad')
        result = gates.check_scope(self.repo, self.base, ['app.py'])
        self.assertEqual(result['status'], 'fail')
        self.assertIn('outside.py', result['violations'])
        (self.repo / 'outside.py').unlink()
        (self.repo / 'layout.json').unlink()
        self.assertIn('layout.json', gates.check_scope(self.repo, self.base, ['app.py'])['violations'])

    def test_frozen_mutation_and_links_fail_before_execution(self):
        frozen = [{'path': 'layout.json', 'sha256': hashlib.sha256(b'{}').hexdigest(), 'kind': 'policy'}]
        gates.snapshot(self.repo, frozen, {})
        (self.repo / 'layout.json').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'frozen'):
            gates.snapshot(self.repo, frozen, {})
        (self.repo / 'layout.json').write_text('{}')
        (self.repo / 'app.py').unlink()
        (self.repo / 'app.py').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            gates.snapshot(self.repo, frozen, {})

    def test_surface_exit_zero_is_not_coverage_or_signature_proof(self):
        expected = [{'path': 'app.py', 'symbol': 'hello', 'signature': 'hello() -> int'}]
        for data in ({}, {'complete': True, 'modules': []},
                     {'complete': False, 'files': ['app.py'], 'exports': []},
                     {'complete': True, 'files': ['app.py'], 'exports': [{'file': 'app.py', 'name': 'hello'}]}):
            with self.subTest(data=data):
                self.assertNotEqual(gates.check_surfaces(expected, data)['status'], 'pass')
        data = {'complete': True, 'files': ['app.py'], 'exports': [dict(expected[0])]}
        self.assertEqual(gates.check_surfaces(expected, data)['status'], 'pass')
        data['exports'].append({'path': 'app.py', 'symbol': 'extra', 'signature': 'extra()'})
        self.assertEqual(gates.check_surfaces(expected, data)['status'], 'fail')

    def test_stale_and_incomplete_evidence_rejected(self):
        binding = {key: 'a' * (40 if key == 'source_commit' else 64) for key in gates.BINDING_FIELDS}
        evidence = {'binding': binding, 'status': 'pass', 'gates': [],
                    'scope': {'status': 'pass'}, 'architecture': {'status': 'pass'}, 'surfaces': {'status': 'pass'}}
        with self.assertRaises(ValueError):
            gates.verify_evidence(evidence, binding)
        stale = dict(binding, source_tree='b' * 64)
        with self.assertRaisesRegex(ValueError, 'binding'):
            gates.verify_evidence(evidence, stale)


    def fixture(self, signature=True, cycles=None, new_cycles=None, extra_exports=(), check_output=None):
        plan = plan_fixture()
        plan['slices'] = plan['slices'][:1]
        item = plan['slices'][0]
        item.update(owns=['app.py'], fr=[])
        item['interfaces'] = [{'path': 'app.py', 'symbol': 'hello', 'signature': 'hello() -> int'}]
        plan.update(base_commit=self.base, frozen_inputs=[])
        plan['policy']['layout']['sha256'] = hashlib.sha256(b'{}').hexdigest()
        for gate in plan['policy']['gate_definitions']:
            gate['argv'] = ['echo', 'approved gate']
        exporter = self.root / 'archgraph'
        report = {'complete': True, 'modules': [{'exported': [{'file': 'app.py', 'name': 'hello'}]}]}
        if signature:
            report['modules'][0]['exported'][0]['signature'] = 'hello() -> int'
        report['modules'][0]['exported'].extend(extra_exports)
        graph = json.dumps({'files': [{'path': entry['file']} for entry in report['modules'][0]['exported']], 'cycles': cycles or [], 'edges': []})
        delta = json.dumps({'new_cycles': new_cycles or [], 'new_forbidden': []})
        check = check_output if check_output is not None else {'schema': 'archgraph/brief/v1', 'kind': 'check',
            'result': {'schema': 'archgraph/v1.2', 'kind': 'check', 'cycles': cycles or [], 'forbidden': []}}
        exporter.write_text(f"""#!/bin/sh
case "$1" in
scan) while [ "$1" != "--output" ]; do shift; done; shift; printf '%s' '{graph}' > "$1";;
diff) printf '%s' '{delta}';;
check) printf '%s' '{json.dumps(check)}';;
surface) printf '%s' '{json.dumps(report)}';;
esac
""")
        exporter.chmod(0o755)
        tools = {name: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                 for name, path in [('archgraph', exporter), ('echo', Path('/bin/echo')),
                                    ('git', Path('/Applications/Xcode.app/Contents/Developer/usr/bin/git')
                                     if Path('/Applications/Xcode.app/Contents/Developer/usr/bin/git').is_file() else Path('/usr/bin/git'))]}
        binding = {**gates.snapshot(self.repo, [], tools), 'plan_sha256': gates.digest(plan),
                   'contract_sha256': gates.digest({'slice': item, 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
        return plan, tools, binding

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_pinned_cli_end_to_end_and_missing_signature(self):
        for signature in (True, False):
            with self.subTest(signature=signature):
                plan, tools, binding = self.fixture(signature)
                evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                          artifacts=self.root / ('logs-' + str(signature)), tools=tools)
                self.assertEqual(evidence['status'], 'pass' if signature else 'unsupported', evidence)
                if signature:
                    gates.verify_evidence(evidence, binding)
                self.assertEqual(len(evidence['gates']), 7)
                for path in (self.root / ('logs-' + str(signature))).glob('*.log'):
                    self.assertLessEqual(path.stat().st_size, 4 * 1024 * 1024)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_existing_cycle_is_observed_and_new_cycle_fails(self):
        cycle = {'level': 'file', 'members': ['app.py', 'old.py']}
        for is_new in (False, True):
            plan, tools, binding = self.fixture(cycles=[cycle], new_cycles=[cycle] if is_new else [])
            evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                      artifacts=self.root / ('cycle-' + str(is_new)), tools=tools)
            self.assertEqual(evidence['status'], 'fail' if is_new else 'pass', evidence)
            self.assertEqual(evidence['architecture']['cycles'], [cycle])

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_gate_cannot_mutate_outside_sentinel_or_source(self):
        sentinel = self.root / 'sentinel'
        sentinel.write_text('protected')
        for target in (str(sentinel), 'app.py'):
            plan, tools, _ = self.fixture()
            path = Path('/usr/bin/touch')
            tools['touch'] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            plan['policy']['gate_definitions'][0]['argv'] = ['touch', target]
            binding = {**gates.snapshot(self.repo, [], tools), 'plan_sha256': gates.digest(plan),
                       'contract_sha256': gates.digest({'slice': plan['slices'][0], 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
            evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                      artifacts=self.root / ('denied-' + Path(target).name), tools=tools)
            self.assertEqual(evidence['status'], 'fail', evidence)
            self.assertEqual(evidence['gates'][0]['status'], 'fail')
            self.assertEqual(sentinel.read_text(), 'protected')
            self.assertEqual((self.repo / 'app.py').read_text(), 'def hello(): return 1\n')

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_actual_typescript_helper_inside_sandbox(self, actual_archgraph=False, unrelated=False, owned_javascript=False, monorepo=False, final_stage=False):
        import shutil
        node = shutil.which('node')
        compiler = Path(os.environ.get('FACTORY_TEST_TYPESCRIPT', '/Users/dan/.nvm/versions/node/v22.15.0/lib/node_modules/typescript/lib/typescript.js'))
        if not node or not compiler.is_file():
            self.skipTest('installed TypeScript and node required')
        (self.repo / 'app.py').unlink()
        if unrelated:
            (self.repo / 'unrelated.ts').write_text('export const other = 1;')
        if owned_javascript:
            (self.repo / 'extra.js').write_text('export const undocumented = 1;')
        source_name = 'apps/frontend/app.ts' if monorepo else 'app.ts'
        if monorepo:
            (self.repo / 'src').mkdir()
            (self.repo / 'src' / 'backend.py').write_text('value = 1')
        source = self.repo / source_name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('export function hello(x: string): string { return x; }\n')
        (self.repo / 'layout.json').write_text(json.dumps({'version': 1, 'modules': [{'id': 'app', 'path': '**'}],
                                                        'public': [{'module': 'app', 'entries': [source_name]}]}))
        self.git('add', '.')
        self.git('commit', '-qm', 'typescript baseline')
        self.base = self.git('rev-parse', 'HEAD').strip()
        plan, tools, _ = self.fixture(signature=False, extra_exports=[{'file': 'unrelated.ts', 'name': 'other'}] if unrelated else [])
        item = plan['slices'][0]
        plan['policy']['layout']['sha256'] = gates._sha(self.repo / 'layout.json')
        item['owns'] = [source_name, 'extra.js'] if owned_javascript else [source_name]
        item['interfaces'] = [{'path': source_name, 'symbol': 'hello', 'signature': '(x: string) => string'}]
        exporter = Path(tools['archgraph']['path'])
        exporter.write_text(exporter.read_text().replace('app.py', 'app.ts'))
        paths = {'archgraph': exporter, 'node': Path(node).resolve(), 'typescript': compiler,
                 'surfacehelper': Path(__file__).resolve().parents[1] / 'kit' / 'v2_surface.cjs',
                 'typescriptlib': compiler.parent}
        if actual_archgraph:
            paths['archgraph'] = Path('/Users/dan/Work/archgraph/target/debug/archgraph')
        tools.update({key: {'path': str(path), 'sha256': gates.tree_sha256(path) if path.is_dir() else gates._sha(path)}
                      for key, path in paths.items()})
        binding = {**gates.snapshot(self.repo, [], tools), 'plan_sha256': gates.digest(plan),
                   'contract_sha256': gates.digest({'slice': item, 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
        if final_stage:
            inputs = [{'path': source_name, 'sha256': gates._sha(source), 'kind': 'interface'}]
            binding['contract_sha256'] = gates.digest({'slice': item, 'files': inputs})
            evidence = gates.run_final_gates(self.repo, plan, binding, artifacts=self.root / 'typescript-logs',
                                            tools=tools, contract_inputs=inputs)
        else:
            evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                      artifacts=self.root / 'typescript-logs', tools=tools)
        if owned_javascript:
            self.assertEqual(evidence['status'], 'unsupported', evidence)
            self.assertFalse(evidence['gates'])
            return
        if monorepo:
            self.assertEqual(evidence['status'], 'unsupported', evidence)
            self.assertIn('architecture scan missing source coverage', evidence['reason'])
            self.assertFalse(any(row['id'] == 'surface-types' for row in evidence['gates']))
            return
        self.assertEqual(evidence['status'], 'pass', evidence)
        gates.verify_evidence(evidence, binding)
        self.assertTrue(any(row['id'] == 'surface-types' for row in evidence['gates']))
        if final_stage:
            index = next(index for index, row in enumerate(evidence['gates'], 1) if row['id'] == 'architecture-final')
            actual = json.loads((self.root / 'typescript-logs' / (str(index) + '.log')).read_text())
            self.assertEqual((actual['schema'], actual['kind']), ('archgraph/brief/v1', 'check'))
        if unrelated:
            observation = evidence['surfaces']['archgraph']
            self.assertTrue(any(entry['file'] == 'unrelated.ts' for entry in observation['global_observed_exports']))
            self.assertFalse(any(entry['file'] == 'unrelated.ts' for entry in observation['observed_exports']))

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_fr_execution_report_and_required_nfr_evidence(self):
        (self.repo / 'cases.json').write_text('{}')
        self.git('add', '.')
        self.git('commit', '-qm', 'frozen cases')
        self.base = self.git('rev-parse', 'HEAD').strip()
        for reported in (False, True):
            plan, tools, _ = self.fixture()
            item = plan['slices'][0]
            item['fr'] = [{'id': 'FR-one', 'given': 'input', 'when': 'run', 'then': 'output',
                           'gate_id': 'tests', 'case_id': 'case-one'}]
            item['gates'].append('nfr')
            item['nfr'] = [{'id': 'NFR-one', 'gate_id': 'nfr', 'threshold': 100}]
            plan['policy']['gate_definitions'][3]['argv'] = ['echo', '{"nfr":{"NFR-one":1}}']
            plan['frozen_inputs'] = [{'path': 'cases.json', 'sha256': gates._sha(self.repo / 'cases.json'), 'kind': 'fr'}]
            if reported:
                plan['policy']['gate_definitions'][0]['argv'] = ['echo', '{"case_ids":["case-one"]}']
            binding = {**gates.snapshot(self.repo, plan['frozen_inputs'], tools), 'plan_sha256': gates.digest(plan),
                       'contract_sha256': gates.digest({'slice': item, 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
            evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                      artifacts=self.root / ('coverage-' + str(reported)), tools=tools)
            self.assertEqual(evidence['status'], 'pass' if reported else 'unsupported', evidence)
            if reported:
                gates.verify_evidence(evidence, binding)
                evidence['gates'] = [row for row in evidence['gates'] if row['kind'] != 'nfr']
                with self.assertRaisesRegex(ValueError, 'required gate'):
                    gates.verify_evidence(evidence, binding)
            else:
                self.assertEqual(len(evidence['gates']), 1)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_explicit_dependency_mount_is_pinned_and_readonly(self):
        dependency_root = self.root / 'cache' / 'node_modules'
        dependency_root.mkdir(parents=True)
        installed_lock = dependency_root / '.package-lock.json'
        installed_lock.write_text('{"installed":true}')
        (self.repo / 'package-lock.json').write_text('{"source":true}')
        self.git('add', '.')
        self.git('commit', '-qm', 'approved dependency lock')
        self.base = self.git('rev-parse', 'HEAD').strip()
        for operation in ('test', 'touch'):
            plan, tools, _ = self.fixture()
            path = Path('/bin/test' if operation == 'test' else '/usr/bin/touch')
            tools[operation] = {'path': str(path), 'sha256': gates._sha(path)}
            tools['dependencylock'] = {'path': str(installed_lock), 'sha256': gates._sha(installed_lock)}
            tools['dependencytree'] = {'path': str(dependency_root), 'sha256': gates.tree_sha256(dependency_root)}
            args = ['test', '-f', 'node_modules/.package-lock.json'] if operation == 'test' else ['touch', 'node_modules/.package-lock.json']
            plan['policy']['gate_definitions'][0]['argv'] = args
            plan['frozen_inputs'] = [{'path': 'package-lock.json', 'sha256': gates._sha(self.repo / 'package-lock.json'), 'kind': 'dependency-lock'}]
            binding = {**gates.snapshot(self.repo, plan['frozen_inputs'], tools), 'plan_sha256': gates.digest(plan),
                       'contract_sha256': gates.digest({'slice': plan['slices'][0], 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
            evidence = gates.run_gates(self.repo, plan, 'contracts', binding, artifacts=self.root / operation,
                                      tools=tools, read_only=[dependency_root])
            self.assertEqual(evidence['status'], 'pass' if operation == 'test' else 'fail', evidence)
            self.assertEqual(installed_lock.read_text(), '{"installed":true}')

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_timeout_and_output_are_bounded(self):
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        for argv, timeout, name in ((['/bin/sleep', '5'], .1, 'timeout'), (['/usr/bin/yes'], 5, 'output')):
            log = self.root / (name + '.log')
            result = gates._command(argv, source, scratch, (), (), log, timeout)
            self.assertEqual(result['status'], 'fail')
            self.assertLess(result['duration_ms'], 2000)
            self.assertLessEqual(log.stat().st_size, 4 * 1024 * 1024)
            self.assertEqual(result['output_sha256'], gates._sha(log))

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/Users/dan/Work/archgraph/target/debug/archgraph').is_file(), 'existing local archgraph binary required')
    def test_actual_archgraph_with_pinned_real_git(self):
        self.test_actual_typescript_helper_inside_sandbox(actual_archgraph=True)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_captured_slice_baseline_allows_dependency_commits(self):
        original_base = self.base
        (self.repo / 'dependency.py').write_text('accepted = True')
        self.git('add', '.')
        self.git('commit', '-qm', 'accepted dependency')
        fork = self.git('rev-parse', 'HEAD').strip()
        plan, tools, binding = self.fixture()
        self.assertEqual(plan['base_commit'], original_base)
        (self.repo / 'app.py').write_text('def hello(): return 2\n')
        binding.update(gates.snapshot(self.repo, [], tools))
        rejected = gates.run_gates(self.repo, plan, 'contracts', binding, artifacts=self.root / 'rejected', tools=tools)
        self.assertEqual(rejected['status'], 'fail')
        accepted = gates.run_gates(self.repo, plan, 'contracts', binding, artifacts=self.root / 'accepted', tools=tools,
                                  scope_base_commit=fork)
        self.assertEqual(accepted['status'], 'pass', accepted)
        self.assertEqual(accepted['scope']['base_commit'], fork)
        self.assertEqual(accepted['scope']['changed'], ['app.py'])

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_final_runs_union_and_all_frozen_cases_once(self):
        (self.repo / 'feature.py').write_text('def feature(): return 1')
        (self.repo / 'cases.json').write_text('{}')
        self.git('add', '.')
        self.git('commit', '-qm', 'frozen final baseline')
        self.base = self.git('rev-parse', 'HEAD').strip()
        plan, tools, _ = self.fixture(extra_exports=[{'file': 'feature.py', 'name': 'feature', 'signature': 'feature() -> int'}])
        feature = plan_fixture()['slices'][1]
        feature.update(owns=['feature.py'], interfaces=[{'path': 'feature.py', 'symbol': 'feature', 'signature': 'feature() -> int'}])
        plan['slices'].append(feature)
        for item in plan['slices']:
            item['fr'] = [{'id': 'FR-' + item['id'], 'given': 'input', 'when': 'run', 'then': 'output',
                           'gate_id': 'tests', 'case_id': 'case-' + item['id']}]
        plan['frozen_inputs'] = [{'path': 'cases.json', 'sha256': gates._sha(self.repo / 'cases.json'), 'kind': 'fr'}]
        plan['policy']['gate_definitions'][0]['argv'] = ['echo', '{"case_ids":["case-contracts","case-feature"]}']
        for index, item in enumerate(plan['slices']):
            item['gates'].append('nfr')
            item['nfr'] = [{'id': 'shared-budget', 'gate_id': 'nfr', 'threshold': 10 - index}]
        plan['policy']['gate_definitions'][3]['argv'] = ['echo', '{"nfr":{"shared-budget":5}}']
        binding = {**gates.snapshot(self.repo, plan['frozen_inputs'], tools), 'plan_sha256': gates.digest(plan),
                   'contract_sha256': gates.digest({'slice': plan['slices'][0], 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
        inputs = [{'path': 'app.py', 'sha256': gates._sha(self.repo / 'app.py'), 'kind': 'interface'}]
        binding['contract_sha256'] = gates.digest({'slice': plan['slices'][0], 'files': inputs})
        evidence = gates.run_final_gates(self.repo, plan, binding, artifacts=self.root / 'final', tools=tools, contract_inputs=inputs)
        self.assertEqual(evidence['status'], 'pass', evidence)
        gates.verify_evidence(evidence, binding)
        self.assertEqual(len([row for row in evidence['gates'] if row['kind'] == 'tests']), 1)
        self.assertIn('architecture-final', [row['id'] for row in evidence['gates']])
        self.assertEqual(evidence['required_gates'][0]['case_ids'], ['case-contracts', 'case-feature'])

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_final_rejects_preexisting_cycles_and_actual_contract_mutation(self):
        plan, tools, _ = self.fixture(cycles=[{'level': 'file', 'members': ['app.py']}])
        inputs = [{'path': 'app.py', 'sha256': gates._sha(self.repo / 'app.py'), 'kind': 'interface'}]
        binding = {**gates.snapshot(self.repo, inputs, tools), 'plan_sha256': gates.digest(plan),
                   'contract_sha256': gates.digest({'slice': plan['slices'][0], 'files': inputs}), 'policy_sha256': gates.digest(plan['policy'])}
        evidence = gates.run_final_gates(self.repo, plan, binding, artifacts=self.root / 'final-cycle', tools=tools, contract_inputs=inputs)
        self.assertEqual(evidence['status'], 'fail', evidence)
        self.assertEqual(evidence['architecture']['status'], 'fail')
        (self.repo / 'app.py').write_text('def hello(): return 99')
        binding.update(gates.snapshot(self.repo, [], tools))
        evidence = gates.run_gates(self.repo, plan, 'contracts', binding, artifacts=self.root / 'mutation', tools=tools,
                                  contract_inputs=inputs)
        self.assertEqual(evidence['status'], 'fail', evidence)
        self.assertFalse(evidence['gates'])
        self.assertIn('frozen input changed', evidence['reason'])

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_loopback_servers_work_and_external_network_is_denied(self):
        import shutil
        node = shutil.which('node')
        if not node:
            self.skipTest('node required')
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        code = """const net = require('node:net');
const remote = net.connect({host:'203.0.113.1',port:80});
remote.on('connect', () => process.exit(12));
remote.on('error', e => {
 if (!['EPERM','EACCES'].includes(e.code)) process.exit(13);
 const server = net.createServer(c => c.end('ok'));
 server.listen(Number(process.env.FACTORY_TEST_PORT), '127.0.0.1', () => {
  const client = net.connect(server.address().port, '127.0.0.1');
  client.on('data', bytes => { if (String(bytes) !== 'ok') process.exit(14); });
  client.on('end', () => server.close());
 });
});
setTimeout(() => process.exit(15), 1500).unref();"""
        result = gates._command([node, '-e', code], source, scratch, (), [Path(node).resolve()], self.root / 'network.log', 3)
        self.assertEqual(result['status'], 'pass', result)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_repeated_approved_derived_output(self):
        plan, tools, _ = self.fixture()
        for gate in plan['policy']['gate_definitions'][:2]:
            gate['outputs'] = ['build/']
        binding = {**gates.snapshot(self.repo, [], tools), 'plan_sha256': gates.digest(plan),
                   'contract_sha256': gates.digest({'slice': plan['slices'][0], 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
        evidence = gates.run_gates(self.repo, plan, 'contracts', binding, artifacts=self.root / 'outputs', tools=tools)
        self.assertEqual(evidence['status'], 'pass', evidence)
        self.assertFalse((self.repo / 'build').exists())

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_unrelated_baseline_exports_do_not_expand_slice_surface(self):
        self.test_actual_typescript_helper_inside_sandbox(unrelated=True)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_nfr_reports_are_finite_and_at_most_the_threshold(self):
        for index, value in enumerate((None, float('nan'), float('inf'), True, 101, 100, -1)):
            with self.subTest(value=value):
                plan, tools, _ = self.fixture()
                item = plan['slices'][0]
                item['gates'].append('nfr')
                item['nfr'] = [{'id': 'NFR-budget', 'gate_id': 'nfr', 'threshold': 100}]
                payload = {'nfr': {} if value is None else {'NFR-budget': value}}
                plan['policy']['gate_definitions'][3]['argv'] = ['echo', json.dumps(payload)]
                binding = {**gates.snapshot(self.repo, [], tools), 'plan_sha256': gates.digest(plan),
                           'contract_sha256': gates.digest({'slice': item, 'files': []}), 'policy_sha256': gates.digest(plan['policy'])}
                evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                          artifacts=self.root / ('nfr-' + str(index)), tools=tools)
                if type(value) is int and value <= 100:
                    self.assertEqual(evidence['status'], 'pass', evidence)
                    row = next(row for row in evidence['gates'] if row['kind'] == 'nfr')
                    self.assertEqual(row['nfr'], [{'id': 'NFR-budget', 'observed': value, 'threshold': 100, 'operator': 'at_most'}])
                    gates.verify_evidence(evidence, binding)
                else:
                    self.assertNotEqual(evidence['status'], 'pass', evidence)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_sandbox_cannot_signal_host_but_can_signal_its_child(self):
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        host = subprocess.Popen(['/bin/sleep', '20'])
        try:
            row = gates._command(['/bin/kill', '-TERM', str(host.pid)], source, scratch, (), (), self.root / 'host-signal.log', 3)
            self.assertNotEqual(row['exit_code'], 0)
            self.assertIsNone(host.poll(), 'sandbox signalled an unrelated host process')
            row = gates._command(['/bin/sh', '-c', 'sleep 20 & child=$!; kill -TERM "$child"; wait "$child"; test "$?" -ne 0'],
                                 source, scratch, (), (), self.root / 'child-signal.log', 3)
            self.assertEqual(row['status'], 'pass', row)
        finally:
            if host.poll() is None:
                host.terminate()
            host.wait()

    def test_dependency_content_changes_invalidate_pins_without_lock_changes(self):
        dependencies = self.root / 'node_modules'
        package = dependencies / 'pkg'
        package.mkdir(parents=True)
        lock = dependencies / '.package-lock.json'
        lock.write_text('{}')
        implementation = package / 'index.js'
        implementation.write_text('module.exports = 1')
        tools = {'dependencylock': {'path': str(lock), 'sha256': gates._sha(lock)}}
        with self.assertRaisesRegex(ValueError, 'dependency tree'):
            gates.snapshot(self.repo, [], tools)
        tools['dependencytree'] = {'path': str(dependencies), 'sha256': gates.tree_sha256(dependencies)}
        original = gates.snapshot(self.repo, [], tools)
        implementation.write_text('module.exports = 2')
        with self.assertRaisesRegex(ValueError, 'pinned tool changed'):
            gates.snapshot(self.repo, [], tools)
        tools['dependencytree']['sha256'] = gates.tree_sha256(dependencies)
        refreshed = gates.snapshot(self.repo, [], tools)
        self.assertNotEqual(refreshed['tools_sha256'], original['tools_sha256'])
        base = {'plan_sha256': 'a' * 64, 'contract_sha256': 'a' * 64, 'policy_sha256': 'a' * 64}
        with self.assertRaisesRegex(ValueError, 'binding mismatch'):
            gates.verify_evidence({'binding': {**base, **original}}, {**base, **refreshed})

    def test_typescript_declaration_changes_invalidate_the_compiler_tree_pin(self):
        library = self.root / 'compiler-lib'
        library.mkdir()
        compiler = library / 'typescript.js'
        compiler.write_text('compiler')
        definitions = library / 'lib.d.ts'
        definitions.write_text('declare const value: string;')
        tools = {'typescript': {'path': str(compiler), 'sha256': gates._sha(compiler)},
                 'typescriptlib': {'path': str(library), 'sha256': gates.tree_sha256(library)}}
        gates.snapshot(self.repo, [], tools)
        definitions.write_text('declare const value: any;')
        with self.assertRaisesRegex(ValueError, 'pinned tool changed: typescriptlib'):
            gates.snapshot(self.repo, [], tools)

    def test_dependency_tree_links_cannot_escape_the_trusted_root(self):
        dependencies = self.root / 'node_modules'
        dependencies.mkdir()
        (dependencies / 'inside.js').write_text('safe')
        (dependencies / 'alias.js').symlink_to('inside.js')
        gates.tree_sha256(dependencies)
        (dependencies / 'escape.js').symlink_to('../repo/app.py')
        with self.assertRaisesRegex(ValueError, 'outside'):
            gates.tree_sha256(dependencies)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_sandbox_denies_synthetic_outside_process_arguments(self):
        import ctypes
        sentinel = 'FACTORY_PROC_SENTINEL=synthetic-test-only'
        host = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'],
                                env={'FACTORY_PROC_SENTINEL': 'synthetic-test-only'})
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            mib = (ctypes.c_int * 3)(1, 49, host.pid)  # Darwin CTL_KERN/KERN_PROCARGS2.
            buffer = ctypes.create_string_buffer(1024 * 1024)
            size = ctypes.c_size_t(len(buffer))
            baseline = libc.sysctl(mib, 3, buffer, ctypes.byref(size), None, 0)
            if baseline != 0 or sentinel.encode() not in buffer.raw[:size.value]:
                self.skipTest('platform baseline does not expose the synthetic process sentinel')
            source, scratch = self.root / 'source', self.root / 'scratch'
            source.mkdir()
            scratch.mkdir()
            code = f"""import ctypes,json
libc=ctypes.CDLL(None,use_errno=True)
mib=(ctypes.c_int*3)(1,49,{host.pid})
buffer=ctypes.create_string_buffer(1048576)
size=ctypes.c_size_t(len(buffer))
result=libc.sysctl(mib,3,buffer,ctypes.byref(size),None,0)
print(json.dumps({{'result':result,'errno':ctypes.get_errno()}}))
"""
            log = self.root / 'procargs.log'
            row = gates._command([sys.executable, '-c', code], source, scratch, (), [Path(sys.prefix).resolve()], log, 5)
            self.assertEqual(row['status'], 'pass', row)
            result = json.loads(log.read_text())
            self.assertNotEqual(result['result'], 0, 'sandbox exposed the outside synthetic process arguments')
            self.assertIn(result['errno'], (1, 13))
        finally:
            if host.poll() is None:
                host.terminate()
            host.wait()

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_sandbox_denies_security_service_lookup_without_using_the_service(self):
        import ctypes
        libc = ctypes.CDLL(None)
        bootstrap = ctypes.c_uint.in_dll(libc, 'bootstrap_port').value
        port = ctypes.c_uint()
        baseline = libc.bootstrap_look_up(bootstrap, b'com.apple.SecurityServer', ctypes.byref(port))
        if baseline != 0:
            self.skipTest('platform baseline denies SecurityServer name lookup')
        libc.mach_port_deallocate(ctypes.c_uint.in_dll(libc, 'mach_task_self_').value, port)
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        code = """import ctypes,json
libc=ctypes.CDLL(None)
bootstrap=ctypes.c_uint.in_dll(libc,'bootstrap_port').value
port=ctypes.c_uint()
result=libc.bootstrap_look_up(bootstrap,b'com.apple.SecurityServer',ctypes.byref(port))
if port.value: libc.mach_port_deallocate(ctypes.c_uint.in_dll(libc,'mach_task_self_').value,port)
print(json.dumps({'result':result}))
"""
        log = self.root / 'mach-lookup.log'
        row = gates._command([sys.executable, '-c', code], source, scratch, (), [Path(sys.prefix).resolve()], log, 5)
        self.assertEqual(row['status'], 'pass', row)
        self.assertNotEqual(json.loads(log.read_text())['result'], 0, 'sandbox obtained a security service port')

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_system_metadata_keeps_node_and_python_runtimes_usable(self):
        import shutil
        node = shutil.which('node')
        if not node:
            self.skipTest('node required')
        code = "const o=require('node:os');console.log(JSON.stringify({cpus:o.cpus().length,available:o.availableParallelism(),memory:o.totalmem()}))"
        baseline = json.loads(subprocess.check_output([node, '-e', code], text=True))
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        log = self.root / 'metadata.log'
        row = gates._command([node, '-e', code], source, scratch, (), [Path(node).resolve()], log, 5)
        self.assertEqual(row['status'], 'pass', row)
        self.assertEqual(json.loads(log.read_text()), baseline)
        python_log = self.root / 'page-size.log'
        row = gates._command([sys.executable, '-c', 'import os; print(os.sysconf("SC_PAGE_SIZE"))'],
                             source, scratch, (), [Path(sys.prefix).resolve()], python_log, 5)
        self.assertEqual(row['status'], 'pass', row)
        self.assertEqual(int(python_log.read_text()), os.sysconf('SC_PAGE_SIZE'))

    def test_dependency_chains_cannot_escape_or_dangle_or_cycle(self):
        dependencies = self.root / 'node_modules'
        dependencies.mkdir()
        package = dependencies / 'pkg'
        package.mkdir()
        (package / 'index.js').write_text('safe')
        bins = dependencies / '.bin'
        bins.mkdir()
        (bins / 'safe').symlink_to('../pkg/index.js')
        (dependencies / 'same').symlink_to('.')
        gates.tree_sha256(dependencies)
        (self.root / 'outside.js').write_text('outside synthetic fixture')
        bad = dependencies / 'escape.js'
        bad.symlink_to('same/../outside.js')
        with self.assertRaisesRegex(ValueError, 'outside'):
            gates.tree_sha256(dependencies)
        bad.unlink()
        for target in ('missing.js', 'escape.js', 'pkg/index.js/../index.js'):
            bad.symlink_to(target)
            with self.assertRaises(ValueError):
                gates.tree_sha256(dependencies)
            bad.unlink()

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_sandbox_cannot_read_an_unrelated_host_http_service(self):
        import http.server
        import shutil
        import threading
        node = shutil.which('node')
        if not node:
            self.skipTest('node required')
        requests = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'synthetic-host-only')
            def log_message(self, *args):
                pass
        host = http.server.HTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=host.serve_forever, daemon=True)
        worker.start()
        try:
            source, scratch = self.root / 'source', self.root / 'scratch'
            source.mkdir()
            scratch.mkdir()
            code = f"""const http=require('node:http');
http.get({{host:'127.0.0.1',port:{host.server_port},path:'/'}},res=>{{res.resume();res.on('end',()=>process.exit(12));}})
.on('error',e=>{{if(!['EPERM','EACCES'].includes(e.code))process.exit(13);}});
setTimeout(()=>process.exit(14),1500).unref();"""
            result = gates._command([node, '-e', code], source, scratch, (), [Path(node).resolve()], self.root / 'host-http.log', 3)
            self.assertEqual(result['status'], 'pass', result)
            self.assertEqual(requests, [])
        finally:
            host.shutdown()
            host.server_close()
            worker.join()

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/Users/dan/Work/archgraph/target/debug/archgraph').is_file(), 'existing local archgraph binary required')
    def test_owned_javascript_cannot_be_omitted_from_surface_proof(self):
        self.test_actual_typescript_helper_inside_sandbox(actual_archgraph=True, owned_javascript=True)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_profile_without_a_test_port_has_no_network_capability(self):
        import shutil
        node = shutil.which('node')
        if not node:
            self.skipTest('node required')
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        profile = gates._sandbox_profile(source, scratch, (), [Path(node).resolve()])
        code = """const net=require('node:net');
const server=net.createServer();
server.on('error',e=>process.exit(['EPERM','EACCES'].includes(e.code)?0:13));
server.on('listening',()=>process.exit(12));
server.listen(0,'127.0.0.1');"""
        result = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, node, '-e', code],
                                env={'PATH': '/usr/bin:/bin', 'HOME': str(scratch), 'TMPDIR': str(scratch)},
                                capture_output=True, timeout=3, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_detached_descendant_limit_is_explicit_and_synthetic_children_are_cleaned(self):
        import signal
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        for index, operation in enumerate(('os.setsid()', 'os.setpgid(0,0)')):
            code = f"""import os,json
read,write=os.pipe()
pid=os.fork()
if pid==0:
 os.close(read)
 try: {operation}
 except OSError:
  os.write(write,b'blocked');os._exit(0)
 null=os.open('/dev/null',os.O_RDWR)
 for fd in (0,1,2):os.dup2(null,fd)
 os.write(write,b'ready');os.close(write)
 os.execv('/bin/sleep',['sleep','5'])
os.close(write)
ready=os.read(read,16)
print(json.dumps({{'pid':pid,'ready':ready.decode()}}),flush=True)
"""
            log = self.root / ('detached-' + str(index) + '.log')
            row = gates._command([sys.executable, '-c', code], source, scratch, (), [Path(sys.prefix).resolve()], log, 2)
            data = json.loads(log.read_text())
            try:
                self.assertEqual(row['status'], 'pass', row)
                self.assertEqual(row['process_lifecycle'], 'leader timeout and current process group cleanup; detached descendants not contained')
                if data['ready'] == 'ready':
                    os.kill(data['pid'], 0)
                else:
                    self.assertEqual(data['ready'], 'blocked')
            finally:
                if data['ready'] == 'ready':
                    try:
                        os.kill(data['pid'], signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_approved_final_test_gate_replaces_slice_tests_and_requires_all_cases(self):
        (self.repo / 'feature.py').write_text('pass')
        (self.repo / 'cases.json').write_text('{}')
        self.git('add', '.')
        self.git('commit', '-qm', 'frozen merged test fixture')
        self.base = self.git('rev-parse', 'HEAD').strip()
        plan, tools, _ = self.fixture()
        feature = plan_fixture()['slices'][1]
        feature.update(owns=['feature.py'], fr=[{'id': 'FR-feature', 'given': 'input', 'when': 'run', 'then': 'output',
                                               'gate_id': 'feature-tests', 'case_id': 'feature-only'}],
                       gates=['feature-tests', 'typecheck', 'lint'])
        plan['slices'][0]['fr'] = [{'id': 'FR-contract', 'given': 'input', 'when': 'run', 'then': 'output',
                                   'gate_id': 'tests', 'case_id': 'contract-only'}]
        plan['slices'].append(feature)
        plan['frozen_inputs'] = [{'path': 'cases.json', 'sha256': gates._sha(self.repo / 'cases.json'), 'kind': 'fr'}]
        definitions = plan['policy']['gate_definitions']
        definitions[0]['argv'] = ['echo', '{"case_ids":["contract-only"]}']
        definitions.extend([{'id': 'feature-tests', 'kind': 'tests', 'argv': ['echo', '{"case_ids":["feature-only"]}'], 'timeout_seconds': 10},
                            {'id': 'merged-tests', 'kind': 'tests', 'argv': ['echo', '{}'], 'timeout_seconds': 10}])
        plan['policy']['final_test_gate'] = 'merged-tests'
        inputs = [{'path': 'app.py', 'sha256': gates._sha(self.repo / 'app.py'), 'kind': 'interface'}]
        for complete in (True, False):
            definitions[-1]['argv'] = ['echo', json.dumps({'case_ids': ['contract-only', 'feature-only'] if complete else ['contract-only']})]
            binding = {**gates.snapshot(self.repo, plan['frozen_inputs'], tools), 'plan_sha256': gates.digest(plan),
                       'contract_sha256': gates.digest({'slice': plan['slices'][0], 'files': inputs}), 'policy_sha256': gates.digest(plan['policy'])}
            evidence = gates.run_final_gates(self.repo, plan, binding, artifacts=self.root / ('merged-' + str(complete)),
                                            tools=tools, contract_inputs=inputs)
            self.assertEqual(evidence['status'], 'pass' if complete else 'unsupported', evidence)
            tests = [row for row in evidence['gates'] if row['kind'] == 'tests']
            self.assertEqual([row['id'] for row in tests], ['merged-tests'])
            self.assertEqual(tests[0]['argv'], ['/bin/echo', definitions[-1]['argv'][1]])
            required = next(row for row in evidence['required_gates'] if row['id'] == 'merged-tests')
            self.assertEqual(set(required['case_ids']), {'contract-only', 'feature-only'})
            if complete:
                gates.verify_evidence(evidence, binding)
                tests[0]['case_ids'].remove('feature-only')
                with self.assertRaisesRegex(ValueError, 'FR execution coverage'):
                    gates.verify_evidence(evidence, binding)
        binding['contract_sha256'] = gates.digest({'slice': plan['slices'][0], 'files': []})
        evidence = gates.run_gates(self.repo, plan, 'contracts', binding, artifacts=self.root / 'slice-only', tools=tools)
        self.assertEqual(evidence['status'], 'pass', evidence)
        self.assertEqual([row['id'] for row in evidence['gates'] if row['kind'] == 'tests'], ['tests'])

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/Users/dan/Work/archgraph/target/debug/archgraph').is_file(), 'existing local archgraph binary required')
    def test_compiler_proof_cannot_replace_missing_monorepo_architecture_coverage(self):
        self.test_actual_typescript_helper_inside_sandbox(actual_archgraph=True, monorepo=True)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_failed_command_exposes_bounded_stderr_tail_but_success_omits_it(self):
        source, scratch = self.root / 'source', self.root / 'scratch'
        source.mkdir()
        scratch.mkdir()
        payload = b'EARLY_LOG_PAYLOAD' + b'x' * 20000 + bytes([255]) * 4096 + b'\napp/api.ts:7 error TS2322: string is not number\n'
        for exit_code in (3, 0):
            code = f'import os,sys; os.write(2,{payload!r}); sys.exit({exit_code})'
            log = self.root / ('diagnostic-' + str(exit_code) + '.log')
            row = gates._command([sys.executable, '-c', code], source, scratch, (), [Path(sys.prefix).resolve()], log, 5)
            self.assertEqual(row['exit_code'], exit_code)
            self.assertEqual(log.read_bytes(), payload)
            self.assertEqual(row['output_sha256'], hashlib.sha256(payload).hexdigest())
            if exit_code:
                excerpt = row['untrusted_output_excerpt']
                self.assertIn('app/api.ts:7 error TS2322: string is not number', excerpt)
                self.assertIn('\ufffd', excerpt)
                self.assertNotIn('EARLY_LOG_PAYLOAD', excerpt)
                self.assertLessEqual(len(excerpt.encode('utf-8')), 8192)
            else:
                self.assertNotIn('untrusted_output_excerpt', row)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/Users/dan/Work/archgraph/target/debug/archgraph').is_file(), 'existing local archgraph binary required')
    def test_actual_native_final_gate_parses_the_brief_check_envelope(self):
        self.test_actual_typescript_helper_inside_sandbox(actual_archgraph=True, final_stage=True)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_malformed_native_brief_check_is_unsupported_even_with_top_level_empty_lists(self):
        valid = {'schema': 'archgraph/v1.2', 'kind': 'check', 'forbidden': [], 'cycles': []}
        malformed = [
            {'schema': 'archgraph/brief/v999', 'kind': 'check', 'result': valid},
            {'schema': 'archgraph/brief/v1', 'kind': 'scan', 'result': valid},
            {'schema': 'archgraph/brief/v1', 'kind': 'check', 'result': {'schema': 'archgraph/v1.2', 'kind': 'check', 'cycles': []}},
            {'schema': 'archgraph/brief/v1', 'kind': 'check', 'result': 'unknown'},
        ]
        for index, output in enumerate(malformed):
            with self.subTest(output=output):
                output.update(forbidden=[], cycles=[])
                plan, tools, _ = self.fixture(check_output=output)
                inputs = [{'path': 'app.py', 'sha256': gates._sha(self.repo / 'app.py'), 'kind': 'interface'}]
                binding = {**gates.snapshot(self.repo, inputs, tools), 'plan_sha256': gates.digest(plan),
                           'contract_sha256': gates.digest({'slice': plan['slices'][0], 'files': inputs}),
                           'policy_sha256': gates.digest(plan['policy'])}
                evidence = gates.run_final_gates(self.repo, plan, binding, artifacts=self.root / ('malformed-' + str(index)),
                                                tools=tools, contract_inputs=inputs)
                self.assertEqual(evidence['status'], 'unsupported', evidence)
                with self.assertRaises(ValueError):
                    gates.verify_evidence(evidence, binding)

    def test_scope_and_stale_binding_block_commands(self):
        plan, tools, binding = self.fixture()
        (self.repo / 'outside.py').write_text('no')
        evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                  artifacts=self.root / 'logs', tools=tools)
        self.assertEqual(evidence['status'], 'fail')
        self.assertFalse(evidence['gates'])
        (self.repo / 'outside.py').unlink()
        binding = {**binding, **gates.snapshot(self.repo, [], tools)}
        (self.repo / 'layout.json').write_text('changed')
        evidence = gates.run_gates(self.repo, plan, 'contracts', binding,
                                  artifacts=self.root / 'logs', tools=tools)
        self.assertEqual(evidence['status'], 'fail')
        self.assertFalse(evidence['gates'])

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/usr/bin/sandbox-exec').exists(), 'requires macOS sandbox-exec')
    def test_actual_sandbox_denies_external_read_and_write(self):
        source = self.root / 'source'
        source.mkdir()
        scratch = self.root / 'scratch'
        scratch.mkdir()
        sentinel = self.root / 'sentinel'
        sentinel.write_text('protected')
        profile = gates._sandbox_profile(source, scratch, (), ())
        for expression in (f'cat {sentinel}', f'echo changed > {sentinel}', f'echo changed > {source}/new'):
            result = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, '/bin/sh', '-c', expression], capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
        alias = Path('/System/Volumes/Data') / sentinel.relative_to('/')
        if alias.exists():
            result = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, '/bin/cat', str(alias)],
                                    capture_output=True, check=False)
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sentinel.read_text(), 'protected')
        self.assertFalse((source / 'new').exists())


if __name__ == '__main__':
    unittest.main()

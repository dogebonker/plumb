"""Compiler-backed surface compatibility and complete export inventory."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parents[1] / 'kit' / 'v2_surface.cjs'
TYPESCRIPT = Path(os.environ.get('FACTORY_TEST_TYPESCRIPT',
    '/Users/dan/.nvm/versions/node/v22.15.0/lib/node_modules/typescript/lib/typescript.js'))


@unittest.skipUnless(TYPESCRIPT.is_file() and shutil.which('node'), 'installed TypeScript compiler and node required')
class SurfaceTests(unittest.TestCase):
    def run_surface(self, sources, interfaces, files=None, config=None, compiler=TYPESCRIPT):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            root.mkdir()
            for name, text in sources.items():
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(text)
            if config is not None:
                (root / 'tsconfig.json').write_text(json.dumps(config))
            expected = Path(tmp) / 'expected.json'
            expected.write_text(json.dumps({'files': files if files is not None else list(sources),
                                           'interfaces': interfaces}))
            before = {p.relative_to(root): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in root.rglob('*') if p.is_file()}
            output = Path(tmp) / 'proof.json'
            result = subprocess.run(['node', str(HELPER), '--root', str(root), '--typescript', str(compiler),
                                     '--expected', str(expected), '--output', str(output)],
                                    capture_output=True, text=True, timeout=60, check=False)
            self.assertEqual(result.stdout, '')
            self.assertEqual(result.stderr, '')
            self.assertEqual(before, {p.relative_to(root): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in root.rglob('*') if p.is_file()})
            return result.returncode, json.loads(output.read_text())

    @staticmethod
    def surface(symbol, signature, path='api.ts'):
        return {'path': path, 'symbol': symbol, 'signature': signature}

    def test_alias_default_type_only_and_relative_contract(self):
        code, proof = self.run_surface({
            'site-contract.ts': 'export interface Article { title: string }',
            'api.ts': 'import type { Article } from "./site-contract";\n'
                      'const list = (): readonly Article[] => []; export { list as articles };\n'
                      'export default function layout(x: string): string { return x; }\n'
                      'export type Entry = Article; export interface Config { title: string }\n'
                      'export const metadata = { title: "hello" };',
        }, [self.surface('articles', '() => readonly import("./site-contract").Article[]'),
            self.surface('default', '(x: string) => string'),
            self.surface('Entry', '{title: string}'), self.surface('Config', '{title: string}'),
            self.surface('metadata', '{title: string}'),
            self.surface('Article', '{title: string}', 'site-contract.ts')])
        self.assertEqual((code, proof['status'], proof['complete']), (0, 'pass', True), proof)
        self.assertTrue(all(e['compatible'] and e['signature'] and e['actual_signature'] for e in proof['exports']))

    def test_incompatible_parameter_and_return(self):
        code, proof = self.run_surface({'api.ts': 'export function f(x: number): number { return x; }'},
                                       [self.surface('f', '(x: string) => string')])
        self.assertEqual((code, proof['status']), (1, 'fail'), proof)
        self.assertFalse(proof['exports'][0]['compatible'])
        self.assertIsNone(proof['exports'][0]['signature'])
        self.assertTrue(any('TS2322' in e for e in proof['errors']), proof)

    def test_extra_export_in_other_owned_file(self):
        code, proof = self.run_surface({'api.ts': 'export const n = 1;', 'other.ts': 'export const extra = true;'},
                                      [self.surface('n', 'number')])
        self.assertEqual((code, proof['status'], proof['complete']), (1, 'fail', True), proof)
        self.assertIn('other.ts', proof['files'])
        self.assertTrue(any(e['symbol'] == 'extra' and not e['compatible'] for e in proof['exports']))

    def test_missing_file_and_missing_export(self):
        for files, symbol in [(['api.ts', 'missing.ts'], 'n'), (['api.ts'], 'absent')]:
            with self.subTest(files=files, symbol=symbol):
                code, proof = self.run_surface({'api.ts': 'export const n = 1;'},
                                               [self.surface(symbol, 'number')], files)
                self.assertEqual((code, proof['status']), (1, 'fail'), proof)
                self.assertTrue(any('missing' in e for e in proof['errors']))

    def test_syntax_error_fails(self):
        code, proof = self.run_surface({'api.ts': 'export const n: = ;'}, [self.surface('n', 'number')])
        self.assertEqual((code, proof['status'], proof['complete']), (1, 'fail', False), proof)
        self.assertTrue(any('TS' in e for e in proof['errors']))

    def test_any_boundaries_fail(self):
        for source, signature in [
                ('export type Bad = any;', 'string'),
                ('export const Bad: any = 1;', 'number'),
                ('export function Bad(x: any): string { return x; }', '(x: string) => string'),
                ('export function Bad(): Promise<any> { return Promise.resolve(1); }', '() => Promise<number>'),
                ('export const Bad = (): Promise<any> => Promise.resolve(1);', '() => Promise<number>'),
                ('export interface Bad { value: any }', '{ value: string }')]:
            with self.subTest(source=source):
                code, proof = self.run_surface({'api.ts': source}, [self.surface('Bad', signature)])
                self.assertEqual((code, proof['status']), (1, 'fail'), proof)
                self.assertFalse(proof['exports'][0]['compatible'])

    def test_inferred_any_in_generic_defaults_and_constraints_fails(self):
        for source, signature in [
                ('export function Bad<T = ReturnType<typeof JSON.parse>>(x?: T): T { return 1 as T; }',
                 '(x?: string) => string'),
                ('export function Bad<T extends {value: ReturnType<typeof JSON.parse>}>(): T { return {} as T; }',
                 '() => {value: string}'),
                ('export function Bad<T = ReturnType<typeof JSON.parse>>(): string { return "value"; }',
                 '() => string')]:
            with self.subTest(source=source):
                code, proof = self.run_surface({'api.ts': source}, [self.surface('Bad', signature)])
                self.assertEqual((code, proof['status']), (1, 'fail'), proof)
                self.assertFalse(proof['exports'][0]['compatible'])

    def test_project_aliases_and_no_unused_config(self):
        code, proof = self.run_surface({'api.ts': 'import type { Entry } from "@/types"; export const n: Entry = {x: 1};',
                                       'types.ts': 'export interface Entry { x: number }'},
                                      [self.surface('n', 'import("@/types").Entry'),
                                       self.surface('Entry', '{x: number}', 'types.ts')],
                                      config={'compilerOptions': {'paths': {'@/*': ['./*']},
                                              'noUnusedLocals': True}})
        self.assertEqual((code, proof['status']), (0, 'pass'), proof)

    def test_inferred_nested_any_is_rejected(self):
        for source, signature in [
                ('export const Bad = {value: JSON.parse("1")};', '{value: string}'),
                ('export const Bad = {outer: {value: JSON.parse("1")}};', '{outer: {value: string}}'),
                ('export function Bad() { return Promise.resolve(JSON.parse("1")); }', '() => Promise<string>'),
                ('export const Bad = [JSON.parse("1")];', 'string[]'),
                ('export const Bad = [JSON.parse("1")] as const;', 'readonly [string]'),
                ('export const Bad = Math.random() ? {value: JSON.parse("1")} : {count: 1};',
                 '{value: string} | {count: number}'),
                (('type Pair = {count: number} & {value: ReturnType<typeof JSON.parse>}; '
                  'export const Bad: Pair = {count: 1, value: 1};'), '{count: number; value: string}'),
                ('export function Bad(arg: {value: ReturnType<typeof JSON.parse>}) { return String(arg.value); }',
                 '(arg: {value: string}) => string'),
                (('type Box<T> = {value: T}; const value: Box<ReturnType<typeof JSON.parse>> = {value: 1}; '
                  'export {value as Bad};'), '{value: string}'),
                (('type Node = {next?: Node; value: ReturnType<typeof JSON.parse>}; '
                  'export const Bad: Node = {value: 1};'), '{next?: unknown; value: string}')]:
            with self.subTest(source=source):
                code, proof = self.run_surface({'api.ts': source}, [self.surface('Bad', signature)])
                self.assertEqual((code, proof['status']), (1, 'fail'), proof)
                self.assertFalse(proof['exports'][0]['compatible'])

    def test_recursive_authored_type_without_any_passes(self):
        code, proof = self.run_surface({'api.ts': 'export interface Node { value: string; next?: Node }'},
                                      [self.surface('Node', '{value: string; next?: unknown}')])
        self.assertEqual((code, proof['status']), (0, 'pass'), proof)

    def test_external_library_internals_are_opaque_but_arguments_checked(self):
        library = 'export interface Element { props: unknown; internal: any }\n'
        code, proof = self.run_surface({
            'node_modules/framework/index.d.ts': library,
            'api.ts': 'import type { Element } from "framework"; '
                      'export function layout(): Element { return {props: null, internal: null}; }',
        }, [self.surface('layout', '() => import("framework").Element')], files=['api.ts'])
        self.assertEqual((code, proof['status']), (0, 'pass'), proof)
        code, proof = self.run_surface({
            'node_modules/framework/index.d.ts': 'export interface Box<T> { value: T; internal: any }',
            'api.ts': 'import type { Box } from "framework"; '
                      'const value: Box<ReturnType<typeof JSON.parse>> = {value: 1, internal: 1}; '
                      'export {value as Bad};',
        }, [self.surface('Bad', 'import("framework").Box<string>')], files=['api.ts'])
        self.assertEqual((code, proof['status']), (1, 'fail'), proof)

    def test_reexported_library_type_is_opaque(self):
        code, proof = self.run_surface({
            'node_modules/framework/index.d.ts': 'export interface Element { internal: any }',
            'api.ts': 'export type { Element } from "framework";',
        }, [self.surface('Element', 'import("framework").Element')], files=['api.ts'])
        self.assertEqual((code, proof['status']), (0, 'pass'), proof)

    def test_external_generic_default_does_not_hide_direct_any(self):
        code, proof = self.run_surface({
            'node_modules/framework/index.d.ts': 'export interface Box<T = any> { value: T }',
            'api.ts': 'import type { Box } from "framework"; '
                      'const value: Box<ReturnType<typeof JSON.parse>> = {value: 1}; '
                      'export {value as Bad};',
        }, [self.surface('Bad', 'import("framework").Box<string>')], files=['api.ts'])
        self.assertEqual((code, proof['status']), (1, 'fail'), proof)

    def test_composite_library_default_cannot_prove_narrower_argument(self):
        code, proof = self.run_surface({
            'node_modules/framework/index.d.ts': 'export interface Box<T = any[]> { value: T }',
            'api.ts': 'import type { Box } from "framework"; export const Bad: Box = {value: []};',
        }, [self.surface('Bad', 'import("framework").Box<string[]>')], files=['api.ts'])
        self.assertEqual((code, proof['status']), (1, 'fail'), proof)

    def test_matching_composite_library_default_is_opaque(self):
        code, proof = self.run_surface({
            'node_modules/framework/index.d.ts':
                'type Constructor<P> = (props: P) => unknown; '
                'export interface Element<T = string | Constructor<any>> { type: T; internal: any }',
            'api.ts': 'import type { Element } from "framework"; '
                      'export function layout(): Element { return {type: "div", internal: null}; }',
        }, [self.surface('layout', '() => import("framework").Element')], files=['api.ts'])
        self.assertEqual((code, proof['status']), (0, 'pass'), proof)

    def test_opaque_default_permission_stays_at_matching_property(self):
        code, proof = self.run_surface({
            'node_modules/framework/index.d.ts': 'export interface Box<T = any[]> { value: T }',
            'api.ts': 'import type { Box } from "framework"; const box: Box = {value: []}; '
                      'export const Bad = {wide: box, narrow: box};',
        }, [self.surface('Bad', '{wide: import("framework").Box; narrow: import("framework").Box<string[]>}')],
           files=['api.ts'])
        self.assertEqual((code, proof['status']), (1, 'fail'), proof)

    def test_exhausted_type_walk_is_unsupported(self):
        nested = '{next:' * 120 + 'string' + '}' * 120
        code, proof = self.run_surface({'api.ts': 'export type Deep = ' + nested},
                                      [self.surface('Deep', 'unknown')])
        self.assertEqual((code, proof['status'], proof['complete']), (2, 'unsupported', False), proof)

    def test_invalid_signature_cannot_inject_statements(self):
        code, proof = self.run_surface({'api.ts': 'export const n = 1;'},
                                      [self.surface('n', 'number; const escape = 1')])
        self.assertEqual((code, proof['status']), (2, 'unsupported'), proof)

    def test_type_error_in_relative_signature_fails(self):
        code, proof = self.run_surface({'api.ts': 'export const n = 1;'},
                                      [self.surface('n', 'import("./missing").Entry')])
        self.assertEqual((code, proof['status']), (1, 'fail'), proof)
        self.assertFalse(proof['exports'][0]['compatible'])

    def test_candidate_code_and_tsconfig_plugins_are_not_executed(self):
        code, proof = self.run_surface({'api.ts': 'throw new Error("candidate executed"); export const n = 1;'},
                                      [self.surface('n', 'number')],
                                      config={'compilerOptions': {'plugins': [{'name': './not-a-real-plugin'}]}})
        self.assertEqual((code, proof['status']), (0, 'pass'), proof)

    def test_missing_compiler_is_unsupported_with_proof(self):
        code, proof = self.run_surface({'api.ts': 'export const n = 1;'}, [self.surface('n', 'number')],
                                      compiler=Path('/missing/compiler/typescript.js'))
        self.assertEqual((code, proof['status'], proof['complete']), (2, 'unsupported', False), proof)

    def test_export_equals_is_explicitly_unsupported(self):
        code, proof = self.run_surface({'api.ts': 'const n = 1; export = n;'}, [])
        self.assertEqual((code, proof['status'], proof['complete']), (2, 'unsupported', False), proof)


if __name__ == '__main__':
    unittest.main()

"""Run: python3 -m unittest discover -s evals -p test_context_adapter.py"""
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import benchmark
import context_adapter


class AdapterTests(unittest.TestCase):
    def fixture(self, root):
        source = root / "source"
        (source / ".claude-plugin").mkdir(parents=True)
        (source / "hooks").mkdir()
        (source / ".git").mkdir()
        (source / ".git/config").write_text("source git metadata")
        manifest = {"name": "context-mode", "version": "1.0.169", "mcpServers": {"context-mode": {
            "command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/start.mjs"]}}}
        hooks = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command":
                                                    'node "${CLAUDE_PLUGIN_ROOT}/start.mjs"'}]}]}}
        (source / ".claude-plugin/plugin.json").write_text(json.dumps(manifest))
        (source / "hooks/hooks.json").write_text(json.dumps(hooks))
        (source / "package.json").write_text('{"dependencies":{}}')
        (source / "start.mjs").write_text('console.log(JSON.stringify({config:process.env.CLAUDE_CONFIG_DIR,'
                                         'data:process.env.CONTEXT_MODE_DIR,work:process.env.CONTEXT_MODE_PROJECT_DIR}));')
        (source / "server.bundle.mjs").write_text(
            'var Rj=(()=>{let name="DARWIN_USER_TEMP_DIR";return"/tmp"})();'
            'function run(){return join(Rj,".ctx-mode-")};'
            'let e=process.platform==="win32"?$g():"/tmp",n=join(e,`context-mode-mcp-ready-${process.pid}`);')
        (source / "hooks/core").mkdir()
        (source / "hooks/core/mcp-ready.mjs").write_text(
            'function sentinelDir(){return process.platform === "win32" ? tmpdir() : "/tmp";}')
        work = root / "work"
        work.mkdir()
        return source, root / "plugin with spaces", work

    def test_unsupported_platform_fails_before_copy(self):
        with patch.object(context_adapter.platform, "system", return_value="Linux"), \
                self.assertRaisesRegex(ValueError, "macOS"):
            context_adapter.prepare("missing", "missing", "missing", [])

    @unittest.skipUnless(platform.system() == "Darwin" and shutil.which("node"), "requires macOS/node")
    def test_missing_dependencies_fail_before_copy_or_initialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination, work = self.fixture(Path(tmp))
            (source / "package.json").write_text('{"dependencies":{"factory-missing-package":"1"}}')
            with self.assertRaisesRegex(ValueError, "dependencies are not ready"):
                context_adapter.prepare(source, destination, work, [])
            self.assertFalse(destination.exists())

    @unittest.skipUnless(platform.system() == "Darwin" and shutil.which("node"), "requires macOS/node")
    def test_browser_runtime_is_required_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"PLAYWRIGHT_MODULE": ""}):
            source, destination, work = self.fixture(Path(tmp))
            with self.assertRaisesRegex(ValueError, "PLAYWRIGHT_MODULE"):
                context_adapter.prepare(source, destination, work, [], browser=True)
            self.assertFalse(destination.exists())

    @unittest.skipUnless(platform.system() == "Darwin" and os.environ.get("PLAYWRIGHT_MODULE"),
                         "requires macOS and installed PLAYWRIGHT_MODULE")
    def test_browser_loopback_and_external_network_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, destination, work = self.fixture(Path(tmp).resolve())
            plugin, provenance = context_adapter.prepare(source, destination, work, [], browser=True)
            server = json.loads((plugin / ".claude-plugin/plugin.json").read_text())["mcpServers"]["context-mode"]
            self.assertEqual(server["env"]["PLAYWRIGHT_MODULE"], os.environ["PLAYWRIGHT_MODULE"])
            script = """
const assert=require('assert'),fs=require('fs'),http=require('http'),net=require('net');
(async()=>{
  const server=http.createServer((req,res)=>res.end('<h1>Loopback dashboard</h1>'));
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await require(process.env.PLAYWRIGHT_MODULE).chromium.launch({headless:true});
  try {
    const page=await browser.newPage();
    await page.goto('http://127.0.0.1:'+server.address().port);
    assert.equal(await page.locator('h1').textContent(),'Loopback dashboard');
    assert.throws(()=>fs.readdirSync(require('os').homedir()),e=>['EPERM','EACCES'].includes(e.code));
    await new Promise((resolve,reject)=>{
      const socket=net.connect({host:'192.0.2.1',port:80});
      socket.setTimeout(3000,()=>{socket.destroy();reject(new Error('External network was not denied'))});
      socket.on('connect',()=>{socket.destroy();reject(new Error('External network connected'))});
      socket.on('error',e=>['EPERM','EACCES'].includes(e.code)?resolve():reject(e));
    });
    console.log('BROWSER_LOOPBACK_ISOLATED');
  } finally {await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exit(1)});
"""
            result = subprocess.run([server["command"], "-f", provenance["sandbox_profile"], provenance["node"],
                                     "-e", script], env={**os.environ, **server["env"]}, cwd=work,
                                    check=False, capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("BROWSER_LOOPBACK_ISOLATED", result.stdout)

    @unittest.skipUnless(platform.system() == "Darwin" and shutil.which("sandbox-exec") and shutil.which("node"),
                         "requires macOS sandbox-exec/node")
    def test_policy_and_report_secrets_outside_home_are_denied(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as policy_tmp:
            root = Path(tmp).resolve()
            source, destination, work = self.fixture(root)
            policy = Path(policy_tmp).resolve() / "owner-policy.json"
            policy.write_text("OWNER_SECRET")
            args = benchmark.argparse.Namespace(operator_policy=str(policy), out=Path(policy_tmp).resolve() / "out")
            args.out.mkdir()
            secrets = benchmark.secret_files(args.out, benchmark.policy_files(args))
            for secret in secrets:
                secret.write_text("OWNER_SECRET")
                self.assertFalse(secret.is_relative_to(Path.home()))
            _, provenance = context_adapter.prepare(source, destination, work, secrets)
            for secret in secrets:
                with self.subTest(secret=secret.name):
                    result = subprocess.run([shutil.which("sandbox-exec"), "-f", provenance["sandbox_profile"], "/bin/cat", str(secret)],
                                            capture_output=True, text=True, check=False)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("OWNER_SECRET", result.stdout)

    @unittest.skipUnless(platform.system() == "Darwin" and shutil.which("sandbox-exec") and shutil.which("node"),
                         "requires macOS sandbox-exec/node")
    def test_child_env_source_preservation_and_os_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            source, destination, work = self.fixture(root)
            protected = root / "cases"
            protected.mkdir()
            secret = protected / "answer"
            secret.write_text("hidden")
            before = {str(p.relative_to(source)): p.read_bytes() for p in source.rglob("*") if p.is_file()}
            parent_config = os.environ.get("CLAUDE_CONFIG_DIR")
            plugin, provenance = context_adapter.prepare(source, destination, work, [protected])
            self.assertEqual(plugin, destination)
            self.assertEqual(provenance["temporary_path_adaptations"], ["server.bundle.mjs", "hooks/core/mcp-ready.mjs"])
            self.assertNotIn("DARWIN_USER_TEMP_DIR", (plugin / "server.bundle.mjs").read_text())
            self.assertFalse((plugin / ".git").exists())
            self.assertEqual(before, {str(p.relative_to(source)): p.read_bytes()
                                      for p in source.rglob("*") if p.is_file()})
            self.assertEqual(os.environ.get("CLAUDE_CONFIG_DIR"), parent_config)
            manifest = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
            server = manifest["mcpServers"]["context-mode"]
            env = {**os.environ, **server["env"], "CLAUDE_PLUGIN_ROOT": str(plugin)}
            cmd = [server["command"], *(a.replace("${CLAUDE_PLUGIN_ROOT}", str(plugin)) for a in server["args"])]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True, env=env, cwd=work)
            self.assertEqual(result.returncode, 0, "Native sandbox probe failed: " + result.stderr)
            child = json.loads(result.stdout)
            self.assertEqual(child["config"], provenance["shadow_config"])
            self.assertEqual(child["data"], provenance["shadow_data"])
            self.assertEqual(child["work"], str(work))
            hook = json.loads((plugin / "hooks/hooks.json").read_text())["hooks"]["SessionStart"][0]["hooks"][0]
            result = subprocess.run(["/bin/sh", "-c", hook["command"]], check=False, capture_output=True, text=True,
                                    env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(plugin)}, cwd=work)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), child)
            sandbox = [server["command"], "-f", provenance["sandbox_profile"]]
            node = provenance["node"]
            script = "const fs=require('fs');fs.writeFileSync(process.argv[1],'ok')"
            inside = subprocess.run([*sandbox, node, "-e", script, str(work / "inside")], check=False, capture_output=True)
            self.assertEqual(inside.returncode, 0, inside.stderr)
            python = subprocess.run([*sandbox, sys.executable, "-c", "print('PYTHON_READY')"],
                                    check=False, capture_output=True)
            self.assertEqual(python.returncode, 0, python.stderr)
            self.assertIn(b"PYTHON_READY", python.stdout)
            outside = subprocess.run([*sandbox, "/bin/bash", "-c", 'echo forbidden > "$1"', "probe", str(root / "outside")],
                                     check=False, capture_output=True)
            self.assertNotEqual(outside.returncode, 0)
            self.assertFalse((root / "outside").exists())
            policy_write = subprocess.run([*sandbox, node, "-e", script, provenance["sandbox_profile"]],
                                          check=False, capture_output=True)
            self.assertNotEqual(policy_write.returncode, 0)
            self.assertTrue(Path(provenance["sandbox_profile"]).read_text().startswith("(version 1)"))
            read = subprocess.run([*sandbox, "/bin/cat", str(secret)], check=False, capture_output=True)
            self.assertNotEqual(read.returncode, 0)
            self.assertNotIn(b"hidden", read.stdout)
            home = subprocess.run([*sandbox, "/bin/ls", str(Path.home())], check=False, capture_output=True)
            self.assertNotEqual(home.returncode, 0)
            network = subprocess.run([*sandbox, node, "-e", ("try{require('net').createServer().listen(0)}"
                                      "catch(e){process.exit(2)}")], check=False, capture_output=True, timeout=10)
            self.assertNotEqual(network.returncode, 0, network.stderr)


if __name__ == "__main__":
    unittest.main()

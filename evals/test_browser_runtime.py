"""Native fixed browser-check wrapper verification."""
import json
import os
import platform
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from browser_runtime import prepare_browser_check


class BrowserRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(platform.system() == "Darwin", "requires macOS")
    def test_missing_runtime_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"PLAYWRIGHT_MODULE": ""}):
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            with self.assertRaisesRegex(ValueError, "PLAYWRIGHT_MODULE"):
                prepare_browser_check(root / "runtime", work, [])
            self.assertFalse((root / "runtime").exists())

    @unittest.skipUnless(platform.system() == "Darwin" and os.environ.get("PLAYWRIGHT_MODULE"),
                         "requires macOS and installed Playwright")
    def test_red_browser_clone_preserves_live_green_and_dirty_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            work = root / "work"
            work.mkdir()
            def git(*args):
                return subprocess.check_output(["git", "-C", str(work), *args], text=True).strip()
            git("init", "-q")
            git("config", "user.name", "Browser test")
            git("config", "user.email", "browser@example.invalid")
            (work / ".gitignore").write_text(".tmp/\nnode_modules/\n")
            change = work / ".software-factory/changes/demo"
            change.mkdir(parents=True)
            (change / "status.yaml").write_text("feature: demo\n")
            dependency = work / "node_modules/fixture-dependency"
            dependency.mkdir(parents=True)
            (dependency / "index.js").write_text("module.exports = 'ancestor dependency';")
            (work / "index.html").write_text("<h1>RED</h1>")
            (work / "test-browser.cjs").write_text("""
const test=require('node:test'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url'),path=require('node:path');
test('actual browser sees GREEN',async()=>{
 assert.equal(require('fixture-dependency'),'ancestor dependency');
 const browser=await require(process.env.PLAYWRIGHT_MODULE).chromium.launch({headless:true});
 try {const page=await browser.newPage();await page.goto(pathToFileURL(path.resolve('index.html')).href);
 assert.equal(await page.locator('h1').textContent(),'GREEN');}finally{await browser.close();}
});
""")
            git("add", ".")
            git("-c", "commit.gpgsign=false", "commit", "-qm", "RED")
            red = git("rev-parse", "HEAD")
            (work / "index.html").write_text("<h1>GREEN</h1>")
            git("add", ".")
            git("-c", "commit.gpgsign=false", "commit", "-qm", "GREEN")
            head = git("rev-parse", "HEAD")
            (work / "index.html").write_text("<h1>GREEN</h1><!-- pending edit -->")
            (work / "untracked.txt").write_text("preserve me")
            before = git("status", "--porcelain")
            runtime = prepare_browser_check(root / "runtime", work, [])
            request = work / ".software-factory/browser-red.json"
            request.write_text(json.dumps({"commit": red, "checkpoint": "slice-01"}))
            rejected = subprocess.run([runtime["red_command"], "extra"], check=False, capture_output=True)
            self.assertEqual(rejected.returncode, 64)
            result = subprocess.run([runtime["red_command"]], check=False, capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("# fail 1", result.stdout, result.stderr)
            records = list((work / ".software-factory/browser-red-evidence").glob("slice-01-*.json"))
            self.assertEqual(len(records), 1)
            record = json.loads(records[0].read_text())
            self.assertEqual(record["test_commit"], red)
            self.assertEqual(record["exit_code"], 1)
            self.assertEqual(record["deliverable_head"], head)
            self.assertTrue(Path(record["raw_log"]).is_file())
            self.assertEqual(git("rev-parse", "HEAD"), head)
            self.assertEqual(git("status", "--porcelain"), before)
            self.assertEqual((work / "index.html").read_text(), "<h1>GREEN</h1><!-- pending edit -->")
            self.assertEqual((work / "untracked.txt").read_text(), "preserve me")
            green = subprocess.run([runtime["command"]], check=False, capture_output=True, text=True, timeout=45)
            self.assertEqual(green.returncode, 0, green.stdout + green.stderr)
            request.write_text(json.dumps({"commit": "HEAD;touch outside", "checkpoint": "../escape"}))
            invalid = subprocess.run([runtime["red_command"]], check=False, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(len(list((work / ".software-factory/browser-red-evidence").glob("*.json"))), 1)

    @unittest.skipUnless(platform.system() == "Darwin" and os.environ.get("PLAYWRIGHT_MODULE"),
                         "requires macOS and installed Playwright")
    def test_loud_failure_is_bounded_and_raw_log_keeps_real_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            work = root / "work"
            work.mkdir()
            runtime = prepare_browser_check(root / "runtime", work, [])
            (work / "test-loud.cjs").write_text("""
const test=require('node:test'),assert=require('node:assert/strict');
test('important failure',()=>{
  console.log('NOISE-BEGIN'+'x'.repeat(100000)+'NOISE-END');
  console.error('STDERR-COMPLETE-MARKER');
  assert.fail('IMPORTANT-PERSISTENCE-FAILURE');
});
""")
            result = subprocess.run([runtime["command"]], check=False, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertLess(len(result.stdout), 9000)
            self.assertIn("IMPORTANT-PERSISTENCE-FAILURE", result.stdout)
            self.assertIn("# fail 1", result.stdout, result.stderr)
            self.assertIn("exit: 1", result.stdout)
            logs = list((work / ".tmp/browser-check").glob("check-*.log"))
            self.assertEqual(len(logs), 1)
            raw = logs[0].read_text()
            self.assertGreaterEqual(raw.count('x'), 100000)
            self.assertIn('NOISE-BEGIN', raw)
            self.assertIn('NOISE-END', raw)
            self.assertIn('STDERR-COMPLETE-MARKER', raw)
            self.assertIn(str(logs[0]), result.stdout)
            subprocess.run([runtime["command"]], check=False, capture_output=True, timeout=30)
            self.assertEqual(len(list((work / ".tmp/browser-check").glob("check-*.log"))), 2)

    @unittest.skipUnless(platform.system() == "Darwin" and os.environ.get("PLAYWRIGHT_MODULE"),
                         "requires macOS and installed Playwright")
    def test_fixed_wrapper_browser_and_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            work = root / "work with spaces"
            work.mkdir()
            protected = root / "cases"
            protected.mkdir()
            (protected / "answer").write_text("secret")
            runtime = prepare_browser_check(root / "runtime with spaces", work, [protected])
            denied = [str(root / "outside"), runtime["profile"], runtime["command"], runtime["helper"], runtime["red_helper"], runtime["red_command"]]
            code = """
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const http=require('node:http'),net=require('node:net');
test('public smoke and isolated browser check',async()=>{
  const server=http.createServer((req,res)=>res.end('<h1>Shared browser capability</h1>'));
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await require(process.env.PLAYWRIGHT_MODULE).chromium.launch({headless:true});
  try {
    const page=await browser.newPage();
    await page.goto('http://127.0.0.1:'+server.address().port);
    assert.equal(await page.locator('h1').textContent(),'Shared browser capability');
    await page.screenshot({path:'screenshot.png'});
    for(const path of DENIED)assert.throws(()=>fs.writeFileSync(path,'bad'),e=>['EPERM','EACCES'].includes(e.code));
    assert.throws(()=>fs.readFileSync(PROTECTED),e=>['EPERM','EACCES'].includes(e.code));
    assert.throws(()=>fs.readdirSync(require('os').homedir()),e=>['EPERM','EACCES'].includes(e.code));
    await new Promise((resolve,reject)=>{
      const socket=net.connect({host:'192.0.2.1',port:80});
      socket.setTimeout(3000,()=>{socket.destroy();reject(new Error('External network was not denied'))});
      socket.on('connect',()=>{socket.destroy();reject(new Error('External network connected'))});
      socket.on('error',e=>['EPERM','EACCES'].includes(e.code)?resolve():reject(e));
    });
  } finally {await browser.close();server.close();}
});
""".replace("DENIED", json.dumps(denied)).replace("PROTECTED", json.dumps(str(protected / "answer")))
            (work / "test-public.cjs").write_text(code)
            rejected = subprocess.run([runtime["command"], "arbitrary"], check=False, capture_output=True)
            self.assertEqual(rejected.returncode, 64)
            result = subprocess.run([runtime["command"]], check=False, capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("# pass 1", result.stdout)
            self.assertTrue((work / "screenshot.png").is_file())
            self.assertFalse((root / "outside").exists())
            hostile = subprocess.run(["/bin/bash", "-c",
                ('cd(){ /usr/bin/touch "$CANARY"; }; exec(){ /usr/bin/touch "$CANARY"; }; '
                 'export -f cd exec; "$WRAPPER"')],
                env={**os.environ, "CANARY": str(root / "outside"), "WRAPPER": runtime["command"]},
                check=False, capture_output=True, text=True, timeout=45)
            self.assertEqual(hostile.returncode, 0, hostile.stdout + hostile.stderr)
            self.assertFalse((root / "outside").exists())


if __name__ == "__main__":
    unittest.main()

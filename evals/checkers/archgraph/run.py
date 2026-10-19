"""Prove native import-boundary enforcement; no language packages are installed."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PIN = "49464a7ec19fe8402b4258e751f7ba050c6eff19"
INSTALL = (
    f"cargo install --git https://github.com/dogebonker/archgraph --rev {PIN} --locked"
)
HERE = Path(__file__).resolve().parent


def main():
    binary = os.environ.get("ARCHGRAPH_BIN") or shutil.which("archgraph")
    if not binary:
        print(f"archgraph: SKIP binary absent; install: {INSTALL}")
        return 0 if os.environ.get("LAY01_ALLOW_SKIP") == "1" else 2
    binary = Path(binary).resolve()
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    expected = os.environ.get("ARCHGRAPH_SHA256")
    if expected:
        if expected != digest:
            raise ValueError("ARCHGRAPH_SHA256 does not match the supplied binary")
        provenance = (
            "caller-supplied binary SHA-256; verify its pinned build separately"
        )
    else:
        receipt = (
            Path(os.environ.get("CARGO_HOME", Path.home() / ".cargo")) / ".crates2.json"
        )
        installs = (
            json.loads(receipt.read_text()).get("installs", {})
            if receipt.exists()
            else {}
        )
        matches = [
            key
            for key, value in installs.items()
            if f"git+https://github.com/dogebonker/archgraph?rev={PIN}#{PIN}" in key
            and "archgraph" in value.get("bins", [])
        ]
        cargo_bin = receipt.parent / "bin" / "archgraph"
        if len(matches) != 1 or not cargo_bin.exists() or cargo_bin.resolve() != binary:
            print(f"archgraph: SKIP unverified installation; install: {INSTALL}")
            print(
                "For a separately verified build, set ARCHGRAPH_BIN and ARCHGRAPH_SHA256."
            )
            return 0 if os.environ.get("LAY01_ALLOW_SKIP") == "1" else 2
        provenance = matches[0]
    tools = (HERE.parents[2] / "kit/layouts/tools.yaml").read_text()
    if tools.count(INSTALL) != 3:
        raise ValueError("all three tools.yaml entries must carry the source pin")
    command = ("command: archgraph scan . --engine native --symbols --rules layout.yaml "
               "-o <tmp>/archgraph-head.json && archgraph check <tmp>/archgraph-head.json")
    if tools.count(command) != 3:
        raise ValueError("all three registry commands must match the tested scan/check recipe")
    work = Path(tempfile.mkdtemp(prefix="lay01-archgraph-"))
    evidence = {
        "source_pin": PIN,
        "binary_sha256": digest,
        "provenance": provenance,
        "stacks": {},
    }
    print(f"archgraph logs: {work}", flush=True)
    failed = False
    for stack in ("typescript", "python", "go"):
        log = work / stack
        tree = log / "tree"
        shutil.copytree(HERE / stack / "fixture", tree)
        states = {}
        try:
            for state in ("clean", "planted"):
                if state == "planted":
                    shutil.copytree(HERE / stack / "planted", tree, dirs_exist_ok=True)
                graph = log / f"{state}.json"
                args = [
                    str(binary),
                    "scan",
                    ".",
                    "--engine",
                    "native",
                    "--language",
                    stack,
                    "--symbols",
                    "--rules",
                    "layout.yaml",
                    "-o",
                    str(graph),
                ]
                with (log / f"{state}-scan.log").open("w") as out:
                    subprocess.run(
                        args,
                        cwd=tree,
                        stdout=out,
                        stderr=subprocess.STDOUT,
                        check=True,
                        timeout=120,
                    )
                result = subprocess.run(
                    [str(binary), "check", str(graph)],
                    cwd=tree,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                (log / f"{state}-check.log").write_text(result.stdout + result.stderr)
                states[state] = {"exit": result.returncode, "output": result.stdout}
            planted = [
                str(p.relative_to(HERE / stack / "planted"))
                for p in (HERE / stack / "planted").rglob("*")
                if p.is_file()
            ]
            ok = (
                states["clean"]["exit"] == 0
                and states["planted"]["exit"] == 1
                and "domain-not-to-adapters" not in states["clean"]["output"]
                and "domain-not-to-adapters" in states["planted"]["output"]
                and all(path in states["planted"]["output"] for path in planted)
            )
            evidence["stacks"][stack] = {"passed": ok, "states": states}
            failed |= not ok
            print(
                f"archgraph/{stack}: {'ok' if ok else 'FAIL'} clean={states['clean']['exit']} planted={states['planted']['exit']}",
                flush=True,
            )
        finally:
            shutil.rmtree(tree)
    (work / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())

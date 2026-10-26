"""History-free real-PR fixtures and held-out test admission (stdlib only).

The controller must keep reference exports outside the actor's readable sandbox.
These helpers prepare files; they do not establish an OS security boundary.
"""

import hashlib
import io
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath

INSTRUCTION_FILES = {"CLAUDE.md", "AGENTS.md"}
PRIVATE_DIRS = {".git", ".claude", ".codex", ".agents", ".plumb", ".software-factory", ".factory", ".omx"}
SETUP_ERRORS = re.compile(
    r"ModuleNotFoundError|ImportError:|Cannot find module|ERR_MODULE_NOT_FOUND|"
    r"command not found|No such file or directory|SyntaxError:|IndentationError:|"
    r"fixture '.+' not found|no tests ran|no tests collected|collected 0 items|"
    r"Failed to collect|ERROR collecting|Test suite failed to run|"
    r"FAIL\s+\S+\s+\[setup failed\]|\[build failed\]|setup failed|"
    r"No test files found|Ran 0 tests|Tests:\s+0 total",
    re.IGNORECASE,
)


def _relative(value):
    if not isinstance(value, str) or not value or any(char in value for char in "\\\x00*?[]"):
        raise ValueError(f"unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"unsafe relative path: {value!r}")
    if ".git" in path.parts:
        raise ValueError("repository history must not be exported")
    return path


def _inside(root, target):
    try:
        target.resolve().relative_to(root.resolve())
    except (ValueError, RuntimeError) as error:
        raise ValueError(f"path escapes export: {target}") from error


def _extract(archive, destination, strip_instructions):
    """Extract validated files first and symlinks last; never follow archive links."""
    root = Path(destination)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as source:
        entries = []
        seen = set()
        for member in source.getmembers():
            name = member.name.rstrip("/")
            path = _relative(name)
            if name in seen:
                raise ValueError(f"duplicate archive path: {name}")
            seen.add(name)
            if not (member.isdir() or member.isfile() or member.issym()):
                raise ValueError(f"unsupported archive entry: {name}")
            if strip_instructions and (set(path.parts) & PRIVATE_DIRS or path.name in INSTRUCTION_FILES):
                continue
            if member.issym():
                if not member.linkname or Path(member.linkname).is_absolute():
                    raise ValueError(f"unsafe symlink: {name}")
                _inside(root, root / str(path.parent) / member.linkname)
            entries.append((member, path))
        links = {str(path) for member, path in entries if member.issym()}
        for _, path in entries:
            if any(str(parent) in links for parent in path.parents):
                raise ValueError(f"archive entry traverses a symlink: {path}")
        for member, path in entries:
            target = root / str(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            if member.isdir():
                target.mkdir(exist_ok=True)
            elif member.isfile():
                with source.extractfile(member) as stream, target.open("wb") as output:
                    shutil.copyfileobj(stream, output)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
        for member, path in entries:
            if member.issym():
                (root / str(path)).symlink_to(member.linkname)
        for _, path in entries:
            _inside(root, root / str(path))


def export_commit(repo, commit, destination, strip_instructions=False, subdir=None):
    """Export an immutable commit to a NEW path with synthetic, local-only Git history."""
    repo, destination = Path(repo).resolve(), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"export destination already exists: {destination}")
    resolved = destination.resolve()
    if resolved == repo or repo in resolved.parents or resolved in repo.parents:
        raise ValueError("export must be separate from the source repository")
    revision = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", f"{commit}^{{commit}}"],
                              capture_output=True, text=True, check=True).stdout.strip()
    archive_revision = revision
    if subdir is not None:
        archive_revision = f"{revision}:{_relative(subdir)}"
        kind = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", archive_revision],
                              capture_output=True, text=True, check=False)
        if kind.returncode or kind.stdout.strip() != "tree":
            raise ValueError("source_subdir must name an exact committed tree, not a file or symlink")
    archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", archive_revision],
                             capture_output=True, check=True).stdout
    destination.mkdir(parents=True)
    try:
        _extract(archive, destination, strip_instructions)
        _init_git(destination)
    except Exception:
        shutil.rmtree(destination)
        raise
    return destination


def _init_git(root):
    # An empty template prevents machine-global Git hooks/config from entering fixtures.
    subprocess.run(["git", "init", "--quiet", "--template=", str(root)], check=True, capture_output=True)
    for key, value in (("user.name", "Benchmark"), ("user.email", "benchmark@example.invalid"),
                       ("commit.gpgsign", "false"), ("tag.gpgsign", "false"), ("core.hooksPath", "/dev/null")):
        subprocess.run(["git", "-C", str(root), "config", "--local", key, value], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "add", "--all"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "commit", "--quiet", "--allow-empty", "-m", "Baseline"],
                   check=True, capture_output=True)


def acceptance_paths(case):
    """Admit exact test paths only; never transplant reference production code."""
    paths = case.get("acceptance_files", [])
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        raise ValueError("acceptance_files must be a nonempty list of unique exact test files")
    result = []
    for value in paths:
        path = _relative(value)
        test_name = re.search(r"(^test_.+\.py$|^.+_test\.go$|[._](test|spec)\.[cm]?[jt]sx?$|^.+Tests?\.py$)", path.name)
        if set(path.parts) & PRIVATE_DIRS or path.name in INSTRUCTION_FILES or not test_name:
            raise ValueError(f"acceptance file must be a test, not production source: {value}")
        result.append(Path(str(path)))
    return result


def is_test_support(value):
    path = _relative(value)
    directories = path.parts[:-1]
    test_dirs = {"test", "tests", "__tests__"}
    support_dirs = {"fixtures", "fixture", "helpers", "helper", "support", "testhelpers", "testutils"}
    return (path.suffix in {".json", ".ts", ".tsx", ".js", ".cjs", ".mjs"}
            and any(part in test_dirs and set(directories[index + 1:]) & support_dirs
                    for index, part in enumerate(directories)))


def support_paths(case):
    """Only test-local fixtures/helpers may accompany held-out executable tests."""
    values = case.get("acceptance_support_files", [])
    if not isinstance(values, list) or len(values) != len(set(values)):
        raise ValueError("acceptance_support_files must be a unique list of exact test-support paths")
    result = []
    for value in values:
        path = _relative(value)
        if (not is_test_support(value) or set(path.parts) & PRIVATE_DIRS
                or Path(str(path)) in acceptance_paths(case)):
            raise ValueError(f"held-out support must be a test-local fixture/helper, not production: {value}")
        result.append(Path(str(path)))
    return result


def _missing_module_reports(output):
    return list(re.finditer(r"Cannot find module ['\"]([^'\"\n]+)['\"] (?:from|imported from) ['\"]?([^'\"\n]+)['\"]?(?=\n|$)", output))


def _reported_test(case, reported):
    reported = reported.replace("\\", "/")
    matches = [path for path in case["acceptance_files"] if path == reported
               or reported.endswith("/" + path) or path.endswith("/" + reported)]
    return matches[0] if len(matches) == 1 else None


def _module_aliases(reference, baseline, source_path):
    """Support only simple committed tsconfig wildcard aliases shared with BASE."""
    configurations = []
    for root in (reference, baseline):
        config = Path(root) / "tsconfig.json"
        if config.is_symlink() or not config.is_file():
            return []
        text = config.read_text()
        base = re.search(r'"baseUrl"\s*:\s*"([^"\n]+)"', text)
        base = base[1] if base else "."
        aliases = set()
        # Deliberately bounded to the common single-wildcard, first-target mapping.
        for alias, target in re.findall(r'"([^"\n]+/\*)"\s*:\s*\[\s*"([^"\n]+/\*)"', text):
            mapped = Path(root) / base / target[:-1]
            _inside(Path(root), mapped)
            try:
                suffix = (Path(root) / source_path).relative_to(mapped)
            except ValueError:
                continue
            if suffix.suffix in {".ts", ".tsx", ".js"}:
                aliases.add(alias[:-1] + suffix.with_suffix("").as_posix())
        configurations.append(aliases)
    return sorted(configurations[0] & configurations[1])


def _expected_feature_failure(case, reference, baseline=None):
    declaration = case.get("expected_feature_failure")
    if declaration is None:
        return None
    if not isinstance(declaration, dict):
        raise TypeError("expected_feature_failure needs pattern, symbol, reference_file")
    symbol, pattern = declaration.get("symbol", ""), declaration.get("pattern", "")
    if (not isinstance(symbol, str) or not re.fullmatch(r"[A-Za-z_]\w{2,}", symbol)
            or not isinstance(pattern, str) or (not declaration.get("missing_module") and re.escape(symbol) not in pattern)):
        raise ValueError("expected failure regex must include a literal known feature symbol")
    source = Path(reference) / str(_relative(declaration.get("reference_file")))
    _inside(Path(reference), source)
    if source.is_symlink() or not source.is_file() or not re.search(r"\b" + re.escape(symbol) + r"\b", source.read_text()):
        raise ValueError("expected feature symbol must exist in a reference source file")
    if source.relative_to(reference) in acceptance_paths(case) + support_paths(case):
        raise ValueError("expected feature symbol must belong to production, not held-out tests")
    if declaration.get("missing_module"):
        module, importer = declaration["missing_module"], declaration.get("importing_test")
        source_path = source.relative_to(reference)
        if (set(source_path.parts) & PRIVATE_DIRS
                or re.search(r"(?:^|[/_.-])(?:tests?|testdata|mocks?|fixtures?|testhelpers?|testutils?)(?:[/_.-]|$)", source_path.as_posix(), re.IGNORECASE)):
            raise ValueError("missing feature module must be production source")
        if not isinstance(module, str) or not module.startswith(("./", "../")) or "\\" in module or "\x00" in module:
            raise ValueError("only an explicit local relative module can be a missing feature")
        importer = Path(str(_relative(importer)))
        if importer not in acceptance_paths(case) or baseline is None:
            raise ValueError("missing feature importer must be a held-out test with a baseline export")
        imported_from = Path(reference) / importer
        _inside(Path(reference), imported_from)
        if (imported_from.is_symlink() or not imported_from.is_file()
                or any((Path(reference) / parent).is_symlink() for parent in importer.parents)):
            raise ValueError("missing feature importer must be a regular reference test")
        if any((Path(reference) / parent).is_symlink() for parent in source.relative_to(reference).parents):
            raise ValueError("missing feature module must not traverse symlinks")
        target = imported_from.parent / module
        _inside(Path(reference), target)
        candidates = [target, *(Path(str(target) + suffix) for suffix in (".ts", ".tsx", ".js")),
                      *(target / ("index" + suffix) for suffix in (".ts", ".tsx", ".js"))]
        if any(candidate.is_symlink() for candidate in candidates):
            raise ValueError("relative module resolution must not use symlinks")
        if source.resolve() not in {candidate.resolve() for candidate in candidates}:
            raise ValueError("relative import does not resolve to the declared production module")
        if not re.search(r"(?:from\s*|(?:require|import)\s*\(\s*)['\"]" + re.escape(module) + r"['\"]", imported_from.read_text()):
            raise ValueError("held-out test does not import the declared missing module")
        if not re.search(r"\bexport\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\s+" + re.escape(symbol) + r"\b", source.read_text()):
            raise ValueError("missing feature symbol must be an exported production declaration")
        for candidate in candidates:
            old = Path(baseline) / candidate.resolve().relative_to(Path(reference).resolve())
            _inside(Path(baseline), old)
            if old.is_file() or old.is_symlink():
                raise ValueError("declared missing production module already exists on baseline")
        if declaration.get("module_aliases", []) != _module_aliases(reference, baseline, source_path):
            raise ValueError("module aliases must resolve through the same committed BASE and reference mapping")
        if pattern not in {re.escape(f"Cannot find module '{module}'"), re.escape(f'Cannot find module "{module}"')}:
            raise ValueError("missing module pattern must match one exact diagnostic literal")
    return re.compile(pattern)


def expected_feature_matches(case, reference, baseline, output):
    expected = _expected_feature_failure(case, reference, baseline)
    if not expected or not expected.search(output):
        return False
    declaration = case["expected_feature_failure"]
    remaining = output
    if declaration.get("missing_module"):
        reports = _missing_module_reports(output)
        if not reports:
            return False
        allowed = {declaration["missing_module"], *declaration.get("module_aliases", [])}
        for report in reports:
            importer = _reported_test(case, report[2])
            if report[1] not in allowed or importer is None:
                return False
            imported = (Path(reference) / importer).read_text()
            if not re.search(r"(?:from\s*|(?:require|import)\s*\(\s*)['\"]" + re.escape(report[1]) + r"['\"]", imported):
                return False
            remaining = remaining.replace(report[0], "")
        for report in re.finditer(r"Could not locate module ([^\s]+) mapped as:", output):
            failures = list(re.finditer(r"^FAIL\s+(\S+)", output[:report.start()], re.MULTILINE))
            importer = _reported_test(case, failures[-1][1]) if failures else None
            if report[1] not in declaration.get("module_aliases", []) or importer is None:
                return False
            if not re.search(r"from\s*['\"]" + re.escape(report[1]) + r"['\"]", (Path(reference) / importer).read_text()):
                return False
            remaining = remaining.replace(report[0], "")
        # Vitest reports zero collected tests when this verified local import blocks loading.
        remaining = re.sub(r"^\s*Tests\s+no tests\s*$", "", remaining, flags=re.MULTILINE)
    return not re.search(r"ModuleNotFoundError|Cannot find module|Could not locate module|Cannot find package|ERR_MODULE_NOT_FOUND|"
                         r"command not found|No such file or directory|SyntaxError:|"
                         r"IndentationError:|fixture '.+' not found|no tests|collected 0 items",
                         remaining, re.IGNORECASE)


def prepare_case(case, destination):
    """Prepare sibling actor/reference exports; controller MUST isolate the reference."""
    tests = acceptance_paths(case) + support_paths(case)
    root = Path(destination)
    repo = Path(case["repo"]).resolve()
    if root.resolve() == repo or repo in root.resolve().parents:
        raise ValueError("case exports must not modify the source repository")
    if root.exists() or root.is_symlink():
        raise ValueError(f"case destination already exists: {root}")
    root.mkdir(parents=True)
    subdir = case.get("source_subdir")
    actor = export_commit(case["repo"], case["base_commit"], root / "actor", True, subdir)
    reference = export_commit(case["repo"], case["reference_commit"], root / "reference", subdir=subdir)
    _expected_feature_failure(case, reference, actor)
    for relative in tests:
        target = actor / relative
        # Preserve public pre-PR tests; only reference test bytes are held out.
        if target.is_symlink():
            raise ValueError(f"acceptance file is a symlink: {relative}")
        if target.exists() and not target.is_file():
            raise ValueError(f"acceptance file is not regular: {relative}")
        _inside(reference, reference / relative)
        if (reference / relative).is_symlink() or not (reference / relative).is_file():
            raise ValueError(f"reference acceptance file missing or symlink: {relative}")
    if case.get("provide_acceptance"):
        _inject_acceptance(case, reference, actor)
        shutil.rmtree(actor / ".git")
        _init_git(actor)
    return {"actor": actor, "reference": reference, "baseline_hash": snapshot_hash(actor),
            "base_commit": case["base_commit"], "reference_commit": case["reference_commit"],
            "source_subdir": subdir}


def snapshot_hash(root):
    """Stable content/path/executable-bit digest, excluding Git metadata and caches."""
    root = Path(root)
    digest = hashlib.sha256()
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in {".git", "__pycache__", ".benchmark-runtime", ".benchmark-grading-runtime", ".tmp"})
        for name in sorted(files + [name for name in dirs if (Path(current) / name).is_symlink()]):
            path = Path(current) / name
            _inside(root, path)
            relative = path.relative_to(root).as_posix().encode()
            data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            mode = b"link" if path.is_symlink() else str(path.stat().st_mode & 0o111).encode()
            for chunk in (relative, mode, data):
                digest.update(len(chunk).to_bytes(8, "big"))
                digest.update(chunk)
    return digest.hexdigest()


def classify_result(returncode, output):
    if SETUP_ERRORS.search(output):
        return "setup_error"
    if returncode == 0:
        return "pass"
    # Executed-test failure reports qualify for admission; arbitrary exit 1 does not.
    unittest_failure = re.search(r"^FAIL: .+", output, re.MULTILINE) and re.search(r"FAILED \(failures=[1-9]", output)
    pytest_failure = re.search(r"\b[1-9]\d* failed\b", output) and re.search(r"AssertionError|^E\s+assert ", output, re.MULTILINE)
    jest_failure = re.search(r"^Tests:\s+(?:\d+ skipped,\s+)?[1-9]\d* failed\b", output, re.MULTILINE)
    go_failure = re.search(r"^--- FAIL: .+", output, re.MULTILINE) and re.search(r"^FAIL\s", output, re.MULTILINE)
    return "assertion_failure" if any((unittest_failure, pytest_failure, jest_failure, go_failure)) else "setup_error"


def _test_settings(workspace, command, test_cwd, test_env):
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
        raise ValueError("test_command must be a nonempty argument list")
    workspace = Path(workspace).resolve()
    cwd = workspace if test_cwd == "." else workspace / str(_relative(test_cwd))
    _inside(workspace, cwd)
    if test_env is None:
        test_env = {}
    if (not isinstance(test_env, dict)
            or not all(isinstance(key, str) and re.fullmatch(r"[A-Za-z_]\w*", key)
                       and isinstance(value, str) and "\x00" not in value
                       for key, value in test_env.items())):
        raise ValueError("test_env must map environment variable names to strings")
    env = {**os.environ, **test_env, "PYTHONDONTWRITEBYTECODE": "1"}
    if "PYTHONPATH" in test_env:
        env["PYTHONPATH"] = os.pathsep.join(str(workspace / path) for path in test_env["PYTHONPATH"].split(os.pathsep))
    return cwd, env


def run_tests(workspace, command, timeout=300, test_cwd=".", test_env=None):
    cwd, env = _test_settings(workspace, command, test_cwd, test_env)
    started = time.monotonic()
    try:
        run = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                             errors="replace", timeout=timeout, env=env, check=False)
        output = run.stdout + run.stderr
        return {"status": classify_result(run.returncode, output), "returncode": run.returncode,
                "output": output, "duration_seconds": time.monotonic() - started}
    except subprocess.TimeoutExpired as error:
        chunks = [value.decode(errors="replace") if isinstance(value, bytes) else value or ""
                  for value in (error.stdout, error.stderr)]
        return {"status": "timeout", "returncode": None, "output": "".join(chunks),
                "duration_seconds": time.monotonic() - started}
    except OSError as error:
        return {"status": "setup_error", "returncode": None, "output": str(error),
                "duration_seconds": time.monotonic() - started}


def _inject_acceptance(case, reference, work):
    reference, work = Path(reference), Path(work)
    tests = acceptance_paths(case) + support_paths(case)
    for relative in tests:
        source, target = reference / relative, work / relative
        _inside(reference, source)
        _inside(work, target)
        if source.is_symlink() or not source.is_file() or target.is_symlink():
            raise ValueError(f"acceptance file is missing or a symlink: {relative}")
        # No parent may redirect the immutable grader test to another source file.
        if any((work / parent).is_symlink() for parent in relative.parents):
            raise ValueError(f"acceptance path traverses a symlink: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def grade_case(case, actor, reference, timeout=300, *, runner=None):
    """Copy actor, refresh immutable acceptance files, execute checks; never mutate the actor."""
    actor, reference = Path(actor), Path(reference)
    snapshot_hash(actor)  # Reject escaping symlinks before copying.
    with tempfile.TemporaryDirectory(prefix="factory-pr-grade-") as temporary:
        work = Path(temporary) / "work"
        shutil.copytree(actor, work, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".benchmark-runtime", ".benchmark-grading-runtime", ".tmp"))
        _inject_acceptance(case, reference, work)
        _test_settings(work, case["test_command"], case.get("test_cwd", "."), case.get("test_env"))
        return (runner or run_tests)(work, case["test_command"], timeout, case.get("test_cwd", "."), case.get("test_env"))


def admit_case(case, destination, timeout=300, *, runner=None):
    """Admit only assertion-failing BASE plus passing actual PR reference."""
    prepared = prepare_case(case, destination)
    baseline = grade_case(case, prepared["actor"], prepared["reference"], timeout, runner=runner)
    reference = grade_case(case, prepared["reference"], prepared["reference"], timeout, runner=runner)
    if (baseline["status"] == "setup_error" and baseline["returncode"] not in (None, 0)
            and expected_feature_matches(case, prepared["reference"], prepared["actor"], baseline["output"])):
        baseline["status"] = "expected_feature_failure"
    return {**prepared, "admitted": baseline["status"] in {"assertion_failure", "expected_feature_failure"} and reference["status"] == "pass",
            "baseline": baseline, "reference_result": reference}

"""Serial Claude CLI inference with retained receipts and explicit usage limits."""

import json
import math
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path


class ClaudeModel:
    """One concrete model boundary; no filesystem or command tools reach the model."""

    def __init__(
        self,
        receipts,
        *,
        model="claude-fable-5-1",
        max_calls=12,
        max_tokens=150000,
        list_cost_limit=3.0,
        tag="interactive",
        prompt=None,
    ):
        self.receipts = Path(receipts).resolve()
        self.receipts.mkdir(parents=True, exist_ok=True)
        self.model, self.max_calls, self.max_tokens = model, max_calls, max_tokens
        self.list_cost_limit, self.tag, self.prompt = list_cost_limit, tag, prompt
        self.last_receipt = None

    def usage(self):
        rows = [
            json.loads(path.read_text())
            for path in sorted(self.receipts.glob("call-[0-9][0-9][0-9][0-9].json"))
        ]
        costs = [row.get("list_cost_usd") for row in rows]
        tokens = [row.get("tokens") for row in rows]
        return {
            "calls": len(rows),
            "list_cost_usd": sum(v for v in costs if v is not None),
            "tokens": sum(v for v in tokens if v is not None),
            "unknown": any(v is None for v in costs + tokens),
        }

    def __call__(self, system, payload):
        usage = self.usage()
        if usage["unknown"]:
            raise RuntimeError(
                "A previous call has unknown usage; stop before another request"
            )
        if usage["calls"] >= self.max_calls or usage["tokens"] >= self.max_tokens:
            raise RuntimeError("Model call/token budget exhausted")
        remaining = self.list_cost_limit - usage["list_cost_usd"]
        if remaining < 0.10:
            raise RuntimeError("Reported list-cost admission budget exhausted")
        if self.prompt is not None:
            system = Path(self.prompt).read_text()
        system += "\nReturn only one JSON object matching response_schema. No Markdown fences."
        content = json.dumps(payload, ensure_ascii=False)
        if len(content.encode()) > 180000:
            raise ValueError("Model context exceeded the bounded request size")
        number = usage["calls"] + 1
        target = self.receipts / f"call-{number:04d}.json"
        prompt_path = target.with_suffix(".prompt.json")
        prompt_path.write_text(
            json.dumps({"system": system, "payload": payload}, indent=2) + "\n"
        )
        command = [
            "claude",
            "--print",
            "--safe-mode",
            "--model",
            self.model,
            "--effort",
            "high",
            "--max-budget-usd",
            str(min(0.60, remaining)),
            "--tools",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--setting-sources",
            "",
            "--system-prompt",
            system,
            "--output-format",
            "json",
            "--no-session-persistence",
            "--no-chrome",
        ]
        environment = dict(
            os.environ,
            CLAUDE_CODE_MAX_OUTPUT_TOKENS="8192",
            CLAUDE_CODE_MAX_RETRIES="0",
            CLAUDE_CODE_MAX_TURNS="2",
        )
        started = time.monotonic()
        record = {
            "model": self.model,
            "tag": self.tag,
            "list_cost_usd": None,
            "tokens": None,
            "status": "started",
            "prompt_path": str(prompt_path),
        }
        target.write_text(json.dumps(record, indent=2) + "\n")
        with tempfile.TemporaryDirectory(prefix="plumb-inference-") as work:
            process = subprocess.Popen(
                command,
                cwd=work,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            try:
                stdout, stderr = process.communicate(content, timeout=120)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    stdout, stderr = process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate()
                record.update(
                    status="timeout",
                    stdout=stdout,
                    stderr=stderr,
                    seconds=time.monotonic() - started,
                )
                target.write_text(json.dumps(record, indent=2) + "\n")
                raise RuntimeError(
                    "Model request timed out; usage unknown, no automatic retry"
                ) from None
        record.update(
            stdout=stdout,
            stderr=stderr,
            returncode=process.returncode,
            seconds=time.monotonic() - started,
        )
        try:
            provider = json.loads(stdout)
            record["provider"] = provider
            cost = provider.get("total_cost_usd")
            models = provider.get("modelUsage", {})
            if isinstance(cost, (int, float)) and math.isfinite(cost) and cost >= 0:
                record["list_cost_usd"] = cost
            if models and all(isinstance(row, dict) for row in models.values()):
                fields = (
                    "inputTokens",
                    "outputTokens",
                    "cacheReadInputTokens",
                    "cacheCreationInputTokens",
                )
                values = [row.get(field) for row in models.values() for field in fields]
                if all(
                    type(v) in (int, float) and math.isfinite(v) and v >= 0
                    for v in values
                ):
                    record["tokens"] = sum(values)
            if (
                process.returncode
                or provider.get("is_error")
                or provider.get("subtype") != "success"
            ):
                raise ValueError("Provider did not complete successfully")
            if set(models) != {self.model}:
                raise ValueError("Provider used an unpinned model")
            if provider.get("subagent_stats", {}).get("spawned", 0) or provider.get(
                "permission_denials"
            ):
                raise ValueError("Unexpected model-side agent/tool activity")
            response = provider.get("structured_output")
            if response is None:
                response = json.loads(provider["result"])
            if not isinstance(response, dict):
                raise TypeError("Model did not return a JSON object")
            record.update(status="completed", response=response)
        except (ValueError, KeyError, TypeError) as error:
            record.update(status="failed", error=str(error))
            target.write_text(json.dumps(record, indent=2) + "\n")
            raise RuntimeError("Model response failed; see " + str(target)) from error
        target.write_text(json.dumps(record, indent=2) + "\n")
        self.last_receipt = str(target)
        return response

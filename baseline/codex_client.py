"""Codex CLI baseline client.

Wraps `codex exec` as a chat-like client so the same Harness loop (prompt,
compile feedback, tests, termination) can drive the baseline framework.
Codex runs as an agent in a fresh read-only workspace; only its final message
is used as the model output.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time

from agent.llm import LLMError, load_env_file

DMX_BASE = "https://www.dmxapi.cn/v1"


def _codex_exe():
    for name in ("codex.cmd", "codex.exe", "codex"):
        p = shutil.which(name)
        if p:
            return p
    raise LLMError("codex CLI not found in PATH")


def _format_messages(messages):
    parts = []
    for m in messages:
        role = m.get("role", "user")
        label = {"system": "系统要求", "user": "用户",
                 "assistant": "你之前的输出"}.get(role, role)
        parts.append("[%s]\n%s" % (label, m.get("content", "")))
    parts.append("[指令]\n请根据最新的用户反馈，仅输出完整的代码块"
                 "（格式见系统要求），不要输出任何额外解释。")
    return "\n\n".join(parts)


class CodexClient:
    framework = "codex"

    def __init__(self, model, timeout=900.0, sandbox="read-only",
                 ignore_user_config=True):
        load_env_file()
        self.model = model
        self.model_name = model
        self.name = "codex/%s" % model
        self.exe = _codex_exe()
        self.timeout = timeout
        self.sandbox = sandbox
        self.ignore_user_config = ignore_user_config
        self.workdir = tempfile.mkdtemp(prefix="codex_task_")
        self.total_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    def _cmd(self, out_file):
        cmd = [self.exe, "exec", "--ephemeral", "--skip-git-repo-check",
               "-s", self.sandbox, "-C", self.workdir,
               "-c", 'model_providers.dmxapi.name="DMXAPI"',
               "-c", 'model_providers.dmxapi.base_url="%s"' % DMX_BASE,
               "-c", 'model_providers.dmxapi.env_key="DMXAPI_API_KEY"',
               "-c", 'model_providers.dmxapi.wire_api="responses"',
               "-c", 'model_provider="dmxapi"',
               "-m", self.model, "-o", out_file, "--json"]
        if self.ignore_user_config:
            cmd.insert(2, "--ignore-user-config")
        return cmd

    def chat(self, messages):
        prompt = _format_messages(messages)
        out_file = os.path.join(self.workdir, "last_message.txt")
        if os.path.exists(out_file):
            os.remove(out_file)
        t0 = time.time()
        try:
            p = subprocess.run(self._cmd(out_file),
                               input=prompt.encode("utf-8"),
                               capture_output=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise LLMError("codex exec timed out after %.0fs" % self.timeout)
        stdout = (p.stdout or b"").decode("utf-8", "replace")
        stderr = (p.stderr or b"").decode("utf-8", "replace")
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        finish = None
        for ln in stdout.splitlines():
            try:
                ev = json.loads(ln)
            except Exception:
                continue
            if ev.get("type") == "turn.completed" and ev.get("usage"):
                usage["prompt_tokens"] += int(ev["usage"].get("input_tokens", 0))
                usage["completion_tokens"] += int(
                    ev["usage"].get("output_tokens", 0))
            if ev.get("type") == "turn.failed":
                finish = "failed"
        if p.returncode != 0 or not os.path.exists(out_file):
            raise LLMError("codex exec failed (exit=%s): %s"
                           % (p.returncode, stderr[-800:]))
        text = open(out_file, encoding="utf-8").read()
        self.total_usage["prompt_tokens"] += usage["prompt_tokens"]
        self.total_usage["completion_tokens"] += usage["completion_tokens"]
        return {
            "text": text,
            "finish_reason": finish or "stop",
            "usage": usage,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "model": self.name,
        }

    def cost_usd(self):
        return None

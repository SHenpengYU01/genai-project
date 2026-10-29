"""OpenAI-compatible LLM client used by the agent harness (stdlib only).

Model aliases map to provider defaults; any field can be overridden via env:
  AGENT_BASE_URL, AGENT_MODEL, AGENT_API_KEY
Provider keys default to DEEPSEEK_API_KEY / DASHSCOPE_API_KEY.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

# price_* are USD per 1M tokens, rough public list prices; override per run.
DEFAULT_MODELS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "key_env": "DEEPSEEK_API_KEY",
        "price_in": 0.27,
        "price_out": 1.10,
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "key_env": "DASHSCOPE_API_KEY",
        "price_in": 0.40,
        "price_out": 1.20,
    },
}


class LLMError(RuntimeError):
    pass


_ENV_LOADED = False


def load_env_file(path=None):
    """Load KEY=VALUE lines from <repo>/.env (or $AGENT_ENV_FILE) once.

    Existing environment variables win. .env is gitignored; .env.example is
    the committed template.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    if path is None:
        path = os.environ.get("AGENT_ENV_FILE")
    if path is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and val and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


def resolve_model(alias):
    load_env_file()
    if alias not in DEFAULT_MODELS:
        raise LLMError("unknown model alias %r (known: %s)"
                       % (alias, ", ".join(DEFAULT_MODELS)))
    cfg = dict(DEFAULT_MODELS[alias])
    cfg["base_url"] = os.environ.get("AGENT_BASE_URL") or cfg["base_url"]
    cfg["model"] = os.environ.get("AGENT_MODEL") or cfg["model"]
    cfg["api_key"] = os.environ.get("AGENT_API_KEY") \
        or os.environ.get(cfg["key_env"], "")
    cfg["alias"] = alias
    return cfg


class OpenAICompatClient:
    def __init__(self, alias, temperature=0.1, max_tokens=4096,
                 timeout=240.0, retries=3):
        self.cfg = resolve_model(alias)
        if not self.cfg["api_key"]:
            raise LLMError("no API key: set %s (or AGENT_API_KEY)"
                           % self.cfg["key_env"])
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retries = retries
        self.name = "%s/%s" % (alias, self.cfg["model"])
        self.total_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    def chat(self, messages):
        url = self.cfg["base_url"].rstrip("/") + "/chat/completions"
        body = {
            "model": self.cfg["model"],
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        last_err = None
        for attempt in range(self.retries):
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + self.cfg["api_key"]})
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                text = payload["choices"][0]["message"]["content"] or ""
                usage = payload.get("usage") or {}
                out = {
                    "text": text,
                    "usage": {
                        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                        "completion_tokens": int(
                            usage.get("completion_tokens", 0)),
                    },
                    "elapsed_ms": int((time.time() - t0) * 1000),
                    "model": self.name,
                }
                self.total_usage["prompt_tokens"] += \
                    out["usage"]["prompt_tokens"]
                self.total_usage["completion_tokens"] += \
                    out["usage"]["completion_tokens"]
                return out
            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", "replace")[:500]
                except Exception:
                    pass
                last_err = "HTTP %s: %s" % (e.code, detail)
                if e.code not in (429, 500, 502, 503, 504):
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_err = "%s: %s" % (type(e).__name__, e)
            time.sleep(2 ** attempt)
        raise LLMError("chat completion failed after retries: %s" % last_err)

    def cost_usd(self):
        c = self.cfg
        return (self.total_usage["prompt_tokens"] * c["price_in"]
                + self.total_usage["completion_tokens"] * c["price_out"]) / 1e6


class MockClient:
    """Offline client: replays scripted responses (used for harness self-test)."""

    def __init__(self, responses, name="mock"):
        self.responses = list(responses)
        self.i = 0
        self.name = name
        self.total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        if self.i >= len(self.responses):
            text = self.responses[-1] if self.responses else ""
        else:
            text = self.responses[self.i]
            self.i += 1
        return {"text": text,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "elapsed_ms": 0, "model": self.name}

    def cost_usd(self):
        return 0.0


def _mask(key):
    if not key:
        return "MISSING"
    return "set(%s***)" % key[:4] if len(key) > 8 else "set(***)"


def main():
    """Print whether each model alias has a key configured (masked)."""
    load_env_file()
    for alias, cfg in DEFAULT_MODELS.items():
        key = os.environ.get("AGENT_API_KEY") \
            or os.environ.get(cfg["key_env"], "")
        print("%-9s model=%-14s %s=%s"
              % (alias, os.environ.get("AGENT_MODEL") or cfg["model"],
                 cfg["key_env"], _mask(key)))


if __name__ == "__main__":
    main()

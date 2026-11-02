"""OpenAI-compatible LLM client used by the agent harness (stdlib only).

Provider: DMXAPI (https://www.dmxapi.cn), one key for DeepSeek/Qwen/etc.
Model names differ per provider page — list them with
``python -m agent.llm --list`` once the key is configured, and override
defaults via DMXAPI_MODEL_DEEPSEEK / DMXAPI_MODEL_QWEN in .env.

Env overrides: AGENT_BASE_URL, AGENT_MODEL, AGENT_API_KEY, DMXAPI_API_KEY.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

DMX_BASE = "https://www.dmxapi.cn/v1"

# price_* are optional (same currency as the provider; DMXAPI bills in RMB).
# Fill them from https://www.dmxapi.cn/rmb to enable cost estimates.
DEFAULT_MODELS = {
    "deepseek": {
        "base_url": DMX_BASE,
        "model": "deepseek-v4.1-flash",
        "key_env": "DMXAPI_API_KEY",
        "model_env": "DMXAPI_MODEL_DEEPSEEK",
        "price_in": None,
        "price_out": None,
    },
    "qwen": {
        "base_url": DMX_BASE,
        "model": "qwen3.7-flash",
        "key_env": "DMXAPI_API_KEY",
        "model_env": "DMXAPI_MODEL_QWEN",
        "price_in": None,
        "price_out": None,
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


def resolve_model(alias, model_name=None):
    load_env_file()
    if alias not in DEFAULT_MODELS:
        raise LLMError("unknown model alias %r (known: %s)"
                       % (alias, ", ".join(DEFAULT_MODELS)))
    cfg = dict(DEFAULT_MODELS[alias])
    cfg["base_url"] = os.environ.get("AGENT_BASE_URL") or cfg["base_url"]
    cfg["model"] = (model_name
                    or os.environ.get("AGENT_MODEL")
                    or os.environ.get(cfg["model_env"], "")
                    or cfg["model"])
    cfg["api_key"] = (os.environ.get("AGENT_API_KEY")
                      or os.environ.get(cfg["key_env"], ""))
    cfg["alias"] = alias
    return cfg


def list_models(alias="deepseek", timeout=60.0):
    """GET {base}/models and return the ids (needs a configured key)."""
    cfg = resolve_model(alias)
    if not cfg["api_key"]:
        raise LLMError("no API key: set %s in .env" % cfg["key_env"])
    url = cfg["base_url"].rstrip("/") + "/models"
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + cfg["api_key"]})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8"))
    return [m.get("id") for m in payload.get("data", []) if m.get("id")]


class OpenAICompatClient:
    def __init__(self, alias, model_name=None, temperature=0.1,
                 max_tokens=None, timeout=240.0, retries=3):
        if max_tokens is None:
            max_tokens = int(os.environ.get("AGENT_MAX_TOKENS", "16384"))
        self.cfg = resolve_model(alias, model_name)
        if not self.cfg["api_key"]:
            raise LLMError("no API key: set %s (or AGENT_API_KEY)"
                           % self.cfg["key_env"])
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.retries = retries
        self.name = "%s/%s" % (alias, self.cfg["model"])
        self.framework = "agent"
        self.model_name = self.cfg["model"]
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
                choice = payload["choices"][0]
                text = choice["message"]["content"] or ""
                usage = payload.get("usage") or {}
                out = {
                    "text": text,
                    "finish_reason": choice.get("finish_reason"),
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
        if c.get("price_in") is None or c.get("price_out") is None:
            return None
        return (self.total_usage["prompt_tokens"] * c["price_in"]
                + self.total_usage["completion_tokens"] * c["price_out"]) / 1e6


class MockClient:
    """Offline client: replays scripted responses (used for harness self-test)."""

    def __init__(self, responses, name="mock"):
        self.responses = list(responses)
        self.i = 0
        self.name = name
        self.framework = "mock"
        self.model_name = name
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
                "finish_reason": "stop",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "elapsed_ms": 0, "model": self.name}

    def cost_usd(self):
        return 0.0


def _mask(key):
    if not key:
        return "MISSING"
    return "set(%s***)" % key[:4] if len(key) > 8 else "set(***)"


def main(argv=None):
    """Show key readiness (masked) or list provider models.

    python -m agent.llm              # readiness per alias
    python -m agent.llm --list       # all model ids from /v1/models
    python -m agent.llm --list qwen  # filter by substring
    """
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", dest="list_filter", nargs="?", const="",
                    default=None)
    ap.add_argument("--alias", default="deepseek")
    args = ap.parse_args(argv)
    load_env_file()

    if args.list_filter is not None:
        try:
            ids = list_models(args.alias)
        except Exception as e:
            print("ERROR: %s" % e)
            return 2
        flt = args.list_filter.lower()
        hits = sorted(i for i in ids if flt in i.lower()) or sorted(ids)
        print("models matching %r (%d of %d):"
              % (args.list_filter or "", len(hits), len(ids)))
        for i in hits:
            print("  " + i)
        return 0

    for alias, cfg in DEFAULT_MODELS.items():
        key = os.environ.get("AGENT_API_KEY") \
            or os.environ.get(cfg["key_env"], "")
        model = os.environ.get(cfg["model_env"], "") or cfg["model"]
        print("%-9s model=%-22s %s=%s  base=%s"
              % (alias, model, cfg["key_env"], _mask(key),
                 os.environ.get("AGENT_BASE_URL") or cfg["base_url"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

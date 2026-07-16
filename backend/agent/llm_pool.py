"""Role-tagged LLM endpoint pool.

Owns a set of LM Studio (OpenAI-compatible) endpoints, each tagged with the
roles it can serve and a per-endpoint concurrency capacity. Tasks borrow an
endpoint for the duration of an agent run via `acquire(role)`; the borrow is
gated by a condition variable so concurrency never exceeds each endpoint's
capacity, and independent tasks fan out across endpoints automatically.

Config (env):
    LM_STUDIO_ENDPOINTS = "<base_url>|<model>|<role,role>;<base_url>|<model>|<roles>"
        - endpoints separated by ';'
        - fields separated by '|':  base_url | model | roles(optional)
        - roles separated by ',' — omitted => all roles
    LM_STUDIO_CONCURRENCY_PER_ENDPOINT = "1"   # capacity per endpoint

Falls back to a single endpoint built from LM_STUDIO_BASE_URL / LM_STUDIO_MODEL
when LM_STUDIO_ENDPOINTS is unset (full backward compatibility).
"""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import httpx
from langchain_openai import ChatOpenAI

# Roles used across the app
ROLE_CLASSIFY = "classify"
ROLE_CHAT = "chat"
ROLE_AGENT = "agent"
ALL_ROLES = {ROLE_CLASSIFY, ROLE_CHAT, ROLE_AGENT}


@dataclass
class EndpointSpec:
    base_url: str               # ends with /v1 (ignored for anthropic)
    model: str
    roles: set[str] = field(default_factory=lambda: set(ALL_ROLES))
    api_key: str = "lm-studio"
    provider: str = "openai"    # "openai" (local LM Studio) | "anthropic"


class _Endpoint:
    def __init__(self, spec: EndpointSpec, capacity: int):
        self.spec = spec
        self.capacity = capacity
        self.in_use = 0

    @property
    def free(self) -> bool:
        return self.in_use < self.capacity


class Lease:
    """A borrowed endpoint. Build a chat model bound to it (local or cloud)."""

    def __init__(self, spec: EndpointSpec):
        self.spec = spec

    def chat(self, **kwargs):
        if self.spec.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            kwargs.setdefault("max_tokens", 4096)  # Anthropic requires a cap
            return ChatAnthropic(
                model=self.spec.model,
                api_key=self.spec.api_key,
                **kwargs,
            )
        return ChatOpenAI(
            base_url=self.spec.base_url,
            api_key=self.spec.api_key,
            model=self.spec.model,
            **kwargs,
        )


class LLMPool:
    def __init__(self, specs: list[EndpointSpec], per_endpoint: int = 1):
        self._eps = [_Endpoint(s, max(1, per_endpoint)) for s in specs]
        self._cond = asyncio.Condition()

    @property
    def size(self) -> int:
        return len(self._eps)

    def describe(self) -> str:
        return ", ".join(
            f"{e.spec.model}@{e.spec.base_url} [{','.join(sorted(e.spec.roles))}] x{e.capacity}"
            for e in self._eps
        )

    @asynccontextmanager
    async def acquire(self, role: str = ROLE_AGENT):
        """Borrow an endpoint that serves `role`. Falls back to any endpoint
        if no endpoint declares that role. Blocks until one is free."""
        role_supported = any(role in e.spec.roles for e in self._eps)

        async with self._cond:
            while True:
                candidates = [
                    e for e in self._eps
                    if e.free and (role in e.spec.roles or not role_supported)
                ]
                if candidates:
                    # least-loaded first for even spread
                    chosen = min(candidates, key=lambda e: e.in_use)
                    chosen.in_use += 1
                    break
                await self._cond.wait()

        try:
            yield Lease(chosen.spec)
        finally:
            async with self._cond:
                chosen.in_use -= 1
                self._cond.notify_all()

    async def healthcheck(self) -> None:
        """Ping each local endpoint's /models; drop unreachable ones. If NONE are
        reachable and ANTHROPIC_API_KEY is set, fall back to Claude (Anthropic)."""
        live: list[_Endpoint] = []
        async with httpx.AsyncClient(timeout=4.0) as client:
            for e in self._eps:
                if e.spec.provider != "openai":
                    live.append(e)  # cloud endpoints aren't ping-checked
                    continue
                try:
                    r = await client.get(f"{e.spec.base_url}/models")
                    if r.status_code != 200:
                        print(f"[llm_pool] DOWN {e.spec.base_url} (HTTP {r.status_code})")
                        continue
                    # LM Studio answers 200 even with no model loaded → check data.
                    models = (r.json() or {}).get("data", [])
                    if models:
                        live.append(e)
                        print(f"[llm_pool] OK   {e.spec.base_url} ({e.spec.model})")
                    else:
                        print(f"[llm_pool] DOWN {e.spec.base_url} (no model loaded)")
                except Exception as ex:
                    print(f"[llm_pool] DOWN {e.spec.base_url} ({type(ex).__name__})")

        if live:
            self._eps = live
            return

        anthropic = _anthropic_spec()
        if anthropic is not None:
            cap = int(os.getenv("ANTHROPIC_CONCURRENCY", "4"))
            self._eps = [_Endpoint(anthropic, cap)]
            print(f"[llm_pool] No local LLM reachable — falling back to Anthropic "
                  f"({anthropic.model}) x{cap}")
        else:
            print("[llm_pool] WARNING: no local endpoint reachable and no "
                  "ANTHROPIC_API_KEY set — keeping configured list")


# ── Config parsing ─────────────────────────────────────────────────────────────

def _anthropic_spec() -> EndpointSpec | None:
    """Cloud fallback spec from env, or None if no API key is configured."""
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001").strip()
    return EndpointSpec(
        base_url="anthropic", model=model, roles=set(ALL_ROLES),
        api_key=key, provider="anthropic",
    )


def _parse_specs() -> list[EndpointSpec]:
    raw = os.getenv("LM_STUDIO_ENDPOINTS", "").strip()
    if raw:
        specs: list[EndpointSpec] = []
        for entry in raw.split(";"):
            entry = entry.strip()
            if not entry:
                continue
            parts = [p.strip() for p in entry.split("|")]
            base_url = parts[0]
            model = parts[1] if len(parts) > 1 and parts[1] else "local-model"
            roles = (
                {r.strip() for r in parts[2].split(",") if r.strip()}
                if len(parts) > 2 and parts[2]
                else set(ALL_ROLES)
            )
            specs.append(EndpointSpec(base_url=base_url, model=model, roles=roles))
        if specs:
            return specs

    # Fallback: single endpoint from legacy env vars
    base = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/api/v1")
    lm_root = base.rstrip("/api/v1").rstrip("/")
    model = os.getenv("LM_STUDIO_MODEL", "qwen/qwen3.5-9b")
    return [EndpointSpec(base_url=f"{lm_root}/v1", model=model, roles=set(ALL_ROLES))]


# ── Module singleton ─────────────────────────────────────────────────────────────

_pool: LLMPool | None = None


def init_pool() -> LLMPool:
    global _pool
    specs = _parse_specs()
    per = int(os.getenv("LM_STUDIO_CONCURRENCY_PER_ENDPOINT", "1"))
    _pool = LLMPool(specs, per_endpoint=per)
    print(f"[llm_pool] Initialised {_pool.size} endpoint(s): {_pool.describe()}")
    return _pool


def get_pool() -> LLMPool:
    """Return the pool, lazily initialising from env if needed (covers scripts/tests)."""
    global _pool
    if _pool is None:
        init_pool()
    return _pool  # type: ignore[return-value]

"""Groq LLM wrapper.

The plan targeted the Claude SDK (tool_runner, messages.parse, native PDF
citations). Groq exposes an OpenAI-compatible surface instead, so this module
provides the equivalents we actually need:

    complete()       -> plain text
    complete_json()  -> JSON-mode output validated against a Pydantic model
    run_agent()      -> OpenAI-style function-calling loop (replaces tool_runner)
    stream()         -> token stream for SSE

Effort ("low"/"high"/"xhigh" in the plan) maps to gpt-oss reasoning_effort.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Iterator, Type, TypeVar

from groq import BadRequestError, Groq
from pydantic import BaseModel, ValidationError

from . import config


def _extract_json(raw: str) -> str:
    """Pull the first balanced JSON object out of a possibly-noisy string."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", raw).strip()
    start = raw.find("{")
    if start == -1:
        return raw
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                return raw[start : i + 1]
    return raw[start:]

_client: Groq | None = None
T = TypeVar("T", bound=BaseModel)


def client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=config.require_key(), max_retries=3, timeout=90.0)
    return _client


def _is_reasoning(model: str) -> bool:
    return model.startswith("openai/gpt-oss")


def _extra(model: str, effort: str) -> dict:
    """reasoning_effort only applies to gpt-oss models."""
    if _is_reasoning(model):
        return {"reasoning_effort": config.EFFORT_MAP.get(effort, "medium")}
    return {}


def complete(
    messages: list[dict],
    *,
    model: str | None = None,
    effort: str = "high",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    model = model or config.REASONING_MODEL
    resp = client().chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        extra_body=_extra(model, effort),
    )
    return resp.choices[0].message.content or ""


def complete_json(
    messages: list[dict],
    schema: Type[T],
    *,
    model: str | None = None,
    effort: str = "high",
    max_tokens: int = 4096,
    temperature: float = 0.2,
    retries: int = 2,
) -> T:
    """JSON-mode completion validated against `schema`. Retries on invalid JSON.

    Replaces Claude's client.messages.parse(). We inject the schema into the
    prompt (json_object mode needs the word "json" present) and validate.
    """
    model = model or config.REASONING_MODEL
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    sys_hint = {
        "role": "system",
        "content": (
            "You output ONLY a single JSON object that conforms to this JSON "
            "Schema. No prose, no markdown fences.\n\n" + schema_json
        ),
    }
    convo = [sys_hint, *messages]
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        # After a failure (or for reasoning models where reasoning tokens eat the
        # budget), fall back to plain generation + manual JSON extraction — Groq's
        # json_object validator can 400 on large nested schemas.
        use_json_mode = attempt == 0
        try:
            resp = client().chat.completions.create(
                model=model,
                messages=convo,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"} if use_json_mode else None,
                extra_body=_extra(model, effort),
            )
            raw = resp.choices[0].message.content or "{}"
        except BadRequestError as e:
            last_err = e
            convo.append(
                {"role": "user", "content": "Output ONLY the JSON object, nothing else."}
            )
            continue
        try:
            return schema.model_validate_json(_extract_json(raw))
        except (ValidationError, json.JSONDecodeError) as e:
            last_err = e
            convo.append({"role": "assistant", "content": raw[:2000]})
            convo.append(
                {"role": "user",
                 "content": f"That did not validate: {e}. Return corrected JSON only, no prose."}
            )
    raise ValueError(f"complete_json failed after {retries + 1} attempts: {last_err}")


def run_agent(
    messages: list[dict],
    tools: list[dict],
    tool_impls: dict[str, Callable[..., Any]],
    *,
    model: str | None = None,
    effort: str = "high",
    max_tokens: int = 4096,
    max_steps: int = 8,
    on_event: Callable[[dict], None] | None = None,
) -> tuple[str, list[dict]]:
    """OpenAI-style function-calling loop (our stand-in for Claude tool_runner).

    `tools` are OpenAI tool schemas; `tool_impls` maps name -> python callable
    taking kwargs. `on_event` receives {type, ...} dicts for streaming the
    "Checking clause 2.3.4…" activity feed to the UI. Returns (final_text, trace).
    """
    model = model or config.REASONING_MODEL
    convo = list(messages)
    trace: list[dict] = []
    for _ in range(max_steps):
        resp = client().chat.completions.create(
            model=model,
            messages=convo,
            tools=tools,
            tool_choice="auto",
            max_tokens=max_tokens,
            extra_body=_extra(model, effort),
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            if on_event:
                on_event({"type": "final"})
            return msg.content or "", trace
        # Record the assistant turn (with its tool calls) verbatim.
        convo.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
            }
        )
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if on_event:
                on_event({"type": "tool_call", "name": name, "args": args})
            impl = tool_impls.get(name)
            if impl is None:
                result = {"error": f"unknown tool {name}"}
            else:
                try:
                    result = impl(**args)
                except Exception as e:  # surface tool errors back to the model
                    result = {"error": str(e)}
            trace.append({"tool": name, "args": args, "result": result})
            if on_event:
                on_event({"type": "tool_result", "name": name})
            convo.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str)[:12000],
                }
            )
    return "Agent stopped: max reasoning steps reached.", trace


def stream(
    messages: list[dict],
    *,
    model: str | None = None,
    effort: str = "high",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> Iterator[str]:
    model = model or config.REASONING_MODEL
    s = client().chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        extra_body=_extra(model, effort),
    )
    for chunk in s:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

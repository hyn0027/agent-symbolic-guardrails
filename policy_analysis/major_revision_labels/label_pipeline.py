"""Label every ID-ed policy item of the three benchmarks as out of scope or not, following criteria.csv,
with Claude Code or the OpenAI API.

Each item is asked in its own call, with the benchmark's whole policy document as context
(plus api_endpoints.md for MedAgentBench). Both backends get the same prompt and answer format.
The document comes first in every call, so it is served from the prompt cache after the first item of a benchmark.

  backend: claude   one headless `claude -p` call per item, no tools. Uses your Claude subscription
                    (run where `claude` is logged in).
  backend: openai   one Responses API call per item. Needs OPENAI_API_KEY in .env.

Results go to labeled_<backend>.csv. Usage: python label_pipeline.py   (settings in config.yaml)
"""

import asyncio
import csv
import json
import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
POLICY_FILES = {
    "CarBench": HERE.parent / "CarBench" / "policies.md",
    "MedAgentBench": HERE.parent / "MedAgentBench" / "policy.md",
    "tau2-airline": HERE.parent / "tau2-airline" / "policy.md",
}
EXTRA_CONTEXT = {"MedAgentBench": HERE / "api_endpoints.md"}  # the APIs the MedAgentBench agent can call
MEDAGENTBENCH_ONLY = "(MedAgentBench only)"
# Claude Code's messages when the subscription's usage limit is reached (it resets after some hours)
USAGE_LIMIT = re.compile(r"usage limit|limit reached|hit your .{0,20}limit|limit (will )?resets?|resets? at|out of .{0,10}usage", re.I)

SYSTEM_PROMPT = (
    "You are labeling candidate requirements from an AI agent's policy document for a research study. "
    "The whole policy document is given for context; answer only about the candidate named in the question, "
    "by choosing exactly one of the given options and applying the option definitions exactly as written."
)
SCHEMA = {
    "type": "object",
    "properties": {
        # asked before the option so the model justifies its choice first; not saved
        "reasoning": {"type": "string", "description": "1-2 sentence justification."},
        "option": {"type": "string", "enum": ["A", "B"]},
    },
    "required": ["reasoning", "option"],
    "additionalProperties": False,
}


class UsageLimitError(Exception):
    pass


def parse_criteria():
    """(question, [(label, [definitions])]) from criteria.csv; a row with no label adds to the label above."""
    question, options = None, []
    with open(HERE / "criteria.csv", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            question = question or row["Instructions"].strip()
            if row["label"].strip():
                options.append((row["label"].strip(), []))
            options[-1][1].append(row["definition"].strip())
    return question, options


def parse_policies(path, benchmark):
    """[(id, text)] for every line of the policy document that starts with an [id]."""
    items = []
    for line in path.read_text().splitlines():
        ids = re.findall(r"\[([^\]]+)\]", line)
        if not ids:
            continue
        # CarBench lines can carry several ids, e.g. [LLM-POL:008][AUT-POL:009]; elsewhere only the first is the id
        item_id = " / ".join(ids) if benchmark == "CarBench" else ids[0]
        text = re.sub(r"^\s*(?:[-#]+\s*)?(?:\[[^\]]+\])+\s*", "", line).strip()
        items.append((item_id, text))
    return items


def build_question(benchmark, item_id, text, question, options):
    lines = [f"Candidate requirement [{item_id}]: {text}", "", "Question:", question, "",
             "Options (choose exactly one):"]
    for letter, (label, definitions) in zip("AB", options):
        defs = [d for d in definitions if benchmark == "MedAgentBench" or not d.startswith(MEDAGENTBENCH_ONLY)]
        if len(defs) == 1:
            lines += [f"{letter}. label: {label}", f"   definition: {defs[0]}"]
        else:
            lines += [f"{letter}. label: {label}", "   definition: if any of the following is satisfied:"]
            lines += [f"   - {d}" for d in defs]
    return "\n".join(lines)


# ---------------------------------------------------------------- backends: return (option letter, cost)


async def ask_claude(cfg, benchmark, context, question_text):
    cmd = [
        "claude", "-p", f"{context}\n\n{question_text}",
        "--system-prompt", SYSTEM_PROMPT,
        "--model", cfg["model"], "--effort", cfg["effort"],
        "--output-format", "json", "--json-schema", json.dumps(SCHEMA),
        "--restricted", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
    ]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}  # use the subscription, not an API key
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=HERE, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=cfg["timeout_minutes"] * 60)
    except asyncio.TimeoutError:
        proc.kill()
        raise TimeoutError("claude timed out")
    try:
        result = json.loads(out)
    except json.JSONDecodeError:
        text = (out + err).decode(errors="replace")[-500:]
        if USAGE_LIMIT.search(text):
            raise UsageLimitError(text.strip())
        raise RuntimeError(f"claude returned no JSON: {text}")
    if result.get("is_error") or result.get("subtype") != "success":
        text = f"{result.get('result') or ''} {result.get('terminal_reason') or ''} {err.decode(errors='replace')[:300]}"
        if USAGE_LIMIT.search(text):
            raise UsageLimitError(text.strip())
        raise RuntimeError(f"claude failed: {text.strip()}")
    return result["structured_output"]["option"], result.get("total_cost_usd") or 0.0


def openai_cost(usage, prices):
    """USD cost of one OpenAI call from its usage and the per-1M-token prices in config.yaml."""
    details = usage.input_tokens_details.model_dump()
    cached = details.get("cached_tokens") or 0
    writes = details.get("cache_write_tokens_details") or {}
    write_30m, write_12h = writes.get("ttl_30m_tokens") or 0, writes.get("ttl_12h_tokens") or 0
    uncached = usage.input_tokens - cached - write_30m - write_12h
    return (
        uncached * prices["input"]
        + cached * prices.get("cached", prices["input"])
        + write_30m * prices.get("write_30m", prices["input"])
        + write_12h * prices.get("write_12h", prices["input"])
        + usage.output_tokens * prices["output"]  # output includes reasoning tokens
    ) / 1_000_000


async def ask_openai(cfg, benchmark, context, question_text, client):
    request = dict(
        model=cfg["model"],
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": context},  # same for every item of a benchmark, so it is cached
            {"type": "input_text", "text": question_text},
        ]}],
        text={"format": {"type": "json_schema", "name": "answer", "strict": True, "schema": SCHEMA}},
        prompt_cache_key=f"policy-labels-{benchmark}",
    )
    if cfg.get("prompt_cache_options"):  # GPT-5.6+ caching controls; extra_body works on any SDK version
        request["extra_body"] = {"prompt_cache_options": cfg["prompt_cache_options"]}
    if cfg.get("effort"):
        request["reasoning"] = {"effort": cfg["effort"]}
    response = await client.responses.create(**request)
    cost = openai_cost(response.usage, cfg["prices"][cfg["model"]])
    # Structured outputs guarantee the schema only for a completed, non-refused answer.
    if response.status != "completed":
        raise ValueError(f"response {response.status}: {response.incomplete_details}")
    return json.loads(response.output_text)["option"], cost


# ---------------------------------------------------------------- main


def write_output(path, rows):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["benchmark", "id", "text", "label"])
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)  # a crash mid-write never leaves a half-written file


async def main():
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    backend = cfg["backend"]
    if backend == "openai":
        from openai import AsyncOpenAI
        load_dotenv(HERE / ".env")
        client = AsyncOpenAI()  # reads OPENAI_API_KEY (and optional OPENAI_BASE_URL)
        if client.api_key == "your-api-key-here":
            raise SystemExit(f"Set OPENAI_API_KEY in {HERE / '.env'}")
        if cfg["model"] not in cfg["prices"]:
            raise SystemExit(f"Add prices for {cfg['model']} to config.yaml")
        ask = lambda b, c, q: ask_openai(cfg, b, c, q, client)
    elif backend == "claude":
        ask = lambda b, c, q: ask_claude(cfg, b, c, q)
    else:
        raise SystemExit(f"backend must be claude or openai, not {backend!r}")
    output = HERE / f"labeled_{backend}.csv"

    question, options = parse_criteria()
    rows, contexts = [], {}
    for benchmark, path in POLICY_FILES.items():
        context = f"Policy document of the {benchmark} agent:\n\n{path.read_text()}"
        if benchmark in EXTRA_CONTEXT:
            context += f"\n\nAPI endpoints available to the agent:\n\n{EXTRA_CONTEXT[benchmark].read_text()}"
        contexts[benchmark] = context
        rows += [{"benchmark": benchmark, "id": i, "text": t, "label": ""} for i, t in parse_policies(path, benchmark)]

    # Items already labeled in the output file are kept as they are and not sent again.
    if output.exists():
        with open(output, newline="", encoding="utf-8") as f:
            done = {(r["benchmark"], r["id"]): r["label"] for r in csv.DictReader(f) if r["label"]}
        for r in rows:
            r["label"] = done.get((r["benchmark"], r["id"]), "")
    todo = [r for r in rows if not r["label"]][: cfg["limit"]]
    print(f"{len(rows) - len([r for r in rows if not r['label']])} policies already in {output.name}; "
          f"labeling {len(todo)} with {backend} ({cfg['model']})")

    sem, run_cost, failures = asyncio.Semaphore(cfg["max_concurrency"]), 0.0, []
    limit_hit = None  # set to Claude's message once the usage limit is reached; no new items start after that

    async def run(row):
        nonlocal run_cost, limit_hit
        q = build_question(row["benchmark"], row["id"], row["text"], question, options)
        async with sem:
            for attempt in range(cfg["max_retries"] + 1):
                if limit_hit:
                    return
                try:
                    option, cost = await ask(row["benchmark"], contexts[row["benchmark"]], q)
                    break
                except UsageLimitError as e:
                    if not limit_hit:
                        print(f"USAGE LIMIT REACHED, not starting more policies: {e}")
                    limit_hit = str(e)
                    return
                except Exception as e:
                    if attempt == cfg["max_retries"]:
                        failures.append((row["benchmark"], row["id"]))
                        print(f"FAILED {row['benchmark']} {row['id']}: {e!r}")
                        return
                    await asyncio.sleep(5 * 2**attempt)  # back off, e.g. on a rate limit
            run_cost += cost
            row["label"] = options["AB".index(option)][0]
            write_output(output, rows)
            print(f"{row['benchmark']} [{row['id']}] {row['label']}  (run total ${run_cost:.4f})")

    await asyncio.gather(*(run(r) for r in todo))
    write_output(output, rows)
    note = " API-equivalent, billed to your subscription" if backend == "claude" else ""
    print(f"Wrote {output}. Run cost: ${run_cost:.4f}{note}")
    if failures:
        print(f"{len(failures)} policies failed; re-run to retry them: {failures}")
    if limit_hit:
        left = len([r for r in todo if not r["label"]])
        print(f"Stopped at the usage limit with {left} policies left. Finished labels are saved; "
              f"run this script again after the limit resets to label the rest.\nClaude said: {limit_hit}")


if __name__ == "__main__":
    asyncio.run(main())

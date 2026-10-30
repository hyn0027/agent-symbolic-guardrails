"""Label every ID-ed policy item of the three benchmarks as out of scope or not, following criteria.csv.

Each item is asked in its own call, with the benchmark's whole policy document as context
(plus api_endpoints.md for MedAgentBench). The document comes first in every call, so it is
served from OpenAI's prompt cache after the first item of a benchmark.

Usage: python label_pipeline.py   (settings in config.yaml, API key in .env)
"""

import asyncio
import csv
import json
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "labeled.csv"
POLICY_FILES = {
    "CarBench": HERE.parent / "CarBench" / "policies.md",
    "MedAgentBench": HERE.parent / "MedAgentBench" / "policy.md",
    "tau2-airline": HERE.parent / "tau2-airline" / "policy.md",
}
EXTRA_CONTEXT = {"MedAgentBench": HERE / "api_endpoints.md"}  # the APIs the MedAgentBench agent can call
MEDAGENTBENCH_ONLY = "(MedAgentBench only)"

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


def call_cost(usage, prices):
    """USD cost of one API call from its usage and the per-1M-token prices in config.yaml."""
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


async def ask(client, cfg, benchmark, context, question_text):
    """Return (option letter, cost); cost also counts attempts that were retried."""
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
    if cfg.get("reasoning_effort"):
        request["reasoning"] = {"effort": cfg["reasoning_effort"]}

    cost = 0.0
    for attempt in range(cfg["max_retries"] + 1):
        try:
            response = await client.responses.create(**request)
            cost += call_cost(response.usage, cfg["prices"][cfg["model"]])
            # Structured outputs guarantee the schema only for a completed, non-refused answer.
            if response.status != "completed":
                raise ValueError(f"response {response.status}: {response.incomplete_details}")
            return json.loads(response.output_text)["option"], cost
        except Exception:
            if attempt == cfg["max_retries"]:
                raise
            await asyncio.sleep(5 * 2**attempt)


def write_output(rows):
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["benchmark", "id", "text", "label"])
        writer.writeheader()
        writer.writerows(rows)


async def main():
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    if cfg["model"] not in cfg["prices"]:
        raise SystemExit(f"Add prices for {cfg['model']} to config.yaml")
    load_dotenv(HERE / ".env")
    client = AsyncOpenAI()  # reads OPENAI_API_KEY (and optional OPENAI_BASE_URL)
    if client.api_key == "your-api-key-here":
        raise SystemExit(f"Set OPENAI_API_KEY in {HERE / '.env'}")

    question, options = parse_criteria()
    rows, contexts = [], {}
    for benchmark, path in POLICY_FILES.items():
        context = f"Policy document of the {benchmark} agent:\n\n{path.read_text()}"
        if benchmark in EXTRA_CONTEXT:
            context += f"\n\nAPI endpoints available to the agent:\n\n{EXTRA_CONTEXT[benchmark].read_text()}"
        contexts[benchmark] = context
        rows += [{"benchmark": benchmark, "id": i, "text": t, "label": ""} for i, t in parse_policies(path, benchmark)]

    # Items already labeled in labeled.csv are kept as they are and not sent again.
    if OUTPUT.exists():
        with open(OUTPUT, newline="", encoding="utf-8") as f:
            done = {(r["benchmark"], r["id"]): r["label"] for r in csv.DictReader(f) if r["label"]}
        for r in rows:
            r["label"] = done.get((r["benchmark"], r["id"]), "")
    todo = [r for r in rows if not r["label"]][: cfg["limit"]]
    print(f"{len(rows) - len([r for r in rows if not r['label']])} policies already labeled; "
          f"labeling {len(todo)} with {cfg['model']}")

    sem, run_cost, failures = asyncio.Semaphore(cfg["max_concurrency"]), 0.0, []

    async def run(row):
        nonlocal run_cost
        async with sem:
            try:
                q = build_question(row["benchmark"], row["id"], row["text"], question, options)
                option, cost = await ask(client, cfg, row["benchmark"], contexts[row["benchmark"]], q)
            except Exception as e:
                failures.append((row["benchmark"], row["id"]))
                print(f"FAILED {row['benchmark']} {row['id']}: {e!r}")
                return
            run_cost += cost
            row["label"] = options["AB".index(option)][0]
            write_output(rows)
            print(f"{row['benchmark']} [{row['id']}] {row['label']}  (run total ${run_cost:.4f})")

    await asyncio.gather(*(run(r) for r in todo))
    write_output(rows)
    print(f"Wrote {OUTPUT}. Run cost: ${run_cost:.4f}")
    if failures:
        print(f"{len(failures)} policies failed; re-run to retry them: {failures}")


if __name__ == "__main__":
    asyncio.run(main())

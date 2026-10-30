"""Label every paper in "working sheet.csv" by following steps 2-6 of criteria.csv.

Usage: python label_pipeline.py   (settings in config.yaml, API key in .env)
"""

import asyncio
import csv
import json
import re
import string
from datetime import datetime
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI

HERE = Path(__file__).resolve().parent
PDF_DIR = HERE / "pdfs"
OUTPUT = HERE / "labeled.csv"
COST_LOG = HERE / "costs.csv"  # one row per labeled paper, appended across runs
DROPPED_COLUMNS = {"notes", "policy example"}  # working-sheet columns left out of labeled.csv
STEP_COLUMNS = {
    2: "tool-use llm-agent",
    3: "safety/security",
    4: "out of scope",
    5: "domain",
    6: "policy",
}

SYSTEM_PROMPT = (
    "You are labeling research papers for a systematic literature review of benchmarks. "
    "The full text of the paper is attached as a PDF. Answer the question by choosing exactly "
    "one of the given options, applying the option definitions exactly as written."
)


def parse_criteria():
    """{step: {"question", "options": [{label, action, definition, why}]}} from criteria.csv."""
    steps, current = {}, None
    with open(HERE / "criteria.csv", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            m = re.match(r"^(\d+)\.", row["Instructions"].strip())
            if m:
                current = steps[int(m.group(1))] = {"question": row["Instructions"].strip(), "options": []}
            if current is None or not row["label"].strip():
                continue
            definition = row["definition"].strip()
            why = re.match(r'^\("why out of scope":\s*(.*?)\)', definition)
            current["options"].append({
                "label": row["label"].strip(),
                # an empty action inherits the action of the option above it
                "action": row["action"].strip() or current["options"][-1]["action"],
                "definition": definition,
                "why": why.group(1) if why else "",
            })
    # The duplicate check needs other papers' context, so leave it to a human.
    steps[4]["options"] = [o for o in steps[4]["options"] if o["why"] != "duplicated"]
    return steps


def step_prompt(step):
    letters = string.ascii_uppercase[: len(step["options"])]
    lines = ["Question:", step["question"], "", "Options (choose exactly one):"]
    for letter, o in zip(letters, step["options"]):
        lines += [f"{letter}. label: {o['label']}", f"   definition: {o['definition']}"]
    return "\n".join(lines)


def answer_schema(n_letters):
    # The same schema is used for every step: the schema is part of the cached prompt prefix,
    # so changing it between steps would invalidate OpenAI's prompt cache.
    props = {
        # asked before the option so the model justifies its choice first; not saved
        "reasoning": {"type": "string", "description": "1-3 sentence justification citing the paper."},
        "option": {"type": "string", "enum": list(string.ascii_uppercase[:n_letters])},
    }
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


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


async def ask(client, cfg, row, content, schema, n_options, previous_response_id):
    """Send one user message, continuing the paper's conversation, and return the response.

    previous_response_id makes OpenAI reuse the earlier turns (PDF, questions, answers and
    reasoning) server-side; the shared prefix is served from OpenAI's prompt cache.
    Returns (response, cost), where cost also counts attempts that were retried.
    """
    request = dict(
        model=cfg["model"],
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": content}],
        previous_response_id=previous_response_id,
        store=True,  # required for later steps to continue from this response
        text={"format": {"type": "json_schema", "name": "answer", "strict": True, "schema": schema}},
        prompt_cache_key=f"major-revision-{row['rand id']}",
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
            answer = json.loads(response.output_text)
            if string.ascii_uppercase.index(answer["option"]) >= n_options:
                raise ValueError(f"option {answer['option']} is not one of this step's options")
            return response, cost
        except Exception:
            if attempt == cfg["max_retries"]:
                raise
            await asyncio.sleep(5 * 2**attempt)


async def label_paper(client, cfg, steps, row, file_id):
    """Ask steps 2-6 in one conversation, each step continuing from the previous answer."""
    labels = {}
    schema = answer_schema(max(len(s["options"]) for s in steps.values()))
    previous_id = None
    input_tokens = cached_tokens = 0
    total_cost = 0.0
    step_no = 2  # step 1 (does the paper propose a benchmark?) is skipped
    while step_no:
        step = steps[step_no]
        content = [{"type": "input_text", "text": step_prompt(step)}]
        if previous_id is None:  # first message carries the PDF and title
            content = [
                {"type": "input_file", "file_id": file_id},
                {"type": "input_text", "text": f"Paper title: {row['Title']}"},
            ] + content
        response, cost = await ask(client, cfg, row, content, schema, len(step["options"]), previous_id)
        previous_id = response.id
        total_cost += cost
        input_tokens += response.usage.input_tokens
        cached_tokens += response.usage.input_tokens_details.cached_tokens

        answer = json.loads(response.output_text)
        opt = step["options"][string.ascii_uppercase.index(answer["option"])]
        labels[STEP_COLUMNS[step_no]] = opt["label"]
        if opt["why"]:
            labels["why out of scope"] = opt["why"]
        m = re.match(r"Proceed to Step (\d+)", opt["action"])
        step_no = int(m.group(1)) if m else None
    return labels, input_tokens, cached_tokens, total_cost


async def get_pdf(http, row, sem):
    path = PDF_DIR / f"{row['rand id']}.pdf"
    if not path.exists():
        async with sem:  # be polite to arXiv
            resp = await http.get(row["Link"], follow_redirects=True, timeout=120)
            resp.raise_for_status()
            if resp.content[:4] != b"%PDF":
                raise ValueError(f"{row['Link']} did not return a PDF")
            path.write_bytes(resp.content)
            await asyncio.sleep(1)
    return path


def write_output(header, rows, done):
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            labels = done.get(row["rand id"], {})
            writer.writerow([labels.get(col, row[col]) for col in header])


async def main():
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    if cfg["model"] not in cfg["prices"]:
        raise SystemExit(f"Add prices for {cfg['model']} to config.yaml")
    load_dotenv(HERE / ".env")
    client = AsyncOpenAI()  # reads OPENAI_API_KEY (and optional OPENAI_BASE_URL)
    if client.api_key == "your-api-key-here":
        raise SystemExit(f"Set OPENAI_API_KEY in {HERE / '.env'}")

    steps = parse_criteria()
    with open(HERE / "working sheet.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [dict(zip(header, r)) for r in reader]
    header = [c for c in header if c not in DROPPED_COLUMNS]

    PDF_DIR.mkdir(exist_ok=True)
    # Papers already labeled in labeled.csv are kept as they are and not sent again.
    # A paper counts as labeled once its first asked column (step 2) is filled.
    done = {}
    if OUTPUT.exists():
        with open(OUTPUT, newline="", encoding="utf-8") as f:
            done = {r["rand id"]: r for r in csv.DictReader(f) if r[STEP_COLUMNS[2]].strip()}
    todo = [r for r in rows if r["rand id"] not in done]
    if cfg.get("only_rand_ids"):  # only (re-)label these papers
        todo = [r for r in todo if r["rand id"] in set(map(str, cfg["only_rand_ids"]))]
    todo = todo[: cfg["limit"]]
    print(f"{len(done)} papers already in {OUTPUT.name}; labeling {len(todo)} with {cfg['model']}")

    paper_sem, download_sem = asyncio.Semaphore(cfg["max_concurrency"]), asyncio.Semaphore(2)
    failures, finished = [], 0
    run_cost = 0.0
    if not COST_LOG.exists():
        COST_LOG.write_text("time,rand id,title,model,input tokens,cached tokens,cost usd\n")

    async with httpx.AsyncClient(headers={"User-Agent": "paper-labeling-pipeline"}) as http:

        async def run(row):
            async with paper_sem:
                try:
                    pdf = await get_pdf(http, row, download_sem)
                    with open(pdf, "rb") as f:
                        file_id = (await client.files.create(file=f, purpose="user_data")).id
                    labels, input_tokens, cached, cost = await label_paper(client, cfg, steps, row, file_id)
                except Exception as e:
                    failures.append(row["rand id"])
                    print(f"FAILED {row['rand id']} {row['Title'][:60]}: {e!r}")
                    return
                nonlocal run_cost, finished
                run_cost += cost
                finished += 1
                done[row["rand id"]] = labels
                write_output(header, rows, done)
                with open(COST_LOG, "a", newline="") as f:
                    csv.writer(f).writerow([datetime.now().isoformat(timespec="seconds"), row["rand id"],
                                            row["Title"], cfg["model"], input_tokens, cached, f"{cost:.6f}"])
                print(f"[{finished}/{len(todo)}] {row['Title'][:60]} "
                      f"(input tokens: {input_tokens}, cached: {cached}, ${cost:.4f}; run total ${run_cost:.4f})")

        await asyncio.gather(*(run(r) for r in todo))

    write_output(header, rows, done)
    print(f"Wrote {OUTPUT}. Run cost: ${run_cost:.4f} (labeled papers only; failed papers are not counted)")
    if failures:
        print(f"{len(failures)} papers failed; re-run to retry them: {failures}")


if __name__ == "__main__":
    asyncio.run(main())

"""Label papers in "working sheet.csv" following steps 2-6 of criteria.csv, with Claude Code or the OpenAI API.

Both backends get the same prompt and answer format. Each paper is one request: the model reads the full paper PDF
and answers every step, giving evidence and a short note per step. A step's label is kept if the human reached that
step (in human_label_1.csv) or the model's own answers lead to it, so both can be compared. Results go to labeled.csv.

  backend: claude   one headless `claude -p` session per paper; Claude reads pdfs/<id>.pdf with its Read tool.
                    Uses your Claude subscription (run where `claude` is logged in).
  backend: openai   one Responses API call per paper with the PDF attached. Needs OPENAI_API_KEY in .env.

Usage: python label.py   (settings in config.yaml)
"""

import asyncio
import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
SHEET = HERE / "working sheet.csv"
HUMAN = HERE / "human_label_1.csv"  # only the steps the human labeled are asked, so every answer can be compared
OUTPUT = HERE / "labeled.csv"
COST_LOG = HERE / "costs.csv"  # one row per labeled paper, appended across runs
PDF_DIR = HERE / "pdfs"
STEP_COLUMNS = {2: "tool-use llm-agent", 3: "safety/security", 4: "out of scope", 5: "domain", 6: "policy"}
# A note admitting the paper was not actually read (the answer would rest on the title only): retry the paper
NOT_READ = re.compile(r"unverified|did not read|could not read|couldn't read|unable to read|pdf (was |is )?unreadable|"
                      r"could not (access|open|check) the (pdf|paper)|pdf could not be read|as a placeholder|re-run with the paper", re.I)
# Claude Code's messages when the subscription's usage limit is reached (it resets after some hours)
USAGE_LIMIT = re.compile(r"usage limit|limit reached|hit your .{0,20}limit|limit (will )?resets?|resets? at|out of .{0,10}usage", re.I)

# How each backend gets the paper into the prompt; everything else in the prompt is shared.
PAPER_SOURCE = {
    "claude": "Read the full paper at {pdf} with the Read tool (read it in page ranges until you have covered the whole "
              "paper, including appendices).",
    "openai": "The full paper is attached as a PDF; read all of it, including appendices.",
}

INSTRUCTIONS = """You are labeling a research paper for a systematic literature review of benchmarks.
{paper_source} Then answer every question below, Step 2 to Step {last}.

For each step, choose exactly one option, applying the option definitions exactly as written. Answer every step
on its own, even if your answer to an earlier step would normally end the labeling there (for example, a "no" in an
earlier step): answer each later step as if the paper had reached it.

For each step, fill in the fields in order, deciding only after the evidence:
1. evidence: a short verbatim quote from the paper that the decision rests on, with where it is (section, figure,
   table, or appendix). Use "none found" if the paper has nothing relevant.
2. note: 1-3 sentences explaining how the evidence leads to the choice.
3. answer: the option.
{step6_checklist}
Paper title: {title}

{steps}
"""

STEP6_CHECKLIST = """
For Step 6, work through these in order before answering:
a. Find and quote every instruction the evaluated agent receives about how to behave safely or securely.
b. For each one, check it against the Step 6 definition of what counts as a policy.
c. For those that count, decide whether they apply across tasks or to a single task.
d. Compare them with each option's definition, then choose the option that fits.
"""


class UsageLimitError(Exception):
    pass


# ---------------------------------------------------------------- criteria, prompt, answers (shared)


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
                "label": row["label"].strip(), "definition": definition, "why": why.group(1) if why else "",
                # an empty action inherits the action of the option above it
                "action": row["action"].strip() or (current["options"][-1]["action"] if current["options"] else ""),
            })
    # The duplicate check needs other papers' context, so leave it to a human.
    steps[4]["options"] = [o for o in steps[4]["options"] if o["why"] != "duplicated"]
    return steps


def option_name(o):
    return f"{o['label']} ({o['why']})" if o["why"] else o["label"]


def build_prompt(backend, steps, row, last):
    blocks = []
    for n in range(2, last + 1):
        lines = [f"Step {n}:", steps[n]["question"], "Options:"]
        for o in steps[n]["options"]:
            lines += [f"- \"{option_name(o)}\"", f"  definition: {o['definition']}"]
        blocks.append("\n".join(lines))
    return INSTRUCTIONS.format(
        paper_source=PAPER_SOURCE[backend].format(pdf=f"pdfs/{row['rand id']}.pdf"), last=last,
        step6_checklist=STEP6_CHECKLIST if last == 6 else "", title=row["Title"], steps="\n\n".join(blocks))


def answer_schema(steps, last):
    props = {}
    for n in range(2, last + 1):
        props[f"step{n}"] = {
            "type": "object",
            # evidence and note come before the answer so the choice follows the evidence
            "properties": {
                "evidence": {"type": "string"},
                "note": {"type": "string"},
                "answer": {"type": "string", "enum": [option_name(o) for o in steps[n]["options"]]},
            },
            "required": ["evidence", "note", "answer"],
            "additionalProperties": False,
        }
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def to_labels(steps, answer, human_last):
    """Keep a step's label if the human reached that step or the model's own answers lead to it (Proceed/Stop rules)."""
    chosen = {}
    for n in STEP_COLUMNS:
        step = answer[f"step{n}"]
        opt = next((o for o in steps[n]["options"] if option_name(o) == step["answer"]), None)
        if opt is None:
            raise ValueError(f"step {n} answered {step['answer']!r}")
        chosen[n] = opt
    model_reached, n = set(), 2
    while n:
        model_reached.add(n)
        m = re.match(r"Proceed to Step (\d+)", chosen[n]["action"])
        n = int(m.group(1)) if m else None
    labels, notes = {}, []
    for n in STEP_COLUMNS:
        if n > human_last and n not in model_reached:
            continue
        opt, step = chosen[n], answer[f"step{n}"]
        labels[STEP_COLUMNS[n]] = opt["label"]
        if opt["why"]:
            labels["why out of scope"] = opt["why"]
        notes.append(f"[Step {n}: {opt['label']}] {step['note']} Evidence: {step['evidence']}")
    labels["notes"] = "\n".join(notes)
    return labels


# ---------------------------------------------------------------- backends: return (answer dict, cost, tokens)


async def ask_claude(cfg, row, prompt, schema):
    cmd = [
        "claude", "-p", prompt,
        "--model", cfg["model"], "--effort", cfg["effort"],
        "--output-format", "json", "--json-schema", json.dumps(schema),
        "--restricted", "--tools", "Read", "--allowedTools", "Read", "--strict-mcp-config",
        "--no-session-persistence",
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
    usage = result.get("usage") or {}
    tokens = (usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
              + usage.get("cache_creation_input_tokens", 0), usage.get("cache_read_input_tokens", 0))
    return result["structured_output"], result.get("total_cost_usd") or 0.0, tokens


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


async def ask_openai(cfg, row, prompt, schema, client):
    with open(PDF_DIR / f"{row['rand id']}.pdf", "rb") as f:
        file_id = (await client.files.create(file=f, purpose="user_data")).id
    request = dict(
        model=cfg["model"],
        input=[{"role": "user", "content": [
            {"type": "input_file", "file_id": file_id},
            {"type": "input_text", "text": prompt},
        ]}],
        text={"format": {"type": "json_schema", "name": "labels", "strict": True, "schema": schema}},
    )
    if cfg.get("effort"):
        request["reasoning"] = {"effort": cfg["effort"]}
    if cfg.get("prompt_cache_options"):  # GPT-5.6+ caching controls; extra_body works on any SDK version
        request["extra_body"] = {"prompt_cache_options": cfg["prompt_cache_options"]}
    response = await client.responses.create(**request)
    cost = openai_cost(response.usage, cfg["prices"][cfg["model"]])
    # Structured outputs guarantee the schema only for a completed, non-refused answer.
    if response.status != "completed":
        raise RuntimeError(f"response {response.status}: {response.incomplete_details}")
    tokens = (response.usage.input_tokens, response.usage.input_tokens_details.cached_tokens or 0)
    return json.loads(response.output_text), cost, tokens


# ---------------------------------------------------------------- papers, output, main (shared)


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


def write_output(header, rows, done):
    # write to a temporary file and swap it in, so an interrupted run never leaves a half-written labeled.csv
    tmp = OUTPUT.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            labels = done.get(row["rand id"], {})
            writer.writerow([labels.get(col, row[col]) for col in header])
    os.replace(tmp, OUTPUT)


def choose_papers(cfg, rows, done, no_benchmark):
    """Papers not labeled yet, in the order of the sheet; at most `limit` per run (null = all).

    Papers the human labeled "No" at step 1 (no benchmark proposed) are never labeled.
    """
    todo = [r for r in rows if r["rand id"] not in done and r["rand id"] not in no_benchmark]
    return todo[: cfg.get("limit")]


async def main():
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    backend = cfg["backend"]
    if backend == "openai":
        from openai import AsyncOpenAI
        load_dotenv(HERE / ".env")
        client = AsyncOpenAI()  # reads OPENAI_API_KEY (and optional OPENAI_BASE_URL)
        if cfg["model"] not in cfg["prices"]:
            raise SystemExit(f"Add prices for {cfg['model']} to config.yaml")
        ask = lambda row, prompt, schema: ask_openai(cfg, row, prompt, schema, client)
    elif backend == "claude":
        ask = lambda row, prompt, schema: ask_claude(cfg, row, prompt, schema)
    else:
        raise SystemExit(f"backend must be claude or openai, not {backend!r}")

    steps = parse_criteria()
    with open(SHEET, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [dict(zip(header, r)) for r in reader]
    # Papers already labeled in labeled.csv are kept as they are and not sent again.
    done = {}
    if OUTPUT.exists():
        with open(OUTPUT, newline="", encoding="utf-8") as f:
            done = {r["rand id"]: r for r in csv.DictReader(f) if r[STEP_COLUMNS[2]].strip()}
    # The last step the human labeled per paper (0 if none); a step is kept if the human or the model reaches it.
    with open(HUMAN, newline="", encoding="utf-8-sig") as f:
        human = {r["random id"]: r for r in csv.DictReader(f)}
    last_step = {r["rand id"]: max([n for n, c in STEP_COLUMNS.items() if human.get(r["rand id"], {}).get(c, "").strip()],
                                   default=0) for r in rows}
    no_benchmark = {i for i, r in human.items() if r.get("propose dataset", "").strip().lower() == "no"}
    todo = choose_papers(cfg, rows, done, no_benchmark)
    print(f"{len(done)} papers already in {OUTPUT.name}; labeling {len(todo)} with {backend} ({cfg['model']})")

    PDF_DIR.mkdir(exist_ok=True)
    if not COST_LOG.exists():
        COST_LOG.write_text("time,rand id,title,model,input tokens,cached tokens,cost usd\n")
    sem, download_sem = asyncio.Semaphore(cfg["max_concurrency"]), asyncio.Semaphore(2)
    failures, finished, run_cost = [], 0, 0.0
    limit_hit = None  # set to Claude's message once the usage limit is reached; no new papers start after that

    async with httpx.AsyncClient(headers={"User-Agent": "paper-labeling-pipeline"}) as http:

        async def run(row):
            nonlocal finished, run_cost, limit_hit
            last = last_step[row["rand id"]]
            # every step is asked; to_labels keeps the ones the human or the model's own answers reach
            prompt, schema = build_prompt(backend, steps, row, 6), answer_schema(steps, 6)
            async with sem:
                for attempt in range(cfg["max_retries"] + 1):
                    if limit_hit:
                        return
                    try:
                        await get_pdf(http, row, download_sem)
                        answer, cost, (input_tokens, cached) = await ask(row, prompt, schema)
                        run_cost += cost
                        if NOT_READ.search(json.dumps(answer)):
                            raise RuntimeError("the paper was not read (the answer says so); retrying")
                        labels = to_labels(steps, answer, last)
                        break
                    except UsageLimitError as e:
                        if not limit_hit:
                            print(f"USAGE LIMIT REACHED, not starting more papers: {e}")
                        limit_hit = str(e)
                        return
                    except Exception as e:
                        if attempt == cfg["max_retries"]:
                            failures.append(row["rand id"])
                            print(f"FAILED {row['rand id']} {row['Title'][:60]}: {e!r}")
                            return
                        await asyncio.sleep(60 * 2**attempt)  # back off, e.g. on a rate limit
                finished += 1
                done[row["rand id"]] = labels
                write_output(header, rows, done)
                with open(COST_LOG, "a", newline="") as f:
                    csv.writer(f).writerow([datetime.now().isoformat(timespec="seconds"), row["rand id"], row["Title"],
                                            cfg["model"], input_tokens, cached, f"{cost:.6f}"])
                print(f"[{finished}/{len(todo)}] {row['Title'][:60]}  ({labels.get('policy') or labels[STEP_COLUMNS[2]]}; "
                      f"${cost:.2f})")

        await asyncio.gather(*(run(r) for r in todo))

    write_output(header, rows, done)
    note = " API-equivalent, billed to your subscription" if backend == "claude" else ""
    print(f"Wrote {OUTPUT}. Cost of this run: ${run_cost:.2f}{note}")
    if failures:
        print(f"{len(failures)} papers failed; re-run to retry them: {failures}")
    if limit_hit:
        left = len([r for r in todo if r["rand id"] not in done])
        print(f"Stopped at the usage limit with {left} papers left. Finished labels are saved; "
              f"run this script again after the limit resets to label the rest.\nClaude said: {limit_hit}")


if __name__ == "__main__":
    asyncio.run(main())

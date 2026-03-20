"""Search arXiv papers with explicit keyword and date constraints.

Requirements:
1) title/abstract contains benchmark or dataset
2) title/abstract contains safety/security/policy terms
3) title/abstract contains agent
4) published year >= 2022
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, List

import arxiv

logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_handler)
logger.setLevel(logging.INFO)


def _arxiv_id_from_entry_id(entry_id: str) -> str:
    # entry_id usually looks like http://arxiv.org/abs/2401.01234v2
    raw_id = entry_id.rsplit("/abs/", maxsplit=1)[-1]
    # Semantic Scholar ARXIV IDs are more reliable without version suffixes.
    return re.sub(r"v\d+$", "", raw_id)


def search_papers(max_results: int = 200) -> List[Dict]:
    """Return filtered arXiv papers sorted by citation count (highest first)."""
    query = (
        "(cat:cs.AI OR cat:cs.CL OR cat:cs.LG) AND "
        "(NOT cat:cs.RO) AND "
        "(ti:bench OR abs:bench OR ti: benchmark OR abs: benchmark OR ti:dataset OR abs:dataset OR ti:framework OR abs:framework) AND "
        "(ti:safety OR abs:safety OR ti:security OR abs:security OR ti:policy OR abs:policy OR ti:risk OR abs:risk OR ti: attack OR abs: attack OR ti:privacy OR abs:privacy OR ti:confidentiality OR abs:confidentiality) AND "
        "(ti:agent OR abs:agent) AND "
        "(NOT abs:robot) AND (NOT abs:self-driving) AND (NOT abs:embodied) AND (NOT abs:reinforcement) AND "
        "(NOT ti:robot) AND (NOT ti:self-driving) AND (NOT ti:embodied) AND (NOT ti:reinforcement) AND "
        "(submittedDate:[202201010000 TO 202603100000])"
    )

    logger.info("Starting arXiv search (max_results=%d)", max_results)
    search = arxiv.Search(query=query, max_results=max_results * 2)
    client = arxiv.Client()

    candidates: List[Dict] = []
    seen_ids: set = set()
    for paper in client.results(search):
        if paper.entry_id in seen_ids:
            continue
        seen_ids.add(paper.entry_id)

        must_be_in_title = ["bench", "dataset", "eval", "assess"]
        if not any(keyword in paper.title.lower() for keyword in must_be_in_title):
            continue

        candidates.append(
            {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "published": paper.published,
                "summary": paper.summary,
                "pdf_url": paper.pdf_url,
                "entry_id": paper.entry_id,
                "citation_count": None,
                # Temporary key used for async citation fetching.
                "_arxiv_id": _arxiv_id_from_entry_id(paper.entry_id),
                "categories": paper.categories,
            }
        )
    logger.info(f"Paper count before filtering: {len(seen_ids)}")
    logger.info(
        "Finished arXiv search. Found %d unique papers.",
        len(candidates),
    )
    return candidates[:max_results]


if __name__ == "__main__":
    papers = search_papers(max_results=5000)

    # for paper in papers:
    #     print(f"Title: {paper['title']}")
    #     print(f"Citations: {paper['citation_count']}")
    #     print(f"Authors: {', '.join(paper['authors'])}")
    #     print(f"Published: {paper['published']}")
    #     print(f"Summary: {paper['summary'][:200]}...")
    #     print(f"PDF URL: {paper['pdf_url']}")
    #     print("-" * 80)

    # save to JSONL file
    with open("filtered_papers.json", "w") as f:
        json.dump(papers, f, indent=2, default=str, ensure_ascii=False)

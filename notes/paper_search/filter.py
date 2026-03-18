import json
import os
import asyncio
import random
from openai import AsyncOpenAI


async def llm_annotate_papers(papers) -> list:
    client = AsyncOpenAI()
    model = "gpt-5-nano"
    system_prompt = (
        "You are an assistant that helps user filter papers based on their title and abstract. "
        "For the paper title and abstract, you will determine whether the paper propose a benchmark or dataset. "
        "If the paper propose a benchmark or dataset, you will return 1, otherwise, you will return 0. "
        "If you are unsure about the paper, you will return -1.\n"
        "You should output a single number (1, 0, or -1) without any explanation or additional text."
    )
    user_prompt = "Title: {title}\nAbstract: {abstract}\n"

    MAX_CONCURRENCY = 30

    async def process_paper(paper) -> str:
        title = paper["title"]
        abstract = paper["summary"]
        prompt = (
            system_prompt + "\n" + user_prompt.format(title=title, abstract=abstract)
        )

        response = await client.responses.create(
            model=model,
            input=prompt,
            prompt_cache_key="prompt_cache_key_filter_paper_hyn",
        )
        return response.output_text.strip()

    async def process_one(paper, sem):
        async with sem:
            try:
                result = await process_paper(paper)
            except Exception:
                result = "-1"
            paper["result"] = result
            return paper

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [process_one(paper, sem) for paper in papers]
    return await asyncio.gather(*tasks)


def print_paper_info(paper) -> None:
    title = paper["title"]
    abstract = paper["summary"]
    paper_info = f"\033[91mTitle:\033[0m {title}\n\033[91mAbstract:\033[0m {abstract}\n"
    for keyword in [
        "agent",
        "bench",
        "dataset",
        "framework",
        "propose",
        "eval",
        "assess",
    ]:
        # change to red color regardless of case
        paper_info = paper_info.replace(keyword, f"\033[91m{keyword}\033[0m")
        paper_info = paper_info.replace(
            keyword.capitalize(), f"\033[91m{keyword.capitalize()}\033[0m"
        )

    print(paper_info)


def human_label(papers, num_label) -> list:

    def request_human_label(paper) -> str:
        if "human_label" in paper:
            return paper["human_label"]
        print_paper_info(paper)
        label = input(
            "Does this paper propose a benchmark or dataset? (1 for yes, 0 for no, -1 for unsure): "
        )
        while label not in ["1", "0", "-1"]:
            label = input(
                "Invalid input. Please enter 1 for yes, 0 for no, or -1 for unsure: "
            )
        return label

    def compute_agreement(papers) -> None:
        # stat test agreement between result and human_label
        from sklearn.metrics import cohen_kappa_score

        pairs = [
            (int(paper["result"]), int(paper["human_label"]))
            for paper in papers
            if "human_label" in paper
        ]
        if not pairs:
            print("No papers have human labels.")
            return
        kappa = cohen_kappa_score(
            [pair[0] for pair in pairs], [pair[1] for pair in pairs]
        )
        print(f"Cohen's kappa: {kappa}")
        print(f"Total papers with human labels: {len(pairs)}")

        confusion_matrix = {
            "TP": sum(1 for pair in pairs if pair[0] == 1 and pair[1] == 1),
            "TN": sum(1 for pair in pairs if pair[0] == 0 and pair[1] == 0),
            "FP": sum(1 for pair in pairs if pair[0] == 1 and pair[1] == 0),
            "FN": sum(1 for pair in pairs if pair[0] == 0 and pair[1] == 1),
        }
        precision = (
            confusion_matrix["TP"] / (confusion_matrix["TP"] + confusion_matrix["FP"])
            if (confusion_matrix["TP"] + confusion_matrix["FP"]) > 0
            else 0
        )
        recall = (
            confusion_matrix["TP"] / (confusion_matrix["TP"] + confusion_matrix["FN"])
            if (confusion_matrix["TP"] + confusion_matrix["FN"]) > 0
            else 0
        )
        f1_score = 2 * (precision * recall) / (precision + recall)
        print(f"Confusion Matrix: {confusion_matrix}")
        print(
            f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1 Score: {f1_score:.2f}"
        )

        ground_truth_positive = sum(1 for pair in pairs if pair[1] == 1)
        ground_truth_negative = sum(1 for pair in pairs if pair[1] == 0)
        print(f"Ground Truth Positive Ratio: {ground_truth_positive / len(pairs):.2f}")
        print(f"Ground Truth Negative Ratio: {ground_truth_negative / len(pairs):.2f}")

        labeled_positive = sum(int(paper["result"]) for paper in papers)
        labeled_negative = sum(1 - int(paper["result"]) for paper in papers)
        print(f"Labeled Positive Ratio: {labeled_positive / len(papers):.2f}")
        print(f"Labeled Negative Ratio: {labeled_negative / len(papers):.2f}")

    unlabeled_paper_idxs = [
        idx for idx, paper in enumerate(papers) if "human_label" not in paper
    ]
    random_ids = random.sample(
        unlabeled_paper_idxs, min(num_label, len(unlabeled_paper_idxs))
    )
    for idx in random_ids:
        paper = papers[idx]
        label = request_human_label(paper)
        paper["human_label"] = label
    compute_agreement(papers)
    return papers


def main() -> None:
    path = "filtered_papers.json"
    with open(path, "r") as f:
        data = json.load(f)

    if os.path.exists("filtered_paper_with_results.json"):
        with open("filtered_paper_with_results.json", "r") as f:
            results = json.load(f)
    else:
        results = asyncio.run(llm_annotate_papers(data))
        with open("filtered_paper_with_results.json", "w") as f:
            json.dump(results, f, indent=4)

    count_res = {}

    for paper in results:
        res = paper["result"]
        count_res[res] = count_res.get(res, 0) + 1
    print(count_res)

    if os.path.exists("human_labeled_papers.json"):
        with open("human_labeled_papers.json", "r") as f:
            results = json.load(f)
    else:
        with open("human_labeled_papers.json", "w") as f:
            json.dump(results, f, indent=4)

    if os.path.exists("human_labeled_papers.json"):
        with open("human_labeled_papers.json", "r") as f:
            results = json.load(f)
        results = human_label(
            results, num_label=0
        )  # print statistics of agreement between human labels and LLM results
    else:
        results = human_label(results, num_label=100)
        with open("human_labeled_papers.json", "w") as f:
            json.dump(results, f, indent=4)

    if os.path.exists("labeled_benchmark_papers.json"):
        with open("labeled_benchmark_papers.json", "r") as f:
            results = json.load(f)
    else:
        labeled_benchmark_papers = [
            paper for paper in results if paper["result"] == "1"
        ]
        with open("labeled_benchmark_papers.json", "w") as f:
            json.dump(labeled_benchmark_papers, f, indent=4)


if __name__ == "__main__":
    main()

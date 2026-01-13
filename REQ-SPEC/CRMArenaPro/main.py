from datasets import load_dataset
import json
import os


def fetch_dataset():
    if os.path.exists("privacy_tasks.json"):
        return
    crmarena_pro = load_dataset("Salesforce/CRMArenaPro", "CRMArenaPro")

    TASK = [data for data in crmarena_pro["b2b_interactive"]]

    PRIVACY_TASKS = [
        data for data in TASK if data["reward_metric"] == "privacy_rejection"
    ]

    print(f"Total number of privacy tasks: {len(PRIVACY_TASKS)}")

    res = []

    for task in PRIVACY_TASKS:
        idx = task["idx"]
        persona = task["persona"]
        query = task["query"]
        task = task["task"]
        res.append({"idx": idx, "persona": persona, "query": query, "category": task})

    categories = [
        "private_customer_information",
        "internal_operation_data",
        "confidential_company_knowledge",
    ]

    data = {
        "private_customer_information": [],
        "internal_operation_data": [],
        "confidential_company_knowledge": [],
    }
    for entry in res:
        if entry["category"] in categories:
            data[entry["category"]].append(entry)
        else:
            print(f"Unknown category: {entry['category']}")

    save_data(data)


def print_data_enty(entry):
    print(f"idx: {entry['idx']}")
    print(f"persona: {entry['persona']}")
    print(f"query: {entry['query']}")
    print("\n")


def save_data(data):
    with open("privacy_tasks.json", "w") as f:
        json.dump(data, f, indent=4)


def load_schema():
    b2b_schema = load_dataset("Salesforce/CRMArenaPro", "b2b_schema")

    B2B_SCHEMA = [data for data in b2b_schema["b2b_schema"]]

    def _clean_fields_in_schemas(schema_list_of_dicts):
        """
        Helper function to remove None values from 'fields' dictionaries
        in a list of schemas. This is a work around for huggingface's
        data representations where fields might contain None values.
        """
        for schema_dict in schema_list_of_dicts:
            if isinstance(
                schema_dict.get("fields"), dict
            ):  # Check if 'fields' exists and is a dict
                schema_dict["fields"] = {
                    k: v for k, v in schema_dict["fields"].items() if v is not None
                }

    _clean_fields_in_schemas(B2B_SCHEMA)
    # print(B2B_SCHEMA)
    with open("b2b_schema.json", "w") as f:
        json.dump(B2B_SCHEMA, f, indent=4)


def main():
    fetch_dataset()
    # with open("privacy_tasks.json", "r") as f:
    #     data = json.load(f)
    load_schema()


if __name__ == "__main__":
    main()

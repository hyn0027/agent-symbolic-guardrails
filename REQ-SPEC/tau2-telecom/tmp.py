import json
import os

FILE_PATH = "spec.json"


def read_json_file(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def save_json_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def add_with_template(template, template_type):
    print("-" * 40)
    print(f"- {template['content']}")
    results = []
    while True:
        proceed = (
            input("Do you want to add another spec with this template? (y/n): ")
            .strip()
            .lower()
        )
        if proceed == "y":
            res = template["content"]
            for param in template.get("parameter", []):
                value = input(f"Please provide value for '{param}': ").strip()
                res = res.replace(f"{{{param}}}", value)
            results.append({"template_type": template_type, "content": res})
        elif proceed == "n":
            break
        else:
            print("Please enter 'y' for yes or 'n' for no.")
    return results


def solution_API_check():
    templates = [
        {
            "content": "API {api} should be blocked with parameters constraint: {params_constraints}",
            "parameter": ["api", "params_constraints"],
        },
        {
            "content": "API {api} should add a check or action: {check_description}",
            "parameter": ["api", "check_description"],
        },
    ]
    results = []
    for template in templates:
        results += add_with_template(template, "API_check")
    return results


def solution_tool_call_sequence():
    templates = [
        {
            "content": "Tool {tool} should not be called in the sequence: {sequence}",
            "parameter": ["tool", "sequence"],
        },
        {
            "content": "Tool {tool} must be called in the sequence: {sequence}",
            "parameter": ["tool", "sequence"],
        },
    ]
    results = []
    for template in templates:
        results += add_with_template(template, "tool_call_sequence")
    return results


def solution_variable_masking():
    templates = [
        {
            "content": "Variable {variable} should be masked from the LLM",
            "parameter": ["variable"],
        }
    ]
    results = []
    for template in templates:
        results += add_with_template(template, "variable_masking")
    return results


def solution_API_redesign():
    templates = [
        {
            "content": "API {api} should be redesigned as {new_design}",
            "parameter": ["api", "new_design"],
        }
    ]
    results = []
    for template in templates:
        results += add_with_template(template, "API_redesign")
    return results


def solution_system_design():
    templates = [
        {
            "content": "The system should be designed to {design_goal}",
            "parameter": ["design_goal"],
        }
    ]
    results = []
    for template in templates:
        results += add_with_template(template, "system_design")
    return results


def process_item(item):
    if "tag" in item:
        return item
    print("*" * 40)
    print((f"Requirement: {item['content']}"))
    while True:
        not_applicable = input("Is this a requirement? (y/n): ").strip().lower()
        if not_applicable == "n":
            item["tag"] = "not_applicable"
            return item
        elif not_applicable == "y":
            break
        else:
            print("Please enter 'y' for yes or 'n' for no.")

    if "spec" not in item:
        item["spec"] = []

    item["spec"] += solution_API_check()
    item["spec"] += solution_tool_call_sequence()
    item["spec"] += solution_variable_masking()
    item["spec"] += solution_API_redesign()
    item["spec"] += solution_system_design()

    while True:
        enforcable = (
            input(f"Is the requirement '{item['content']}' enforcable? (y/n): ")
            .strip()
            .lower()
        )
        if enforcable in ["y", "n"]:
            break
        else:
            print("Please enter 'y' for yes or 'n' for no.")

    item["tag"] = "enforcable" if enforcable == "y" else "not_enforcable"
    return item


def main():
    spec = read_json_file(FILE_PATH)
    spec = [item for item in spec if item.get("content", "").strip() != ""]
    for index, item in enumerate(spec):
        processed_item = process_item(item)
        spec[index] = processed_item
        save_json_file(FILE_PATH, spec)


def generate_python():
    with open("main_policy.md", "r") as f:
        content_by_line = f.readlines()
    res = []
    for i, line in enumerate(content_by_line):
        if line.strip() != "":
            res.append({"line_number": i + 1, "content": line.strip()})
    save_json_file(FILE_PATH, res)


if __name__ == "__main__":
    # generate_python()
    main()

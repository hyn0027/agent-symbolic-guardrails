import json
import requests

file_path = "test_data_v2.json"

with open(file_path, "r") as f:
    data = json.load(f)


for item in data:
    if item["id"].startswith("task1_"):  # already have name and dob
        continue

    # add name and dob
    mrn = item["eval_MRN"]
    url = "http://127.0.0.1:8080/fhir/Patient/" + mrn
    response = requests.get(url)
    family_name = response.json().get("name", [{}])[0].get("family", "N/A")
    given_name = response.json().get("name", [{}])[0].get("given", ["N/A"])[0]
    dob = response.json().get("birthDate", "N/A")
    item["context"] = (
        item.get("context", "")
        + f" The patient's name is {given_name} {family_name}. The patient's date of birth is {dob}."
    )

    # ammend task 10 for formatting instruction
    if item["id"].startswith("task10_"):
        item["instruction"] = (
            item.get("instruction", "")
            + ' Respond your answer as "last_value, last_time", where last_value is a numerical value and last_time is a iso format time string. If no recent potassium value, respond with "-1, N/A".'
        )
        item["context"] = item["context"].replace("[-1]", '"-1, N/A"')

# write
with open("test_data_v2_augmented.json", "w") as f:
    json.dump(data, f, indent=4)

---
configs:
  # ── Tasks ──────────────────────────────────────────────────────────────
  - config_name: tasks_base
    default: true
    data_files:
      - split: train
        path: "tasks/base_train.jsonl"
      - split: test
        path: "tasks/base_test.jsonl"
  - config_name: tasks_disambiguation
    data_files:
      - split: train
        path: "tasks/disambiguation_train.jsonl"
      - split: test
        path: "tasks/disambiguation_test.jsonl"
  - config_name: tasks_hallucination
    data_files:
      - split: train
        path: "tasks/hallucination_train.jsonl"
      - split: test
        path: "tasks/hallucination_test.jsonl"

  # ── Mock Data: Navigation ──────────────────────────────────────────────
  - config_name: mock_locations
    data_files: "mock_data/navigation/locations.jsonl"
  - config_name: mock_pois
    data_files: "mock_data/navigation/pois.jsonl"
  - config_name: mock_weather
    data_files: "mock_data/navigation/weather.jsonl"
  - config_name: mock_routes_location_location
    data_files: "mock_data/navigation/routes_location_location.jsonl"
  - config_name: mock_routes_location_poi
    data_files: "mock_data/navigation/routes_location_poi.jsonl"
  - config_name: mock_routes_poi_location
    data_files: "mock_data/navigation/routes_poi_location.jsonl"
  - config_name: mock_routes_index
    data_files: "mock_data/navigation/routes_index.jsonl"
  - config_name: mock_routes_metadata
    data_files: "mock_data/navigation/routes_metadata.jsonl"

  # ── Mock Data: Productivity & Communication ────────────────────────────
  - config_name: mock_calendars
    data_files: "mock_data/productivity_and_communication/calendars.jsonl"
  - config_name: mock_contacts
    data_files: "mock_data/productivity_and_communication/contacts.jsonl"

license: mit
task_categories:
  - text-generation
  - question-answering
language:
  - en
tags:
  - benchmark
  - car
  - voice-assistant
  - agentic
  - tool-use
  - function-calling
size_categories:
  - 1K<n<10K
---

# CAR-Bench Dataset

**CAR-Bench** is a benchmark for evaluating AI voice assistants in a realistic automotive (car) environment.
It tests an agent's ability to correctly use vehicle control tools, handle disambiguation, and avoid hallucinations.

## Dataset Structure

The dataset is organized into **task configs** and **mock data configs**:

### Tasks

Each task defines a user persona, an instruction, the initial vehicle/environment context, and the ground-truth sequence of tool-call actions the assistant should perform.

| Config | Description | Train | Test |
|--------|-------------|-------|------|
| `tasks_base` | Standard tasks covering vehicle controls, navigation, calendar, etc. | 50 | 50 |
| `tasks_disambiguation` | Tasks requiring the agent to disambiguate parameters (internally via preferences or by asking the user) | 30 | 26 |
| `tasks_hallucination` | Tasks where certain tools/parameters are intentionally removed to test if the agent hallucinates | 48 | 50 |

**Task schema:**

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique task identifier |
| `persona` | string | Description of the simulated user's personality and communication style |
| `calendar_id` | string | Reference to a calendar in the mock data |
| `instruction` | string | The instruction given to the simulated user |
| `context_init_config` | string (JSON) | Initial vehicle and environment state (battery, seats, location, weather, preferences, etc.) |
| `actions` | string (JSON) | Ground-truth sequence of tool calls `[{name, kwargs, index, dependent_on_action_index}]` |
| `task_type` | string | One of: `base`, `disambiguation_internal`, `disambiguation_user`, `hallucination_missing_tool`, `hallucination_missing_tool_parameter`, `hallucination_missing_tool_response` |
| `disambiguation_element_internal` | string or null | What needs to be disambiguated internally (only set in disambiguation tasks) |
| `disambiguation_element_user` | string or null | What needs to be disambiguated with the user (only set in disambiguation tasks) |
| `disambiguation_element_note` | string or null | Note explaining the disambiguation (only set in disambiguation tasks) |
| `removed_part` | string (JSON) or null | Which tools/parameters were removed (only set in hallucination tasks) |

### Mock Data

The mock data simulates a realistic car environment database used by the tools during benchmark execution.

| Config | Rows | Description |
|--------|------|-------------|
| `mock_locations` | 48 | European cities with GPS coordinates |
| `mock_pois` | 130,693 | Points of interest (airports, bakeries, restaurants, etc.) |
| `mock_weather` | 48 | Weather data per location (8 time-slots/day) |
| `mock_routes_location_location` | 6,768 | Routes between locations (3 alternatives each) |
| `mock_routes_location_poi` | 1,378 | Routes from locations to POIs |
| `mock_routes_poi_location` | 1,378 | Routes from POIs to locations |
| `mock_routes_index` | 1,763,870 | Route lookup index |
| `mock_routes_metadata` | 1,754,346 | Metadata for POI-to-POI route generation |
| `mock_calendars` | 100 | Calendar entries with meetings |
| `mock_contacts` | 100 | Contact information |

## Usage

### With the CAR-Bench benchmark

The [CAR-Bench codebase](https://github.com/CAR-bench/car-bench) loads tasks and mock data from this dataset automatically:

```bash
pip install -e .
python run.py --model gpt-4.1-mini --task-type base --task-split test --num-tasks 3
```

### Standalone

```python
from datasets import load_dataset

# Load tasks
tasks = load_dataset("johanneskirmayr/car-bench-dataset", "tasks_base")
print(tasks["test"][0])

# Load mock data
locations = load_dataset("johanneskirmayr/car-bench-dataset", "mock_locations", split="train")
contacts = load_dataset("johanneskirmayr/car-bench-dataset", "mock_contacts", split="train")

# Parse nested JSON fields
import json
task = tasks["test"][0]
context = json.loads(task["context_init_config"])
actions = json.loads(task["actions"])
```

## Citation

If you use this dataset, please cite the CAR-Bench paper:

```bibtex
@misc{kirmayr2026carbenchevaluatingconsistencylimitawareness,
      title={CAR-bench: Evaluating the Consistency and Limit-Awareness of LLM Agents under Real-World Uncertainty}, 
      author={Johannes Kirmayr and Lukas Stappen and Elisabeth André},
      year={2026},
      eprint={2601.22027},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2601.22027}, 
}
```

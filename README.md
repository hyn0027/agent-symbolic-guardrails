# mcp-agent

> This is an on-going work.

## Project Structure

- Folder `agent` contains the code for the cutomized LLM-agent.
- Folder `mcp-server` contains the code for the server that host the MCP tools.
- Folder `data` contains experiment data.
- Folder `logs_to_save` contains intermediate results. These will be cleaned upon project completion.
- Folder `notes` contains intermediate notes.

## To run the project

Installation:

```bash
pip install -e ./mcp-server
pip install -e ./agent
```

Note an env param `$OPENAI_API_KEY` is expected to run this application. Please see OpenAI document for details.

Execute:

```bash
human_interaction # This command lets user interact (i.e.) talk with the agent interactively in the CLI

run_random_task # This command randomly samples one task and simulates the agent-user interaction autonomously

run_given_task --id <id> # This commands run and evaluates the task with #id and simulates the agent-user interaction autonomously

run_dataset # This runs all tasks in the dataset and performs evaluation
```

## Configurations

Agent evaluation configureation can be find and modified at `agent/src/config/config.yml`.

Server configurations can be find and modified at `mcp-server/src/test_config.yml` and `mcp-server/src/golden_config.yml`.
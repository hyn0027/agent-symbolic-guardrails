from mcp_server import mcp
from config_loader import CONFIG
from safety_check import *

if CONFIG.DATASET.NAME == "tau2":
    if CONFIG.DATASET.DOMAIN == "airline":
        import dataset_domains.tau2
        from dataset_domains.tau2.airlines.tools import *
elif CONFIG.DATASET.NAME == "MedAgentBench":
    import dataset_domains.MedAgentBench
    from dataset_domains.MedAgentBench.tools import *


def main():
    print("Starting MCP server...")
    mcp.run(
        show_banner=False,
        log_level="WARNING",
    )


if __name__ == "__main__":
    main()

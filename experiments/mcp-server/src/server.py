from mcp_server import mcp
from config_loader import CONFIG

if CONFIG.DATASET.NAME == "tau2":
    import dataset_domains.tau2
    if CONFIG.DATASET.DOMAIN == "airline":
        import dataset_domains.tau2.airlines
elif CONFIG.DATASET.NAME == "MedAgentBench":
    import dataset_domains.MedAgentBench


def main() -> None:
    print("Starting MCP server...")
    mcp.run(
        show_banner=False,
        log_level="WARNING",
    )


if __name__ == "__main__":
    main()

from mcp_server import mcp
from config_loader import CONFIG

if CONFIG.DATASET.NAME == "tau2":
    if CONFIG.DATASET.DOMAIN == "airline":
        from datasets.tau2.airlines.tools import *


def main():
    mcp.run(
        show_banner=False,
        log_level="WARNING",
    )


if __name__ == "__main__":
    main()

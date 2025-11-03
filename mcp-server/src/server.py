from mcp_server import mcp
from tau2.airlines.tools import *


def main():
    mcp.run(
        show_banner=False,
        log_level="WARNING",
    )


if __name__ == "__main__":
    main()

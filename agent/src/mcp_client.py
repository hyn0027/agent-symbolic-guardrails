import json
from typing import List, Dict, Any, Union

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import Tool


class MCPClient:
    def __init__(self, server_params: str):
        self.tools: List[Tool] = []
        self.initialized = False
        self.server_params = StdioServerParameters(
            command=server_params,
        )

    async def initialize(self):
        """Initialize the MCP client by connecting to the server and fetching tools."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    self.tools.append(tool)
                self.initialized = True

    def list_OPENAI_tools(self) -> List[Dict[str, Any]]:
        """List tools in a format compatible with OpenAI's tool calling."""
        if not self.initialized:
            raise ValueError("MCP Client is not initialized. Call initialize() first.")
        openai_tools = []
        for tool in self.tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            param: {
                                "type": (
                                    tool.inputSchema["properties"][param]["type"]
                                    if "type" in tool.inputSchema["properties"][param]
                                    else "string"
                                ),
                                "description": (
                                    tool.inputSchema["properties"][param]["description"]
                                    if "description"
                                    in tool.inputSchema["properties"][param]
                                    else ""
                                ),
                            }
                            for param in tool.inputSchema["properties"]
                        },
                        "required": [param for param in tool.inputSchema["required"]],
                    },
                },
            }
            openai_tools.append(openai_tool)
        return openai_tools

    async def call_tool(self, name: str, arguments: Union[str, Dict[str, Any]]) -> Any:
        """Call a tool by its name with the provided input data."""
        if not self.initialized:
            raise ValueError("MCP Client is not initialized. Call initialize() first.")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON string for arguments: {str(e)}"}
        if not isinstance(arguments, dict):
            return {
                "error": "Arguments must be a dictionary or a JSON string representing a dictionary."
            }
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    response = await session.call_tool(name, arguments=arguments)
                    return response.content[0]
        except Exception as e:
            return {"error": str(e)}

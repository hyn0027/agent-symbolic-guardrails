import json
from typing import List, Dict, Any, Union

from fastmcp import Client
from mcp.types import Tool, ContentBlock


class MCPClient:
    def __init__(self, server_params: str):
        self.tools: List[Tool] = []
        self.initialized = False
        self.client = Client(
            {
                "mcpServers": {
                    "local_server": {
                        "transport": "stdio",
                        "command": server_params,
                    }
                }
            }
        )

    async def initialize(self):
        """Initialize the MCP client by connecting to the server and fetching tools."""
        async with self.client:
            self.tools = await self.client.list_tools()
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
                    "parameters": tool.inputSchema,
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
            async with self.client:
                result = await self.client.call_tool(name=name, arguments=arguments)
            res = self.tool_call_res_to_json(result)
            if res["is_error"]:
                return {"error": res["data"]}
            return res
        except Exception as e:
            return {"error": str(e)}

    def tool_call_res_to_json(self, tool_call_response: Any) -> Dict[str, Any]:
        """Convert tool call response to a JSON-serializable dictionary."""
        is_error = tool_call_response.is_error
        data = tool_call_response.data
        structured_content = tool_call_response.structured_content
        content: list[ContentBlock] = tool_call_response.content
        return {
            "is_error": is_error,
            "data": data,
            "structured_content": structured_content,
            "content": [block for block in content],
        }

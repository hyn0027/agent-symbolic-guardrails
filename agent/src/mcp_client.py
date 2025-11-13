import json
from typing import List, Dict, Any, Union

from fastmcp import Client
from mcp.types import Tool


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
        self.attempted_tool_calls = []
        self.successful_tool_calls = []
        async with self.client:
            self.tools = await self.client.list_tools()
            self.tools = [
                tool for tool in self.tools if tool.meta.get("disclose_to_model", True)
            ]
            self.initialized = True

    def get_tool_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata of a tool by its name."""
        if not self.initialized:
            raise ValueError("MCP Client is not initialized. Call initialize() first.")
        for tool in self.tools:
            if tool.name == name:
                return tool.meta if tool.meta else {}
        raise ValueError(f"Tool with name '{name}' not found.")

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

    async def call_tool(
        self, name: str, arguments: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
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

        self.attempted_tool_calls.append({"name": name, "arguments": arguments})
        try:
            async with self.client:
                result = await self.client.call_tool(name=name, arguments=arguments)
            res = self._tool_call_res_to_json(result)
            if res["is_error"]:
                return {"error": res["data"]}
            self.successful_tool_calls.append(
                {"name": name, "arguments": arguments, "response": res}
            )
            return res
        except Exception as e:
            return {"error": str(e)}

    async def report_error_statistics(self) -> Dict:
        """Call the report_error_statistics tool to get error statistics."""
        if not self.initialized:
            raise ValueError("MCP Client is not initialized. Call initialize() first.")
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="report_error_statistics", arguments={}
                )
            res = self._tool_call_res_to_json(result)
            if res["is_error"]:
                return {"error": res["data"]}
            return res["structured_content"]
        except Exception as e:
            return {"error": str(e)}

    def _tool_call_res_to_json(self, tool_call_response: Any) -> Dict[str, Any]:
        return {
            "is_error": tool_call_response.is_error,
            "data": tool_call_response.data,
            "structured_content": tool_call_response.structured_content,
            "content": [block for block in tool_call_response.content],
        }

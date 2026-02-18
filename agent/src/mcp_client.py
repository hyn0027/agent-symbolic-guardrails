import json
from typing import List, Dict, Any, Union

from fastmcp import Client
from mcp.types import Tool
from config.logger import LOGGER


class MCPClient:
    def __init__(self, server_params: str, server_args: str = ""):
        self.tools: List[Tool] = []
        self.initialized = False
        self.client = Client(
            transport={
                "mcpServers": {
                    "local_server": {
                        "transport": "stdio",
                        "command": server_params,
                        "args": server_args.split(),
                    }
                }
            },
            init_timeout=300,
        )

    async def initialize(self) -> None:
        """Initialize the MCP client by connecting to the server and fetching tools."""
        self.attempted_tool_calls = []
        self.successful_tool_calls = []
        async with self.client:
            self.tools = await self.client.list_tools()
            self.tools = [
                tool
                for tool in self.tools
                if tool.meta is None or tool.meta.get("disclose_to_model", True)
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

    def _traverse_and_set_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively traverse and set the schema additional properties to False."""
        if "type" in schema and schema["type"] == "object":
            schema["additionalProperties"] = False
            if "properties" in schema:
                for prop in schema["properties"].values():
                    self._traverse_and_set_schema(prop)
            if "$defs" in schema:
                for defn in schema["$defs"].values():
                    self._traverse_and_set_schema(defn)
        elif "type" in schema and schema["type"] == "array":
            if "items" in schema:
                self._traverse_and_set_schema(schema["items"])
        elif "anyOf" in schema:
            for subschema in schema["anyOf"]:
                self._traverse_and_set_schema(subschema)
        return schema

    def list_OPENAI_tools(self) -> List[Dict[str, Any]]:
        """List tools in a format compatible with OpenAI's tool calling."""
        if not self.initialized:
            raise ValueError("MCP Client is not initialized. Call initialize() first.")
        openai_tools = []
        for tool in self.tools:
            tool.inputSchema = self._traverse_and_set_schema(tool.inputSchema)
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                    "strict": True,
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

    async def save_state(self) -> bool:
        """Call the save_state tool to persist the current state."""
        if not self.initialized:
            raise ValueError("MCP Client is not initialized. Call initialize() first.")
        try:
            async with self.client:
                result = await self.client.call_tool(
                    name="save_state", arguments={}, timeout=90
                )
            res = self._tool_call_res_to_json(result)
            if res["is_error"]:
                return False
            return True
        except Exception as e:
            raise RuntimeError(f"Error saving state: {str(e)}") from e
            return False

    async def get_user_confirmation_details(
        self, func_name: str, func_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the get_user_confirmation_details tool to get details for user confirmation."""
        if not self.initialized:
            raise ValueError("MCP Client is not initialized. Call initialize() first.")
        try:
            arguments = {"func_name": func_name, "func_args": func_args}
            LOGGER.debug(
                f"Getting user confirmation details with arguments: {arguments}"
            )
            async with self.client:
                result = await self.client.call_tool(
                    name="get_user_confirmation_details", arguments=arguments
                )
            res = self._tool_call_res_to_json(result)
            LOGGER.debug(f"User confirmation details response: {res}")
            if res["is_error"]:
                return {"error": res["data"]}
            return {"user_confirmation_details": res["data"]}
        except Exception as e:
            LOGGER.error(f"Error getting user confirmation details: {str(e)}")
            return {"error": str(e)}

    def _tool_call_res_to_json(self, tool_call_response: Any) -> Dict[str, Any]:
        return {
            "is_error": tool_call_response.is_error,
            "data": tool_call_response.data,
            "structured_content": tool_call_response.structured_content,
            "content": [block for block in tool_call_response.content],
        }

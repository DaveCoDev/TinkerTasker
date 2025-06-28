from fastmcp.utilities.types import MCPContent
import mcp.types
from mcp.types import TextContent
from openai.types.chat import ChatCompletionToolParam


def mcp_tool_to_openai(tool: mcp.types.Tool) -> ChatCompletionToolParam:
    parameters = tool.inputSchema or {}
    parameters["additionalProperties"] = False
    openai_tool: ChatCompletionToolParam = ChatCompletionToolParam(
        type="function",
        function={
            "name": tool.name,
            "description": tool.description or "",
            "parameters": parameters,
            "strict": True,
        },
    )
    return openai_tool


def parse_tool_call_content(mcp_tool_result: list[MCPContent]) -> str:
    """Simplifies the type of the tool result to just a string."""
    if not mcp_tool_result:
        content = "Tool executed but returned no result."
    else:
        first_content = mcp_tool_result[0]
        if isinstance(first_content, TextContent):
            content = first_content.text
        else:
            content = f"Tool returned {type(first_content).__name__} which is not supported. Tell the user their MCP server is not supported yet."
    return content

from fastmcp import FastMCP

mcp = FastMCP(
    name="WebServer",
    instructions="""Interacts with websites""",
)


@mcp.tool
def search(query: str) -> str:
    return "Search not implemented yet."


if __name__ == "__main__":
    mcp.run()

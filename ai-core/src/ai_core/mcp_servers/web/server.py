from functools import lru_cache
import warnings

from fastmcp import FastMCP
import tiktoken

warnings.filterwarnings("ignore", category=DeprecationWarning)

from not_again_ai.data.web import process_url  # noqa: E402

mcp = FastMCP(
    name="Web",
    instructions="Provides the ability to fetch web content and facilitate web exploration.",
)


@lru_cache(maxsize=2)
def _get_encoding(model: str = "gpt-4o") -> tiktoken.Encoding:
    """Returns the encoding for the specified model."""
    return tiktoken.encoding_for_model(model)


def _count_tokens(text: str) -> int:
    """Counts the number of tokens in a given text."""
    encoding = _get_encoding("gpt-4o")
    tokens = encoding.encode(
        text,
        allowed_special=set(),
        disallowed_special=(),
    )
    return len(tokens)


def _truncate_str(text: str, max_len: int) -> str:
    encoding = _get_encoding("gpt-4o")
    tokens = encoding.encode(
        text,
        allowed_special=set(),
        disallowed_special=(),
    )
    if len(tokens) > max_len:
        tokens = tokens[:max_len]
        truncated_text = encoding.decode(tokens)
        return truncated_text
    else:
        return text


@mcp.tool
async def fetch(url: str) -> str:
    """Fetches web content as Markdown for the given URL. Use this tool when you need to retrieve and analyze web content.
    Returns a list of the links found on the page so you can use this tool as the beginning of a web exploration task.
    Go to a website that might lead you to other useful links that you can continue to explore.

    Results may be truncated if the content is very large.
    Some links may have been filtered out if they are too long or too many.

    Args:
        url (str): The URL to fetch which must be a fully-formed valid URL.
    """
    url_result = await process_url(url)
    markdown = _truncate_str(url_result.markdown, max_len=8000)

    # Format output according to expected structure, limit to first 100 links
    links_section = ""
    if url_result.links:
        # Filter links that have more than 100 tokens and take first 100
        filtered_links = [
            link for link in url_result.links if _count_tokens(link.url) <= 100
        ][:100]

        if filtered_links:
            links_xml = "\n".join(f"<link>{link.url}</link>" for link in filtered_links)
            links_section = f"<links>\n{links_xml}\n</links>"

    formatted_output = f"""<website>
<url>{url_result.url}</url>
<content>{markdown}</content>
{links_section}
</website>"""

    return formatted_output


if __name__ == "__main__":
    mcp.run()

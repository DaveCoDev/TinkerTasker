"""An MCP server for interacting with the local filesystem.
See https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/text-editor-tool for more details on text editing tools.
"""

from pathlib import Path

from fastmcp import Context, FastMCP


async def get_working_dir(ctx: Context, cwd_fallback: bool = False) -> Path | str:
    """Get the working directory as the first root directory configured in the MCP client.

    Returns:
        Either the working directory Path or an error string
    """
    roots = await ctx.list_roots()

    if roots and roots[0].uri and roots[0].uri.path:
        return Path(roots[0].uri.path)
    elif cwd_fallback:
        return Path.cwd()

    return (
        "Error: No working directory configured. Ask the user to set a root directory."
    )


async def resolve_path(
    ctx: Context, path: str, cwd_fallback: bool = False
) -> Path | str:
    """Resolve a file path to an absolute Path object if it is not already.
    If cwd_fallback is True, it will use the current working directory as a fallback.
    If cwd_fallback is False, it will check to see if the path is within the configured root directory.

    Args:
        ctx: The MCP context
        path: The path to resolve (absolute or relative)
        cwd_fallback: If True, use the current working directory if no root is configured

    Returns:
        Either the resolved Path object or an error string
    """
    working_dir = await get_working_dir(ctx, cwd_fallback=cwd_fallback)
    if isinstance(working_dir, str):
        return working_dir

    path_obj = Path(path)
    if path_obj.is_absolute():
        resolved_path = path_obj.resolve()
    else:
        resolved_path = (working_dir / path_obj).resolve()

    if not cwd_fallback:
        try:
            resolved_path.relative_to(working_dir)
        except ValueError:
            return f"Error: Path must be within the configured root directory: {resolved_path}"
    return resolved_path


def format_directory_tree(path: Path, max_depth: int = 1) -> str:
    """Format a directory as a tree structure with configurable depth.

    Args:
        path: The directory path to format
        max_depth: Maximum depth to traverse (1 = immediate children only, -1 = unlimited)
    """
    lines = [f"- {path}/"]
    try:
        if max_depth == 1:
            # Use iterdir() for immediate children only
            for item in sorted(path.iterdir()):
                name = item.name + ("/" if item.is_dir() else "")
                lines.append(f"  - {name}")
        else:
            # Use rglob() for recursive traversal
            for item in sorted(path.rglob("*")):
                relative = item.relative_to(path)
                depth = len(relative.parts)

                # Skip items beyond max_depth if specified
                if max_depth > 0 and depth > max_depth:
                    continue

                indent = "  " * depth
                name = item.name + ("/" if item.is_dir() else "")
                lines.append(f"{indent}- {name}")
    except PermissionError:
        lines.append("  (Permission denied)")
    return "\n".join(lines)


async def validate_file_for_editing(ctx: Context, path: str) -> tuple[Path, str] | str:
    """Validate a file path for editing operations.

    Returns either:
    - A tuple of (resolved_path, content) if validation succeeds
    - An error string if validation fails
    """
    resolved_path = await resolve_path(ctx, path, cwd_fallback=False)
    if isinstance(resolved_path, str):
        return resolved_path

    try:
        if not resolved_path.exists():
            return f"Error: File not found at {resolved_path}"
        if resolved_path.is_dir():
            return f"Error: Cannot edit directory: {resolved_path}"
        content = resolved_path.read_text(encoding="utf-8")
        return resolved_path, content

    except UnicodeDecodeError:
        return f"Error: Cannot edit binary files. The file appears to be a binary {resolved_path.suffix} file"
    except PermissionError:
        return f"Error: Permission denied at {resolved_path}"
    except Exception as e:
        return f"Error reading {resolved_path}: {e!s}"


mcp = FastMCP(
    name="FilesystemServer",
    instructions="""This server provides the ability to interact with the local filesystem.""",
)


@mcp.tool
async def view(
    ctx: Context,
    path: str,
    view_range: tuple[int, int] | None = None,
) -> str:
    """The view command examines the contents of a file or list the contents of a directory.
    It can read the entire file or a specific range of lines.

    Args:
        path (str): The path to the file or directory to view, which can be absolute or relative to the working directory.
        view_range (tuple[int, int], optional):  An array of two integers specifying the start (inclusive) and end (inclusive) line numbers to view.
        Line numbers are 1-indexed, and -1 for the end line means read to the end of the file.
        This parameter only applies when viewing files, not directories.
    """
    resolved_path = await resolve_path(ctx, path, cwd_fallback=True)
    if isinstance(resolved_path, str):
        return resolved_path

    try:
        if not resolved_path.exists():
            return f"Error: Path not found: {path}"
        if resolved_path.is_dir():
            return format_directory_tree(resolved_path, max_depth=1)

        content = resolved_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        if view_range:
            start_line, end_line = view_range
            # Convert to 0-indexed
            start_idx = max(0, start_line - 1)
            end_idx = len(lines) if end_line == -1 else min(len(lines), end_line)
            selected_lines = lines[start_idx:end_idx]
            line_offset = start_idx
        else:
            selected_lines = lines
            line_offset = 0

        # Keeps the line numbers aligned
        max_line_num = line_offset + len(selected_lines)
        width = len(str(max_line_num))

        numbered_lines = []
        for i, line in enumerate(selected_lines):
            line_num = line_offset + i + 1
            numbered_lines.append(f"{line_num:>{width}}→{line}")
        return "\n".join(numbered_lines)
    except UnicodeDecodeError:
        return f"Error: This tool cannot read binary files. The file appears to be a binary {resolved_path.suffix} file"
    except PermissionError:
        return f"Error: Permission denied: {resolved_path}"
    except Exception as e:
        return f"Error reading {resolved_path}: {e!s}"


@mcp.tool
async def insert(ctx: Context, path: str, insert_line: int, new_str: str) -> str:
    """The insert command inserts text at a specific location in a file.

    Args:
        path (str): The path to the file to modify. This file must be in the current working directory or a subdirectory.
        insert_line (int): The line number after which to insert the text (0 for beginning of file)
        new_str (str): The text to insert
    """
    validation_result = await validate_file_for_editing(ctx, path)
    if isinstance(validation_result, str):
        return validation_result
    resolved_path, content = validation_result

    try:
        lines = content.splitlines()

        # Validate insert_line parameter
        if insert_line < 0:
            return f"Error: insert_line must be >= 0, got {insert_line}"

        # If insert_line is beyond the end of the file, append to the end
        if insert_line > len(lines):
            insert_line = len(lines)

        lines.insert(insert_line, new_str)
        new_content = "\n".join(lines)
        resolved_path.write_text(new_content, encoding="utf-8")

        # Show context around the inserted line
        context_lines = 2
        start_idx = max(0, insert_line - context_lines)
        end_idx = min(len(lines), insert_line + context_lines + 1)
        selected_lines = lines[start_idx:end_idx]
        line_offset = start_idx

        # Keeps the line numbers aligned (like view function)
        max_line_num = line_offset + len(selected_lines)
        width = len(str(max_line_num))

        # Build the output showing line numbers and content (like Edit tool)
        output_lines = [
            f"Successfully inserted text at line {insert_line} in {resolved_path}:"
        ]
        for i, line in enumerate(selected_lines):
            line_num = line_offset + i + 1
            output_lines.append(f"{line_num:>{width}}→{line}")

        return "\n".join(output_lines)
    except Exception as e:
        return f"Error inserting into {resolved_path}: {e!s}"


@mcp.tool
async def str_replace(
    ctx: Context, path: str, old_str: str, new_str: str, replace_all: bool = False
) -> str:
    """The str_replace command replaces a specific string in a file with a new string.
    This is used for making precise edits.

    Args:
        path (str): The path to the file to modify. This file must be in the current working directory or a subdirectory.
        old_str (str): The text to replace (must match exactly, including whitespace and indentation)
        new_str (str): The new text to insert in place of the old text
        replace_all (bool): If True, replaces all occurrences of old_str with new_str.
                            If False, replaces only the first occurrence.
    """
    validation_result = await validate_file_for_editing(ctx, path)
    if isinstance(validation_result, str):
        return validation_result
    resolved_path, content = validation_result

    try:
        if old_str not in content:
            return f"Error: String not found in {path}: '{old_str}'"

        # Check for multiple occurrences when replace_all is False
        occurrence_count = content.count(old_str)
        if not replace_all and occurrence_count > 1:
            return f"Error: replace_all is False, but {occurrence_count} occurrences were found. Set replace_all to True if you want to replace all occurrences, or make old_str more specific to replace only one instance."

        if replace_all:
            new_content = content.replace(old_str, new_str)
            replacement_count = occurrence_count
        else:
            new_content = content.replace(old_str, new_str, 1)
            replacement_count = 1

        resolved_path.write_text(new_content, encoding="utf-8")

        # Show context around the replacement (like insert function)
        lines = new_content.splitlines()

        # Find the first line that changed by comparing with original content
        original_lines = content.splitlines()
        changed_line_idx = 0  # Default to first line if we can't find the change

        for i, (old_line, new_line) in enumerate(
            zip(original_lines, lines, strict=True)
        ):
            if old_line != new_line:
                changed_line_idx = i
                break

        # Show context around the changed line
        context_lines = 2
        start_idx = max(0, changed_line_idx - context_lines)
        end_idx = min(len(lines), changed_line_idx + context_lines + 1)
        selected_lines = lines[start_idx:end_idx]
        line_offset = start_idx

        # Keeps the line numbers aligned (like view function)
        max_line_num = line_offset + len(selected_lines)
        width = len(str(max_line_num))

        # Build the output showing line numbers and content
        if replace_all:
            output_lines = [
                f"Successfully replaced {replacement_count} occurrences in {resolved_path}:"
            ]
        else:
            output_lines = [f"Successfully replaced text in {resolved_path}:"]

        for i, line in enumerate(selected_lines):
            line_num = line_offset + i + 1
            output_lines.append(f"{line_num:>{width}}→{line}")

        return "\n".join(output_lines)
    except Exception as e:
        return f"Error replacing in {path}: {e!s}"


@mcp.tool
async def create(ctx: Context, path: str, file_text: str) -> str:
    """Creates a new file with the specified text.

    Args:
        path (str): The path to the new file to create. This file must be in the current working directory or a subdirectory.
        file_text (str): The content to write to the new file
    """
    resolved_path = await resolve_path(ctx, path, cwd_fallback=False)
    if isinstance(resolved_path, str):
        return resolved_path

    try:
        if resolved_path.is_dir():
            return f"Error: Cannot create file at directory: {resolved_path}"
        if resolved_path.exists():
            return f"Error: File already exists at {resolved_path} use str_replace or insert to modify it."

        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(file_text, encoding="utf-8")
        return f"File successfully created at {resolved_path}"
    except PermissionError:
        return f"Error: Permission denied: {resolved_path}"
    except Exception as e:
        return f"Error creating {resolved_path}: {e!s}"


if __name__ == "__main__":
    mcp.run()

from contextlib import asynccontextmanager
from pathlib import Path
import tempfile

from fastmcp import Client
import mcp.types as mcp_types
from mcp.types import TextContent
from pydantic import FileUrl

from ai_core.mcp_servers.filesystem.server import mcp


@asynccontextmanager
async def filesystem_test_setup():
    """Helper that creates a temporary directory and filesystem client."""
    with tempfile.TemporaryDirectory() as tmpdir:
        async with Client(
            mcp,
            roots=[
                mcp_types.Root(
                    uri=FileUrl(f"file://{tmpdir}"), name="Working Directory"
                )
            ],
        ) as client:
            yield tmpdir, client


# region view


async def call_view_and_check(
    client, path, expected_text, start_line: int = 1, end_line: int = -1
):
    """Helper to call view tool and check the expected result."""
    params = {"path": path, "start_line": start_line, "end_line": end_line}

    result = await client.call_tool("view", params)
    assert result == [TextContent(type="text", text=expected_text)]


async def test_view_file():
    """Test viewing a file shows its contents with line numbers."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        await call_view_and_check(
            client, str(test_file), "Read 1 lines\n1→Hello, World!"
        )


async def test_view_file_relative_path():
    """Test viewing a file with a relative path shows its contents with line numbers."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        await call_view_and_check(client, "test.txt", "Read 1 lines\n1→Hello, World!")


async def test_view_range():
    """Test viewing a range of lines in a file shows the correct content."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "multiline.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")
        await call_view_and_check(
            client, str(test_file), "Read 1 lines\n2→Line 2", start_line=2, end_line=2
        )


async def test_view_start_range():
    """Test viewing a file with a start range of -1"""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "multiline.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

        # Start at -1 should be treated as 0 (start of file) due to max(0, start_line - 1)
        await call_view_and_check(
            client,
            str(test_file),
            "Read 2 lines\n1→Line 1\n2→Line 2",
            start_line=-1,
            end_line=2,
        )


async def test_view_end_range():
    """Test viewing a file with an end range of -1"""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "multiline.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

        # End at -1 should read to end of file
        await call_view_and_check(
            client,
            str(test_file),
            "Read 3 lines\n3→Line 3\n4→Line 4\n5→Line 5",
            start_line=3,
            end_line=-1,
        )


async def test_view_zero_range():
    """Test viewing a file with a zero range ignores the 0"""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "multiline.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

        # Start at 0 should be treated as max(0, 0-1) = 0, so shows line 1
        await call_view_and_check(
            client,
            str(test_file),
            "Read 2 lines\n1→Line 1\n2→Line 2",
            start_line=0,
            end_line=2,
        )


async def test_view_binary_file():
    """Test viewing a binary file shows an error message."""
    async with filesystem_test_setup() as (tmpdir, client):
        binary_file = Path(tmpdir) / "binary.bin"
        binary_file.write_bytes(b"\xff\xfe\xfd\xfc\x80\x81\x82\x83")

        await call_view_and_check(
            client,
            str(binary_file),
            "Read 1 lines\n1→The filetype `bin` is not supported or the file itself is malformed: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte",
        )


async def test_view_directory():
    """Test viewing a directory lists its contents."""
    async with filesystem_test_setup() as (tmpdir, client):
        base_dir = Path(tmpdir) / "test_dir"
        base_dir.mkdir()
        (base_dir / "file1.txt").write_text("content1")
        (base_dir / "file2.py").write_text("print('hello')")
        subdir = base_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.json").write_text('{"key": "value"}')

        # Expected tree structure output
        expected_text = f"""Listed 3 paths
- {base_dir}/
  - file1.txt
  - file2.py
  - subdir/"""

        await call_view_and_check(client, str(base_dir), expected_text)


async def test_view_directory_empty():
    """Test viewing an empty directory shows just the directory name."""
    async with filesystem_test_setup() as (tmpdir, client):
        empty_dir = Path(tmpdir) / "empty_dir"
        empty_dir.mkdir()
        expected_text = "The directory is empty"
        await call_view_and_check(client, str(empty_dir), expected_text)


async def test_view_pdf_file():
    """Test viewing a PDF file converts it to readable text."""
    async with filesystem_test_setup() as (tmpdir, client):
        sample_files_dir = Path(__file__).parent / "sample_files"
        sample_pdf = sample_files_dir / "Sample Doc.pdf"
        test_pdf = Path(tmpdir) / "test.pdf"
        test_pdf.write_bytes(sample_pdf.read_bytes())

        expected_text = """Read 4 lines
1→Hello!
2→This is some sample Word document content
3→Across four lines of text
4→The END!"""

        await call_view_and_check(client, "test.pdf", expected_text)


async def test_view_docx_file():
    """Test viewing a DOCX file converts it to readable text."""
    async with filesystem_test_setup() as (tmpdir, client):
        sample_files_dir = Path(__file__).parent / "sample_files"
        sample_docx = sample_files_dir / "Sample Doc.docx"
        test_docx = Path(tmpdir) / "test.docx"
        test_docx.write_bytes(sample_docx.read_bytes())

        expected_text = """Read 7 lines
1→Hello!
2→
3→This is some sample Word document content
4→
5→Across four lines of text
6→
7→The END!"""

        await call_view_and_check(client, "test.docx", expected_text)


async def test_view_pdf_file_with_line_range():
    """Test viewing a PDF file with specific line range."""
    async with filesystem_test_setup() as (tmpdir, client):
        sample_files_dir = Path(__file__).parent / "sample_files"
        sample_pdf = sample_files_dir / "Sample Doc.pdf"
        test_pdf = Path(tmpdir) / "test.pdf"
        test_pdf.write_bytes(sample_pdf.read_bytes())

        expected_text = """Read 2 lines
2→This is some sample Word document content
3→Across four lines of text"""

        await call_view_and_check(
            client, "test.pdf", expected_text, start_line=2, end_line=3
        )


async def test_view_docx_file_with_line_range():
    """Test viewing a DOCX file with specific line range."""
    async with filesystem_test_setup() as (tmpdir, client):
        sample_files_dir = Path(__file__).parent / "sample_files"
        sample_docx = sample_files_dir / "Sample Doc.docx"
        test_docx = Path(tmpdir) / "test.docx"
        test_docx.write_bytes(sample_docx.read_bytes())

        expected_text = """Read 2 lines
2→
3→This is some sample Word document content"""

        await call_view_and_check(
            client, "test.docx", expected_text, start_line=2, end_line=3
        )


# endregion


# region insert
async def test_insert():
    """Test inserting a line into a file with proper width alignment."""
    async with filesystem_test_setup() as (tmpdir, client):
        # Create a test file with enough lines to test width alignment (12 lines)
        lines = [f"Line {i}" for i in range(1, 13)]
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("\n".join(lines))

        # Insert a new line after line 8 (at position 8) to test double-digit line numbers
        result = await client.call_tool(
            "insert", {"path": "test.txt", "insert_line": 8, "new_str": "Inserted Line"}
        )

        # Check that the insert was successful and shows proper width alignment
        # Line numbers should be right-aligned to width of largest line number (12)
        expected_output = f"""Successfully inserted text at line 8 in {test_file}
 7→Line 7
 8→Line 8
 9→Inserted Line
10→Line 9
11→Line 10"""
        assert result == [TextContent(type="text", text=expected_output)]

        # Verify the file content was updated correctly
        updated_content = test_file.read_text()
        expected_lines = [*lines[:8], "Inserted Line", *lines[8:]]
        expected_content = "\n".join(expected_lines)
        assert updated_content == expected_content


async def test_insert_beginning():
    """Test inserting a line at the beginning of a file."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4")

        result = await client.call_tool(
            "insert",
            {"path": "test.txt", "insert_line": 0, "new_str": "New First Line"},
        )

        # Check that the insert was successful and shows context from beginning
        expected_output = f"""Successfully inserted text at line 0 in {test_file}
1→New First Line
2→Line 1
3→Line 2"""
        assert result == [TextContent(type="text", text=expected_output)]

        updated_content = test_file.read_text()
        assert updated_content == "New First Line\nLine 1\nLine 2\nLine 3\nLine 4"


async def test_insert_past_end():
    """Test inserting a line past the end of a file."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        result = await client.call_tool(
            "insert",
            {"path": "test.txt", "insert_line": 100, "new_str": "Appended Line"},
        )

        # Should be clamped to the end of the file (after line 3, so at position 3)
        expected_output = f"""Successfully inserted text at line 3 in {test_file}
2→Line 2
3→Line 3
4→Appended Line"""
        assert result == [TextContent(type="text", text=expected_output)]

        updated_content = test_file.read_text()
        expected_content = "Line 1\nLine 2\nLine 3\nAppended Line"
        assert updated_content == expected_content


async def test_insert_nonexistent_file():
    """Test inserting into a file that does not exist."""
    async with filesystem_test_setup() as (tmpdir, client):
        result = await client.call_tool(
            "insert",
            {"path": "nonexistent.txt", "insert_line": 0, "new_str": "This won't work"},
        )

        nonexistent_file = Path(tmpdir) / "nonexistent.txt"
        expected_output = f"Error: File not found at {nonexistent_file}"
        assert result == [TextContent(type="text", text=expected_output)]
        assert not nonexistent_file.exists()


async def test_insert_outside_workdir():
    """Test inserting into a file outside the working directory."""
    async with filesystem_test_setup() as (_, client):
        outside_file = Path("/tmp/outside_file.txt")
        outside_file.write_text("This is outside the working directory")

        try:
            result = await client.call_tool(
                "insert",
                {
                    "path": str(outside_file),
                    "insert_line": 0,
                    "new_str": "This should be blocked",
                },
            )

            expected_output = f"Error: Path must be within the configured root directory: {outside_file}"
            assert result == [TextContent(type="text", text=expected_output)]

            assert outside_file.read_text() == "This is outside the working directory"
        finally:
            if outside_file.exists():
                outside_file.unlink()


# endregion

# region str_replace


async def test_str_replace():
    """Test replacing a string in a file."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello World\nThis is a test\nHello again\nEnd of file")

        result = await client.call_tool(
            "str_replace",
            {
                "path": "test.txt",
                "old_str": "Hello World",
                "new_str": "Hi World",
                "replace_all": False,
            },
        )

        expected_output = f"""Successfully replaced text in {test_file}:
1→Hi World
2→This is a test
3→Hello again"""
        assert result == [TextContent(type="text", text=expected_output)]

        updated_content = test_file.read_text()
        expected_content = "Hi World\nThis is a test\nHello again\nEnd of file"
        assert updated_content == expected_content


async def test_str_replace_old_not_found():
    """Test replacing a string that does not exist in the file."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello World\nThis is a test\nEnd of file")

        result = await client.call_tool(
            "str_replace",
            {
                "path": "test.txt",
                "old_str": "NonExistentString",
                "new_str": "Replacement",
                "replace_all": False,
            },
        )

        expected_output = "Error: String not found in test.txt: 'NonExistentString'"
        assert result == [TextContent(type="text", text=expected_output)]

        updated_content = test_file.read_text()
        original_content = "Hello World\nThis is a test\nEnd of file"
        assert updated_content == original_content


async def test_str_replace_replace_all():
    """Test replacing multiple occurrences of a string in a file when replace_all is True."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text(
            "Hello World\nHello Python\nThis is Hello\nHello again\nGoodbye"
        )

        result = await client.call_tool(
            "str_replace",
            {
                "path": "test.txt",
                "old_str": "Hello",
                "new_str": "Hi",
                "replace_all": True,
            },
        )

        expected_output = f"""Successfully replaced 4 occurrences in {test_file}
1→Hi World
2→Hi Python
3→This is Hi"""
        assert result == [TextContent(type="text", text=expected_output)]

        updated_content = test_file.read_text()
        expected_content = "Hi World\nHi Python\nThis is Hi\nHi again\nGoodbye"
        assert updated_content == expected_content


async def test_str_replace_multiple_found():
    """Test when replace_all is False, and multiple occurrences are found."""
    async with filesystem_test_setup() as (tmpdir, client):
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello World\nHello Python\nThis is Hello\nGoodbye")

        result = await client.call_tool(
            "str_replace",
            {
                "path": "test.txt",
                "old_str": "Hello",
                "new_str": "Hi",
                "replace_all": False,
            },
        )
        expected_output = "Error: replace_all is False, but 3 occurrences were found. Set replace_all to True if you want to replace all occurrences, or make old_str more specific to replace only one instance."
        assert result == [TextContent(type="text", text=expected_output)]

        updated_content = test_file.read_text()
        original_content = "Hello World\nHello Python\nThis is Hello\nGoodbye"
        assert updated_content == original_content


async def test_str_replace_nonexistent_file():
    """Test replacing a string in a file that does not exist."""
    async with filesystem_test_setup() as (tmpdir, client):
        result = await client.call_tool(
            "str_replace",
            {
                "path": "nonexistent.txt",
                "old_str": "Hello",
                "new_str": "Hi",
                "replace_all": False,
            },
        )

        nonexistent_file = Path(tmpdir) / "nonexistent.txt"
        expected_output = f"Error: File not found at {nonexistent_file}"
        assert result == [TextContent(type="text", text=expected_output)]
        assert not nonexistent_file.exists()


# endregion

# region create


async def test_create_new_file():
    """Test creating a new file with content."""
    async with filesystem_test_setup() as (tmpdir, client):
        result = await client.call_tool(
            "create",
            {
                "path": "newfile.txt",
                "file_text": "Hello from new file",
            },
        )

        new_file = Path(tmpdir) / "newfile.txt"
        expected_output = f"File successfully created at {new_file}"
        assert result == [TextContent(type="text", text=expected_output)]
        assert new_file.exists()
        assert new_file.read_text() == "Hello from new file"


async def test_create_file_already_exists():
    """Test creating a file that already exists."""
    async with filesystem_test_setup() as (tmpdir, client):
        existing_file = Path(tmpdir) / "existing.txt"
        existing_file.write_text("Original content")

        result = await client.call_tool(
            "create",
            {
                "path": "existing.txt",
                "file_text": "New content",
            },
        )

        expected_output = f"Error: File already exists at {existing_file} use str_replace or insert to modify it."
        assert result == [TextContent(type="text", text=expected_output)]
        assert existing_file.read_text() == "Original content"


async def test_create_file_at_directory():
    """Test creating a file at a path that is a directory."""
    async with filesystem_test_setup() as (tmpdir, client):
        dir_path = Path(tmpdir) / "mydir"
        dir_path.mkdir()

        result = await client.call_tool(
            "create",
            {
                "path": "mydir",
                "file_text": "Content",
            },
        )

        expected_output = f"Error: Cannot create file at directory: {dir_path}"
        assert result == [TextContent(type="text", text=expected_output)]
        assert dir_path.is_dir()


async def test_create_file_in_subdirectory():
    """Test creating a file in a subdirectory that doesn't exist yet."""
    async with filesystem_test_setup() as (tmpdir, client):
        result = await client.call_tool(
            "create",
            {
                "path": "subdir/newfile.txt",
                "file_text": "File in subdirectory",
            },
        )

        new_file = Path(tmpdir) / "subdir" / "newfile.txt"
        expected_output = f"File successfully created at {new_file}"
        assert result == [TextContent(type="text", text=expected_output)]
        assert new_file.exists()
        assert new_file.read_text() == "File in subdirectory"
        assert new_file.parent.is_dir()


async def test_create_file_outside_workdir():
    """Test creating a file outside the working directory."""
    async with filesystem_test_setup() as (_, client):
        result = await client.call_tool(
            "create",
            {
                "path": "/tmp/outside_file.txt",
                "file_text": "This should be blocked",
            },
        )

        outside_file = Path("/tmp/outside_file.txt")
        expected_output = (
            f"Error: Path must be within the configured root directory: {outside_file}"
        )
        assert result == [TextContent(type="text", text=expected_output)]
        assert not outside_file.exists()


# endregion

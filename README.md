# Obsidian MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude to interact with your Obsidian vault. This server provides tools for reading, creating, searching, and managing notes in Obsidian through direct filesystem access.

## Features

- 📖 **Read & write notes** - Full access to your Obsidian vault with automatic overwrite protection
- 🔍 **Smart search** - Find notes by content, tags, or modification date
- 📁 **Browse vault** - List and navigate your notes and folders by directory
- 🏷️ **Tag management** - Add, remove, and organize tags (supports both frontmatter and inline tags)
- 🔗 **Link management** - Find backlinks, analyze outgoing links, and identify broken links
- 📊 **Note insights** - Get statistics like word count and link analysis
- 🎯 **AI-optimized** - Clear error messages and smart defaults for better AI interactions
- 🔒 **Secure** - Direct filesystem access with path validation
- ⚡ **Performance optimized** - Concurrent operations and batching for large vaults
- 🚀 **Bulk operations** - Create folder hierarchies and move entire folders with all their contents

## Prerequisites

- **Obsidian** vault on your local filesystem
- **Python 3.10+** installed on your system
- **Node.js** (optional, for running MCP Inspector)

## Installation

### Quick Install

1. **Locate your Obsidian vault:**
   - Find the path to your Obsidian vault on your filesystem
   - Example: `/Users/yourname/Documents/MyVault` or `C:\Users\YourName\Documents\MyVault`

2. **Configure your AI tool:**

   <details>
   <summary><b>Claude Desktop</b></summary>
   
   Edit your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "uvx",
         "args": ["obsidian-mcp"],
         "env": {
           "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
         }
       }
     }
   }
   ```
   </details>

   <details>
   <summary><b>Cursor IDE</b></summary>
   
   Add to your Cursor settings:
   - Project-specific: `.cursor/mcp.json` in your project directory
   - Global: `~/.cursor/mcp.json` in your home directory

   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "uvx",
         "args": ["obsidian-mcp"],
         "env": {
           "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
         }
       }
     }
   }
   ```
   
   Then: Open Settings → Cursor Settings → Enable MCP
   </details>

   <details>
   <summary><b>Windsurf IDE</b></summary>
   
   Edit your Windsurf config file:
   - Location: `~/.codeium/windsurf/mcp_config.json`

   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "uvx",
         "args": ["obsidian-mcp"],
         "env": {
           "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
         }
       }
     }
   }
   ```
   
   Then: Open Windsurf Settings → Advanced Settings → Cascade → Add Server → Refresh
   </details>

3. **Restart your AI tool** to load the new configuration.

That's it! The server will now be available in your AI tool with access to your Obsidian vault.

> **Note:** This uses `uvx` which automatically downloads and runs the server in an isolated environment. Most users won't need to install anything else. If you don't have `uv` installed, you can also use `pipx install obsidian-mcp` and change the command to `"obsidian-mcp"` in the config.

#### Try It Out

Here are some example prompts to get started:

- "Show me all notes I modified this week"
- "Create a new daily note for today with my meeting agenda"
- "Search for all notes about project planning"
- "Read my Ideas/startup.md note"

### Development Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/natestrong/obsidian-mcp
   cd obsidian-mcp
   ```

2. **Set up Python environment:**
   ```bash
   # Using pyenv (recommended)
   pyenv virtualenv 3.12.9 obsidian-mcp
   pyenv activate obsidian-mcp
   
   # Or using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   export OBSIDIAN_VAULT_PATH="/path/to/your/obsidian/vault"
   ```

5. **Run the server:**
   ```bash
   python -m obsidian_mcp.server
   ```

6. **Add to Claude Desktop (for development):**

   Edit your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "obsidian": {
         "command": "/path/to/python",
         "args": ["-m", "obsidian_mcp.server"],
         "cwd": "/path/to/obsidian-mcp",
         "env": {
           "PYTHONPATH": "/path/to/obsidian-mcp",
           "OBSIDIAN_VAULT_PATH": "/path/to/your/obsidian/vault"
         }
       }
     }
   }
   ```

## Project Structure

```
obsidian-mcp/
├── obsidian_mcp/
│   ├── server.py           # Main entry point with rich parameter schemas
│   ├── tools/              # Tool implementations
│   │   ├── note_management.py    # CRUD operations
│   │   ├── search_discovery.py   # Search and navigation
│   │   ├── organization.py       # Tags, moves, metadata
│   │   └── link_management.py    # Backlinks, outgoing links, broken links
│   ├── models/             # Pydantic models for validation
│   │   └── obsidian.py    # Note, SearchResult, VaultItem models
│   ├── utils/              # Shared utilities
│   │   ├── filesystem.py        # Direct filesystem access
│   │   ├── validators.py        # Path validation, sanitization
│   │   └── validation.py        # Comprehensive parameter validation
│   └── constants.py       # Constants and error messages
├── tests/
│   ├── run_tests.py       # Test runner
│   └── test_filesystem_integration.py # Integration tests
├── docs/                  # Additional documentation
├── requirements.txt       # Python dependencies
├── CLAUDE.md             # Instructions for Claude Code
└── README.md
```

## Available Tools

### Note Management

#### `read_note`
Read the content and metadata of a specific note.

**Parameters:**
- `path`: Path to the note (e.g., "Daily/2024-01-15.md")

**Returns:**
```json
{
  "path": "Daily/2024-01-15.md",
  "content": "# Daily Note\n\nContent here...",
  "metadata": {
    "tags": ["daily", "journal"],
    "aliases": [],
    "frontmatter": {}
  }
}
```

#### `create_note`
Create a new note or update an existing one.

**Parameters:**
- `path`: Path where the note should be created
- `content`: Markdown content of the note (consider adding tags for organization)
- `overwrite` (default: `false`): Whether to overwrite existing notes

**Best Practices:**
- Add relevant tags when creating notes to maintain organization
- Use `list_tags` to see existing tags and maintain consistency
- Tags can be added as inline hashtags (`#tag`) or in frontmatter

#### `update_note`
Update the content of an existing note.

⚠️ **IMPORTANT**: By default, this tool REPLACES the entire note content. Always read the note first if you need to preserve existing content.

**Parameters:**
- `path`: Path to the note to update
- `content`: New markdown content (REPLACES existing content unless using append)
- `create_if_not_exists` (default: `false`): Create if doesn't exist
- `merge_strategy` (default: `"replace"`): How to handle content
  - `"replace"`: Overwrites entire note content (default)
  - `"append"`: Adds new content to the end of existing content

**Safe Update Pattern:**
1. ALWAYS read first to preserve content
2. Modify the content as needed
3. Update with the complete new content
4. Or use append mode to add content to the end

#### `delete_note`
Delete a note from the vault.

**Parameters:**
- `path`: Path to the note to delete

### Search and Discovery

#### `search_notes`
Search for notes containing specific text or tags.

**Parameters:**
- `query`: Search query (supports Obsidian search syntax)
- `context_length` (default: `100`): Number of characters to show around matches

**Search Syntax:**
- Text search: `"machine learning"`
- Tag search: `tag:project` or `tag:#project`
- Path search: `path:Daily/`
- Combined: `tag:urgent TODO`

#### `search_by_date`
Search for notes by creation or modification date.

**Parameters:**
- `date_type` (default: `"modified"`): Either "created" or "modified"
- `days_ago` (default: `7`): Number of days to look back
- `operator` (default: `"within"`): Either "within" (last N days) or "exactly" (exactly N days ago)

**Returns:**
```json
{
  "query": "Notes modified within last 7 days",
  "count": 15,
  "results": [
    {
      "path": "Daily/2024-01-15.md",
      "date": "2024-01-15T10:30:00",
      "days_ago": 1
    }
  ]
}
```

**Example usage:**
- "Show me all notes modified today" → `search_by_date("modified", 0, "within")`
- "Show me all notes modified this week" → `search_by_date("modified", 7, "within")`
- "Find notes created in the last 30 days" → `search_by_date("created", 30, "within")`
- "What notes were modified exactly 2 days ago?" → `search_by_date("modified", 2, "exactly")`

#### `search_by_regex`
Search for notes using regular expressions for advanced pattern matching.

**Parameters:**
- `pattern`: Regular expression pattern to search for
- `flags` (optional): List of regex flags ("ignorecase", "multiline", "dotall")
- `context_length` (default: `100`): Characters to show around matches
- `max_results` (default: `50`): Maximum number of results

**When to use:**
- Finding code patterns (functions, imports, syntax)
- Searching for structured data
- Complex text patterns that simple search can't handle

**Common patterns:**
```python
# Find Python imports
"(import|from)\\s+fastmcp"

# Find function definitions
"def\\s+\\w+\\s*\\([^)]*\\):"

# Find TODO comments
"(TODO|FIXME)\\s*:?\\s*(.+)"

# Find URLs
"https?://[^\\s)>]+"

# Find code blocks
"```python([^`]+)```"
```

**Returns:**
```json
{
  "pattern": "def\\s+search\\w*",
  "count": 2,
  "results": [
    {
      "path": "code/utils.py",
      "match_count": 3,
      "matches": [
        {
          "match": "def search_notes",
          "line": 42,
          "context": "...async def search_notes(query)..."
        }
      ]
    }
  ]
}
```

#### `list_notes`
List notes in your vault with optional recursive traversal.

**Parameters:**
- `directory` (optional): Specific directory to list (e.g., "Daily", "Projects")
- `recursive` (default: `true`): List all notes recursively

**Returns:**
```json
{
  "directory": "Daily",
  "recursive": true,
  "count": 365,
  "notes": [
    {"path": "Daily/2024-01-01.md", "name": "2024-01-01.md"},
    {"path": "Daily/2024-01-02.md", "name": "2024-01-02.md"}
  ]
}
```

#### `list_folders`
List folders in your vault with optional recursive traversal.

**Parameters:**
- `directory` (optional): Specific directory to list from
- `recursive` (default: `true`): Include all nested subfolders

**Returns:**
```json
{
  "directory": "Projects",
  "recursive": true,
  "count": 12,
  "folders": [
    {"path": "Projects/Active", "name": "Active"},
    {"path": "Projects/Archive", "name": "Archive"},
    {"path": "Projects/Ideas", "name": "Ideas"}
  ]
}
```

### Organization

#### `create_folder`
Create a new folder in the vault, including all parent folders in the path.

**Parameters:**
- `folder_path`: Path of the folder to create (e.g., "Apple/Studies/J71P")
- `create_placeholder` (default: `true`): Whether to create a placeholder file

**Returns:**
```json
{
  "folder": "Apple/Studies/J71P",
  "created": true,
  "placeholder_file": "Apple/Studies/J71P/.gitkeep",
  "folders_created": ["Apple", "Apple/Studies", "Apple/Studies/J71P"]
}
```

**Note:** This tool will create all necessary parent folders. For example, if "Apple" exists but "Studies" doesn't, it will create both "Studies" and "J71P".

#### `move_note`
Move a note to a new location.

**Parameters:**
- `source_path`: Current path of the note
- `destination_path`: New path for the note
- `update_links` (default: `true`): Update links in other notes (future enhancement)

#### `move_folder`
Move an entire folder and all its contents to a new location.

**Parameters:**
- `source_folder`: Current folder path (e.g., "Projects/Old")
- `destination_folder`: New folder path (e.g., "Archive/Projects/Old")
- `update_links` (default: `true`): Update links in other notes (future enhancement)

**Returns:**
```json
{
  "source": "Projects/Completed",
  "destination": "Archive/2024/Projects",
  "moved": true,
  "notes_moved": 15,
  "folders_moved": 3,
  "links_updated": 0
}
```

#### `add_tags`
Add tags to a note's frontmatter.

**Parameters:**
- `path`: Path to the note
- `tags`: List of tags to add (without # prefix)

#### `update_tags`
Update tags on a note - either replace all tags or merge with existing.

**Parameters:**
- `path`: Path to the note
- `tags`: New tags to set (without # prefix)
- `merge` (default: `false`): If true, adds to existing tags. If false, replaces all tags

**Perfect for AI workflows:**
```
User: "Tell me what this note is about and add appropriate tags"
AI: [reads note] "This note is about machine learning research..."
AI: [uses update_tags to set tags: ["ai", "research", "neural-networks"]]
```

#### `remove_tags`
Remove tags from a note's frontmatter.

**Parameters:**
- `path`: Path to the note
- `tags`: List of tags to remove

#### `get_note_info`
Get metadata and statistics about a note without retrieving its full content.

**Parameters:**
- `path`: Path to the note

**Returns:**
```json
{
  "path": "Projects/AI Research.md",
  "exists": true,
  "metadata": {
    "tags": ["ai", "research"],
    "aliases": [],
    "frontmatter": {}
  },
  "stats": {
    "size_bytes": 4523,
    "word_count": 823,
    "link_count": 12
  }
}
```

#### `list_tags`
List all unique tags used across your vault with usage statistics.

**Parameters:**
- `include_counts` (default: `true`): Include usage count for each tag
- `sort_by` (default: `"name"`): Sort by "name" or "count"

**Returns:**
```json
{
  "total_tags": 25,
  "tags": [
    {"name": "project", "count": 42},
    {"name": "meeting", "count": 38},
    {"name": "idea", "count": 15}
  ]
}
```

**Performance Notes:**
- Fast for small vaults (<1000 notes)
- May take several seconds for large vaults
- Uses concurrent batching for optimization

### Link Management

**⚡ Performance Note:** Link management tools have been heavily optimized in v1.1.5:
- **84x faster** link validity checking
- **96x faster** broken link detection
- **2x faster** backlink searches
- Includes automatic caching and batch processing

#### `get_backlinks`
Find all notes that link to a specific note.

**Parameters:**
- `path`: Path to the note to find backlinks for
- `include_context` (default: `true`): Whether to include text context around links
- `context_length` (default: `100`): Number of characters of context to include

**Returns:**
```json
{
  "target_note": "Projects/AI Research.md",
  "backlink_count": 5,
  "backlinks": [
    {
      "source_path": "Daily/2024-01-15.md",
      "link_text": "AI Research",
      "link_type": "wiki",
      "context": "...working on the [[AI Research]] project today..."
    }
  ]
}
```

**Use cases:**
- Understanding which notes reference a concept or topic
- Discovering relationships between notes
- Building a mental map of note connections

#### `get_outgoing_links`
List all links from a specific note.

**Parameters:**
- `path`: Path to the note to extract links from
- `check_validity` (default: `false`): Whether to check if linked notes exist

**Returns:**
```json
{
  "source_note": "Projects/Overview.md",
  "link_count": 8,
  "links": [
    {
      "path": "Projects/AI Research.md",
      "display_text": "AI Research",
      "type": "wiki",
      "exists": true
    }
  ]
}
```

**Use cases:**
- Understanding what a note references
- Checking note dependencies before moving/deleting
- Exploring the structure of index or hub notes

#### `find_broken_links`
Find all broken links in the vault, a specific directory, or a single note.

**Parameters:**
- `directory` (optional): Specific directory to check (defaults to entire vault)
- `single_note` (optional): Check only this specific note for broken links

**Returns:**
```json
{
  "directory": "/",
  "broken_link_count": 3,
  "affected_notes": 2,
  "broken_links": [
    {
      "source_path": "Projects/Overview.md",
      "broken_link": "Projects/Old Name.md",
      "link_text": "Old Project",
      "link_type": "wiki"
    }
  ]
}
```

**Use cases:**
- After renaming or deleting notes
- Regular vault maintenance
- Before reorganizing folder structure

## Testing

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Or with pytest directly
pytest tests/
```

Tests create temporary vaults for isolation and don't require a running Obsidian instance.

### Testing with MCP Inspector

1. **Set your vault path:**
   ```bash
   export OBSIDIAN_VAULT_PATH="/path/to/your/vault"
   ```

2. **Run the MCP Inspector:**
   ```bash
   npx @modelcontextprotocol/inspector python -m obsidian_mcp.server
   ```

3. **Open the Inspector UI** at `http://localhost:5173`

4. **Test the tools** interactively with your actual vault

## Integration with Claude Desktop

For development installations, see the [Development Installation](#development-installation) section above.

## Enhanced Error Handling

The server provides detailed, actionable error messages to help AI systems recover from errors:

### Example Error Messages

**Invalid Path**:
```
Invalid note path: '../../../etc/passwd'. 
Valid paths must: 1) End with .md or .markdown, 2) Use forward slashes (e.g., 'folder/note.md'), 
3) Not contain '..' or start with '/', 4) Not exceed 255 characters. 
Example: 'Daily/2024-01-15.md' or 'Projects/My Project.md'
```

**Empty Search Query**:
```
Search query cannot be empty. 
Valid queries: 1) Keywords: 'machine learning', 
2) Tags: 'tag:#project', 3) Paths: 'path:Daily/', 
4) Combined: 'tag:#urgent TODO'
```

**Invalid Date Parameters**:
```
Invalid date_type: 'invalid'. 
Must be either 'created' or 'modified'. 
Use 'created' to find notes by creation date, 'modified' for last edit date
```

## Troubleshooting

### "Vault not found" error
- Ensure the OBSIDIAN_VAULT_PATH environment variable is set correctly
- Verify the path points to an existing Obsidian vault directory
- Check that you have read/write permissions for the vault directory

### Tags not showing up
- Ensure tags are properly formatted (with or without # prefix)
- Tags in frontmatter should be in YAML array format: `tags: [tag1, tag2]`
- Inline tags should use the # prefix: `#project #urgent`
- Tags inside code blocks are automatically excluded

### "File too large" error
- The server has a 10MB limit for note files and 50MB for images
- This prevents memory issues with very large files
- Consider splitting large notes into smaller ones

### "Module not found" error
- Ensure your virtual environment is activated
- Run from the project root: `python -m obsidian_mcp.server`
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Empty results when listing notes
- Specify a directory when using `list_notes` (e.g., "Daily", "Projects")
- Root directory listing requires recursive implementation
- Check if notes are in subdirectories

### Tags not updating
- Ensure notes have YAML frontmatter section for frontmatter tags
- Frontmatter must include a `tags:` field (even if empty)
- The server now properly reads both frontmatter tags and inline hashtags

## Best Practices for AI Assistants

### Preventing Data Loss

1. **Always read before updating**: The `update_note` tool REPLACES content by default
2. **Use append mode for additions**: When adding to existing notes, use `merge_strategy="append"`
3. **Check note existence**: Use `read_note` to verify a note exists before modifying
4. **Be explicit about overwrites**: Only use `overwrite=true` when intentionally replacing content

### Recommended Workflows

**Safe note editing:**
1. Read the existing note first
2. Modify the content as needed
3. Update with the complete new content

**Adding to daily notes:**
- Use `merge_strategy="append"` to add entries without losing existing content

**Creating new notes:**
- Use `create_note` with `overwrite=false` (default) to prevent accidental overwrites
- Add relevant tags to maintain organization
- Use `list_tags` to see existing tags and avoid creating duplicates

**Organizing with tags:**
- Check existing tags with `list_tags` before creating new ones
- Maintain consistent naming (e.g., use "project" not "projects")
- Use tags to enable powerful search and filtering

## Security Considerations

- **Vault path access** - The server only accesses the specified vault directory
- The server validates all paths to prevent directory traversal attacks
- File operations are restricted to the vault directory
- Large files are rejected to prevent memory exhaustion
- Path validation prevents access to system files

## Development

### Code Style
- Uses FastMCP framework for MCP implementation
- Pydantic models for type safety and validation
- Modular architecture with separated concerns
- Comprehensive error handling and user-friendly messages

### Adding New Tools
1. Create tool function in appropriate module under `src/tools/`
2. Add Pydantic models if needed in `src/models/`
3. Register the tool in `src/server.py` with the `@mcp.tool()` decorator
4. Include comprehensive docstrings
5. Add tests in `tests/`
6. Test with MCP Inspector before deploying

## Changelog

### v1.1.8 (2025-01-15)
- 🔧 Fixed FastMCP compatibility issue that prevented PyPI package from running
- 📦 Updated to FastMCP 2.8.1 for better stability
- 🐛 Fixed Pydantic V2 deprecation warnings (migrated to @field_validator)
- ✨ Changed FastMCP initialization to use 'instructions' parameter
- 🚀 Improved compatibility with uvx and pipx installation methods

### v1.1.7 (2025-01-10)
- 🔄 Changed default API endpoint to HTTP (`http://127.0.0.1:27123`) for easier setup
- 📝 Updated documentation to reflect HTTP as default, HTTPS as optional
- 🔧 Added note about automatic trailing slash handling in URLs
- ✨ Improved first-time user experience with zero-configuration setup

### v1.1.6 (2025-01-10)
- 🐛 Fixed timeout errors when creating or updating large notes
- ⚡ Added graceful timeout handling for better reliability with large content
- 🔧 Improved error reporting to prevent false failures on successful operations

### v1.1.5 (2025-01-09)
- ⚡ **Massive performance optimization for link management:**
  - 84x faster link validity checking
  - 96x faster broken link detection  
  - 2x faster backlink searches
  - Added automatic caching and batch processing
- 🔧 Optimized concurrent operations for large vaults
- 📝 Enhanced documentation for performance considerations

### v1.1.4 (2025-01-09)
- 🔗 Added link management tools for comprehensive vault analysis:
  - `get_backlinks` - Find all notes linking to a specific note
  - `get_outgoing_links` - List all links from a note with validity checking
  - `find_broken_links` - Identify broken links for vault maintenance
- 🔧 Fixed URL construction to support both HTTPS (default) and HTTP endpoints
- 📝 Enhanced link parsing to handle both wiki-style and markdown links
- ⚡ Optimized backlink search to handle various path formats

### v1.1.3 (2025-01-09)
- 🐛 Fixed search_by_date to properly find notes modified today (days_ago=0)
- ✨ Added list_folders tool for exploring vault folder structure
- ✨ Added create_folder tool that creates full folder hierarchies
- ✨ Added move_folder tool for bulk folder operations
- ✨ Added update_tags tool for AI-driven tag management
- 🐛 Fixed tag reading to properly handle both frontmatter and inline hashtags
- ✨ Added list_tags tool to discover existing tags with usage statistics
- ⚡ Optimized performance with concurrent batching for large vaults
- 📝 Improved documentation and error messages following MCP best practices
- 🎯 Enhanced create_note to encourage tag usage for better organization

### v1.1.2 (2025-01-09)
- Fixed PyPI package documentation

### v1.1.1 (2025-01-06)
- Initial PyPI release

## Publishing (for maintainers)

To publish a new version to PyPI:

```bash
# 1. Update version in pyproject.toml
# 2. Clean old builds
rm -rf dist/ build/ *.egg-info/

# 3. Build the package
python -m build

# 4. Check the package
twine check dist/*

# 5. Upload to PyPI
twine upload dist/* -u __token__ -p $PYPI_API_KEY

# 6. Create and push git tag
git tag -a v1.1.8 -m "Release version 1.1.8"
git push origin v1.1.8
```

Users can then install and run with:
```bash
# Using uvx (recommended - no installation needed)
uvx obsidian-mcp

# Or install globally with pipx
pipx install obsidian-mcp
obsidian-mcp

# Or with pip
pip install obsidian-mcp
obsidian-mcp
```

## Configuration

### Performance Notes

- **Search indexing** - The server builds an in-memory search index that refreshes every 60 seconds
- **Concurrent operations** - File operations use async I/O for better performance
- **Large vaults** - Batch operations automatically adjust size based on vault size
- **Image handling** - Images are base64 encoded which uses more memory

### Migration from REST API Version

If you were using a previous version that required the Local REST API plugin:

1. **You no longer need the Obsidian Local REST API plugin** - This server now uses direct filesystem access
2. Replace `OBSIDIAN_REST_API_KEY` with `OBSIDIAN_VAULT_PATH` in your configuration
3. Remove any `OBSIDIAN_API_URL` settings
4. The new version is significantly faster and more reliable
5. All features work offline without requiring Obsidian to be running

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-tool`)
3. Write tests for new functionality
4. Ensure all tests pass
5. Commit your changes (`git commit -m 'Add amazing tool'`)
6. Push to the branch (`git push origin feature/amazing-tool`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Anthropic](https://anthropic.com) for creating the Model Context Protocol
- [Obsidian](https://obsidian.md) team for the amazing note-taking app
- [coddingtonbear](https://github.com/coddingtonbear) for the original Local REST API plugin (no longer required)
- [dsp-ant](https://github.com/dsp-ant) for the FastMCP framework
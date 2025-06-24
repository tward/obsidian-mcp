# Obsidian MCP Tool Patterns

This document describes the design patterns and conventions used in the Obsidian MCP server to ensure it follows reasoning-friendly MCP best practices.

## Tool Naming Convention

All tools follow a clear **verb-object** naming pattern:
- `read_note` - Read a specific note
- `create_note` - Create a new note
- `search_notes` - Search for notes
- `list_folders` - List folders
- `move_note` - Move a note
- `add_tags` - Add tags to a note

This pattern immediately conveys the tool's purpose and makes it intuitive for AI systems to understand what each tool does.

## Parameter Design

### Semantic Naming
Parameters use clear, semantic names that describe their purpose rather than technical implementation:
- ❌ `src_path` → ✅ `path` (with description: "Note location within your vault")
- ❌ `recursive_flag` → ✅ `recursive` (with description: "Include all nested subfolders")
- ❌ `ctx` → Hidden from tool interface (system parameter)

### Progressive Disclosure
Required parameters are truly essential, with optional parameters providing enhancement:
```python
# Required: Just the path
path: str

# Optional with sensible defaults
overwrite: bool = False
context_length: int = 100
recursive: bool = True
```

### AI-Friendly Descriptions
Parameter descriptions explain purpose and provide examples:
```python
path: Annotated[str, Field(
    description="Note location within your vault (e.g., 'Projects/AI Research.md'). Use forward slashes for folders.",
    examples=["Daily/2024-01-15.md", "Projects/AI Research.md"]
)]
```

## Standardized Response Structures

All tools return consistent response structures based on operation type:

### CRUD Operations (Create, Read, Update, Delete)
```python
{
    "success": True,
    "path": "Projects/AI Research.md",
    "operation": "created",  # or "read", "updated", "deleted"
    "details": {
        # Operation-specific details
    }
}
```

### Search Operations
```python
{
    "results": [...],
    "count": 42,
    "query": {
        # Search parameters used
    },
    "truncated": False
}
```

### List Operations
```python
{
    "items": [...],
    "total": 25,
    "scope": {
        # What was listed (directory, filters, etc.)
    }
}
```

### Analysis Operations (backlinks, broken links)
```python
{
    "findings": [...],
    "summary": {
        # Statistical summary
    },
    "target": "what was analyzed",
    "scope": {
        # Analysis parameters
    }
}
```

### Tag Operations
```python
{
    "success": True,
    "path": "note.md",
    "operation": "added",  # or "updated", "removed"
    "tags": {
        "before": [...],
        "after": [...],
        "changes": {
            "added": [...],
            "removed": [...]
        }
    }
}
```

### Move Operations
```python
{
    "success": True,
    "source": "old/path.md",
    "destination": "new/path.md",
    "type": "note",  # or "folder"
    "details": {
        "items_moved": 1,
        "links_updated": 0
    }
}
```

## Tool Documentation Structure

Each tool follows a consistent documentation pattern:

1. **Brief Description**: One-line summary of what the tool does
2. **When to Use**: Clear scenarios where this tool is appropriate
3. **When NOT to Use**: Alternative tools for different scenarios
4. **Examples**: Concrete usage examples with expected outputs
5. **Performance Notes**: For operations that might be slow on large vaults

Example:
```python
"""
Search for notes containing specific text or matching search criteria.

When to use:
- Finding notes by content keywords
- Locating notes with specific tags
- Searching within specific folders

When NOT to use:
- Searching by date (use search_by_date instead)
- Listing all notes (use list_notes for better performance)

Returns:
    Search results with matched notes, relevance scores, and context
"""
```

## Error Handling

All tools provide specific, actionable error messages:
```python
# Bad: Generic error
"Operation failed"

# Good: Specific with solutions
"Note not found at path: 'Daily/2024-01-15.md'. To fix: 
1) Check if the path is correct (case-sensitive), 
2) Ensure the note exists in your vault, 
3) Use list_notes to see available notes"
```

## Tool Organization

Tools are organized into logical groups:
- **Note Management**: `read_note`, `create_note`, `update_note`, `delete_note`
- **Search & Discovery**: `search_notes`, `search_by_date`, `search_by_regex`, `search_by_property`, `list_notes`, `list_folders`
- **Organization**: `move_note`, `move_folder`, `create_folder`, `add_tags`, `update_tags`, `remove_tags`, `get_note_info`, `list_tags`
- **Link Management**: `get_backlinks`, `get_outgoing_links`, `find_broken_links`
- **Image Management**: `read_image`, `view_note_images`

## Best Practices Applied

1. **Single Responsibility**: Each tool has one clear purpose
2. **Consistent Patterns**: Similar operations use similar parameter names and return structures
3. **Clear Boundaries**: Tools don't overlap in functionality
4. **Progressive Complexity**: Simple operations are simple, complex operations build on simple ones
5. **Stateless Design**: Tools don't maintain state between calls
6. **Idempotent Operations**: Safe operations can be retried without side effects

## Future Improvements

As the MCP server evolves, we maintain these principles:
- New tools follow the established patterns
- Parameter names remain consistent across tools
- Response structures use the defined templates
- Documentation follows the standard format
- Error messages provide actionable guidance
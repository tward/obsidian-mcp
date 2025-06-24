"""Search and discovery tools for Obsidian MCP server."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from ..utils.filesystem import get_vault
from ..utils import is_markdown_file
from ..utils.validation import (
    validate_search_query,
    validate_context_length,
    validate_date_search_params,
    validate_directory_path
)
from ..models import VaultItem
from ..constants import ERROR_MESSAGES


async def _search_by_tag(vault, tag: str, context_length: int) -> List[Dict[str, Any]]:
    """Search for notes containing a specific tag."""
    results = []
    
    # Get all notes
    all_notes = await vault.list_notes(recursive=True)
    
    for note_info in all_notes:
        try:
            # Read the note to get its tags
            note = await vault.read_note(note_info["path"])
            
            # Check if tag is in the note's tags
            if tag in note.metadata.tags:
                # Get context around the tag
                content = note.content
                tag_pattern = f"#{tag}"
                
                # Find tag occurrences in content
                contexts = []
                idx = 0
                while True:
                    idx = content.find(tag_pattern, idx)
                    if idx == -1:
                        break
                    
                    # Extract context
                    start = max(0, idx - context_length // 2)
                    end = min(len(content), idx + len(tag_pattern) + context_length // 2)
                    context = content[start:end].strip()
                    contexts.append(context)
                    idx += 1
                
                results.append({
                    "path": note.path,
                    "score": 1.0,
                    "matches": [tag],
                    "context": " ... ".join(contexts) if contexts else f"Note contains tag: #{tag}"
                })
        except Exception:
            # Skip notes we can't read
            continue
    
    return results


async def _search_by_path(vault, path_pattern: str, context_length: int) -> List[Dict[str, Any]]:
    """Search for notes matching a path pattern."""
    results = []
    
    # Get all notes
    all_notes = await vault.list_notes(recursive=True)
    
    for note_info in all_notes:
        # Check if path matches pattern
        if path_pattern.lower() in note_info["path"].lower():
            try:
                # Read note to get some content for context
                note = await vault.read_note(note_info["path"])
                
                # Get first N characters as context
                context = note.content[:context_length].strip()
                if len(note.content) > context_length:
                    context += "..."
                
                results.append({
                    "path": note.path,
                    "score": 1.0,
                    "matches": [path_pattern],
                    "context": context
                })
            except Exception:
                # If we can't read, still include in results
                results.append({
                    "path": note_info["path"],
                    "score": 1.0,
                    "matches": [path_pattern],
                    "context": ""
                })
    
    return results


async def search_notes(
    query: str,
    context_length: int = 100,
    ctx=None
) -> dict:
    """
    Search for notes containing specific text or matching search criteria.
    
    Use this tool to find notes by content, title, or metadata. Supports
    Obsidian's search syntax including tags, paths, and content matching.
    
    Args:
        query: Search query (supports Obsidian search syntax)
        context_length: Number of characters to show around matches (default: 100)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing search results with matched notes and context
        
    Example:
        >>> await search_notes("tag:#project AND Machine Learning", ctx=ctx)
        {
            "query": "tag:#project AND Machine Learning",
            "count": 3,
            "results": [
                {
                    "path": "Projects/ML Pipeline.md",
                    "score": 0.95,
                    "matches": ["implementing machine learning models"],
                    "context": "...focused on implementing machine learning models for production..."
                }
            ]
        }
    """
    # Validate parameters
    is_valid, error = validate_search_query(query)
    if not is_valid:
        raise ValueError(error)
    
    is_valid, error = validate_context_length(context_length)
    if not is_valid:
        raise ValueError(error)
    
    if ctx:
        ctx.info(f"Searching notes with query: {query}")
    
    vault = get_vault()
    
    try:
        # Handle special search syntax
        if query.startswith("tag:"):
            # Tag search
            tag = query[4:].lstrip("#")
            results = await _search_by_tag(vault, tag, context_length)
        elif query.startswith("path:"):
            # Path search
            path_pattern = query[5:]
            results = await _search_by_path(vault, path_pattern, context_length)
        else:
            # Regular content search
            results = await vault.search_notes(query, context_length)
        
        return {
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        if ctx:
            ctx.info(f"Search failed: {str(e)}")
        return {
            "query": query,
            "count": 0,
            "results": [],
            "error": f"Search failed: {str(e)}"
        }


async def search_by_date(
    date_type: str = "modified",
    days_ago: int = 7,
    operator: str = "within",
    ctx=None
) -> dict:
    """
    Search for notes by creation or modification date.
    
    Use this tool to find notes created or modified within a specific time period.
    This is useful for finding recent work, tracking activity, or reviewing old notes.
    
    Args:
        date_type: Either "created" or "modified" (default: "modified")
        days_ago: Number of days to look back (default: 7)
        operator: Either "within" (last N days) or "exactly" (exactly N days ago) (default: "within")
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing search results with matched notes
        
    Example:
        >>> await search_by_date("modified", 7, "within", ctx=ctx)
        {
            "query": "Notes modified within last 7 days",
            "count": 15,
            "results": [
                {
                    "path": "Daily/2024-01-15.md",
                    "date": "2024-01-15T10:30:00Z",
                    "days_ago": 1
                }
            ]
        }
    """
    # Validate parameters
    is_valid, error = validate_date_search_params(date_type, days_ago, operator)
    if not is_valid:
        raise ValueError(error)
    
    # Calculate the date threshold
    now = datetime.now()
    
    if operator == "within":
        # For "within", we want notes from the start of (now - days_ago) to now
        # Calculate the start of the target day
        target_date = now - timedelta(days=days_ago)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        query_description = f"Notes {date_type} within last {days_ago} days"
    else:
        # For "exactly", we want notes from that specific day
        target_date = now - timedelta(days=days_ago)
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        query_description = f"Notes {date_type} exactly {days_ago} days ago"
    
    if ctx:
        ctx.info(f"Searching for {query_description}")
    
    vault = get_vault()
    
    try:
        # Get all notes in the vault
        all_notes = await vault.list_notes(recursive=True)
        
        # Filter by date
        formatted_results = []
        for note_info in all_notes:
            note_path = note_info["path"]
            
            # Get file stats
            full_path = vault._ensure_safe_path(note_path)
            stat = full_path.stat()
            
            # Get the appropriate timestamp
            if date_type == "created":
                timestamp = stat.st_ctime
            else:
                timestamp = stat.st_mtime
            
            file_date = datetime.fromtimestamp(timestamp)
            
            # Check if it matches our criteria
            if operator == "within":
                if file_date >= start_date:
                    days_diff = (now - file_date).days
                    formatted_results.append({
                        "path": note_path,
                        "date": file_date.isoformat(),
                        "days_ago": days_diff
                    })
            else:
                # "exactly" - check if it's on that specific day
                if start_date <= file_date < end_date:
                    days_diff = (now - file_date).days
                    formatted_results.append({
                        "path": note_path,
                        "date": file_date.isoformat(),
                        "days_ago": days_diff
                    })
        
        # Sort by date (most recent first)
        formatted_results.sort(key=lambda x: x["date"], reverse=True)
        
        return {
            "query": query_description,
            "count": len(formatted_results),
            "results": formatted_results
        }
        
    except Exception as e:
        if ctx:
            ctx.info(f"Date search failed: {str(e)}")
        return {
            "query": query_description,
            "count": 0,
            "results": [],
            "error": f"Date-based search failed: {str(e)}"
        }


async def list_notes(
    directory: Optional[str] = None,
    recursive: bool = True,
    ctx=None
) -> dict:
    """
    List notes in the vault or a specific directory.
    
    Use this tool to browse the vault structure and discover notes. You can list
    all notes or focus on a specific directory. This is helpful when you know
    the general location but not the exact filename.
    
    Args:
        directory: Specific directory to list (optional, defaults to root)
        recursive: Whether to list all subdirectories recursively (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing vault structure and note paths
        
    Example:
        >>> await list_notes("Projects", recursive=True, ctx=ctx)
        {
            "directory": "Projects",
            "recursive": true,
            "count": 12,
            "notes": [
                {"path": "Projects/Web App.md", "name": "Web App.md"},
                {"path": "Projects/Ideas/AI Assistant.md", "name": "AI Assistant.md"}
            ]
        }
    """
    # Validate directory parameter
    is_valid, error = validate_directory_path(directory)
    if not is_valid:
        raise ValueError(error)
    
    if ctx:
        if directory:
            ctx.info(f"Listing notes in: {directory}")
        else:
            ctx.info("Listing all notes in vault")
    
    vault = get_vault()
    
    try:
        notes = await vault.list_notes(directory, recursive)
        
        return {
            "directory": directory or "/",
            "recursive": recursive,
            "count": len(notes),
            "notes": notes
        }
    except Exception as e:
        if ctx:
            ctx.info(f"Failed to list notes: {str(e)}")
        return {
            "directory": directory or "/",
            "recursive": recursive,
            "count": 0,
            "notes": [],
            "error": f"Failed to list notes: {str(e)}"
        }


async def list_folders(
    directory: Optional[str] = None,
    recursive: bool = True,
    ctx=None
) -> dict:
    """
    List folders in the vault or a specific directory.
    
    Use this tool to explore the vault's folder structure. This is helpful for
    verifying folder names before creating notes, understanding the organizational
    hierarchy, or checking if a specific folder exists.
    
    Args:
        directory: Specific directory to list folders from (optional, defaults to root)
        recursive: Whether to include all nested subfolders (default: true)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing folder structure with paths and folder counts
        
    Example:
        >>> await list_folders("Projects", recursive=True, ctx=ctx)
        {
            "directory": "Projects",
            "recursive": true,
            "count": 5,
            "folders": [
                {"path": "Projects/Active", "name": "Active"},
                {"path": "Projects/Archive", "name": "Archive"},
                {"path": "Projects/Ideas", "name": "Ideas"}
            ]
        }
    """
    # Validate directory parameter
    is_valid, error = validate_directory_path(directory)
    if not is_valid:
        raise ValueError(error)
    
    if ctx:
        if directory:
            ctx.info(f"Listing folders in: {directory}")
        else:
            ctx.info("Listing all folders in vault")
    
    vault = get_vault()
    
    try:
        # Determine search path
        if directory:
            search_path = vault._ensure_safe_path(directory)
            if not search_path.exists() or not search_path.is_dir():
                return {
                    "directory": directory,
                    "recursive": recursive,
                    "count": 0,
                    "folders": []
                }
        else:
            search_path = vault.vault_path
        
        # Find all directories
        folders = []
        if recursive:
            # Recursive search
            for path in search_path.rglob("*"):
                if path.is_dir():
                    rel_path = path.relative_to(vault.vault_path)
                    # Skip hidden directories
                    if not any(part.startswith(".") for part in rel_path.parts):
                        folders.append({
                            "path": str(rel_path),
                            "name": path.name
                        })
        else:
            # Non-recursive - only immediate subdirectories
            for path in search_path.iterdir():
                if path.is_dir():
                    rel_path = path.relative_to(vault.vault_path)
                    # Skip hidden directories
                    if not path.name.startswith("."):
                        folders.append({
                            "path": str(rel_path),
                            "name": path.name
                        })
        
        # Sort by path
        folders.sort(key=lambda x: x["path"])
        
        return {
            "directory": directory or "/",
            "recursive": recursive,
            "count": len(folders),
            "folders": folders
        }
    except Exception as e:
        if ctx:
            ctx.info(f"Failed to list folders: {str(e)}")
        return {
            "directory": directory or "/",
            "recursive": recursive,
            "count": 0,
            "folders": [],
            "error": f"Failed to list folders: {str(e)}"
        }
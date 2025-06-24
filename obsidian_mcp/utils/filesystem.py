"""Filesystem operations for Obsidian vault access."""

import os
import re
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from ..models import Note, NoteMetadata


class ObsidianVault:
    """Direct filesystem access to Obsidian vault."""
    
    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize vault access.
        
        Args:
            vault_path: Path to vault. If not provided, uses OBSIDIAN_VAULT_PATH env var.
        """
        self.vault_path = Path(vault_path or os.getenv("OBSIDIAN_VAULT_PATH", ""))
        
        if not self.vault_path:
            raise ValueError(
                "Vault path not provided. Set OBSIDIAN_VAULT_PATH environment variable "
                "or pass vault_path parameter."
            )
        
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        
        if not self.vault_path.is_dir():
            raise ValueError(f"Vault path is not a directory: {self.vault_path}")
    
    def _ensure_safe_path(self, path: str) -> Path:
        """
        Ensure the path is safe and within the vault.
        
        Args:
            path: Relative path within vault
            
        Returns:
            Full path object
            
        Raises:
            ValueError: If path is unsafe
        """
        # Remove any leading/trailing slashes
        path = path.strip("/")
        
        # Convert to Path object
        full_path = self.vault_path / path
        
        # Resolve to absolute path and check it's within vault
        try:
            resolved = full_path.resolve()
            resolved.relative_to(self.vault_path.resolve())
        except (ValueError, RuntimeError):
            raise ValueError(f"Path escapes vault: {path}")
        
        return resolved
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Full markdown content
            
        Returns:
            Tuple of (frontmatter dict, content without frontmatter)
        """
        frontmatter = {}
        clean_content = content
        
        # Check if content starts with frontmatter
        if content.startswith("---\n"):
            try:
                # Find the closing ---
                end_index = content.find("\n---\n", 4)
                if end_index != -1:
                    # Extract frontmatter
                    fm_text = content[4:end_index]
                    # Simple YAML parsing (could use yaml library for complex cases)
                    for line in fm_text.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Handle lists
                            if value.startswith('[') and value.endswith(']'):
                                value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                            # Handle quoted strings
                            elif value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            frontmatter[key] = value
                    
                    # Remove frontmatter from content
                    clean_content = content[end_index + 4:].lstrip()
            except Exception:
                # If parsing fails, just return original content
                pass
        
        return frontmatter, clean_content
    
    def _extract_tags(self, content: str, frontmatter: Dict[str, Any]) -> List[str]:
        """
        Extract all tags from content and frontmatter.
        
        Args:
            content: Markdown content
            frontmatter: Parsed frontmatter
            
        Returns:
            List of unique tags (without # prefix)
        """
        tags = set()
        
        # Get tags from frontmatter
        fm_tags = frontmatter.get("tags", [])
        if isinstance(fm_tags, str):
            fm_tags = [fm_tags]
        elif not isinstance(fm_tags, list):
            fm_tags = []
        
        for tag in fm_tags:
            if isinstance(tag, str):
                tags.add(tag.lstrip('#'))
        
        # Find inline tags in content
        inline_tags = re.findall(r'#([a-zA-Z0-9_\-/]+)', content)
        tags.update(inline_tags)
        
        return sorted(list(tags))
    
    async def read_note(self, path: str) -> Note:
        """
        Read a note from the vault.
        
        Args:
            path: Path to note relative to vault root
            
        Returns:
            Note object with content and metadata
        """
        # Ensure .md extension
        if not path.endswith('.md'):
            path += '.md'
        
        full_path = self._ensure_safe_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")
        
        # Read file content
        content = full_path.read_text(encoding='utf-8')
        
        # Parse frontmatter
        frontmatter, clean_content = self._parse_frontmatter(content)
        
        # Extract tags
        tags = self._extract_tags(clean_content, frontmatter)
        
        # Get file stats
        stat = full_path.stat()
        
        # Create metadata
        metadata = NoteMetadata(
            tags=tags,
            aliases=frontmatter.get("aliases", []),
            created=datetime.fromtimestamp(stat.st_ctime),
            modified=datetime.fromtimestamp(stat.st_mtime),
            frontmatter=frontmatter
        )
        
        return Note(
            path=path,
            content=content,
            metadata=metadata
        )
    
    async def write_note(self, path: str, content: str, overwrite: bool = False) -> Note:
        """
        Write a note to the vault.
        
        Args:
            path: Path to note relative to vault root
            content: Markdown content
            overwrite: Whether to overwrite existing file
            
        Returns:
            Created/updated Note object
        """
        # Ensure .md extension
        if not path.endswith('.md'):
            path += '.md'
        
        full_path = self._ensure_safe_path(path)
        
        # Check if exists
        if full_path.exists() and not overwrite:
            raise FileExistsError(f"Note already exists: {path}")
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        full_path.write_text(content, encoding='utf-8')
        
        # Return the newly created note
        return await self.read_note(path)
    
    async def delete_note(self, path: str) -> bool:
        """
        Delete a note from the vault.
        
        Args:
            path: Path to note relative to vault root
            
        Returns:
            True if deleted successfully
        """
        # Ensure .md extension
        if not path.endswith('.md'):
            path += '.md'
        
        full_path = self._ensure_safe_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Note not found: {path}")
        
        # Delete the file
        full_path.unlink()
        return True
    
    async def search_notes(self, query: str, context_length: int = 100) -> List[Dict[str, Any]]:
        """
        Search for notes containing query text.
        
        Args:
            query: Search query
            context_length: Characters to show around match
            
        Returns:
            List of search results
        """
        results = []
        
        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()
        
        # Search all markdown files
        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                content_lower = content.lower()
                
                # Check if query is in content
                if query_lower in content_lower:
                    # Find the match position
                    match_pos = content_lower.find(query_lower)
                    
                    # Extract context
                    start = max(0, match_pos - context_length // 2)
                    end = min(len(content), match_pos + len(query) + context_length // 2)
                    context = content[start:end].strip()
                    
                    # Get relative path
                    rel_path = md_file.relative_to(self.vault_path)
                    
                    results.append({
                        "path": str(rel_path),
                        "score": 1.0,  # Simple scoring for now
                        "matches": [query],
                        "context": context
                    })
            except Exception:
                # Skip files we can't read
                continue
        
        # Sort by score (all 1.0 for now, but ready for better scoring)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results
    
    async def list_notes(self, directory: Optional[str] = None, recursive: bool = True) -> List[Dict[str, str]]:
        """
        List all notes in vault or specific directory.
        
        Args:
            directory: Specific directory to list (optional)
            recursive: Whether to include subdirectories
            
        Returns:
            List of note paths and names
        """
        notes = []
        
        # Determine search path
        if directory:
            search_path = self._ensure_safe_path(directory)
            if not search_path.exists() or not search_path.is_dir():
                return []
        else:
            search_path = self.vault_path
        
        # Find markdown files
        pattern = "**/*.md" if recursive else "*.md"
        for md_file in search_path.glob(pattern):
            rel_path = md_file.relative_to(self.vault_path)
            notes.append({
                "path": str(rel_path),
                "name": md_file.name
            })
        
        # Sort by path
        notes.sort(key=lambda x: x["path"])
        
        return notes
    
    async def find_image(self, filename: str) -> Optional[str]:
        """
        Find an image file anywhere in the vault.
        
        Args:
            filename: Image filename to search for
            
        Returns:
            Relative path to image if found, None otherwise
        """
        # Common image extensions
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}
        
        # Check if filename has valid extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in image_extensions:
            return None
        
        # Search for the image file
        for image_file in self.vault_path.rglob(filename):
            if image_file.is_file():
                return str(image_file.relative_to(self.vault_path))
        
        return None
    
    async def read_image(self, path: str) -> Dict[str, Any]:
        """
        Read an image file from the vault.
        
        Args:
            path: Path to image relative to vault root
            
        Returns:
            Dictionary with image data and metadata
        """
        full_path = self._ensure_safe_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        # Read binary content
        content = full_path.read_bytes()
        
        # Encode to base64
        import base64
        base64_content = base64.b64encode(content).decode('utf-8')
        
        # Determine MIME type
        ext = full_path.suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
            '.bmp': 'image/bmp',
            '.ico': 'image/x-icon'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        return {
            "path": path,
            "content": base64_content,
            "mime_type": mime_type,
            "size": len(content)
        }


# Global vault instance (will be initialized in server.py)
vault: Optional[ObsidianVault] = None


def get_vault() -> ObsidianVault:
    """Get the global vault instance."""
    if vault is None:
        raise RuntimeError("Vault not initialized. Call init_vault() first.")
    return vault


def init_vault(vault_path: Optional[str] = None) -> ObsidianVault:
    """Initialize the global vault instance."""
    global vault
    vault = ObsidianVault(vault_path)
    return vault
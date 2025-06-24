"""Persistent search index using SQLite for Obsidian vault."""

import os
import hashlib
import json
import asyncio
import aiosqlite
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PersistentSearchIndex:
    """SQLite-based persistent search index for efficient vault searching."""
    
    def __init__(self, vault_path: Path, index_path: Optional[Path] = None):
        """
        Initialize persistent search index.
        
        Args:
            vault_path: Path to the Obsidian vault
            index_path: Path to store the SQLite database (defaults to vault/.obsidian/search-index.db)
        """
        self.vault_path = vault_path
        
        # Default index location in .obsidian folder
        if index_path is None:
            obsidian_dir = vault_path / ".obsidian"
            obsidian_dir.mkdir(exist_ok=True)
            self.index_path = obsidian_dir / "mcp-search-index.db"
        else:
            self.index_path = index_path
            
        self.db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize database connection and create tables if needed."""
        self.db = await aiosqlite.connect(str(self.index_path))
        
        # Enable WAL mode for better concurrent access
        await self.db.execute("PRAGMA journal_mode=WAL")
        
        # Create tables
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS file_index (
                filepath TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_lower TEXT NOT NULL,
                mtime REAL NOT NULL,
                size INTEGER NOT NULL,
                content_hash TEXT NOT NULL,
                last_indexed REAL NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create indexes for faster searching
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mtime ON file_index(mtime)
        """)
        
        # Create FTS5 virtual table for full-text search
        await self.db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS file_search
            USING fts5(
                filepath UNINDEXED,
                content,
                content_lower,
                tokenize='porter unicode61'
            )
        """)
        
        await self.db.commit()
        
    async def close(self):
        """Close database connection."""
        if self.db:
            await self.db.close()
            self.db = None
            
    async def get_file_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Get cached file information."""
        async with self._lock:
            cursor = await self.db.execute(
                "SELECT mtime, size, content_hash, last_indexed FROM file_index WHERE filepath = ?",
                (filepath,)
            )
            row = await cursor.fetchone()
            
            if row:
                return {
                    "mtime": row[0],
                    "size": row[1],
                    "content_hash": row[2],
                    "last_indexed": row[3]
                }
            return None
            
    async def needs_update(self, filepath: str, current_mtime: float, current_size: int) -> bool:
        """Check if a file needs to be re-indexed."""
        file_info = await self.get_file_info(filepath)
        
        if not file_info:
            return True
            
        # Check if file has been modified
        if file_info["mtime"] != current_mtime or file_info["size"] != current_size:
            return True
            
        return False
        
    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
        
    async def index_file(self, filepath: str, content: str, mtime: float, size: int, metadata: Optional[Dict] = None):
        """Index a single file."""
        content_hash = self._compute_hash(content)
        content_lower = content.lower()
        metadata_json = json.dumps(metadata) if metadata else None
        now = datetime.now().timestamp()
        
        async with self._lock:
            # Update main index
            await self.db.execute("""
                INSERT OR REPLACE INTO file_index 
                (filepath, content, content_lower, mtime, size, content_hash, last_indexed, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (filepath, content, content_lower, mtime, size, content_hash, now, metadata_json))
            
            # Update FTS index
            await self.db.execute(
                "DELETE FROM file_search WHERE filepath = ?",
                (filepath,)
            )
            await self.db.execute(
                "INSERT INTO file_search (filepath, content, content_lower) VALUES (?, ?, ?)",
                (filepath, content, content_lower)
            )
            
            await self.db.commit()
            
    async def remove_file(self, filepath: str):
        """Remove a file from the index."""
        async with self._lock:
            await self.db.execute("DELETE FROM file_index WHERE filepath = ?", (filepath,))
            await self.db.execute("DELETE FROM file_search WHERE filepath = ?", (filepath,))
            await self.db.commit()
            
    async def search_content(self, query: str, limit: int = 50) -> List[Tuple[str, str]]:
        """
        Search for content using FTS5.
        
        Returns list of (filepath, snippet) tuples.
        """
        # Use FTS5 for efficient full-text search
        cursor = await self.db.execute("""
            SELECT filepath, snippet(file_search, 1, '<b>', '</b>', '...', 32)
            FROM file_search
            WHERE file_search MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        results = await cursor.fetchall()
        return results
        
    async def search_simple(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Simple substring search (for compatibility with current implementation).
        
        Returns list of file info dictionaries.
        """
        query_lower = query.lower()
        cursor = await self.db.execute("""
            SELECT filepath, content, mtime, size
            FROM file_index
            WHERE content_lower LIKE ?
            LIMIT ?
        """, (f"%{query_lower}%", limit))
        
        results = []
        async for row in cursor:
            results.append({
                "filepath": row[0],
                "content": row[1],
                "mtime": row[2],
                "size": row[3]
            })
            
        return results
        
    async def get_all_files(self) -> List[str]:
        """Get list of all indexed files."""
        cursor = await self.db.execute("SELECT filepath FROM file_index")
        files = [row[0] for row in await cursor.fetchall()]
        return files
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        cursor = await self.db.execute("SELECT COUNT(*), SUM(size), MAX(last_indexed) FROM file_index")
        row = await cursor.fetchone()
        
        return {
            "total_files": row[0] or 0,
            "total_size": row[1] or 0,
            "last_update": datetime.fromtimestamp(row[2]) if row[2] else None
        }
        
    async def clear_orphaned_entries(self, existing_files: set):
        """Remove index entries for files that no longer exist."""
        async with self._lock:
            cursor = await self.db.execute("SELECT filepath FROM file_index")
            indexed_files = {row[0] for row in await cursor.fetchall()}
            
            orphaned = indexed_files - existing_files
            
            for filepath in orphaned:
                await self.remove_file(filepath)
                logger.info(f"Removed orphaned index entry: {filepath}")
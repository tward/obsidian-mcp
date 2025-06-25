#!/usr/bin/env python3
"""Comprehensive tests for search metadata implementation."""

import os
import asyncio
import tempfile
import shutil
import logging
from pathlib import Path
import pytest
import pytest_asyncio

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.utils.filesystem import ObsidianVault, init_vault
from obsidian_mcp.tools import search_notes

# Capture logging to verify deprecation warnings
logging.basicConfig(level=logging.WARNING)


class TestSearchMetadata:
    """Test suite for search metadata functionality."""
    
    @pytest_asyncio.fixture
    async def test_vault(self):
        """Create a temporary test vault with many notes."""
        temp_dir = tempfile.mkdtemp(prefix="obsidian_test_metadata_")
        os.environ["OBSIDIAN_VAULT_PATH"] = temp_dir
        
        # Create 75 notes with "common" word for testing truncation
        for i in range(75):
            note_path = Path(temp_dir) / f"note_{i:03d}.md"
            content = f"# Note {i}\n\nThis is a common note with index {i}."
            note_path.write_text(content)
        
        # Create 25 notes without "common" word
        for i in range(25):
            note_path = Path(temp_dir) / f"other_{i:02d}.md"
            content = f"# Other {i}\n\nThis is a different note without the search term."
            note_path.write_text(content)
        
        # Create notes with tags for special search testing
        tagged_note = Path(temp_dir) / "tagged.md"
        tagged_note.write_text("""---
tags: [project, important, project/web]
---
# Tagged Note

This has hierarchical tags.""")
        
        # Create notes with properties
        property_note = Path(temp_dir) / "property.md"
        property_note.write_text("""---
status: active
priority: 3
---
# Property Note

This has frontmatter properties.""")
        
        vault = init_vault(temp_dir)
        
        # Update search index
        from obsidian_mcp.utils.filesystem import get_vault
        current_vault = get_vault()
        if current_vault:
            await current_vault._update_search_index()
        
        yield vault
        
        # Cleanup
        if current_vault and current_vault.persistent_index:
            await current_vault.persistent_index.close()
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_sqlite_search_metadata(self, test_vault):
        """Test SQLite index returns correct metadata."""
        # Default limit (50)
        result = await search_notes("common")
        assert result["count"] == 50
        assert result["total_count"] == 75
        assert result["truncated"] == True
        
        # Custom small limit
        result = await search_notes("common", max_results=10)
        assert result["count"] == 10
        assert result["total_count"] == 75
        assert result["truncated"] == True
        
        # Custom large limit
        result = await search_notes("common", max_results=100)
        assert result["count"] == 75
        assert result["total_count"] == 75
        assert result["truncated"] == False
        
        # Empty results
        result = await search_notes("nonexistent")
        assert result["count"] == 0
        assert result["total_count"] == 0
        assert result["truncated"] == False
    
    
    @pytest.mark.asyncio
    async def test_max_results_parameter_validation(self, test_vault):
        """Test max_results parameter bounds."""
        # Valid values
        for max_results in [1, 50, 100, 500]:
            result = await search_notes("common", max_results=max_results)
            assert result["count"] <= max_results
        
        # Edge cases
        result = await search_notes("common", max_results=1)
        assert result["count"] == 1
        assert result["truncated"] == True
        
        result = await search_notes("common", max_results=500)
        assert result["count"] == 75  # All available results
        assert result["truncated"] == False
    
    @pytest.mark.asyncio
    async def test_special_search_metadata(self, test_vault):
        """Test metadata for special search types (tag, path, property)."""
        # Tag search - may not have truncation metadata
        result = await search_notes("tag:project")
        assert result["count"] >= 1
        assert "total_count" in result
        assert "truncated" in result
        
        # Path search
        result = await search_notes("path:note_")
        assert result["count"] > 0
        assert "total_count" in result
        
        # Property search
        result = await search_notes("property:status:active")
        assert result["count"] >= 1
        assert "total_count" in result
    
    @pytest.mark.asyncio
    async def test_exact_limit_match(self, test_vault):
        """Test when results exactly match the limit."""
        # Create exactly 50 notes with unique term
        unique_term = "exactmatch"
        for i in range(50):
            note_path = Path(os.environ["OBSIDIAN_VAULT_PATH"]) / f"exact_{i:02d}.md"
            content = f"# Exact {i}\n\nThis contains {unique_term}."
            note_path.write_text(content)
        
        # Force index update
        from obsidian_mcp.utils.filesystem import get_vault
        vault = get_vault()
        vault._index_timestamp = None
        
        # Search with default limit (50)
        result = await search_notes(unique_term)
        assert result["count"] == 50
        assert result["total_count"] == 50
        assert result["truncated"] == False  # Exactly at limit, not truncated
    
    @pytest.mark.asyncio
    async def test_single_result(self, test_vault):
        """Test metadata with single search result."""
        # Create note with unique content
        unique_path = Path(os.environ["OBSIDIAN_VAULT_PATH"]) / "unique.md"
        unique_path.write_text("# Unique\n\nThis has a uniqueidentifier123.")
        
        result = await search_notes("uniqueidentifier123")
        assert result["count"] == 1
        assert result["total_count"] == 1
        assert result["truncated"] == False
    
    @pytest.mark.asyncio
    async def test_hierarchical_tag_search(self, test_vault):
        """Test hierarchical tag search results."""
        # Search for parent tag
        result = await search_notes("tag:project")
        assert result["count"] >= 1  # Should find both project and project/web
        
        # Search for child tag
        result = await search_notes("tag:web")
        assert result["count"] >= 1  # Should find project/web
        
        # Search for exact hierarchical tag
        result = await search_notes("tag:project/web")
        assert result["count"] >= 1
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, test_vault):
        """Test that concurrent searches don't interfere with metadata."""
        # Run multiple searches concurrently
        tasks = [
            search_notes("common", max_results=10),
            search_notes("note", max_results=20),
            search_notes("different", max_results=30),
            search_notes("index", max_results=40),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Each should have correct metadata
        assert results[0]["count"] == 10
        assert results[0]["truncated"] == True
        
        assert results[1]["count"] == 20
        assert results[1]["total_count"] >= 20
        
        assert results[2]["count"] <= 30
        assert results[3]["count"] <= 40
    
    @pytest.mark.asyncio 
    async def test_search_after_vault_changes(self, test_vault):
        """Test metadata accuracy after adding/removing notes."""
        # Initial search
        result = await search_notes("common")
        initial_total = result["total_count"]
        
        # Add new notes with "common"
        for i in range(5):
            note_path = Path(os.environ["OBSIDIAN_VAULT_PATH"]) / f"new_{i}.md"
            note_path.write_text(f"# New {i}\n\nAnother common note.")
        
        # Force index update
        from obsidian_mcp.utils.filesystem import get_vault
        vault = get_vault()
        vault._index_timestamp = None
        
        # Search again
        result = await search_notes("common")
        assert result["total_count"] == initial_total + 5
        
        # Delete some notes
        for i in range(3):
            note_path = Path(os.environ["OBSIDIAN_VAULT_PATH"]) / f"note_{i:03d}.md"
            if note_path.exists():
                note_path.unlink()
        
        # Force index update and search
        vault._index_timestamp = None
        result = await search_notes("common")
        assert result["total_count"] == initial_total + 5 - 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
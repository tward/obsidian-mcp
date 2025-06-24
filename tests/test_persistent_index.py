#!/usr/bin/env python3
"""Test persistent search index functionality."""

import os
import asyncio
import tempfile
import shutil
from pathlib import Path
import pytest
import pytest_asyncio

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.utils.filesystem import ObsidianVault
from obsidian_mcp.utils.persistent_index import PersistentSearchIndex


class TestPersistentIndex:
    """Test suite for persistent search index."""
    
    @pytest_asyncio.fixture
    async def test_vault_dir(self):
        """Create a temporary vault directory."""
        temp_dir = tempfile.mkdtemp(prefix="obsidian_test_index_")
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_index_creation(self, test_vault_dir):
        """Test that index is created properly."""
        index = PersistentSearchIndex(Path(test_vault_dir))
        await index.initialize()
        
        # Check that database file was created
        db_path = Path(test_vault_dir) / ".obsidian" / "mcp-search-index.db"
        assert db_path.exists()
        
        await index.close()
    
    @pytest.mark.asyncio
    async def test_file_indexing(self, test_vault_dir):
        """Test indexing a file."""
        index = PersistentSearchIndex(Path(test_vault_dir))
        await index.initialize()
        
        # Index a test file
        await index.index_file(
            "test.md",
            "# Test Note\n\nThis is test content.",
            1234567890.0,
            100,
            {"tags": ["test"]}
        )
        
        # Check that file was indexed
        file_info = await index.get_file_info("test.md")
        assert file_info is not None
        assert file_info["mtime"] == 1234567890.0
        assert file_info["size"] == 100
        
        await index.close()
    
    @pytest.mark.asyncio
    async def test_incremental_update(self, test_vault_dir):
        """Test that only changed files are re-indexed."""
        index = PersistentSearchIndex(Path(test_vault_dir))
        await index.initialize()
        
        # Index a file
        await index.index_file("test.md", "Content 1", 1000.0, 10)
        
        # Check that it doesn't need update with same mtime/size
        assert not await index.needs_update("test.md", 1000.0, 10)
        
        # Check that it needs update with different mtime
        assert await index.needs_update("test.md", 2000.0, 10)
        
        # Check that it needs update with different size
        assert await index.needs_update("test.md", 1000.0, 20)
        
        await index.close()
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, test_vault_dir):
        """Test searching indexed content."""
        index = PersistentSearchIndex(Path(test_vault_dir))
        await index.initialize()
        
        # Index some test files
        await index.index_file("note1.md", "This is about Python programming", 1000.0, 100)
        await index.index_file("note2.md", "This is about JavaScript", 1000.0, 100)
        await index.index_file("note3.md", "Python is great for data science", 1000.0, 100)
        
        # Search for Python
        results = await index.search_simple("python", 10)
        assert len(results) == 2
        assert any(r["filepath"] == "note1.md" for r in results)
        assert any(r["filepath"] == "note3.md" for r in results)
        
        await index.close()
    
    @pytest.mark.asyncio
    async def test_vault_integration(self, test_vault_dir):
        """Test ObsidianVault with persistent index."""
        # Create test notes
        notes_dir = Path(test_vault_dir)
        (notes_dir / "note1.md").write_text("# Note 1\n\nThis is the first note about Python.")
        (notes_dir / "note2.md").write_text("# Note 2\n\nThis is about JavaScript.")
        
        # Create vault with persistent index
        os.environ["OBSIDIAN_VAULT_PATH"] = test_vault_dir
        vault = ObsidianVault(test_vault_dir, use_persistent_index=True)
        
        # First search (builds index)
        results = await vault.search_notes("python")
        assert len(results) == 1
        assert results[0]["path"] == "note1.md"
        
        # Add a new note
        (notes_dir / "note3.md").write_text("# Note 3\n\nMore Python content here.")
        
        # Force index update
        vault._index_timestamp = None
        
        # Second search (should find new note)
        results = await vault.search_notes("python")
        assert len(results) == 2
        
        # Close vault
        await vault.close()
    
    @pytest.mark.asyncio
    async def test_persistence_across_sessions(self, test_vault_dir):
        """Test that index persists between vault instances."""
        notes_dir = Path(test_vault_dir)
        (notes_dir / "persistent_test.md").write_text("# Persistent Test\n\nThis should persist.")
        
        # First session
        vault1 = ObsidianVault(test_vault_dir, use_persistent_index=True)
        results1 = await vault1.search_notes("persist")
        assert len(results1) == 1
        await vault1.close()
        
        # Second session (should use existing index)
        vault2 = ObsidianVault(test_vault_dir, use_persistent_index=True)
        # Don't update index timestamp to test persistence
        vault2._index_timestamp = 9999999999  # Far future
        
        results2 = await vault2.search_notes("persist")
        assert len(results2) == 1  # Should find the note without re-indexing
        
        await vault2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
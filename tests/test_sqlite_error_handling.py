#!/usr/bin/env python3
"""Tests for SQLite error handling and fallback scenarios."""

import os
import asyncio
import tempfile
import shutil
import logging
from pathlib import Path
import pytest
import pytest_asyncio
import stat

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.utils.filesystem import ObsidianVault
from obsidian_mcp.utils.persistent_index import PersistentSearchIndex


class TestSQLiteErrorHandling:
    """Test suite for SQLite initialization error handling."""
    
    @pytest_asyncio.fixture
    async def test_vault_dir(self):
        """Create a temporary vault directory."""
        temp_dir = tempfile.mkdtemp(prefix="obsidian_test_error_")
        
        # Create some test notes
        for i in range(5):
            note_path = Path(temp_dir) / f"note_{i}.md"
            note_path.write_text(f"# Note {i}\n\nTest content with searchable text.")
        
        yield temp_dir
        
        # Cleanup - restore permissions first
        for root, dirs, files in os.walk(temp_dir):
            for d in dirs:
                os.chmod(os.path.join(root, d), stat.S_IRWXU)
            for f in files:
                os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR)
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_read_only_obsidian_dir(self, test_vault_dir, caplog):
        """Test handling of read-only .obsidian directory."""
        # Create .obsidian directory
        obsidian_dir = Path(test_vault_dir) / ".obsidian"
        obsidian_dir.mkdir()
        
        # Make it read-only
        os.chmod(obsidian_dir, stat.S_IRUSR | stat.S_IXUSR)  # r-x------
        
        # Try to create vault - should fall back to memory index
        with caplog.at_level(logging.INFO):
            vault = ObsidianVault(test_vault_dir)
            await vault._update_search_index()
            
            # Should see error and fallback messages
            assert any("unable to open database file" in record.message for record in caplog.records) or \
                   any("falling back" in record.message.lower() for record in caplog.records) or \
                   any("deprecation" in record.message.lower() for record in caplog.records)
            
            # Search should still work (using memory index)
            results = await vault.search_notes("searchable")
            assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_no_write_permissions_vault(self, test_vault_dir, caplog):
        """Test handling when entire vault is read-only."""
        # Make vault read-only
        os.chmod(test_vault_dir, stat.S_IRUSR | stat.S_IXUSR)  # r-x------
        
        # Try to create vault
        with caplog.at_level(logging.WARNING):
            try:
                vault = ObsidianVault(test_vault_dir)
                # Should either work with fallback or raise error
                await vault._update_search_index()
                
                # If it worked, should be using memory index
                assert vault.persistent_index is None or not vault._persistent_index_initialized
                assert any("deprecation" in record.message.lower() for record in caplog.records)
            except Exception as e:
                # If it failed, should have helpful error message
                assert "permission" in str(e).lower() or "read-only" in str(e).lower()
        
        # Restore permissions for cleanup
        os.chmod(test_vault_dir, stat.S_IRWXU)
    
    @pytest.mark.asyncio
    async def test_corrupted_database_recovery(self, test_vault_dir, caplog):
        """Test handling of corrupted database file."""
        # Create .obsidian directory
        obsidian_dir = Path(test_vault_dir) / ".obsidian"
        obsidian_dir.mkdir()
        
        # Create corrupted database file
        db_path = obsidian_dir / "mcp-search-index.db"
        db_path.write_text("This is not a valid SQLite database!")
        
        # Try to create vault
        with caplog.at_level(logging.ERROR):
            vault = ObsidianVault(test_vault_dir)
            await vault._update_search_index()
            
            # Should see error about database
            assert any("database" in record.message.lower() for record in caplog.records)
            
            # Search should still work (fallback to memory)
            results = await vault.search_notes("searchable")
            assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_missing_obsidian_dir_creation(self, test_vault_dir):
        """Test that .obsidian directory is created if missing."""
        # Ensure no .obsidian directory exists
        obsidian_dir = Path(test_vault_dir) / ".obsidian"
        if obsidian_dir.exists():
            shutil.rmtree(obsidian_dir)
        
        # Create vault with persistent index
        vault = ObsidianVault(test_vault_dir, use_persistent_index=True)
        await vault._update_search_index()
        
        # .obsidian directory should be created
        assert obsidian_dir.exists()
        
        # Database should exist
        db_path = obsidian_dir / "mcp-search-index.db"
        assert db_path.exists()
        
        # Search should work
        results = await vault.search_notes("searchable")
        assert len(results) == 5
        
        # Clean up
        if vault.persistent_index:
            await vault.persistent_index.close()
    
    @pytest.mark.asyncio
    async def test_explicit_memory_index_warning(self, test_vault_dir, caplog):
        """Test deprecation warning when explicitly choosing memory index."""
        # Clear any previous warnings
        ObsidianVault._memory_index_warning_shown = False
        
        with caplog.at_level(logging.WARNING):
            vault = ObsidianVault(test_vault_dir, use_persistent_index=False)
            
            # Should see deprecation warning
            assert any("DEPRECATION WARNING" in record.message for record in caplog.records)
            assert any("memory-based search index is deprecated" in record.message.lower() for record in caplog.records)
            
            # Search should work
            await vault._update_search_index()
            results = await vault.search_notes("searchable")
            assert len(results) == 5
    
    @pytest.mark.asyncio
    async def test_actionable_error_messages(self, test_vault_dir, caplog):
        """Test that error messages provide actionable guidance."""
        # Create a file where directory should be
        obsidian_file = Path(test_vault_dir) / ".obsidian"
        obsidian_file.write_text("This is a file, not a directory")
        
        with caplog.at_level(logging.ERROR):
            vault = ObsidianVault(test_vault_dir)
            await vault._update_search_index()
            
            # Should see helpful error messages
            error_found = False
            for record in caplog.records:
                if record.levelname == "ERROR":
                    error_found = True
                    msg = record.message.lower()
                    # Check for actionable guidance
                    assert any(word in msg for word in [
                        "permission", "write", "database", "corrupted", 
                        "missing", "package", "aiosqlite"
                    ])
            
            assert error_found or vault.persistent_index is None
    
    @pytest.mark.asyncio
    async def test_fallback_preserves_functionality(self, test_vault_dir):
        """Test that all search features work after fallback to memory index."""
        # Force SQLite to fail by creating invalid .obsidian entry
        obsidian_path = Path(test_vault_dir) / ".obsidian"
        obsidian_path.write_text("not a directory")
        
        vault = ObsidianVault(test_vault_dir, use_persistent_index=True)
        await vault._update_search_index()
        
        # All search types should work
        
        # Content search
        results = await vault.search_notes("searchable")
        assert len(results) == 5
        
        # With max_results
        results = await vault.search_notes("searchable", max_results=3)
        assert len(results) == 3
        metadata = vault.get_last_search_metadata()
        assert metadata["truncated"] == True
        
        # Empty search
        results = await vault.search_notes("nonexistent")
        assert len(results) == 0
        
        # Clean up
        os.remove(obsidian_path)
    
    @pytest.mark.asyncio
    async def test_concurrent_initialization_errors(self, test_vault_dir, caplog):
        """Test handling of concurrent vault initialization with errors."""
        # Make .obsidian directory read-only after creation
        obsidian_dir = Path(test_vault_dir) / ".obsidian"
        obsidian_dir.mkdir()
        os.chmod(obsidian_dir, stat.S_IRUSR | stat.S_IXUSR)
        
        # Try to create multiple vaults concurrently
        async def create_vault_and_search():
            try:
                vault = ObsidianVault(test_vault_dir)
                await vault._update_search_index()
                results = await vault.search_notes("searchable")
                return len(results)
            except Exception as e:
                return str(e)
        
        # Run concurrent operations
        results = await asyncio.gather(
            create_vault_and_search(),
            create_vault_and_search(),
            create_vault_and_search(),
            return_exceptions=True
        )
        
        # All should either succeed with fallback or fail gracefully
        for result in results:
            if isinstance(result, int):
                assert result == 5  # Found all notes
            else:
                assert isinstance(result, str)  # Error message
        
        # Restore permissions
        os.chmod(obsidian_dir, stat.S_IRWXU)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
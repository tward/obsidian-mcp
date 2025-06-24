#!/usr/bin/env python3
"""Test optimized regex search functionality."""

import os
import re
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
from obsidian_mcp.tools import search_by_regex


class TestRegexOptimization:
    """Test suite for regex search optimization."""
    
    @pytest_asyncio.fixture
    async def test_vault_dir(self):
        """Create a temporary vault directory with test content."""
        temp_dir = tempfile.mkdtemp(prefix="obsidian_test_regex_")
        
        # Create test notes with various patterns
        test_files = {
            "code_example.md": """# Code Examples

Here's a Python function:

```python
def search_notes(query: str) -> List[str]:
    '''Search through all notes'''
    return results

def filter_by_tags(tags: List[str]) -> None:
    pass
```

TODO: Add more examples
FIXME: Handle edge cases
""",
            "urls_and_links.md": """# Resources

Check out these links:
- https://example.com/docs
- http://test.org/api
- [GitHub](https://github.com/test/repo)

More info at https://docs.python.org/3/
""",
            "tags_example.md": """---
tags: [python, testing, regex]
---

# Tag Examples

This note has #python and #testing tags.
Also mentions #regex-patterns and #code-search.
""",
        }
        
        for filename, content in test_files.items():
            (Path(temp_dir) / filename).write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_regex_with_persistent_index(self, test_vault_dir):
        """Test that regex search uses persistent index efficiently."""
        vault = ObsidianVault(test_vault_dir, use_persistent_index=True)
        
        # First do a simple search to ensure index is built
        _ = await vault.search_notes("def")
        
        # Search for function definitions - simpler pattern
        results = await vault.search_by_regex(
            r"def\s+\w+",  # Simpler pattern without the full function signature
            max_results=10
        )
        
        assert len(results) > 0
        assert results[0]["path"] == "code_example.md"
        assert results[0]["match_count"] >= 2  # At least 2 functions
        
        # Check that matches are found
        matches = results[0]["matches"]
        assert len(matches) >= 2
        assert "search_notes" in matches[0]["match"]
        assert matches[0]["line"] > 0
        
        await vault.close()
    
    @pytest.mark.asyncio
    async def test_regex_early_termination(self, test_vault_dir):
        """Test that regex search stops early when limit is reached."""
        vault = ObsidianVault(test_vault_dir, use_persistent_index=True)
        
        # Search with a very low limit
        results = await vault.search_by_regex(
            r"#[a-zA-Z0-9_\-/]+",  # Match hashtags
            max_results=1
        )
        
        assert len(results) == 1  # Should stop after finding first result
        
        await vault.close()
    
    @pytest.mark.asyncio
    async def test_regex_line_numbers(self, test_vault_dir):
        """Test that line numbers are calculated correctly."""
        vault = ObsidianVault(test_vault_dir, use_persistent_index=True)
        
        # Search for TODO comments
        results = await vault.search_by_regex(
            r"TODO\s*:?\s*(.+)",
            flags=re.IGNORECASE
        )
        
        assert len(results) > 0
        for result in results:
            for match in result["matches"]:
                assert match["line"] > 0  # Line numbers should be positive
                assert "TODO" in match["match"].upper()
        
        await vault.close()
    
    @pytest.mark.asyncio
    async def test_regex_with_groups(self, test_vault_dir):
        """Test regex with capture groups."""
        vault = ObsidianVault(test_vault_dir, use_persistent_index=True)
        
        # Search for URLs with protocol group
        results = await vault.search_by_regex(
            r"(https?)://([^\s)>]+)"
        )
        
        assert len(results) > 0
        for result in results:
            for match in result["matches"]:
                assert match["groups"] is not None
                assert len(match["groups"]) == 2  # Protocol and domain
                assert match["groups"][0] in ["http", "https"]
        
        await vault.close()
    
    @pytest.mark.asyncio 
    async def test_regex_fallback_to_memory(self, test_vault_dir):
        """Test that regex falls back to memory index when persistent is disabled."""
        vault = ObsidianVault(test_vault_dir, use_persistent_index=False)
        
        # Should still work with in-memory index
        results = await vault.search_by_regex(
            r"def\s+\w+",
            max_results=10
        )
        
        assert len(results) > 0
        assert results[0]["path"] == "code_example.md"
        
        await vault.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
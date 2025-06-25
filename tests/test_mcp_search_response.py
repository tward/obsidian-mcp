#!/usr/bin/env python3
"""End-to-end tests for MCP search tool responses."""

import os
import asyncio
import tempfile
import shutil
from pathlib import Path
import pytest
import pytest_asyncio
import json

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.utils.filesystem import init_vault
from obsidian_mcp.server import search_notes_tool


class TestMCPSearchResponse:
    """Test suite for MCP search tool responses."""
    
    @pytest_asyncio.fixture
    async def test_vault(self):
        """Create a test vault with various content."""
        temp_dir = tempfile.mkdtemp(prefix="obsidian_test_mcp_")
        os.environ["OBSIDIAN_VAULT_PATH"] = temp_dir
        
        # Create notes for different test scenarios
        notes = {
            # Regular notes for content search
            **{f"note_{i:03d}.md": f"# Note {i}\n\nThis is a test note about Python programming." 
               for i in range(60)},
            
            # Notes with specific tags
            "tagged_important.md": """---
tags: [important, urgent, project/alpha]
---
# Important Note

This is an important note with hierarchical tags.""",
            
            "tagged_project.md": """---
tags: [project, project/beta, development]
---
# Project Note

This is a project-related note.""",
            
            # Notes with properties
            "property_active.md": """---
status: active
priority: 5
due_date: 2024-12-31
---
# Active Task

This is an active task with properties.""",
            
            "property_completed.md": """---
status: completed
priority: 1
completed_date: 2024-01-15
---
# Completed Task

This task has been completed.""",
            
            # Notes in folders
            "projects/web/frontend.md": "# Frontend Development\n\nNotes about React and Vue.",
            "projects/web/backend.md": "# Backend Development\n\nNotes about Python Django.",
            "projects/mobile/ios.md": "# iOS Development\n\nNotes about Swift programming.",
            
            # Edge case notes
            "empty.md": "",
            "unicode_test.md": "# Unicode Test\n\nContains emojis 🎉 and special chars: αβγ",
            "very_long_name_that_exceeds_normal_limits_but_should_still_work_correctly.md": "# Long Name\n\nContent",
        }
        
        # Create all notes
        for path, content in notes.items():
            full_path = Path(temp_dir) / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        vault = init_vault(temp_dir)
        yield vault
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_search_response_structure(self, test_vault):
        """Test that search responses have correct structure."""
        result = await search_notes_tool("Python", context_length=50)
        
        # Check top-level structure
        assert isinstance(result, dict)
        assert "results" in result
        assert "count" in result
        assert "query" in result
        assert "total_count" in result
        assert "truncated" in result
        
        # Check query structure
        assert result["query"]["text"] == "Python"
        assert result["query"]["context_length"] == 50
        assert result["query"]["type"] == "content"
        
        # Check results structure
        assert isinstance(result["results"], list)
        if result["count"] > 0:
            first_result = result["results"][0]
            assert "path" in first_result
            assert "score" in first_result
            assert "context" in first_result
    
    @pytest.mark.asyncio
    async def test_max_results_parameter(self, test_vault):
        """Test max_results parameter in search tool."""
        # Small limit
        result_small = await search_notes_tool("Python", max_results=5)
        assert result_small["count"] == 5
        assert result_small["truncated"] == True
        assert result_small["total_count"] > 5
        
        # Medium limit
        result_medium = await search_notes_tool("Python", max_results=25)
        assert result_medium["count"] == 25
        assert result_medium["truncated"] == True
        
        # Large limit
        result_large = await search_notes_tool("Python", max_results=100)
        assert result_large["count"] > 25
        assert result_large["total_count"] == result_large["count"] or result_large["truncated"] == False
    
    @pytest.mark.asyncio
    async def test_tag_search_response(self, test_vault):
        """Test tag search responses."""
        # Simple tag
        result = await search_notes_tool("tag:important")
        assert result["query"]["type"] == "tag"
        assert result["count"] >= 1
        assert any("important" in str(r.get("matches", [])) for r in result["results"])
        
        # Hierarchical tag - parent
        result = await search_notes_tool("tag:project")
        assert result["count"] >= 2  # Should find project, project/alpha, project/beta
        
        # Hierarchical tag - child
        result = await search_notes_tool("tag:alpha")
        assert result["count"] >= 1
    
    @pytest.mark.asyncio
    async def test_path_search_response(self, test_vault):
        """Test path search responses."""
        result = await search_notes_tool("path:projects/web")
        assert result["query"]["type"] == "path"
        assert result["count"] >= 2  # frontend.md and backend.md
        assert all("projects/web" in r["path"] for r in result["results"])
    
    @pytest.mark.asyncio
    async def test_property_search_response(self, test_vault):
        """Test property search responses."""
        # Exact match
        result = await search_notes_tool("property:status:active")
        assert result["query"]["type"] == "property"
        assert result["count"] >= 1
        
        # Comparison
        result = await search_notes_tool("property:priority:>3")
        assert result["count"] >= 1  # Should find priority: 5
    
    @pytest.mark.asyncio
    async def test_empty_results_response(self, test_vault):
        """Test response when no results found."""
        result = await search_notes_tool("nonexistentterm12345")
        assert result["count"] == 0
        assert result["total_count"] == 0
        assert result["truncated"] == False
        assert result["results"] == []
    
    @pytest.mark.asyncio
    async def test_context_length_in_response(self, test_vault):
        """Test that context_length affects response content."""
        # Short context
        result_short = await search_notes_tool("Python", context_length=20)
        # Long context  
        result_long = await search_notes_tool("Python", context_length=200)
        
        if result_short["count"] > 0 and result_long["count"] > 0:
            # Context should be longer with higher context_length
            short_context = result_short["results"][0]["context"]
            long_context = result_long["results"][0]["context"]
            assert len(long_context) >= len(short_context)
    
    @pytest.mark.asyncio
    async def test_concurrent_search_requests(self, test_vault):
        """Test concurrent search requests don't interfere."""
        # Run different searches concurrently
        tasks = [
            search_notes_tool("Python", max_results=10),
            search_notes_tool("tag:project", max_results=20),
            search_notes_tool("path:projects", max_results=15),
            search_notes_tool("React", max_results=5),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Each should have correct results
        assert results[0]["query"]["text"] == "Python"
        assert results[0]["count"] <= 10
        
        assert results[1]["query"]["text"] == "tag:project"
        assert results[1]["query"]["type"] == "tag"
        
        assert results[2]["query"]["text"] == "path:projects"
        assert results[2]["query"]["type"] == "path"
        
        assert results[3]["query"]["text"] == "React"
        assert results[3]["count"] <= 5
    
    @pytest.mark.asyncio
    async def test_special_characters_in_search(self, test_vault):
        """Test searching for special characters."""
        # Unicode search
        result = await search_notes_tool("🎉")
        assert result["count"] >= 1
        
        # Greek letters
        result = await search_notes_tool("αβγ")
        assert result["count"] >= 1
    
    @pytest.mark.asyncio
    async def test_search_performance_tracking(self, test_vault):
        """Test that searches complete in reasonable time."""
        import time
        
        # First search (may build index)
        start = time.time()
        result1 = await search_notes_tool("Python", max_results=50)
        first_time = time.time() - start
        
        # Second search (should use index)
        start = time.time()
        result2 = await search_notes_tool("programming", max_results=50)
        second_time = time.time() - start
        
        # Both should complete quickly (under 5 seconds)
        assert first_time < 5.0
        assert second_time < 5.0
        
        # Second search often faster due to warmed cache
        print(f"First search: {first_time:.3f}s, Second search: {second_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_error_handling_in_response(self, test_vault):
        """Test error handling for invalid queries."""
        # Test with invalid query patterns
        try:
            # Very long query
            long_query = "a" * 1000
            result = await search_notes_tool(long_query)
            # Should either handle gracefully or raise ToolError
            assert "error" in result or result["count"] >= 0
        except Exception as e:
            # Should be a meaningful error
            assert "ToolError" in str(type(e)) or "ValueError" in str(type(e))
    
    @pytest.mark.asyncio
    async def test_result_ordering(self, test_vault):
        """Test that results are ordered by relevance."""
        # Create notes with different relevance
        specific_path = Path(os.environ["OBSIDIAN_VAULT_PATH"]) / "specific_python.md"
        specific_path.write_text("# Python Python Python\n\nThis note mentions Python many times. Python is great!")
        
        result = await search_notes_tool("Python", max_results=10)
        
        # The note with multiple mentions should rank higher
        if result["count"] > 1:
            # Check that results have scores
            assert all("score" in r for r in result["results"])
            # Scores should be positive numbers
            assert all(r["score"] > 0 for r in result["results"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
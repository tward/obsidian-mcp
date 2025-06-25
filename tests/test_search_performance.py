#!/usr/bin/env python3
"""Performance tests for search functionality."""

import os
import asyncio
import tempfile
import shutil
import time
import random
import string
from pathlib import Path
import pytest
import pytest_asyncio
import psutil
import gc

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.utils.filesystem import ObsidianVault


class TestSearchPerformance:
    """Performance benchmarks for search functionality."""
    
    @pytest_asyncio.fixture
    async def large_vault(self):
        """Create a large test vault for performance testing."""
        temp_dir = tempfile.mkdtemp(prefix="obsidian_perf_test_")
        
        # Generate random words for content variety
        words = ["python", "javascript", "programming", "development", "algorithm", 
                 "data", "structure", "machine", "learning", "artificial", "intelligence",
                 "web", "mobile", "cloud", "database", "security", "performance",
                 "optimization", "testing", "debugging", "documentation"]
        
        # Create 1000 notes with varied content
        print(f"\nCreating performance test vault with 1000 notes...")
        for i in range(1000):
            # Generate random content
            content_words = random.choices(words, k=random.randint(50, 200))
            content = f"# Note {i:04d}\n\n" + " ".join(content_words)
            
            # Add some structure
            if i % 10 == 0:
                content += "\n\n## Special Section\n\nThis note is special and contains unique content."
            
            # Add tags to some notes
            if i % 5 == 0:
                tags = random.sample(["important", "project", "review", "archive"], k=random.randint(1, 3))
                content = f"---\ntags: {tags}\n---\n" + content
            
            # Create in folders
            if i % 3 == 0:
                folder = random.choice(["projects", "archive", "daily", "reference"])
                path = Path(temp_dir) / folder / f"note_{i:04d}.md"
                path.parent.mkdir(exist_ok=True)
            else:
                path = Path(temp_dir) / f"note_{i:04d}.md"
            
            path.write_text(content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_index_creation_performance(self, large_vault):
        """Test initial index creation performance."""
        # Test SQLite index
        print("\n=== SQLite Index Creation ===")
        vault_sqlite = ObsidianVault(large_vault, use_persistent_index=True)
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        await vault_sqlite._update_search_index()
        
        sqlite_time = time.time() - start_time
        sqlite_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
        
        print(f"SQLite index creation: {sqlite_time:.2f}s, Memory: {sqlite_memory:.1f}MB")
        assert sqlite_time < 30  # Should complete within 30 seconds
        
        if vault_sqlite.persistent_index:
            await vault_sqlite.persistent_index.close()
        
        # Test memory index
        print("\n=== Memory Index Creation ===")
        vault_memory = ObsidianVault(large_vault, use_persistent_index=False)
        
        gc.collect()
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        await vault_memory._update_search_index()
        
        memory_time = time.time() - start_time
        memory_memory = psutil.Process().memory_info().rss / 1024 / 1024 - start_memory
        
        print(f"Memory index creation: {memory_time:.2f}s, Memory: {memory_memory:.1f}MB")
        assert memory_time < 30  # Should complete within 30 seconds
    
    @pytest.mark.asyncio
    async def test_search_performance_comparison(self, large_vault):
        """Compare search performance between SQLite and memory index."""
        # Initialize both indexes
        vault_sqlite = ObsidianVault(large_vault, use_persistent_index=True)
        vault_memory = ObsidianVault(large_vault, use_persistent_index=False)
        
        await vault_sqlite._update_search_index()
        await vault_memory._update_search_index()
        
        search_terms = ["python", "algorithm", "special", "note 0500", "machine learning"]
        
        print("\n=== Search Performance Comparison ===")
        for term in search_terms:
            # SQLite search
            start = time.time()
            sqlite_results = await vault_sqlite.search_notes(term, max_results=50)
            sqlite_time = time.time() - start
            
            # Memory search
            start = time.time()
            memory_results = await vault_memory.search_notes(term, max_results=50)
            memory_time = time.time() - start
            
            print(f"\nSearch '{term}':")
            print(f"  SQLite: {sqlite_time:.3f}s, found {len(sqlite_results)} results")
            print(f"  Memory: {memory_time:.3f}s, found {len(memory_results)} results")
            
            # Both should be reasonably fast
            assert sqlite_time < 2.0
            assert memory_time < 2.0
        
        if vault_sqlite.persistent_index:
            await vault_sqlite.persistent_index.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self, large_vault):
        """Test performance with concurrent searches."""
        vault = ObsidianVault(large_vault)
        await vault._update_search_index()
        
        search_terms = ["python", "javascript", "data", "algorithm", "web", 
                       "mobile", "cloud", "testing", "security", "machine"]
        
        print("\n=== Concurrent Search Performance ===")
        
        # Sequential searches
        start = time.time()
        sequential_results = []
        for term in search_terms:
            result = await vault.search_notes(term, max_results=20)
            sequential_results.append(len(result))
        sequential_time = time.time() - start
        
        # Concurrent searches
        start = time.time()
        tasks = [vault.search_notes(term, max_results=20) for term in search_terms]
        concurrent_results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start
        
        print(f"Sequential: {sequential_time:.2f}s")
        print(f"Concurrent: {concurrent_time:.2f}s")
        print(f"Speedup: {sequential_time/concurrent_time:.1f}x")
        
        # Concurrent should be faster
        assert concurrent_time < sequential_time
        
        if vault.persistent_index:
            await vault.persistent_index.close()
    
    @pytest.mark.asyncio
    async def test_search_with_different_limits(self, large_vault):
        """Test how max_results affects performance."""
        vault = ObsidianVault(large_vault)
        await vault._update_search_index()
        
        limits = [10, 50, 100, 200, 500]
        
        print("\n=== Performance vs Result Limit ===")
        for limit in limits:
            start = time.time()
            results = await vault.search_notes("python", max_results=limit)
            search_time = time.time() - start
            
            metadata = vault.get_last_search_metadata()
            print(f"Limit {limit}: {search_time:.3f}s, returned {len(results)}, "
                  f"total: {metadata.get('total_count', 'N/A')}, "
                  f"truncated: {metadata.get('truncated', 'N/A')}")
            
            # Should still be fast even with high limits
            assert search_time < 3.0
        
        if vault.persistent_index:
            await vault.persistent_index.close()
    
    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self, large_vault):
        """Test memory usage with different vault sizes."""
        print("\n=== Memory Usage Scaling ===")
        
        # Test with subset of notes
        for note_count in [100, 500, 1000]:
            vault = ObsidianVault(large_vault)
            
            gc.collect()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Only index first N notes
            vault._index_batch_size = note_count
            await vault._update_search_index()
            
            # Perform searches
            for _ in range(10):
                await vault.search_notes("python", max_results=50)
            
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = end_memory - start_memory
            
            print(f"{note_count} notes: {memory_used:.1f}MB")
            
            # Memory usage should be reasonable
            assert memory_used < 500  # Less than 500MB even for 1000 notes
            
            if vault.persistent_index:
                await vault.persistent_index.close()
    
    @pytest.mark.asyncio
    async def test_incremental_update_performance(self, large_vault):
        """Test performance of incremental index updates."""
        vault = ObsidianVault(large_vault)
        
        # Initial index
        await vault._update_search_index()
        
        # Add new notes
        print("\n=== Incremental Update Performance ===")
        for i in range(10):
            new_path = Path(large_vault) / f"new_note_{i}.md"
            new_path.write_text(f"# New Note {i}\n\nThis is a newly added note with Python content.")
        
        # Force re-index
        vault._index_timestamp = None
        
        start = time.time()
        await vault._update_search_index()
        update_time = time.time() - start
        
        print(f"Incremental update (10 new notes): {update_time:.2f}s")
        
        # Should be fast since most notes are unchanged
        assert update_time < 5.0
        
        # Verify new notes are searchable
        results = await vault.search_notes("newly added")
        assert len(results) == 10
        
        if vault.persistent_index:
            await vault.persistent_index.close()
    
    @pytest.mark.asyncio
    async def test_search_result_quality(self, large_vault):
        """Test that performance optimizations don't affect result quality."""
        vault = ObsidianVault(large_vault)
        await vault._update_search_index()
        
        # Search for exact note
        results = await vault.search_notes("note 0500", max_results=10)
        assert any("note_0500.md" in r["path"] for r in results)
        
        # Search for phrase
        results = await vault.search_notes("machine learning", max_results=50)
        assert all("machine" in r["context"].lower() or "learning" in r["context"].lower() 
                  for r in results)
        
        if vault.persistent_index:
            await vault.persistent_index.close()


if __name__ == "__main__":
    # Run with: pytest tests/test_search_performance.py -v -s
    # The -s flag shows print output
    pytest.main([__file__, "-v", "-s"])
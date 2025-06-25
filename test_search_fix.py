#!/usr/bin/env python3
"""Test script for the search index timeout fix."""

import asyncio
import os
import logging
from obsidian_mcp.utils.filesystem import init_vault

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_search_fix():
    """Test the search functionality with the new timeout prevention."""
    
    # Initialize vault with your path
    os.environ["OBSIDIAN_VAULT_PATH"] = "/path/to/your/obsidian/vault"
    
    # Test with different configurations
    print("\n=== Testing with default settings ===")
    vault = init_vault()
    
    # Try a search (should work with SQLite index)
    print("\n1. Testing search...")
    try:
        results = await vault.search_notes("video inferencing", context_length=100, max_results=5)
        print(f"Search completed! Found {results['total_count']} total results")
        print(f"Returning {len(results['results'])} results (truncated: {results['truncated']})")
        for i, result in enumerate(results['results'][:3]):
            print(f"  {i+1}. {result['path']} (score: {result['score']})")
    except Exception as e:
        print(f"Search failed: {e}")
    
    # Test search with larger result set
    print("\n2. Testing search with max_results=100...")
    try:
        results = await vault.search_notes("the", context_length=50, max_results=100)
        print(f"Search completed! Found {results['total_count']} total results")
        print(f"Returning {len(results['results'])} results (truncated: {results['truncated']})")
    except Exception as e:
        print(f"Search failed: {e}")
    
    # Close vault
    await vault.close()
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_search_fix())
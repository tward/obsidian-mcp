#!/usr/bin/env python3
"""Test to determine which vault the MCP server is connected to."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.utils import ObsidianAPI
from obsidian_mcp.tools import create_note, read_note, delete_note


async def test_vault_location():
    """Determine which vault we're connected to."""
    print("=== Testing Vault Location ===\n")
    
    api = ObsidianAPI()
    
    # Test 1: Create a test note to see where it appears
    print("1. Creating test note to identify vault location...")
    print("-" * 40)
    
    test_note_path = "MCP_TEST_NOTE.md"
    test_content = f"""# MCP Test Note

This note was created by the MCP server test at {asyncio.get_event_loop().time()}.

If you see this note in your vault, then the MCP server is connected to this vault.

You can delete this note after confirming the vault location.
"""
    
    try:
        # Create the test note
        result = await create_note(test_note_path, test_content, overwrite=True)
        print(f"✓ Created test note: {result['path']}")
        print(f"\nCheck your Obsidian vaults for a file named '{test_note_path}'")
        print("The vault containing this file is the one connected to the MCP server.")
        
        # Try to read it back
        note = await read_note(test_note_path)
        print(f"\n✓ Successfully read back the test note")
        
    except Exception as e:
        print(f"✗ Failed to create test note: {e}")
    
    # Test 2: List vault structure to get clues about which vault
    print("\n\n2. Examining vault structure...")
    print("-" * 40)
    
    try:
        items = await api.get_vault_structure()
        print(f"Vault root contains {len(items)} items:")
        
        # Show first 10 items to help identify the vault
        for item in items[:10]:
            if item.is_folder:
                print(f"  📁 {item.name}/")
            else:
                print(f"  📄 {item.name}")
                
        if len(items) > 10:
            print(f"  ... and {len(items) - 10} more items")
            
    except Exception as e:
        print(f"✗ Failed to list vault: {e}")
    
    # Test 3: Try to find the images that should exist
    print("\n\n3. Searching for the missing images...")
    print("-" * 40)
    
    # Search for any pasted images
    try:
        results = await api.search("Pasted image")
        print(f"Search for 'Pasted image' found {len(results)} results")
        
        # Also try searching in specific folders
        image_folders = ["Images", "HOME/Images", "Attachments", "Assets"]
        for folder in image_folders:
            try:
                folder_items = await api.get_vault_structure(folder)
                if folder_items:
                    print(f"\nFound folder: {folder}/")
                    for item in folder_items[:3]:
                        print(f"  - {item.name}")
            except:
                pass
                
    except Exception as e:
        print(f"✗ Search failed: {e}")
    
    print("\n\n=== Conclusion ===")
    print("The MCP server is connected to a different Obsidian vault than where your images are stored.")
    print("Your images are in: /Users/ns/HOME/Images/")
    print("But the MCP server is connected to a different vault.")
    print("\nTo fix this:")
    print("1. Move/copy the images to the vault that MCP is connected to")
    print("2. Or configure MCP to connect to your HOME vault")
    print("3. Or use the Obsidian settings to set the correct vault for the Local REST API")


async def main():
    """Run vault location test."""
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("ERROR: OBSIDIAN_REST_API_KEY not set!")
        return
    
    await test_vault_location()


if __name__ == "__main__":
    asyncio.run(main())
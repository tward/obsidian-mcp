#!/usr/bin/env python3
"""Debug image handling in Obsidian MCP."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.utils import ObsidianAPI


async def debug_images():
    """Debug image handling."""
    api = ObsidianAPI()
    
    print("=== Debugging Image Handling ===\n")
    
    # Test 1: List vault structure to find images
    print("1. Scanning vault for image files...")
    print("-" * 40)
    try:
        # Get root structure
        items = await api.get_vault_structure()
        print(f"Found {len(items)} items in vault root")
        
        # Look for common image locations
        image_folders = ['attachments', 'assets', 'images', 'media', 'Attachments', 'Assets', 'Images']
        
        for folder in image_folders:
            try:
                folder_items = await api.get_vault_structure(folder)
                if folder_items:
                    print(f"\nFound folder: {folder}/")
                    for item in folder_items[:5]:  # Show first 5 items
                        print(f"  - {item.name}")
            except:
                pass
                
    except Exception as e:
        print(f"Error scanning vault: {e}")
    
    # Test 2: Try specific image paths
    print("\n\n2. Testing specific image paths...")
    print("-" * 40)
    
    test_paths = [
        "Pasted image 20250623180450.png",
        "attachments/Pasted image 20250623180450.png",
        "Attachments/Pasted image 20250623180450.png",
        "assets/Pasted image 20250623180450.png",
        "Assets/Pasted image 20250623180450.png",
    ]
    
    for path in test_paths:
        try:
            print(f"\nTrying: {path}")
            result = await api.get_image(path)
            if result:
                print(f"  ✓ SUCCESS! Found image at: {path}")
                print(f"    MIME type: {result['mime_type']}")
                print(f"    Size: {result['size']} bytes")
                break
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                print(f"  ✗ Not found (404)")
            else:
                print(f"  ✗ Error: {error_msg[:100]}")
    
    # Test 3: Check the note content for exact image references
    print("\n\n3. Checking note content for image references...")
    print("-" * 40)
    try:
        note = await api.get_note("Note with Images.md")
        if note:
            print("Note content:")
            print(note.content)
            print("\nExtracting image references...")
            
            import re
            # Find wiki-style image embeds
            wiki_pattern = r'!\[\[([^]]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp|ico))\]\]'
            matches = re.findall(wiki_pattern, note.content, re.IGNORECASE)
            
            if matches:
                print(f"Found {len(matches)} image references:")
                for img in matches:
                    print(f"  - {img}")
            else:
                print("No image references found in note")
    except Exception as e:
        print(f"Error reading note: {e}")


async def main():
    """Run debug tests."""
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("ERROR: OBSIDIAN_REST_API_KEY not set!")
        return
    
    await debug_images()


if __name__ == "__main__":
    asyncio.run(main())
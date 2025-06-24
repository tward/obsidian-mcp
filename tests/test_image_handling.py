#!/usr/bin/env python3
"""Test image handling functionality in Obsidian MCP server."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_mcp.tools import read_note, read_image
from obsidian_mcp.utils import ObsidianAPI


async def test_image_reading():
    """Test various image reading scenarios."""
    print("=== Testing Obsidian MCP Image Handling ===\n")
    
    # Test 1: Read a note with embedded images
    print("Test 1: Reading note with embedded images")
    print("-" * 40)
    try:
        # Try to read a note that might have images
        test_note_path = "Note with Images.md"
        result = await read_note(test_note_path, include_images=True)
        
        print(f"✓ Successfully read note: {result['path']}")
        print(f"  Content preview: {result['content'][:100]}...")
        
        if 'images' in result:
            print(f"  Found {len(result['images'])} embedded images:")
            for img in result['images']:
                print(f"    - {img['path']} ({img['mime_type']})")
                print(f"      Base64 preview: {img['content'][:50]}...")
        else:
            print("  No embedded images found")
            # Extract image references from content
            import re
            wiki_pattern = r'!\[\[([^]]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp|ico))\]\]'
            matches = re.findall(wiki_pattern, result['content'], re.IGNORECASE)
            if matches:
                print(f"  Note references {len(matches)} images that weren't loaded:")
                for img in matches:
                    print(f"    - {img} (file may not exist in vault)")
            
    except Exception as e:
        print(f"✗ Failed to read note with images: {e}")
    
    print("\n")
    
    # Test 2: Direct image reading
    print("Test 2: Reading image directly")
    print("-" * 40)
    
    # Common image paths to test
    test_image_paths = [
        "Pasted image 20250623180450.png",
        "attachments/screenshot.png",
        "Images/42511292-90AA-454B-9265-A4A37A5CCB38_1_105_c.jpeg",  # Known existing image
        "images/diagram.jpg",
        "Assets/logo.png"
    ]
    
    for image_path in test_image_paths:
        try:
            result = await read_image(image_path, include_metadata=True)
            print(f"✓ Successfully read image: {result['path']}")
            print(f"  MIME type: {result['mime_type']}")
            if 'size' in result:
                print(f"  Size: {result['size']} bytes")
            print(f"  Base64 preview: {result['content'][:50]}...")
            break  # Stop after first successful read
        except FileNotFoundError:
            print(f"  Image not found: {image_path}")
        except Exception as e:
            print(f"✗ Error reading {image_path}: {e}")
    
    print("\n")
    
    # Test 3: Test error handling for invalid paths
    print("Test 3: Error handling for invalid paths")
    print("-" * 40)
    
    invalid_paths = [
        "Pasted image.png.md",  # Should not have .md extension
        "invalid/../../etc/passwd",  # Path traversal attempt
        "image.txt",  # Invalid extension
        ""  # Empty path
    ]
    
    for invalid_path in invalid_paths:
        try:
            await read_image(invalid_path)
            print(f"✗ Should have failed for: {invalid_path}")
        except ValueError as e:
            print(f"✓ Correctly rejected {invalid_path}: {e}")
        except Exception as e:
            print(f"✓ Correctly failed for {invalid_path}: {type(e).__name__}: {e}")
    
    print("\n")
    
    # Test 4: Check API connectivity
    print("Test 4: API Connectivity")
    print("-" * 40)
    try:
        api = ObsidianAPI()
        # Try a simple operation to verify connectivity
        await api.get_vault_structure()
        print("✓ Successfully connected to Obsidian REST API")
    except Exception as e:
        print(f"✗ Failed to connect to Obsidian REST API: {e}")
        print("  Make sure Obsidian is running with Local REST API plugin enabled")


async def main():
    """Run all tests."""
    # Check environment
    if not os.getenv("OBSIDIAN_REST_API_KEY"):
        print("ERROR: OBSIDIAN_REST_API_KEY environment variable not set!")
        print("Please set it before running tests.")
        return
    
    await test_image_reading()
    
    print("=== Test Summary ===")
    print("Check the output above for any failures.")
    print("\nTips for troubleshooting:")
    print("1. Ensure Obsidian is running with Local REST API plugin enabled")
    print("2. Check that the test notes/images exist in your vault")
    print("3. Verify OBSIDIAN_REST_API_KEY is correct")


if __name__ == "__main__":
    asyncio.run(main())
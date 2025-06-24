"""Image management tools for Obsidian MCP server."""

from typing import Optional
from fastmcp import Context
from ..utils.filesystem import get_vault
from ..utils import validate_note_path, sanitize_path
from ..constants import ERROR_MESSAGES


async def read_image(
    path: str,
    include_metadata: bool = False,
    max_width: int = 800,
    ctx: Optional[Context] = None
) -> dict:
    """
    Read an image file from the Obsidian vault and return it as base64-encoded data.
    
    Use this tool when you need to retrieve image files from the vault. The image
    is returned as base64-encoded data that can be displayed by MCP clients.
    Images larger than max_width are automatically resized to prevent memory issues.
    
    Args:
        path: Path to the image file relative to vault root (e.g., "attachments/screenshot.png")
        include_metadata: Whether to include file metadata like size (default: false)
        max_width: Maximum width for automatic resizing in pixels (default: 800)
        ctx: MCP context for progress reporting
        
    Returns:
        Dictionary containing the base64-encoded image data and metadata
        
    Example:
        >>> await read_image("images/diagram.png", include_metadata=True, max_width=1200, ctx=ctx)
        {
            "path": "images/diagram.png",
            "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "mime_type": "image/png",
            "size": 1234,
            "resized": true,
            "dimensions": {
                "original": {"width": 2400, "height": 1800},
                "resized": {"width": 1200, "height": 900}
            }
        }
    """
    # Validate path (reuse existing validation but allow image extensions)
    if not path:
        raise ValueError("Path cannot be empty")
    
    # Check for common image extensions
    valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico'}
    ext = path.lower().split('.')[-1] if '.' in path else ''
    if f'.{ext}' not in valid_extensions:
        raise ValueError(f"Invalid image file extension. Supported: {', '.join(valid_extensions)}")
    
    # Don't sanitize path for images - it adds .md extension
    
    if ctx:
        ctx.info(f"Reading image: {path}")
    
    vault = get_vault()
    
    try:
        image_data = await vault.read_image(path, max_width=max_width)
    except FileNotFoundError:
        raise FileNotFoundError(ERROR_MESSAGES["note_not_found"].format(path=path))
    
    result = {
        "path": image_data["path"],
        "content": image_data["content"],
        "mime_type": image_data["mime_type"]
    }
    
    if include_metadata:
        result["size"] = image_data["size"]
        if "original_size" in image_data:
            result["original_size"] = image_data["original_size"]
        if "resized" in image_data:
            result["resized"] = image_data["resized"]
        if "dimensions" in image_data:
            result["dimensions"] = image_data["dimensions"]
    
    return result
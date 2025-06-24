# Release Notes - v2.0.0

## 🎉 Major Release: Complete Architecture Overhaul

We're thrilled to announce Obsidian MCP v2.0.0, a complete rewrite that brings massive performance improvements, new features, and a more reliable architecture.

## 🚀 Key Highlights

### Direct Filesystem Access
- **No REST API required** - Works directly with your vault files
- **No Obsidian plugins needed** - Operates independently
- **Works offline** - No network connection required
- **Instant startup** - No waiting for API connections

### 5x Performance Improvement
- **Persistent SQLite indexing** - Search index survives between sessions
- **Incremental updates** - Only re-indexes changed files
- **Concurrent operations** - Optimized for large vaults
- **90% less memory usage** - Efficient streaming architecture

### New Features
- **🖼️ Image support** - View and analyze images from your vault
- **🔍 Regex search** - Find complex patterns with optimized streaming
- **🗂️ Property search** - Query by frontmatter properties with operators
- **🎯 One-command setup** - Auto-configure Claude Desktop instantly

## 📋 Complete Feature List

### Enhanced Search Capabilities
- **Persistent search index** using SQLite for lightning-fast queries
- **Regex pattern matching** with streaming for large files
- **Property-based queries** with advanced operators (>, <, contains, exists)
- **Hierarchical tag support** - Full support for Obsidian's nested tag system
  - Search parent tags to find all children (e.g., `tag:project` finds `project/web`)
  - Search child tags across any hierarchy (e.g., `tag:web` finds `project/web`, `design/web`)
  - Exact hierarchical matching (e.g., `tag:project/web`)

### Metadata & Properties
- **Automatic property migration** - Handles legacy properties (`tag`→`tags`, `alias`→`aliases`)
- **Array/list property searching** - Find items within array properties
- **Date property comparisons** - ISO format support with intelligent comparison
- **Numeric comparisons** - Works with both numbers and array lengths

### Image Tools
- **read_image** - View images with automatic resizing for optimal display
- **view_note_images** - Extract and analyze all images embedded in notes
- Supports PNG, JPG/JPEG, GIF, WebP, SVG, BMP formats

### Improved Tool Definitions
All tools now follow MCP best practices:
- **Semantic parameter descriptions** - AI-friendly explanations
- **Comprehensive examples** - Clear usage patterns
- **Standardized responses** - Consistent return structures
- **Better error messages** - Actionable feedback

## 🔄 Migration Guide

### From v1.x (REST API)
The auto-configuration tool will handle migration automatically:

```bash
uvx --from obsidian-mcp obsidian-mcp-configure --vault-path /path/to/your/vault
```

This will:
- Detect existing REST API configuration
- Migrate to filesystem-based setup
- Preserve your vault path
- Create backup of old configuration

### Manual Migration
If you prefer manual setup, update your Claude Desktop config:

**Old (v1.x):**
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["obsidian-mcp"],
      "env": {
        "OBSIDIAN_REST_API_KEY": "your-key"
      }
    }
  }
}
```

**New (v2.0):**
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/path/to/your/vault"
      }
    }
  }
}
```

## 🐛 Bug Fixes
- Fixed timeout errors with large notes
- Resolved memory leaks in long-running sessions
- Improved error handling for missing files
- Better Unicode support for international content

## ⚡ Performance Improvements
- Search operations: 5x faster with persistent index
- Memory usage: 90% reduction through streaming
- Startup time: Near instant (no API connection needed)
- Large file handling: Streaming regex search
- Concurrent operations: Optimized for multi-core systems

## 💔 Breaking Changes
- **REST API removed** - Now uses direct filesystem access
- **Environment variable changed** - `OBSIDIAN_REST_API_KEY` → `OBSIDIAN_VAULT_PATH`
- **Local REST API plugin not required** - Works without any Obsidian plugins
- **Some return structures updated** - Following MCP best practices (tools remain compatible)

## 🔧 Technical Details
- Migrated from `httpx` to `aiofiles` for file operations
- Added `aiosqlite` for persistent search indexing
- Implemented streaming architecture for large file processing
- Added `Pillow` for image processing capabilities
- Optimized concurrent operations with semaphore-based limiting

## 📝 Notes
- The search index is stored in `.obsidian/mcp-search-index.db`
- First search after installation will build the index (one-time operation)
- Index updates incrementally as files change
- All file operations respect Obsidian's conventions

## 🙏 Acknowledgments
Special thanks to all users who provided feedback on v1.x performance issues and feature requests. This complete rewrite was driven by your needs for a faster, more reliable MCP server.

## 📚 Documentation
For detailed documentation and examples, visit:
https://github.com/natestrong/obsidian-mcp

---
*Released: January 24, 2025*
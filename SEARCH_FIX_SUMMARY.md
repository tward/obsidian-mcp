# Search Index Timeout Fix Summary

## Problem
The `search_notes_tool` was timing out after 4 minutes when trying to update the search index for large vaults. The issue was that the entire index update process (checking and re-indexing 341+ files) was happening synchronously during the search request.

## Solution Implemented

### 1. **Background Index Updates**
- Index updates now happen in the background and don't block search requests
- Search operations return immediately with the current index state
- Updates are tracked with `_index_update_in_progress` flag

### 2. **Configurable Update Intervals**
- Default update interval changed from 60 seconds to 5 minutes
- Prevents frequent re-indexing of large vaults

### 3. **Batch Processing**
- Files are processed in configurable batches (default: 50 files)
- Progress logging shows which files are being indexed
- Yields control periodically to prevent blocking

### 4. **New Environment Variables**
- `OBSIDIAN_INDEX_UPDATE_INTERVAL` - How often to update index (default: 300 seconds)
- `OBSIDIAN_INDEX_BATCH_SIZE` - Files per batch (default: 50)
- `OBSIDIAN_AUTO_INDEX_UPDATE` - Enable/disable auto updates (default: true)

### 5. **Search Result Transparency**
- Search now returns metadata: total_count, limit, truncated
- Users can specify max_results (1-500) in search_notes_tool

## Usage


### Recommended Configuration for Large Vaults
```json
{
  "mcpServers": {
    "obsidian": {
      "env": {
        "OBSIDIAN_INDEX_UPDATE_INTERVAL": "600",  // 10 minutes
        "OBSIDIAN_INDEX_BATCH_SIZE": "25",        // Smaller batches
        "OBSIDIAN_AUTO_INDEX_UPDATE": "false"     // Manual updates only
      }
    }
  }
}
```

### Using Search with Result Limits

1. **Specify Maximum Results**
   ```
   Use search_notes_tool with max_results parameter:
   - Default: 50 results
   - Range: 1-500 results
   - Returns metadata showing total_count and if results were truncated
   ```

2. **Understanding Search Responses**
   ```
   Search results now include:
   - results: Array of matched notes
   - total_count: Total number of matches found
   - limit: The max_results value used
   - truncated: Boolean indicating if more results exist
   ```

## Testing

Run the test script to verify the fix:
```bash
cd /path/to/obsidian-mcp
python test_search_fix.py
```

## What's Different Now

1. **No More Timeouts** - Searches return immediately, even if index is updating
2. **Background Updates** - Index updates don't block operations
3. **Better Logging** - See exactly what's happening during updates
4. **Manual Control** - Refresh index when you want, not on every search
5. **Configurable** - Tune settings for your vault size

## Performance Tips

- For vaults with 300+ files, consider:
  - Increasing update interval to 10+ minutes
  - Disabling auto-update and using manual refresh
  - Using smaller batch sizes for smoother updates
  
- Monitor logs with:
  ```bash
  tail -f ~/Library/Logs/Claude/mcp-server-obsidian.log | grep -E "Index|search"
  ```
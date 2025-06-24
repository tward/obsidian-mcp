# Obsidian's metadata architecture revealed

Obsidian stores metadata through a sophisticated two-tier caching system built on IndexedDB, with frontmatter parsed as YAML and properties introduced in version 1.4 as a visual layer over traditional frontmatter. The system maintains both ephemeral and persistent caches, with the persistent cache storing aggregated results including links, embeds, tags, and frontmatter positions for every file in the vault.

## Frontmatter parsing and internal storage

Obsidian processes frontmatter using a **remark parser** that extracts YAML metadata from the beginning of each Markdown file. The frontmatter must be delimited by triple dashes (---) at the very top of the file, with metadata stored in key-value pairs following strict YAML syntax. When a file loads, Obsidian's parser extracts this metadata block and stores it in the persistent cache via IndexedDB, maintaining exact position information for each metadata element.

The parsing process occurs during initial vault loading and continues through event-driven updates. Every file modification, rename, or deletion triggers the parser to update the cached metadata. **The persistent cache holds comprehensive parsing results** including links, embeds, list items, sections, tags, and frontmatter data with their precise document positions. This positional data enables features like hover previews and quick navigation.

Obsidian supports standard YAML formatting including strings, numbers, booleans, arrays (using either comma-separated values or hyphenated lists), and dates. **Internal links within frontmatter require special syntax** - they must be wrapped in quotes like `link: "[[Note Name]]"` for proper parsing. The system has evolved from supporting formats like `tag: value` to requiring plural forms and list structures, with `tags`, `aliases`, and `cssclasses` now being the standard properties.

## Properties system architecture 

The Properties feature, introduced in Obsidian 1.4, represents a major architectural shift in metadata handling. Rather than replacing frontmatter, Properties provides a **visual interface layer** that sits atop the traditional YAML structure while maintaining complete backward compatibility. The system supports eight distinct property types: text, list, number, checkbox, date, datetime, tags, and aliases, each with specific validation and rendering behaviors.

Properties data remains stored as YAML frontmatter in the actual Markdown files, ensuring plain-text compatibility and portability. The Properties UI **automatically migrates legacy frontmatter keys** - converting `tag` to `tags`, `alias` to `aliases`, and `cssClass` to `cssclasses` while enforcing list-type values. This migration happens transparently during file editing without modifying files until they're actively edited.

The Properties system implements **intelligent autocompletion** by indexing all property keys and values across the vault. When adding a property, Obsidian suggests existing property names and previously used values, maintaining consistency across notes. The system also validates property types in real-time, preventing incompatible data entry like text in number fields.

## Tag storage and indexing mechanisms

Obsidian implements a dual tag system supporting both inline tags (using # syntax) and frontmatter tags, with both types indexed in the persistent cache. **Hierarchical tags use forward slashes** to denote parent-child relationships (#parent/child), creating an implicit tree structure without requiring explicit hierarchy definitions. The tag indexing system maintains relationships between all tag levels, automatically inferring parent tags when child tags are applied.

The tag cache operates as part of the metadata cache stored in IndexedDB, with each file's tags indexed by position and type. Inline tags are parsed during document processing and stored with their exact character positions, while frontmatter tags are extracted during YAML parsing. **The cache enables rapid tag searches** without requiring full-text searches across files, significantly improving performance for large vaults.

Tag autocomplete functionality leverages the cached tag index to provide fuzzy search suggestions. The system maintains a global tag registry that tracks all unique tags and their usage frequency across the vault. Nested tags are stored both as complete paths and as individual components, allowing searches to match either parent tags, child tags, or complete hierarchical paths.

## Technical storage architecture

Obsidian's storage architecture centers on **IndexedDB as the primary metadata store**, located in the operating system's application data directory rather than within the vault itself. The IndexedDB implementation stores parsed metadata for every file in a structured format that enables rapid querying without repeatedly parsing Markdown files. This separation of metadata from content files allows for efficient synchronization and prevents cache corruption during sync operations.

The caching system operates in two tiers: an ephemeral cache for active session data and the persistent IndexedDB cache for long-term storage. **The persistent cache aggregates parsing results** from the remark processor, storing comprehensive metadata about links, embeds, sections, tags, and frontmatter with precise positional data. Cache updates occur through event-driven triggers responding to file operations like creation, modification, renaming, or deletion.

Within the vault structure, the `.obsidian` folder contains configuration files, plugin data, and workspace information, but the actual metadata cache resides outside the vault in the system directory. This design **prevents synchronization conflicts** and allows multiple devices to maintain independent caches while sharing the same vault files. The cache uses the vault ID as a namespace to support multiple vaults on the same system.

## Evolution and compatibility considerations

Obsidian's metadata handling has undergone significant evolution, with version 1.4 marking a watershed moment through the introduction of Properties. The migration from singular property names (`tag`, `alias`, `cssClass`) to plural forms (`tags`, `aliases`, `cssclasses`) with mandatory list types represents a breaking change that required careful backward compatibility handling. **The Properties UI automatically performs this migration** when files are edited, preserving existing functionality while modernizing the metadata structure.

The system maintains backward compatibility through multiple strategies: legacy property names continue to be recognized in read operations, the Properties editor automatically converts old formats during editing, and plugins using the older API continue to function through compatibility layers. **Version 1.4 also introduced new file properties** accessible through plugins, including `file.path`, `file.links`, and `file.tags`, expanding the metadata available for querying and automation.

Future compatibility considerations center on the extensible `.base` file format introduced for the Bases feature, which separates property configurations from content. This architecture suggests Obsidian is moving toward more sophisticated metadata handling while maintaining its commitment to plain-text storage and local-first principles. The roadmap indicates continued enhancement of database-like functionality built atop the existing metadata infrastructure.
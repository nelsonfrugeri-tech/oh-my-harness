from oh_my_kb.mcp.tools.kb_expand import KB_EXPAND_TOOL, handle_kb_expand
from oh_my_kb.mcp.tools.kb_recent import KB_RECENT_TOOL, handle_kb_recent
from oh_my_kb.mcp.tools.kb_search import KB_SEARCH_TOOL, handle_kb_search
from oh_my_kb.mcp.tools.kb_tree import KB_TREE_TOOL, handle_kb_tree
from oh_my_kb.mcp.tools.kb_write import KB_WRITE_TOOL, handle_kb_write

# Canonical ordered list of all MCP tools.  Both ``server.py:_list_tools`` and
# ``template.py:render_dynamic_block`` consume this list so that adding a new
# tool in one place automatically reflects in the other.
# Insertion order is intentional: write-first so the harness block prioritises
# the most-used action, then retrieval tools in frequency order.
ALL_TOOLS = [
    KB_WRITE_TOOL,
    KB_SEARCH_TOOL,
    KB_TREE_TOOL,
    KB_EXPAND_TOOL,
    KB_RECENT_TOOL,
]

__all__ = [
    "ALL_TOOLS",
    "KB_EXPAND_TOOL",
    "KB_RECENT_TOOL",
    "KB_SEARCH_TOOL",
    "KB_TREE_TOOL",
    "KB_WRITE_TOOL",
    "handle_kb_expand",
    "handle_kb_recent",
    "handle_kb_search",
    "handle_kb_tree",
    "handle_kb_write",
]

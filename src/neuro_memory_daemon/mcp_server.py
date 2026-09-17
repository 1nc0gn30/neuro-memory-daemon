"""
neuro_memory_daemon.mcp_server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Model Context Protocol (MCP) Server over stdio with JSON-RPC 2.0 protocol handling.
Pure Python standard library implementation.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from . import MemoryDaemon, __version__, get_default_daemon
except ImportError:
    from neuro_memory_daemon import MemoryDaemon, __version__, get_default_daemon

# Protocol specification version
MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "neuro-memory-daemon"


def _log(msg: str) -> None:
    """Log to stderr to preserve stdio JSON-RPC stream integrity on stdout."""
    sys.stderr.write(f"[mcp-server] {msg}\n")
    sys.stderr.flush()


class MCPServer:
    """
    Model Context Protocol (MCP) stdio JSON-RPC 2.0 server.
    Exposes neuro-cognitive memory tools to AI agents and IDEs.
    """

    def __init__(self, daemon: Optional[MemoryDaemon] = None, db_path: Optional[str] = None):
        self.daemon = daemon or get_default_daemon(db_path=db_path)
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._register_default_tools()

    def _register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Register an MCP tool definition and its handler."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self.handlers[name] = handler

    def _register_default_tools(self) -> None:
        """Register standard neuro-memory cognitive tools."""
        
        # 1. memory_store
        self._register_tool(
            name="memory_store",
            description=(
                "Store an episodic, semantic, procedural, or working memory in the neural substrate. "
                "Automatically computes associative term embeddings and forms synaptic connections."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Textual content or description of the memory to store.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Alternative alias for text content.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags/keywords associated with this memory.",
                    },
                    "importance": {
                        "type": "number",
                        "description": "Importance score between 0.0 and 1.0 (default: 0.5).",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "category": {
                        "type": "string",
                        "enum": ["episodic", "semantic", "procedural", "working"],
                        "description": "Category of memory (default: 'episodic').",
                    },
                    "perspective": {
                        "type": "string",
                        "description": "Perspective (e.g. 'first_person', 'third_person', 'agent', 'user', 'system').",
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Identifier of the agent creating or owning the memory.",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional custom key-value metadata to attach to the memory.",
                    },
                },
                "required": [],
            },
            handler=self._tool_memory_store,
        )

        # 2. memory_recall
        self._register_tool(
            name="memory_recall",
            description=(
                "Pattern completion associative recall for a query cue. Traverses synaptic connections "
                "to retrieve associated memory nodes based on semantic resonance and graph spreading activation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Retrieval cue or prompt to trigger associative recall.",
                    },
                    "cue": {
                        "type": "string",
                        "description": "Alternative alias for query cue.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of memories to recall (default: 5).",
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum associative resonance threshold (0.0 to 1.0, default: 0.1).",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["episodic", "semantic", "procedural", "working"],
                        "description": "Optional category filter.",
                    },
                    "spread_hops": {
                        "type": "integer",
                        "description": "Number of associative spreading activation hops across synapses (default: 2).",
                    },
                },
                "required": [],
            },
            handler=self._tool_memory_recall,
        )

        # 3. memory_search
        self._register_tool(
            name="memory_search",
            description="Full-text and tag filtered search with token relevance ranking across all stored memories.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter results by specific tags.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter results by memory category.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (default: 10).",
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Filter results by source agent ID.",
                    },
                },
                "required": ["query"],
            },
            handler=self._tool_memory_search,
        )

        # 4. memory_graph
        self._register_tool(
            name="memory_graph",
            description="Return synaptic graph relationships as JSON, Mermaid diagram syntax, or ASCII representation.",
            input_schema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["json", "mermaid", "ascii", "dot"],
                        "description": "Output format: 'json', 'mermaid', 'ascii', or 'dot' (default: 'json').",
                    },
                    "min_weight": {
                        "type": "number",
                        "description": "Minimum synaptic weight threshold for edges (default: 0.1).",
                    },
                    "node_limit": {
                        "type": "integer",
                        "description": "Maximum number of memory nodes to render (default: 50).",
                    },
                    "root_id": {
                        "type": "string",
                        "description": "Optional focus memory ID to extract local ego-subgraph.",
                    },
                },
            },
            handler=self._tool_memory_graph,
        )

        # 5. memory_consolidate
        self._register_tool(
            name="memory_consolidate",
            description=(
                "Trigger sleep/consolidation pass: applies Spike-Timing-Dependent Plasticity (STDP), "
                "exponential memory decay, and synaptic pruning of sub-threshold connections."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "decay_rate": {
                        "type": "number",
                        "description": "Temporal decay coefficient per consolidation interval (default: 0.05).",
                    },
                    "prune_threshold": {
                        "type": "number",
                        "description": "Weight threshold below which weak synaptic connections are pruned (default: 0.05).",
                    },
                    "stdp_window": {
                        "type": "number",
                        "description": "STDP correlation time window in seconds (default: 3600.0).",
                    },
                },
            },
            handler=self._tool_memory_consolidate,
        )

        # 6. memory_stats
        self._register_tool(
            name="memory_stats",
            description="Return memory telemetry metrics: total count, working memory usage, synaptic density, and topic counts.",
            input_schema={
                "type": "object",
                "properties": {
                    "detailed": {
                        "type": "boolean",
                        "description": "Include detailed breakdown of categories, tags, and cluster distribution.",
                    },
                },
            },
            handler=self._tool_memory_stats,
        )

        # 7. memory_diagnostics
        self._register_tool(
            name="memory_diagnostics",
            description="System diagnostics: substrate health, storage file status, database integrity, OS/Python environment, and runtime metrics.",
            input_schema={
                "type": "object",
                "properties": {
                    "verbose": {
                        "type": "boolean",
                        "description": "Include detailed file system and memory allocation checks.",
                    },
                },
            },
            handler=self._tool_memory_diagnostics,
        )

    # -----------------------------------------------------------------------
    # Tool Handlers
    # -----------------------------------------------------------------------

    def _tool_memory_store(self, args: Dict[str, Any]) -> str:
        text = args.get("text") or args.get("content") or ""
        if not text:
            raise ValueError("Parameter 'text' or 'content' is required.")
        
        tags = args.get("tags")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        
        importance = float(args.get("importance", 0.5))
        category = str(args.get("category", "episodic"))
        perspective = str(args.get("perspective", "first_person"))
        agent_id = str(args.get("agent_id", "default"))
        metadata = args.get("metadata") or {}

        res = self.daemon.store(
            text=text,
            tags=tags,
            importance=importance,
            category=category,
            perspective=perspective,
            agent_id=agent_id,
            metadata=metadata,
        )
        return json.dumps(res, indent=2)

    def _tool_memory_recall(self, args: Dict[str, Any]) -> str:
        query = args.get("query") or args.get("cue") or ""
        if not query:
            raise ValueError("Parameter 'query' or 'cue' is required.")
        
        top_k = int(args.get("top_k", 5))
        min_score = float(args.get("min_score", 0.1))
        category = args.get("category")
        spread_hops = int(args.get("spread_hops", 2))

        results = self.daemon.recall(
            query=query,
            top_k=top_k,
            min_score=min_score,
            category=category,
            spread_hops=spread_hops,
        )
        return json.dumps(results, indent=2)

    def _tool_memory_search(self, args: Dict[str, Any]) -> str:
        query = args.get("query") or ""
        tags = args.get("tags")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        
        category = args.get("category")
        limit = int(args.get("limit", 10))
        agent_id = args.get("agent_id")

        results = self.daemon.search(
            query=query,
            tags=tags,
            category=category,
            limit=limit,
            agent_id=agent_id,
        )
        return json.dumps(results, indent=2)

    def _tool_memory_graph(self, args: Dict[str, Any]) -> str:
        fmt = args.get("format", "json")
        min_weight = float(args.get("min_weight", 0.1))
        node_limit = int(args.get("node_limit", 50))
        root_id = args.get("root_id")

        graph = self.daemon.get_graph(
            format=fmt,
            min_weight=min_weight,
            node_limit=node_limit,
            root_id=root_id,
        )
        if isinstance(graph, dict):
            return json.dumps(graph, indent=2)
        return str(graph)

    def _tool_memory_consolidate(self, args: Dict[str, Any]) -> str:
        decay_rate = float(args.get("decay_rate", 0.05))
        prune_threshold = float(args.get("prune_threshold", 0.05))
        stdp_window = float(args.get("stdp_window", 3600.0))

        res = self.daemon.consolidate(
            decay_rate=decay_rate,
            prune_threshold=prune_threshold,
            stdp_window=stdp_window,
        )
        return json.dumps(res, indent=2)

    def _tool_memory_stats(self, args: Dict[str, Any]) -> str:
        detailed = bool(args.get("detailed", False))
        stats = self.daemon.get_stats(detailed=detailed)
        return json.dumps(stats, indent=2)

    def _tool_memory_diagnostics(self, args: Dict[str, Any]) -> str:
        verbose = bool(args.get("verbose", False))
        diag = self.daemon.diagnostics(verbose=verbose)
        return json.dumps(diag, indent=2)

    # -----------------------------------------------------------------------
    # JSON-RPC 2.0 Protocol Dispatcher
    # -----------------------------------------------------------------------

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process an incoming JSON-RPC 2.0 request or notification."""
        if not isinstance(request, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request: expected JSON object"},
            }

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        # 1. MCP Initialization Handshake
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "logging": {},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": __version__,
                    },
                },
            }

        # 2. Initialization notification from client (no response for notifications)
        if method in ("notifications/initialized", "initialized"):
            _log("Client initialized successfully.")
            return None

        # 3. Ping
        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # 4. Tools list
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": list(self.tools.values())},
            }

        # 5. Tools call
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}

            if tool_name not in self.handlers:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: Tool '{tool_name}' not found.",
                            }
                        ],
                        "isError": True,
                    },
                }

            try:
                handler = self.handlers[tool_name]
                result_text = handler(tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": str(result_text)}],
                        "isError": False,
                    },
                }
            except Exception as e:
                err_msg = f"Tool '{tool_name}' execution error: {str(e)}\n{traceback.format_exc()}"
                _log(err_msg)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True,
                    },
                }

        # 6. Standard MCP resource and prompt discovery stubs
        if method == "resources/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}}

        if method == "prompts/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": []}}

        if method == "logging/setLevel":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # Unknown method
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found",
                },
            }
        return None

    # -----------------------------------------------------------------------
    # Stdio Transport Reader & Writer Loop
    # -----------------------------------------------------------------------

    def run_stdio(self) -> None:
        """Run the MCP server over standard input/output until EOF."""
        _log(f"Starting {SERVER_NAME} v{__version__} MCP stdio transport...")
        
        # Binary or text stream reader
        stdin_stream = sys.stdin

        while True:
            try:
                line = stdin_stream.readline()
                if not line:
                    break  # EOF

                line_stripped = line.strip()
                if not line_stripped:
                    continue

                # Handle optional Content-Length header framing (HTTP/LSP-style framing)
                if line_stripped.lower().startswith("content-length:"):
                    parts = line_stripped.split(":", 1)
                    length = int(parts[1].strip())
                    # Consume following blank lines
                    while True:
                        blank = stdin_stream.readline()
                        if not blank or blank.strip() == "":
                            break
                    body = stdin_stream.read(length)
                    req_data = json.loads(body)
                else:
                    req_data = json.loads(line_stripped)

                # Process request
                response = self.handle_request(req_data)
                if response is not None:
                    out_str = json.dumps(response)
                    sys.stdout.write(out_str + "\n")
                    sys.stdout.flush()

            except json.JSONDecodeError as jde:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(jde)}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
            except KeyboardInterrupt:
                _log("Received KeyboardInterrupt, shutting down.")
                break
            except Exception as ex:
                _log(f"Transport loop exception: {ex}")
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": f"Internal error: {str(ex)}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

        _log("MCP stdio server terminated.")


def run_mcp_server(daemon: Optional[MemoryDaemon] = None, db_path: Optional[str] = None) -> None:
    """Launch the MCP server stdio session."""
    server = MCPServer(daemon=daemon, db_path=db_path)
    server.run_stdio()


if __name__ == "__main__":
    run_mcp_server()

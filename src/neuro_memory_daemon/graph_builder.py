"""Cognitive graph builder and visualization engine for neuro-memory-daemon.

Generates:
1. Mermaid flowchart diagrams with category subgraphs, weighted synaptic links,
   active working memory highlights, and CSS styling classes.
2. Rich JSON adjacency graphs with node attributes, synaptic edges, graph metrics,
   and community topic clustering.
3. Associative pathway discovery (Dijkstra minimum synaptic resistance).
4. Knowledge hub identification (degree and centrality analysis).
Zero external dependencies (pure Python standard library).
"""

from __future__ import annotations

import heapq
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from neuro_memory_daemon.storage import MemoryRecord, SynapseRecord, normalize_tags

# Category emoji badges for visual presentation
CATEGORY_EMOJIS: Dict[str, str] = {
    "debug": "🐛",
    "security": "🔒",
    "architecture": "🏛️",
    "general": "💡",
    "tool": "🛠️",
    "insight": "✨",
    "episodic": "📖",
    "semantic": "🧠",
    "procedure": "⚙️",
}


def sanitize_mermaid_id(raw_id: str) -> str:
    """Sanitize arbitrary string into a valid alphanumeric Mermaid node ID."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", raw_id)
    if not clean or clean[0].isdigit():
        clean = f"n_{clean}"
    return clean


def escape_mermaid_label(text: str, max_length: int = 50) -> str:
    """Escape and format text for safe inclusion inside Mermaid label quotes."""
    if not text:
        return ""

    # Replace newlines with spaces
    single_line = " ".join(text.replace("\r", " ").replace("\n", " ").split())

    # Truncate
    if len(single_line) > max_length:
        single_line = single_line[: max_length - 3] + "..."

    # Escape quotes and brackets
    escaped = (
        single_line.replace('"', "#quot;")
        .replace("[", "&#91;")
        .replace("]", "&#93;")
        .replace("(", "&#40;")
        .replace(")", "&#41;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )
    return escaped


@dataclass
class AssociativeStep:
    """A single hop in an associative pathway."""

    from_node: str
    to_node: str
    weight: float
    hop_type: str = "synapse"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "weight": round(self.weight, 4),
            "hop_type": self.hop_type,
        }


class GraphBuilder:
    """Constructs and analyzes cognitive synaptic memory graphs."""

    def __init__(self) -> None:
        pass

    # -------------------------------------------------------------------------
    # 1. Mermaid Flowchart Generator
    # -------------------------------------------------------------------------

    def to_mermaid(
        self,
        memories: List[MemoryRecord],
        synapses: Optional[List[SynapseRecord]] = None,
        direction: str = "TD",
        active_memory_ids: Optional[Set[str]] = None,
        max_memories: int = 40,
        max_synapses: int = 60,
        include_tags: bool = True,
        group_by_category: bool = True,
    ) -> str:
        """Generate valid Mermaid flowchart syntax from memories and synapses.

        Args:
            memories: List of MemoryRecord instances.
            synapses: Optional list of SynapseRecord instances.
            direction: Diagram layout direction ('TD', 'LR', 'BT', 'RL').
            active_memory_ids: Set of memory IDs currently in DLPFC working memory.
            max_memories: Maximum memory nodes to render.
            max_synapses: Maximum synaptic edges to render.
            include_tags: Whether to render tag nodes and memory-tag links.
            group_by_category: Whether to wrap memory nodes in category subgraphs.

        Returns:
            Mermaid formatted string.
        """
        active_ids = active_memory_ids or set()
        rendered_mems = memories[:max_memories]

        lines: List[str] = [f"flowchart {direction}"]

        # Collect tags present in the memory subset
        active_tags: Set[str] = set()
        for m in rendered_mems:
            active_tags.update(m.tags)

        # 1. Group memories by category into subgraphs
        if group_by_category:
            cat_groups: Dict[str, List[MemoryRecord]] = defaultdict(list)
            for m in rendered_mems:
                cat_groups[m.category].items() if False else cat_groups[m.category].append(m)

            for cat, mem_list in sorted(cat_groups.items()):
                emoji = CATEGORY_EMOJIS.get(cat, "📁")
                subgraph_id = sanitize_mermaid_id(f"subgraph_{cat}")
                lines.append(f'    subgraph {subgraph_id} ["{emoji} {cat.capitalize()} ({len(mem_list)})"]')

                for m in mem_list:
                    m_id = sanitize_mermaid_id(f"mem_{m.id}")
                    label = escape_mermaid_label(m.text, max_length=45)
                    is_active = m.id in active_ids

                    if is_active:
                        lines.append(f'        {m_id}[["⚡ {label}"]]:::activeNode')
                    else:
                        lines.append(f'        {m_id}["{label}"]:::memoryNode')

                lines.append("    end")
        else:
            for m in rendered_mems:
                m_id = sanitize_mermaid_id(f"mem_{m.id}")
                label = escape_mermaid_label(m.text, max_length=45)
                is_active = m.id in active_ids
                if is_active:
                    lines.append(f'    {m_id}[["⚡ {label}"]]:::activeNode')
                else:
                    lines.append(f'    {m_id}["{label}"]:::memoryNode')

        # 2. Render Tag nodes
        if include_tags and active_tags:
            lines.append('    subgraph subgraph_tags ["🏷️ Semantic Associative Tags"]')
            for tag in sorted(active_tags):
                tag_id = sanitize_mermaid_id(f"tag_{tag}")
                clean_tag = escape_mermaid_label(tag, max_length=25)
                lines.append(f'        {tag_id}(["🏷️ #{clean_tag}"]):::tagNode')
            lines.append("    end")

            # 3. Render Memory -> Tag connections
            for m in rendered_mems:
                m_id = sanitize_mermaid_id(f"mem_{m.id}")
                for tag in m.tags:
                    tag_id = sanitize_mermaid_id(f"tag_{tag}")
                    lines.append(f"    {m_id} -.-> {tag_id}")

        # 4. Render Synaptic Links between tags
        rendered_synapses: Set[Tuple[str, str]] = set()
        syn_list = synapses or []
        edge_count = 0

        for syn in syn_list:
            if edge_count >= max_synapses:
                break

            src = syn.source.strip().lower()
            tgt = syn.target.strip().lower()

            # Skip if tags are not part of the active tag set
            if include_tags and (src not in active_tags or tgt not in active_tags):
                continue

            pair = (min(src, tgt), max(src, tgt))
            if pair in rendered_synapses:
                continue
            rendered_synapses.add(pair)

            src_id = sanitize_mermaid_id(f"tag_{src}")
            tgt_id = sanitize_mermaid_id(f"tag_{tgt}")
            w = round(syn.weight, 2)

            # Link styling by synaptic strength
            if w >= 0.7:
                lines.append(f"    {src_id} ===|w={w}| {tgt_id}")
            elif w >= 0.35:
                lines.append(f"    {src_id} ---|w={w}| {tgt_id}")
            else:
                lines.append(f"    {src_id} -.-|w={w}| {tgt_id}")

            edge_count += 1

        # 5. Styling Class Definitions (Dark cinematic / High contrast)
        lines.append("")
        lines.append("    classDef memoryNode fill:#1e293b,stroke:#3b82f6,stroke-width:1px,color:#f8fafc;")
        lines.append("    classDef activeNode fill:#312e81,stroke:#a855f7,stroke-width:2px,color:#ffffff;")
        lines.append("    classDef tagNode fill:#0f172a,stroke:#10b981,stroke-width:1px,color:#6ee7b7;")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 2. JSON Adjacency Graph Builder
    # -------------------------------------------------------------------------

    def build_adjacency_graph(
        self,
        memories: List[MemoryRecord],
        synapses: Optional[List[SynapseRecord]] = None,
        active_memory_ids: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Construct a structured JSON adjacency graph with metrics and clusters.

        Args:
            memories: List of MemoryRecord instances.
            synapses: List of SynapseRecord instances.
            active_memory_ids: Set of memory IDs in active working memory.

        Returns:
            JSON-serializable dictionary with nodes, edges, clusters, and graph metrics.
        """
        active_ids = active_memory_ids or set()
        syn_list = synapses or []

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_node_ids: Set[str] = set()
        tag_degrees: Dict[str, int] = defaultdict(int)

        # 1. Add Memory Nodes
        for m in memories:
            m_node_id = f"mem_{m.id}"
            seen_node_ids.add(m_node_id)
            nodes.append(
                {
                    "id": m_node_id,
                    "type": "memory",
                    "raw_id": m.id,
                    "label": m.text[:60] + ("..." if len(m.text) > 60 else ""),
                    "category": m.category,
                    "importance": float(m.importance),
                    "access_count": int(m.access_count),
                    "entropy_score": float(m.entropy_score),
                    "decay_factor": float(m.decay_factor),
                    "immutable": bool(m.immutable),
                    "is_active": m.id in active_ids,
                    "tags": list(m.tags),
                    "created_at": float(m.created_at),
                }
            )

            # Memory to Tag edges
            for tag in m.tags:
                tag_node_id = f"tag_{tag}"
                tag_degrees[tag] += 1
                edges.append(
                    {
                        "source": m_node_id,
                        "target": tag_node_id,
                        "weight": 1.0,
                        "type": "memory_tag",
                        "co_occurrence_count": 1,
                    }
                )

        # 2. Add Tag Nodes
        for tag, degree in tag_degrees.items():
            tag_node_id = f"tag_{tag}"
            seen_node_ids.add(tag_node_id)
            nodes.append(
                {
                    "id": tag_node_id,
                    "type": "tag",
                    "raw_id": tag,
                    "label": f"#{tag}",
                    "degree": degree,
                    "weight": 1.0,
                }
            )

        # 3. Add Synaptic Edges
        seen_syn_edges: Set[Tuple[str, str]] = set()
        for syn in syn_list:
            src_tag_id = f"tag_{syn.source}"
            tgt_tag_id = f"tag_{syn.target}"

            # Ensure tag nodes exist in node list if not already added
            for tid, raw_tag in [(src_tag_id, syn.source), (tgt_tag_id, syn.target)]:
                if tid not in seen_node_ids:
                    seen_node_ids.add(tid)
                    nodes.append(
                        {
                            "id": tid,
                            "type": "tag",
                            "raw_id": raw_tag,
                            "label": f"#{raw_tag}",
                            "degree": 1,
                            "weight": float(syn.weight),
                        }
                    )

            edge_pair = (min(src_tag_id, tgt_tag_id), max(src_tag_id, tgt_tag_id))
            if edge_pair not in seen_syn_edges:
                seen_syn_edges.add(edge_pair)
                edges.append(
                    {
                        "source": src_tag_id,
                        "target": tgt_tag_id,
                        "weight": round(float(syn.weight), 4),
                        "type": syn.synapse_type,
                        "co_occurrence_count": int(syn.co_occurrence_count),
                        "last_stimulated_at": float(syn.last_stimulated_at),
                    }
                )

        # 4. Community Topic Clusters (Connected Components / Label Propagation)
        clusters = self.detect_topic_clusters(memories, syn_list)

        # 5. Graph Topology Metrics
        total_nodes = len(nodes)
        total_edges = len(edges)
        avg_degree = (2.0 * total_edges / total_nodes) if total_nodes > 0 else 0.0
        max_possible_edges = (total_nodes * (total_nodes - 1)) / 2 if total_nodes > 1 else 1
        density = (total_edges / max_possible_edges) if max_possible_edges > 0 else 0.0

        return {
            "version": "1.0.0",
            "nodes": nodes,
            "edges": edges,
            "clusters": clusters,
            "metrics": {
                "total_nodes": total_nodes,
                "memory_nodes_count": len(memories),
                "tag_nodes_count": len(tag_degrees),
                "total_edges": total_edges,
                "average_degree": round(avg_degree, 3),
                "density": round(density, 4),
                "clusters_count": len(clusters),
            },
        }

    # -------------------------------------------------------------------------
    # 3. Community Topic Clustering & Centrality
    # -------------------------------------------------------------------------

    def detect_topic_clusters(
        self,
        memories: List[MemoryRecord],
        synapses: List[SynapseRecord],
    ) -> List[Dict[str, Any]]:
        """Identify coherent semantic topic clusters using graph community analysis.

        Args:
            memories: List of MemoryRecords.
            synapses: List of SynapseRecords.

        Returns:
            List of topic cluster dictionaries.
        """
        # Adjacency list for tag graph
        adj: Dict[str, Set[str]] = defaultdict(set)
        for syn in synapses:
            if syn.weight >= 0.15:
                src = syn.source.lower()
                tgt = syn.target.lower()
                adj[src].add(tgt)
                adj[tgt].add(src)

        # Add memory-tag co-occurrences
        for m in memories:
            for i in range(len(m.tags)):
                for j in range(i + 1, len(m.tags)):
                    t1, t2 = m.tags[i].lower(), m.tags[j].lower()
                    adj[t1].add(t2)
                    adj[t2].add(t1)

        # Connected components on tag network
        visited: Set[str] = set()
        tag_clusters: List[Set[str]] = []

        all_tags = set(adj.keys())
        for m in memories:
            all_tags.update(m.tags)

        for tag in sorted(all_tags):
            if tag in visited:
                continue
            comp: Set[str] = set()
            queue = [tag]
            visited.add(tag)
            while queue:
                curr = queue.pop(0)
                comp.add(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            if comp:
                tag_clusters.append(comp)

        # Match memories into clusters based on tag overlap
        clusters_out: List[Dict[str, Any]] = []
        for idx, tag_set in enumerate(tag_clusters):
            cluster_mems = [m for m in memories if any(t.lower() in tag_set for t in m.tags)]
            if not cluster_mems and not tag_set:
                continue

            # Dominant category
            cat_counts = Counter(m.category for m in cluster_mems)
            dom_cat = cat_counts.most_common(1)[0][0] if cat_counts else "general"

            # Cluster name heuristics
            name_tags = sorted(list(tag_set), key=lambda t: -len(t))[:3]
            cluster_name = " & ".join(t.capitalize() for t in name_tags) if name_tags else f"Topic Cluster {idx + 1}"

            clusters_out.append(
                {
                    "cluster_id": f"cluster_{idx + 1}",
                    "name": cluster_name,
                    "dominant_category": dom_cat,
                    "tags": sorted(list(tag_set)),
                    "memory_ids": [m.id for m in cluster_mems],
                    "size": len(cluster_mems) + len(tag_set),
                }
            )

        clusters_out.sort(key=lambda c: c["size"], reverse=True)
        return clusters_out

    def find_knowledge_hubs(
        self,
        graph_data: Dict[str, Any],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Identify key knowledge hubs (highest degree and centrality nodes).

        Args:
            graph_data: Output of build_adjacency_graph.
            top_k: Number of top hubs to return.

        Returns:
            List of hub node dictionaries with centrality metrics.
        """
        degree_map: Dict[str, int] = defaultdict(int)
        for edge in graph_data.get("edges", []):
            degree_map[edge["source"]] += 1
            degree_map[edge["target"]] += 1

        nodes_by_id = {n["id"]: n for n in graph_data.get("nodes", [])}
        ranked: List[Dict[str, Any]] = []

        for node_id, degree in sorted(degree_map.items(), key=lambda x: x[1], reverse=True):
            node_info = nodes_by_id.get(node_id, {})
            ranked.append(
                {
                    "id": node_id,
                    "label": node_info.get("label", node_id),
                    "type": node_info.get("type", "unknown"),
                    "degree": degree,
                    "importance": node_info.get("importance", 1.0),
                }
            )

        return ranked[:top_k]

    # -------------------------------------------------------------------------
    # 4. Associative Pathway Discovery (Dijkstra)
    # -------------------------------------------------------------------------

    def find_associative_path(
        self,
        graph_data: Dict[str, Any],
        start_id: str,
        end_id: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Discover the path of maximum synaptic conductance (minimum resistance) between two nodes.

        Uses Dijkstra's algorithm where edge resistance = 1.0 / (weight + 0.001).

        Args:
            graph_data: Output of build_adjacency_graph.
            start_id: Origin node ID (e.g. 'tag_auth' or 'mem_uuid').
            end_id: Destination node ID.

        Returns:
            List of step dictionaries along the associative pathway, or None if unreachable.
        """
        # Build adjacency with weights
        adj: Dict[str, List[Tuple[str, float, str]]] = defaultdict(list)
        for edge in graph_data.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            w = max(0.01, float(edge.get("weight", 0.1)))
            edge_type = edge.get("type", "synapse")
            adj[src].append((tgt, w, edge_type))
            adj[tgt].append((src, w, edge_type))

        # Dijkstra priority queue: (cumulative_resistance, current_node, path_steps)
        pq: List[Tuple[float, str, List[Dict[str, Any]]]] = [(0.0, start_id, [])]
        best_resistance: Dict[str, float] = {start_id: 0.0}

        while pq:
            curr_res, curr_node, path = heapq.heappop(pq)

            if curr_node == end_id:
                return path

            if curr_res > best_resistance.get(curr_node, float("inf")):
                continue

            for neighbor, weight, edge_type in adj[curr_node]:
                # Resistance inversely proportional to synaptic weight
                step_res = 1.0 / (weight + 0.001)
                next_res = curr_res + step_res

                if next_res < best_resistance.get(neighbor, float("inf")):
                    best_resistance[neighbor] = next_res
                    step_info = {
                        "from": curr_node,
                        "to": neighbor,
                        "weight": round(weight, 4),
                        "type": edge_type,
                    }
                    heapq.heappush(pq, (next_res, neighbor, path + [step_info]))

        return None

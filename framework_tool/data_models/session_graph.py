# framework_tool/data_models/session_graph.py
# All comments and identifiers in English

import uuid # For generating unique node IDs
from typing import List, Dict, Any, Optional

class ActionNode:
    """
    Represents a single node within a SessionActionsGraph.
    Each node is an instance of an action to be performed at a specific point
    in the session's flow.
    """
    def __init__(self,
                 action_label_to_execute: str, # References an ActionDefinition's label
                 node_id: Optional[str] = None, # Unique ID for this node instance
                 parent_node_id: Optional[str] = None,
                 children_node_ids: Optional[List[str]] = None, # ORDERED list
                 forced_next_node_id: Optional[str] = None):

        if not action_label_to_execute:
            raise ValueError("action_label_to_execute cannot be empty for an ActionNode.")

        self.node_id: str = node_id if node_id else str(uuid.uuid4())
        self.action_label_to_execute: str = action_label_to_execute
        
        # Structural relationships
        self.parent_node_id: Optional[str] = parent_node_id
        # Children nodes. The order in this list is CRITICAL for:
        # 1. Defining sequential execution if children form a direct sequence.
        # 2. The "ratio interna" (internal rule) for ActionsMng to pick an instance
        #    if multiple children share the same ActionLabel and are simultaneously enabled.
        self.children_node_ids: List[str] = children_node_ids if children_node_ids is not None else []
        self.forced_next_node_id: Optional[str] = forced_next_node_id
        
        # Note: uiPosition, disableSiblingBranchesOnChildSelection, and completionConditionForParent
        # have been removed as per our discussion. Their logic will be handled by the
        # graph interpreter (ActionsMng) based on graph structure and predefined behavioral rules.

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "nodeId": self.node_id,
            "actionLabelToExecute": self.action_label_to_execute,
            # childrenNodeIds is always present, even if empty, to maintain structure
            "childrenNodeIds": self.children_node_ids 
        }
        if self.parent_node_id is not None:
            data["parentNodeId"] = self.parent_node_id
        if self.forced_next_node_id is not None:
            data["forcedNextNodeId"] = self.forced_next_node_id
        
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionNode':
        node_id = data.get("nodeId")
        action_label = data.get("actionLabelToExecute")

        if not node_id: # Should always be present from editor
            # If generating for the first time from an older format or simple list,
            # we might generate one, but strict parsing would require it.
            # For now, let's assume editor always provides it.
             raise ValueError("nodeId is required in ActionNode data.")
        if not action_label:
            raise ValueError("actionLabelToExecute is required in ActionNode data.")

        return cls(
            node_id=node_id,
            action_label_to_execute=action_label,
            parent_node_id=data.get("parentNodeId"),
            children_node_ids=data.get("childrenNodeIds", []), # Default to empty list if missing
            forced_next_node_id=data.get("forcedNextNodeId")
        )


class SessionActionsGraph:
    """
    Represents a complete session or scenario, defined as a graph of ActionNodes.
    """
    def __init__(self,
                 session_name: str,
                 entry_node_ids: Optional[List[str]] = None, # Entry points for this session
                 nodes: Optional[List[ActionNode]] = None):
        
        if not session_name:
            raise ValueError("session_name cannot be empty.")

        self.session_name: str = session_name
        # The list of node IDs that are the starting points for this session.
        # Often, this will be a single node ID.
        self.entry_node_ids: List[str] = entry_node_ids if entry_node_ids is not None else []
        # A flat list of all nodes in this session's graph.
        # Relationships (parent, child, sequence) are defined within each ActionNode.
        self.nodes: List[ActionNode] = nodes if nodes is not None else []
        
        # Internal lookup for quick node access by ID, built upon loading or modification
        self._nodes_by_id: Dict[str, ActionNode] = {node.node_id: node for node in self.nodes}
        self._validate_graph_integrity()


    def _validate_graph_integrity(self):
        """
        Performs basic validation of the graph structure.
        Can be expanded with more checks.
        """
        if not self.nodes and self.entry_node_ids:
            raise ValueError(f"Session '{self.session_name}': Entry node IDs specified but no nodes defined.")

        node_ids = set()
        for node in self.nodes:
            if node.node_id in node_ids:
                raise ValueError(f"Session '{self.session_name}': Duplicate nodeId '{node.node_id}' found.")
            node_ids.add(node.node_id)

        for entry_id in self.entry_node_ids:
            if entry_id not in node_ids:
                raise ValueError(f"Session '{self.session_name}': Entry nodeId '{entry_id}' not found in defined nodes.")
        
        for node in self.nodes:
            if node.parent_node_id and node.parent_node_id not in node_ids:
                raise ValueError(f"Session '{self.session_name}', Node '{node.node_id}': parentNodeId '{node.parent_node_id}' not found.")
            for child_id in node.children_node_ids:
                if child_id not in node_ids:
                    raise ValueError(f"Session '{self.session_name}', Node '{node.node_id}': childNodeId '{child_id}' not found.")
            if node.forced_next_node_id and node.forced_next_node_id not in node_ids:
                 raise ValueError(f"Session '{self.session_name}', Node '{node.node_id}': forcedNextNodeId '{node.forced_next_node_id}' not found.")

    def rebuild_node_lookup(self):
        """Rebuilds the internal node lookup dictionary. Call after modifying the nodes list."""
        self._nodes_by_id = {node.node_id: node for node in self.nodes}
        self._validate_graph_integrity() # Re-validate after rebuilding

    def get_node_by_id(self, node_id: str) -> Optional[ActionNode]:
        return self._nodes_by_id.get(node_id)

    def to_dict(self) -> Dict[str, Any]:
        # Sort nodes by nodeId for consistent JSON output, though order in this flat list
        # doesn't dictate execution logic beyond how the editor might present it.
        # The relationships define the graph structure.
        return {
            "sessionName": self.session_name,
            "entryNodeIds": sorted(list(set(self.entry_node_ids))), # Ensure uniqueness and order
            "nodes": sorted([node.to_dict() for node in self.nodes], key=lambda n: n["nodeId"])
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionActionsGraph':
        session_name = data.get("sessionName")
        if not session_name:
            raise ValueError("sessionName is required for SessionActionsGraph.")

        nodes_data = data.get("nodes", [])
        nodes_list = [ActionNode.from_dict(node_data) for node_data in nodes_data]
        
        instance = cls(
            session_name=session_name,
            entry_node_ids=data.get("entryNodeIds", []),
            nodes=nodes_list # The constructor will build the lookup and validate
        )
        return instance
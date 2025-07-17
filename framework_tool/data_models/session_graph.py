# framework_tool/data_models/session_graph.py
# All comments and identifiers in English

import uuid 
from typing import List, Dict, Any, Optional

class ActionNode:
    """
    Represents a single node within a SessionActionsGraph.
    Each node is an instance of an action to be performed.
    Its position in the sequence is determined by its relationship
    to parent/children nodes or as a root node within a StepDefinition.
    Sequences are primarily defined by the parent-child relationship and the order
    of children in children_node_ids.
    """
    def __init__(self,
                 action_label_to_execute: str, 
                 node_id: Optional[str] = None, 
                 parent_node_id: Optional[str] = None, # ID of the ActionNode that this is a child of
                 children_node_ids: Optional[List[str]] = None, # ORDERED list of child node IDs
                 instance_label: str = "",  # Custom label for this instance
                 custom_field_values: Optional[Dict[str, Any]] = None): # Values for custom fields
        
        if not action_label_to_execute:
            raise ValueError("action_label_to_execute cannot be empty for an ActionNode.")

        self.node_id: str = node_id if node_id else str(uuid.uuid4())
        self.action_label_to_execute: str = action_label_to_execute
        
        self.parent_node_id: Optional[str] = parent_node_id
        # Children define subsequent actions. If multiple children, they might be parallel options
        # or a sequence if the game logic interprets their order strictly.
        self.children_node_ids: List[str] = children_node_ids if children_node_ids is not None else []
        
        # Instance customization
        self.instance_label: str = instance_label
        self.custom_field_values: Dict[str, Any] = custom_field_values if custom_field_values is not None else {}
        
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "nodeId": self.node_id,
            "actionLabelToExecute": self.action_label_to_execute,
            "childrenNodeIds": self.children_node_ids,
            "instanceLabel": self.instance_label,
            "customFieldValues": self.custom_field_values
        }
        if self.parent_node_id is not None:
            data["parentNodeId"] = self.parent_node_id
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionNode':
        node_id = data.get("nodeId")
        action_label = data.get("actionLabelToExecute")

        if not node_id:
             raise ValueError("nodeId is required in ActionNode data.")
        if not action_label:
            raise ValueError("actionLabelToExecute is required in ActionNode data.")

        return cls(
            node_id=node_id,
            action_label_to_execute=action_label,
            parent_node_id=data.get("parentNodeId"),
            children_node_ids=data.get("childrenNodeIds", []),
            instance_label=data.get("instanceLabel", ""),
            custom_field_values=data.get("customFieldValues", {})
        )

class StepDefinition:
    """
    Defines a single step in a SessionActionsGraph.
    A step contains one or more root ActionNodes that can be initiated.
    These root nodes can represent parallel starting points for action sequences within the step.
    """
    def __init__(self,
                 step_id: Optional[str] = None,
                 step_name: str = "", 
                 root_node_ids: Optional[List[str]] = None): 
        
        self.step_id: str = step_id if step_id else str(uuid.uuid4())
        self.step_name: str = step_name
        self.root_node_ids: List[str] = root_node_ids if root_node_ids is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stepId": self.step_id,
            "stepName": self.step_name,
            "rootNodeIds": self.root_node_ids
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepDefinition':
        step_id = data.get("stepId")
        return cls(
            step_id=step_id if step_id else str(uuid.uuid4()),
            step_name=data.get("stepName", ""),
            root_node_ids=data.get("rootNodeIds", [])
        )


class SessionActionsGraph:
    """
    Represents a complete session or scenario, defined as an ordered list of Steps.
    Each Step, in turn, points to root ActionNodes.
    The graph also contains a flat list of all ActionNode definitions.
    """
    def __init__(self,
                 session_name: str,
                 steps: Optional[List[StepDefinition]] = None, 
                 nodes: Optional[List[ActionNode]] = None): 
        
        if not session_name:
            raise ValueError("session_name cannot be empty.")

        self.session_name: str = session_name
        self.steps: List[StepDefinition] = steps if steps is not None else []
        self.nodes: List[ActionNode] = nodes if nodes is not None else []
        
        self._nodes_by_id: Dict[str, ActionNode] = {node.node_id: node for node in self.nodes}
        self._validate_graph_integrity()


    def _validate_graph_integrity(self):
        node_ids_defined = set()
        for node in self.nodes:
            if node.node_id in node_ids_defined:
                raise ValueError(f"Session '{self.session_name}': Duplicate nodeId '{node.node_id}' found in nodes list.")
            node_ids_defined.add(node.node_id)

        for step_idx, step in enumerate(self.steps):
            if not step.step_id:
                 raise ValueError(f"Session '{self.session_name}', Step {step_idx}: step_id is missing.")
            for root_node_id in step.root_node_ids:
                if root_node_id not in node_ids_defined:
                    raise ValueError(f"Session '{self.session_name}', Step '{step.step_name}' ({step.step_id}): "
                                     f"rootNodeId '{root_node_id}' not found in defined nodes list.")
        
        for node in self.nodes:
            if node.parent_node_id and node.parent_node_id not in node_ids_defined:
                raise ValueError(f"Session '{self.session_name}', Node '{node.node_id}': parentNodeId '{node.parent_node_id}' not found.")
            for child_id in node.children_node_ids:
                if child_id not in node_ids_defined:
                    raise ValueError(f"Session '{self.session_name}', Node '{node.node_id}': childNodeId '{child_id}' not found.")
            # No forced_next_node_id to validate anymore

    def rebuild_node_lookup(self):
        self._nodes_by_id = {node.node_id: node for node in self.nodes}

    def get_node_by_id(self, node_id: str) -> Optional[ActionNode]:
        return self._nodes_by_id.get(node_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sessionName": self.session_name,
            "steps": [step.to_dict() for step in self.steps], 
            "nodes": sorted([node.to_dict() for node in self.nodes], key=lambda n: n["nodeId"])
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionActionsGraph':
        session_name = data.get("sessionName")
        if not session_name:
            raise ValueError("sessionName is required for SessionActionsGraph.")

        steps_data = data.get("steps", [])
        steps_list = [StepDefinition.from_dict(step_data) for step_data in steps_data]
        
        nodes_data = data.get("nodes", [])
        nodes_list = [ActionNode.from_dict(node_data) for node_data in nodes_data]
        
        instance = cls(
            session_name=session_name,
            steps=steps_list,
            nodes=nodes_list 
        )
        return instance

# framework_tool/gui/widgets/session_flow_editor_widget.py
# All comments and identifiers in English

import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QGridLayout, QSpacerItem, QSizePolicy, QMenu,
    QMessageBox, QInputDialog, QApplication, QMainWindow 
)
from PySide6.QtGui import QAction, QCursor, QColor, QPalette
from PySide6.QtCore import Qt, Signal, Slot, QPoint
from typing import Optional, List, Dict, Any, Tuple

# Import data models
from ...data_models.project_data import ProjectData
from ...data_models.session_graph import SessionActionsGraph, ActionNode, StepDefinition
from ...data_models.action_definition import ActionDefinition

# Import dialogs
from ..dialogs.select_action_label_dialog import SelectActionLabelDialog
from .action_card_widget import ActionCardWidget


class SessionFlowEditorWidget(QWidget):
    session_graph_changed = Signal()
    action_node_selected = Signal(object) 

    def __init__(self, project_data_ref: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data_ref = project_data_ref
        self._current_session_graph: Optional[SessionActionsGraph] = None
        self._current_session_name: Optional[str] = None
        self._action_card_widgets: Dict[str, ActionCardWidget] = {}
        self._selected_action_card: Optional[ActionCardWidget] = None
        self._step_frames: Dict[str, QFrame] = {} 
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.session_name_display = QLabel("Editing Session: [No Session Loaded]")
        self.session_name_display.setStyleSheet("font-weight: bold; padding: 5px;")
        main_layout.addWidget(self.session_name_display)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.steps_container_widget = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container_widget)
        self.steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steps_layout.setSpacing(10) 
        self.scroll_area.setWidget(self.steps_container_widget)
        main_layout.addWidget(self.scroll_area)
        buttons_layout = QHBoxLayout()
        self.create_step_button = QPushButton("Create New Step", self)
        self.create_step_button.clicked.connect(self._create_new_step)
        buttons_layout.addWidget(self.create_step_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
        self._enable_editing_controls(False)

    def _enable_editing_controls(self, enabled: bool):
        self.scroll_area.setEnabled(enabled)
        self.create_step_button.setEnabled(enabled)

    def load_session_graph(self, session_name: str, graph: Optional[SessionActionsGraph]):
        self._current_session_name = session_name
        self._current_session_graph = graph
        self._action_card_widgets.clear()
        if self._selected_action_card:
            self._selected_action_card.set_selected(False)
        self._selected_action_card = None
        self.action_node_selected.emit(None)
        self._step_frames.clear()
        while self.steps_layout.count():
            child = self.steps_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if graph:
            self.session_name_display.setText(f"Editing Session: {session_name}")
            self._populate_steps_display(graph)
            self._enable_editing_controls(True)
        else:
            self.session_name_display.setText("Editing Session: [No Session Loaded]")
            self._enable_editing_controls(False)

    def _populate_steps_display(self, graph: SessionActionsGraph):
        if not graph or not graph.steps:
            for i in reversed(range(self.steps_layout.count())):
                item = self.steps_layout.itemAt(i)
                if isinstance(item.widget(), QLabel) and "This session has no steps" in item.widget().text():
                    item.widget().deleteLater()
            no_steps_label = QLabel("This session has no steps. Click 'Create New Step' to begin.")
            no_steps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steps_layout.addWidget(no_steps_label)
            return

        for step_index, step_def in enumerate(graph.steps):
            step_widget = self._create_step_widget(step_def, step_index, graph)
            self.steps_layout.addWidget(step_widget)
            self._step_frames[step_def.step_id] = step_widget
        self.steps_layout.addStretch()

    def _create_step_widget(self, step_def: StepDefinition, step_index: int, graph: SessionActionsGraph) -> QFrame:
        step_frame = QFrame(self)
        step_frame.setFrameShape(QFrame.Shape.StyledPanel); step_frame.setLineWidth(1)
        step_frame.setObjectName(f"StepFrame_{step_def.step_id}")
        step_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        step_frame.customContextMenuRequested.connect(
            lambda pos, current_sd=step_def, current_frame=step_frame: self._show_step_context_menu(pos, current_sd, current_frame)
        )
        step_frame.setProperty("step_definition_obj", step_def)
        step_main_layout = QVBoxLayout(step_frame)
        step_main_layout.setContentsMargins(5,5,5,5); step_main_layout.setSpacing(5)
        title_text = f"Step {step_index}"
        if step_def.step_name: title_text += f": {step_def.step_name}"
        step_title_label = QLabel(title_text)
        step_title_label.setStyleSheet("font-weight: bold; background-color: #E8E8E8; padding: 5px; border-radius: 3px;")
        step_main_layout.addWidget(step_title_label)
        action_grid_container = QWidget(step_frame) 
        action_grid_layout = QGridLayout(action_grid_container)
        action_grid_layout.setSpacing(5) 
        action_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        step_main_layout.addWidget(action_grid_container)
        self._build_action_grid_for_step(step_def, graph, action_grid_layout)
        return step_frame

    def _build_action_grid_for_step(self, step_def: StepDefinition, graph: SessionActionsGraph, grid_layout: QGridLayout):
        while grid_layout.count():
            item = grid_layout.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()
        
        if not step_def.root_node_ids:
            grid_layout.addWidget(QLabel("  No actions defined for this step's root level.", self), 0, 0)
            return
        
        base_colors = [
            QColor(230,230,250), QColor(200,240,200), QColor(250,220,200), 
            QColor(200,220,250), QColor(250,200,220), QColor(220,250,220)
        ]
        
        current_grid_col_for_next_root_branch = 0
        for root_idx, root_node_id in enumerate(step_def.root_node_ids):
            branch_color = base_colors[root_idx % len(base_colors)]
            # Layout the branch starting at row 0 of the current available column block
            _max_row_in_branch, cols_spanned_by_branch = self._layout_action_branch_recursive(
                root_node_id, graph, grid_layout, branch_color, 
                0, current_grid_col_for_next_root_branch # Start column for this root branch
            )
            current_grid_col_for_next_root_branch += cols_spanned_by_branch
        
        if grid_layout.columnCount() > 0 : grid_layout.setColumnStretch(grid_layout.columnCount(), 1)
        if grid_layout.rowCount() > 0 : grid_layout.setRowStretch(grid_layout.rowCount(), 1)

    def _layout_action_branch_recursive(self, 
                                      node_id: str, 
                                      graph: SessionActionsGraph, 
                                      grid_layout: QGridLayout, 
                                      branch_color: QColor, 
                                      current_row: int, 
                                      start_col_for_this_node: int) -> Tuple[int, int]:
        action_node = graph.get_node_by_id(node_id)
        if not action_node: 
            # Add a placeholder for missing node to maintain grid structure
            # grid_layout.addWidget(QLabel(f"Missing {node_id[:4]}"), current_row, start_col_for_this_node)
            return current_row, 1 # Occupies one cell

        card = ActionCardWidget(action_node, self.project_data_ref, branch_color, self)
        card.clicked.connect(self._on_action_card_selected)
        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(
            lambda pos, an=action_node, cw=card: self._show_action_card_context_menu(pos, an, cw)
        )
        
        max_row_occupied_by_branch = current_row # This node occupies the current_row
        cols_spanned_by_this_node = 1 # Default span for this node itself

        if action_node.children_node_ids:
            next_row_for_children = current_row + 1
            current_col_offset_for_children = 0 # Relative to start_col_for_this_node

            for child_id in action_node.children_node_ids:
                # Recursively layout child branch. It starts in the row below the current node.
                # Its column starts at start_col_for_this_node + current_col_offset_for_children.
                max_row_in_child_branch, cols_spanned_by_child = self._layout_action_branch_recursive(
                    child_id, graph, grid_layout, branch_color,
                    next_row_for_children,
                    start_col_for_this_node + current_col_offset_for_children
                )
                max_row_occupied_by_branch = max(max_row_occupied_by_branch, max_row_in_child_branch)
                current_col_offset_for_children += cols_spanned_by_child
            
            # The current node should span all the columns its children collectively occupy
            if current_col_offset_for_children > 0:
                cols_spanned_by_this_node = current_col_offset_for_children
        
        # Add the current node's card to the grid, potentially spanning columns
        grid_layout.addWidget(card, current_row, start_col_for_this_node, 1, cols_spanned_by_this_node)
        self._action_card_widgets[action_node.node_id] = card
        
        return max_row_occupied_by_branch, cols_spanned_by_this_node

    @Slot(str)
    def _on_action_card_selected(self, node_id: str):
        if self._selected_action_card and self._selected_action_card.action_node.node_id != node_id:
            self._selected_action_card.set_selected(False)
        self._selected_action_card = self._action_card_widgets.get(node_id)
        if self._selected_action_card:
            self._selected_action_card.set_selected(True)
            self.action_node_selected.emit(self._selected_action_card.action_node)
        else: self.action_node_selected.emit(None)

    @Slot(QPoint)
    def _show_step_context_menu(self, position: QPoint, step_def: StepDefinition, step_frame_widget: QFrame):
        menu = QMenu(self)
        add_root_action = menu.addAction("Add Action to Step (Root)")
        add_root_action.triggered.connect(lambda: self._handle_add_action_to_step(step_def))
        current_step_index = -1
        if self._current_session_graph:
            try: current_step_index = self._current_session_graph.steps.index(step_def)
            except ValueError: pass 
        if current_step_index != -1:
            menu.addSeparator()
            move_step_up = menu.addAction("Move Step Up")
            move_step_up.setEnabled(current_step_index > 0)
            move_step_up.triggered.connect(lambda: self._handle_move_step(step_def, "up"))
            move_step_down = menu.addAction("Move Step Down")
            move_step_down.setEnabled(current_step_index < len(self._current_session_graph.steps) -1 if self._current_session_graph else False)
            move_step_down.triggered.connect(lambda: self._handle_move_step(step_def, "down"))
        menu.addSeparator()
        remove_step = menu.addAction("Remove This Step")
        remove_step.triggered.connect(lambda: self._handle_remove_step(step_def))
        menu.exec(step_frame_widget.mapToGlobal(position))

    @Slot(QPoint)
    def _show_action_card_context_menu(self, position: QPoint, action_node: ActionNode, card_widget: ActionCardWidget):
        menu = QMenu(self)
        add_child_action = menu.addAction(f"Add Child Action to '{action_node.action_label_to_execute}'")
        add_child_action.triggered.connect(lambda: self._handle_add_child_action(action_node))
        menu.addSeparator()
        remove_action = menu.addAction(f"Remove Action '{action_node.action_label_to_execute}'")
        remove_action.triggered.connect(lambda: self._handle_remove_action_node(action_node))
        menu.exec(card_widget.mapToGlobal(position))

    @Slot()
    def _create_new_step(self):
        if not self._current_session_graph: return
        step_name, ok = QInputDialog.getText(self, "Create New Step", "Enter optional name for the new step:")
        if not ok: return
        new_step = StepDefinition(step_name=step_name.strip())
        self._current_session_graph.steps.append(new_step)
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_move_step(self, step_to_move: StepDefinition, direction: str):
        if not self._current_session_graph: return
        try:
            current_idx = self._current_session_graph.steps.index(step_to_move)
            steps_list = self._current_session_graph.steps
            if direction == "up" and current_idx > 0:
                steps_list.pop(current_idx); steps_list.insert(current_idx - 1, step_to_move)
            elif direction == "down" and current_idx < len(steps_list) - 1:
                steps_list.pop(current_idx); steps_list.insert(current_idx + 1, step_to_move)
            else: return 
            self.load_session_graph(self._current_session_name, self._current_session_graph)
            self.session_graph_changed.emit()
        except ValueError: QMessageBox.critical(self, "Error", "Could not find step in data model to move.")

    def _handle_add_action_to_step(self, step_def: StepDefinition):
        if not self._current_session_graph or not self.project_data_ref: return
        if not self.project_data_ref.action_definitions:
            QMessageBox.warning(self, "No Actions Defined", "Please define some Actions first."); return
        selected_action_label = SelectActionLabelDialog.get_selected_action_label(self.project_data_ref.action_definitions, self)
        if not selected_action_label: return 
        new_action_node = ActionNode(action_label_to_execute=selected_action_label, parent_node_id=None)
        self._current_session_graph.nodes.append(new_action_node) 
        step_def.root_node_ids.append(new_action_node.node_id)
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_add_child_action(self, parent_action_node: ActionNode):
        if not self._current_session_graph or not self.project_data_ref: return
        if not self.project_data_ref.action_definitions:
            QMessageBox.warning(self, "No Actions Defined", "Please define some Actions first."); return
        selected_action_label = SelectActionLabelDialog.get_selected_action_label(self.project_data_ref.action_definitions, self)
        if not selected_action_label: return
        new_action_node = ActionNode(action_label_to_execute=selected_action_label, parent_node_id=parent_action_node.node_id)
        self._current_session_graph.nodes.append(new_action_node)
        parent_action_node.children_node_ids.append(new_action_node.node_id)
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_remove_step(self, step_to_remove: StepDefinition):
        if not self._current_session_graph: return
        reply = QMessageBox.question(self, "Confirm Removal", f"Remove Step '{step_to_remove.step_name or step_to_remove.step_id[:8]}' and ALL its actions?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            nodes_to_delete_ids = set()
            queue = list(step_to_remove.root_node_ids)
            processed_for_step_removal = set()
            while queue:
                node_id = queue.pop(0)
                if node_id in processed_for_step_removal: continue
                processed_for_step_removal.add(node_id)
                nodes_to_delete_ids.add(node_id)
                node = self._current_session_graph.get_node_by_id(node_id)
                if node: queue.extend(node.children_node_ids)
            self._current_session_graph.nodes = [n for n in self._current_session_graph.nodes if n.node_id not in nodes_to_delete_ids]
            if step_to_remove in self._current_session_graph.steps: self._current_session_graph.steps.remove(step_to_remove)
            self._current_session_graph.rebuild_node_lookup()
            self.load_session_graph(self._current_session_name, self._current_session_graph)
            self.session_graph_changed.emit()

    def _handle_remove_action_node(self, action_to_remove: ActionNode):
        if not self._current_session_graph: return
        reply = QMessageBox.question(self, "Confirm Removal", f"Remove Action '{action_to_remove.action_label_to_execute}' and ALL its child actions?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            nodes_to_delete_ids = set()
            queue = [action_to_remove.node_id]
            processed_for_action_removal = set()
            while queue:
                node_id = queue.pop(0)
                if node_id in processed_for_action_removal : continue 
                processed_for_action_removal.add(node_id)
                nodes_to_delete_ids.add(node_id)
                node = self._current_session_graph.get_node_by_id(node_id)
                if node: queue.extend(node.children_node_ids)
            self._current_session_graph.nodes = [n for n in self._current_session_graph.nodes if n.node_id not in nodes_to_delete_ids]
            if action_to_remove.parent_node_id:
                parent_node = self._current_session_graph.get_node_by_id(action_to_remove.parent_node_id)
                if parent_node and action_to_remove.node_id in parent_node.children_node_ids:
                    parent_node.children_node_ids.remove(action_to_remove.node_id)
            else: 
                for step_def_iter in self._current_session_graph.steps:
                    if action_to_remove.node_id in step_def_iter.root_node_ids:
                        step_def_iter.root_node_ids.remove(action_to_remove.node_id)
                        break
            self._current_session_graph.rebuild_node_lookup()
            self.load_session_graph(self._current_session_name, self._current_session_graph)
            self.session_graph_changed.emit()

# Standalone test
if __name__ == '__main__':
    if __package__ is None: 
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_script_dir)
        framework_tool_dir = os.path.dirname(gui_dir)
        project_root_dir = os.path.dirname(framework_tool_dir)
        if project_root_dir not in sys.path:
            sys.path.insert(0, project_root_dir)

    from PySide6.QtWidgets import QApplication, QMainWindow
    from framework_tool.data_models.project_data import ProjectData as TestProjectData
    from framework_tool.data_models.session_graph import SessionActionsGraph as TestSessionGraph, ActionNode as TestActionNode, StepDefinition as TestStepDefinition
    from framework_tool.data_models.action_definition import ActionDefinition as TestActionDef
    from framework_tool.gui.widgets.action_card_widget import ActionCardWidget 

    app = QApplication(sys.argv)
    dummy_project = TestProjectData()
    dummy_project.action_definitions["ActionA"] = TestActionDef(help_label="A: First Root")
    dummy_project.action_definitions["ActionB"] = TestActionDef(description="B: Second Root")
    dummy_project.action_definitions["ActionC"] = TestActionDef(help_label="C: Child of A")
    dummy_project.action_definitions["ActionD"] = TestActionDef(help_label="D: Child of A (parallel to C)")
    dummy_project.action_definitions["ActionE"] = TestActionDef(help_label="E: Child of C")
    dummy_project.action_definitions["ActionF"] = TestActionDef(help_label="F: Child of B")
    dummy_project.action_definitions["ActionG"] = TestActionDef(help_label="G: Third Root")
    dummy_project.action_definitions["ActionH"] = TestActionDef(help_label="H: Child of G")
    
    # Step 0: A
    s0_a = TestActionNode("ActionA")
    step0 = TestStepDefinition(step_name="Step 0: Action A", root_node_ids=[s0_a.node_id])

    # Step 1: (C -> (D -> E, F_parallel_to_D)), G -> H
    s1_c = TestActionNode("ActionC") # Root 1 of Step 1
    s1_d = TestActionNode("ActionD", parent_node_id=s1_c.node_id)
    s1_e = TestActionNode("ActionE", parent_node_id=s1_d.node_id)
    s1_f = TestActionNode("ActionF", parent_node_id=s1_c.node_id) # F is parallel to D, under C
    s1_c.children_node_ids = [s1_d.node_id, s1_f.node_id]
    s1_d.children_node_ids = [s1_e.node_id]

    s1_g = TestActionNode("ActionG") # Root 2 of Step 1
    s1_h = TestActionNode("ActionH", parent_node_id=s1_g.node_id)
    s1_g.children_node_ids = [s1_h.node_id]
    
    step1 = TestStepDefinition(step_name="Step 1: Complex", root_node_ids=[s1_c.node_id, s1_g.node_id])
    
    all_nodes = [s0_a, s1_c, s1_d, s1_e, s1_f, s1_g, s1_h]
    
    dummy_graph = TestSessionGraph(
        session_name="Test PDF Layout",
        steps=[step0, step1],
        nodes=all_nodes
    )
    dummy_project.session_actions.append(dummy_graph)

    test_main_window = QMainWindow() 
    editor = SessionFlowEditorWidget(project_data_ref=dummy_project, parent=test_main_window)
    
    def print_selected_node_details(node_obj):
        if node_obj: print(f"Details Panel Update for: {node_obj.action_label_to_execute}")
        else: print("Details Panel Cleared")
    editor.action_node_selected.connect(print_selected_node_details)
    
    editor.load_session_graph(dummy_graph.session_name, dummy_graph)
    test_main_window.setCentralWidget(editor)
    test_main_window.setWindowTitle("Test SessionFlow Editor (Advanced Grid)")
    test_main_window.resize(1000, 700)
    test_main_window.show()
    sys.exit(app.exec())

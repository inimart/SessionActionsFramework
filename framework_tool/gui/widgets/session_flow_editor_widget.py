# framework_tool/gui/widgets/session_flow_editor_widget.py
# All comments and identifiers in English

import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QGridLayout, QSpacerItem, QSizePolicy, QMenu,
    QMessageBox, QInputDialog, QApplication, QMainWindow, QCheckBox, QLineEdit
)
from PySide6.QtGui import QAction, QCursor, QColor, QPalette
from PySide6.QtCore import Qt, Signal, Slot, QPoint
from typing import Optional, List, Dict, Any, Tuple
import copy

# Import data models
from framework_tool.data_models.project_data import ProjectData
from framework_tool.data_models.session_graph import SessionActionsGraph, ActionNode, StepDefinition
from framework_tool.data_models.action_definition import ActionDefinition

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
        self._step_clipboard: Optional[List[ActionNode]] = None  # Store copied step content 
        self._action_clipboard: Optional[ActionNode] = None  # Store copied single action
        self._branch_clipboard: Optional[List[ActionNode]] = None  # Store copied branch
        self._collapsed_steps: set = set()  # Track collapsed steps
        self._filter_text: str = ""  # Track filter text
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        self.session_name_display = QLabel("Editing Session: [No Session Loaded]")
        self.session_name_display.setStyleSheet("font-weight: bold; padding: 5px;")
        main_layout.addWidget(self.session_name_display)
        
        # Add filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter Actions:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type action name to highlight...")
        self.filter_input.textChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_input)
        
        clear_filter_button = QPushButton("Clear")
        clear_filter_button.clicked.connect(self._clear_filter)
        filter_layout.addWidget(clear_filter_button)
        
        main_layout.addLayout(filter_layout)
        
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
        
    def _on_filter_changed(self, text: str):
        """Handle filter text changes."""
        self._filter_text = text.lower().strip()
        self._update_action_highlights()
        
    def _clear_filter(self):
        """Clear the filter text."""
        self.filter_input.setText("")
        
    def _update_action_highlights(self):
        """Update action card highlights based on current filter."""
        for node_id, card_widget in self._action_card_widgets.items():
            if card_widget:
                action_node = card_widget.action_node
                is_match = (self._filter_text == "" or 
                           self._filter_text in action_node.action_label_to_execute.lower())
                card_widget.set_highlighted(is_match and self._filter_text != "")

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

    def refresh_current_view(self):
        """Refresh the current view to update action card content without full reload."""
        if not self._current_session_graph:
            return
            
        # Update all existing action cards
        for node_id, card_widget in self._action_card_widgets.items():
            if card_widget:
                card_widget.refresh_content()
        
        # Update step titles if needed
        for step_def, step_frame in self._step_frames.items():
            if hasattr(step_frame, 'step_label'):
                step_frame.step_label.setText(f"Step: {step_def.step_name}")

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
        
        # Create title section with checkbox
        title_section = QHBoxLayout()
        title_section.setContentsMargins(0,0,0,0)
        
        # Create enabled checkbox
        enabled_checkbox = QCheckBox()
        enabled_checkbox.setChecked(step_def.enabled)
        enabled_checkbox.stateChanged.connect(lambda state, sd=step_def: self._handle_step_enabled_changed(sd, state == Qt.CheckState.Checked.value))
        title_section.addWidget(enabled_checkbox)
        
        # Create collapsible title button
        title_text = f"Step {step_index}"
        if step_def.step_name: title_text += f": {step_def.step_name}"
        
        is_collapsed = step_def.step_id in self._collapsed_steps
        collapse_indicator = "▶ " if is_collapsed else "▼ "
        
        step_title_button = QPushButton(collapse_indicator + title_text)
        step_title_button.setStyleSheet("font-weight: bold; background-color: #E8E8E8; color: black; padding: 5px; border-radius: 3px; text-align: left;")
        step_title_button.clicked.connect(lambda: self._toggle_step_collapse(step_def.step_id))
        title_section.addWidget(step_title_button)
        title_section.addStretch()
        
        # Add title section to main layout
        title_widget = QWidget()
        title_widget.setLayout(title_section)
        step_main_layout.addWidget(title_widget)
        
        # Store reference to checkbox for later updates
        step_frame.enabled_checkbox = enabled_checkbox
        
        # Create action grid container (collapsible content)
        action_grid_container = QWidget(step_frame) 
        action_grid_layout = QGridLayout(action_grid_container)
        action_grid_layout.setSpacing(5) 
        action_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        step_main_layout.addWidget(action_grid_container)
        
        # Store reference to action container for collapsing
        step_frame.action_grid_container = action_grid_container
        
        # Hide content if collapsed
        is_collapsed = step_def.step_id in self._collapsed_steps
        action_grid_container.setVisible(not is_collapsed)
        
        # Build action grid only if not collapsed
        if not is_collapsed:
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
        # Connect hover button signals
        card.add_parent_requested.connect(self._handle_add_parent_action)
        card.add_child_requested.connect(self._handle_add_child_action_from_hover)
        card.add_sibling_requested.connect(self._handle_add_sibling_action)
        card.insert_intermediate_requested.connect(self._handle_insert_intermediate_action)
        
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
        
        # Apply current filter highlighting if any
        if self._filter_text:
            is_match = self._filter_text in action_node.action_label_to_execute.lower()
            card.set_highlighted(is_match)
        
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
        
        menu.addSeparator()
        
        # Copy/Paste functionality
        copy_step = menu.addAction("Copy step")
        copy_step.triggered.connect(lambda: self._handle_copy_step(step_def))
        
        paste_step = menu.addAction("Paste step content")
        paste_step.setEnabled(self._step_clipboard is not None)
        paste_step.triggered.connect(lambda: self._handle_paste_step_content(step_def))
        
        current_step_index = -1
        if self._current_session_graph:
            try: current_step_index = self._current_session_graph.steps.index(step_def)
            except ValueError: pass 
        if current_step_index != -1:
            menu.addSeparator()
            
            # Add step above/below
            add_step_above = menu.addAction("Add step above")
            add_step_above.triggered.connect(lambda: self._handle_add_step_above(step_def))
            
            add_step_below = menu.addAction("Add step below")
            add_step_below.triggered.connect(lambda: self._handle_add_step_below(step_def))
            
            menu.addSeparator()
            
            move_step_up = menu.addAction("Move Step Up")
            move_step_up.setEnabled(current_step_index > 0)
            move_step_up.triggered.connect(lambda: self._handle_move_step(step_def, "up"))
            move_step_down = menu.addAction("Move Step Down")
            move_step_down.setEnabled(current_step_index < len(self._current_session_graph.steps) -1 if self._current_session_graph else False)
            move_step_down.triggered.connect(lambda: self._handle_move_step(step_def, "down"))
        menu.addSeparator()
        rename_step = menu.addAction("Rename Step")
        rename_step.triggered.connect(lambda: self._handle_rename_step(step_def))
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
        
        # Copy/Paste actions
        copy_action = menu.addAction("Copy action")
        copy_action.triggered.connect(lambda: self._handle_copy_action(action_node))
        
        copy_branch = menu.addAction("Copy branch")
        copy_branch.triggered.connect(lambda: self._handle_copy_branch(action_node))
        
        menu.addSeparator()
        
        paste_action_as_child = menu.addAction("Paste action content as child")
        paste_action_as_child.setEnabled(self._action_clipboard is not None)
        paste_action_as_child.triggered.connect(lambda: self._handle_paste_action_as_child(action_node))
        
        paste_action_as_brother = menu.addAction("Paste action content as brother")
        paste_action_as_brother.setEnabled(self._action_clipboard is not None)
        paste_action_as_brother.triggered.connect(lambda: self._handle_paste_action_as_brother(action_node))
        
        paste_branch_as_child = menu.addAction("Paste branch content as child")
        paste_branch_as_child.setEnabled(self._branch_clipboard is not None)
        paste_branch_as_child.triggered.connect(lambda: self._handle_paste_branch_as_child(action_node))
        
        paste_branch_as_brother = menu.addAction("Paste branch content as brother")
        paste_branch_as_brother.setEnabled(self._branch_clipboard is not None)
        paste_branch_as_brother.triggered.connect(lambda: self._handle_paste_branch_as_brother(action_node))
        
        paste_action_as_parent = menu.addAction("Paste action content as parent")
        paste_action_as_parent.setEnabled(self._action_clipboard is not None)
        paste_action_as_parent.triggered.connect(lambda: self._handle_paste_action_as_parent(action_node))
        
        paste_branch_as_parent = menu.addAction("Paste branch content as parent")
        paste_branch_as_parent.setEnabled(self._branch_clipboard is not None)
        paste_branch_as_parent.triggered.connect(lambda: self._handle_paste_branch_as_parent(action_node))
        
        # Check conditions for move up/down actions
        can_move_up = self._can_move_action_up(action_node)
        can_move_down = self._can_move_action_down(action_node)
        
        menu.addSeparator()
        
        if can_move_up or can_move_down:
            if can_move_up:
                move_up_action = menu.addAction("Sposta action in su")
                move_up_action.triggered.connect(lambda: self._handle_move_action_up(action_node))
            
            if can_move_down:
                move_down_action = menu.addAction("Sposta action in giù")
                move_down_action.triggered.connect(lambda: self._handle_move_action_down(action_node))
        
        menu.addSeparator()
        remove_action = menu.addAction(f"Remove Action '{action_node.action_label_to_execute}'")
        remove_action.triggered.connect(lambda: self._handle_remove_action_only(action_node))
        remove_branch = menu.addAction(f"Remove Branch '{action_node.action_label_to_execute}'")
        remove_branch.triggered.connect(lambda: self._handle_remove_action_node(action_node))
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

    def refresh_current_view(self):
        """
        Refreshes the current view by updating existing action cards when their data changes.
        This is more efficient than completely reloading the session graph as it preserves
        the current UI state (selections, scroll position, etc.) while updating card content.
        """
        if not self._current_session_graph or not self._action_card_widgets:
            return
        
        # Update all existing action card widgets with their current data
        for node_id, card_widget in self._action_card_widgets.items():
            # Find the corresponding action node in the current session graph
            action_node = self._current_session_graph.get_node_by_id(node_id)
            if action_node:
                # Update the card widget's action node reference
                card_widget.action_node = action_node
                # Refresh the card's visual content
                card_widget.refresh_content()
        
        # Update step title labels and checkbox states to reflect any changes
        for step_def in self._current_session_graph.steps:
            if step_def.step_id in self._step_frames:
                step_frame = self._step_frames[step_def.step_id]
                step_index = self._current_session_graph.steps.index(step_def)
                title_text = f"Step {step_index}"
                if step_def.step_name:
                    title_text += f": {step_def.step_name}"
                
                # Update checkbox state
                if hasattr(step_frame, 'enabled_checkbox'):
                    step_frame.enabled_checkbox.setChecked(step_def.enabled)
                
                # Find and update the step title label
                step_layout = step_frame.layout()
                if step_layout and step_layout.count() > 0:
                    title_widget = step_layout.itemAt(0).widget()
                    if hasattr(title_widget, 'layout'):
                        title_section_layout = title_widget.layout()
                        if title_section_layout and title_section_layout.count() > 1:
                            title_label = title_section_layout.itemAt(1).widget()
                            if isinstance(title_label, QLabel):
                                title_label.setText(title_text)
        
        # Emit signal to notify other components that the view has been refreshed
        self.session_graph_changed.emit()

    def _handle_add_parent_action(self, node_id: str):
        """Handle adding a parent action from hover button."""
        if not self._current_session_graph or not self.project_data_ref:
            return
        
        action_node = self._current_session_graph.get_node_by_id(node_id)
        if not action_node:
            return
            
        if not self.project_data_ref.action_definitions:
            QMessageBox.warning(self, "No Actions Defined", "Please define some Actions first.")
            return
            
        selected_action_label = SelectActionLabelDialog.get_selected_action_label(self.project_data_ref.action_definitions, self)
        if not selected_action_label:
            return
            
        # Create new parent action
        new_parent_node = ActionNode(action_label_to_execute=selected_action_label, parent_node_id=action_node.parent_node_id)
        self._current_session_graph.nodes.append(new_parent_node)
        
        # Update relationships
        if action_node.parent_node_id:
            # Child node - update existing parent's children
            old_parent = self._current_session_graph.get_node_by_id(action_node.parent_node_id)
            if old_parent:
                old_parent.children_node_ids = [new_parent_node.node_id if child_id == node_id else child_id for child_id in old_parent.children_node_ids]
        else:
            # Root node - update step's root nodes
            for step_def in self._current_session_graph.steps:
                if node_id in step_def.root_node_ids:
                    step_def.root_node_ids = [new_parent_node.node_id if root_id == node_id else root_id for root_id in step_def.root_node_ids]
                    break
        
        # Set new parent-child relationship
        action_node.parent_node_id = new_parent_node.node_id
        new_parent_node.children_node_ids = [node_id]
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_add_child_action_from_hover(self, node_id: str):
        """Handle adding a child action from hover button (wrapper for existing method)."""
        action_node = self._current_session_graph.get_node_by_id(node_id) if self._current_session_graph else None
        if action_node:
            self._handle_add_child_action(action_node)

    def _handle_add_sibling_action(self, node_id: str):
        """Handle adding a sibling action from hover button."""
        if not self._current_session_graph or not self.project_data_ref:
            return
        
        action_node = self._current_session_graph.get_node_by_id(node_id)
        if not action_node:
            return
            
        if not self.project_data_ref.action_definitions:
            QMessageBox.warning(self, "No Actions Defined", "Please define some Actions first.")
            return
            
        selected_action_label = SelectActionLabelDialog.get_selected_action_label(self.project_data_ref.action_definitions, self)
        if not selected_action_label:
            return
            
        # Create new sibling action
        new_sibling_node = ActionNode(action_label_to_execute=selected_action_label, parent_node_id=action_node.parent_node_id)
        self._current_session_graph.nodes.append(new_sibling_node)
        
        # Add to same parent or step
        if action_node.parent_node_id:
            # Has parent - add to parent's children
            parent_node = self._current_session_graph.get_node_by_id(action_node.parent_node_id)
            if parent_node:
                parent_node.children_node_ids.append(new_sibling_node.node_id)
        else:
            # Root node - add to same step
            for step_def in self._current_session_graph.steps:
                if node_id in step_def.root_node_ids:
                    step_def.root_node_ids.append(new_sibling_node.node_id)
                    break
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_insert_intermediate_action(self, node_id: str):
        """Handle inserting an intermediate action between a node and its multiple children."""
        if not self._current_session_graph or not self.project_data_ref:
            return
        
        action_node = self._current_session_graph.get_node_by_id(node_id)
        if not action_node or len(action_node.children_node_ids) <= 1:
            return  # Only works with nodes that have multiple children
            
        if not self.project_data_ref.action_definitions:
            QMessageBox.warning(self, "No Actions Defined", "Please define some Actions first.")
            return
            
        selected_action_label = SelectActionLabelDialog.get_selected_action_label(self.project_data_ref.action_definitions, self)
        if not selected_action_label:
            return
            
        # Create intermediate action
        intermediate_node = ActionNode(action_label_to_execute=selected_action_label, parent_node_id=action_node.node_id)
        self._current_session_graph.nodes.append(intermediate_node)
        
        # Update relationships: intermediate becomes sole child of original node
        # and takes over all the original children
        original_children = action_node.children_node_ids.copy()
        action_node.children_node_ids = [intermediate_node.node_id]
        intermediate_node.children_node_ids = original_children
        
        # Update parent references of original children
        for child_id in original_children:
            child_node = self._current_session_graph.get_node_by_id(child_id)
            if child_node:
                child_node.parent_node_id = intermediate_node.node_id
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_remove_action_only(self, action_to_remove: ActionNode):
        """Remove only the specified action, promoting its children to the parent level."""
        if not self._current_session_graph:
            return
            
        reply = QMessageBox.question(self, "Confirm Removal", 
                                   f"Remove Action '{action_to_remove.action_label_to_execute}' only? Its children will be promoted to the parent level.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Get children that will be promoted
        children_to_promote = action_to_remove.children_node_ids.copy()
        
        # Update parent relationships for promoted children
        for child_id in children_to_promote:
            child_node = self._current_session_graph.get_node_by_id(child_id)
            if child_node:
                child_node.parent_node_id = action_to_remove.parent_node_id
        
        # Update parent's children or step's root nodes
        if action_to_remove.parent_node_id:
            # Has parent - update parent's children list
            parent_node = self._current_session_graph.get_node_by_id(action_to_remove.parent_node_id)
            if parent_node:
                # Replace the removed action with its children
                new_children = []
                for child_id in parent_node.children_node_ids:
                    if child_id == action_to_remove.node_id:
                        new_children.extend(children_to_promote)  # Add promoted children
                    else:
                        new_children.append(child_id)  # Keep existing children
                parent_node.children_node_ids = new_children
        else:
            # Is root node - update step's root nodes
            for step_def in self._current_session_graph.steps:
                if action_to_remove.node_id in step_def.root_node_ids:
                    # Replace the removed action with its children
                    new_roots = []
                    for root_id in step_def.root_node_ids:
                        if root_id == action_to_remove.node_id:
                            new_roots.extend(children_to_promote)  # Add promoted children
                        else:
                            new_roots.append(root_id)  # Keep existing roots
                    step_def.root_node_ids = new_roots
                    break
        
        # Remove the action from the graph
        self._current_session_graph.nodes = [n for n in self._current_session_graph.nodes if n.node_id != action_to_remove.node_id]
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_copy_step(self, step_def: StepDefinition):
        """Copy all action nodes from a step to the clipboard."""
        if not self._current_session_graph:
            return
        
        # Get all nodes in this step (including hierarchical structure)
        nodes_to_copy = []
        queue = list(step_def.root_node_ids)
        processed = set()
        
        while queue:
            node_id = queue.pop(0)
            if node_id in processed:
                continue
            processed.add(node_id)
            
            node = self._current_session_graph.get_node_by_id(node_id)
            if node:
                nodes_to_copy.append(node)
                queue.extend(node.children_node_ids)
        
        # Deep copy the nodes to avoid reference issues
        self._step_clipboard = copy.deepcopy(nodes_to_copy)
        
        QMessageBox.information(self, "Step Copied", f"Step '{step_def.step_name or step_def.step_id[:8]}' with {len(self._step_clipboard)} actions copied to clipboard.")

    def _handle_paste_step_content(self, step_def: StepDefinition):
        """Paste copied step content into the current step."""
        if not self._step_clipboard or not self._current_session_graph:
            return
        
        # Check if step has existing content
        has_existing_content = bool(step_def.root_node_ids)
        
        if has_existing_content:
            reply = QMessageBox.question(
                self, 
                "Replace Step Content",
                f"Step '{step_def.step_name or step_def.step_id[:8]}' already has content. "
                "Do you want to replace it with the copied content?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Remove existing content if any
        if has_existing_content:
            nodes_to_remove = set()
            queue = list(step_def.root_node_ids)
            processed = set()
            
            while queue:
                node_id = queue.pop(0)
                if node_id in processed:
                    continue
                processed.add(node_id)
                nodes_to_remove.add(node_id)
                
                node = self._current_session_graph.get_node_by_id(node_id)
                if node:
                    queue.extend(node.children_node_ids)
            
            # Remove old nodes
            self._current_session_graph.nodes = [n for n in self._current_session_graph.nodes if n.node_id not in nodes_to_remove]
            step_def.root_node_ids.clear()
        
        # Add copied nodes
        node_id_mapping = {}  # Map old IDs to new IDs
        new_nodes = []
        
        for copied_node in self._step_clipboard:
            # Create new node with new ID and preserve all properties
            new_node = ActionNode(
                action_label_to_execute=copied_node.action_label_to_execute,
                parent_node_id=None,  # Will be set later
                instance_label=copied_node.instance_label,
                custom_field_values=copy.deepcopy(copied_node.custom_field_values)
            )
            new_nodes.append(new_node)
            node_id_mapping[copied_node.node_id] = new_node.node_id
        
        # Update parent-child relationships with new IDs
        for i, copied_node in enumerate(self._step_clipboard):
            new_node = new_nodes[i]
            
            # Update parent reference
            if copied_node.parent_node_id and copied_node.parent_node_id in node_id_mapping:
                new_node.parent_node_id = node_id_mapping[copied_node.parent_node_id]
            
            # Update children references
            new_node.children_node_ids = [
                node_id_mapping[child_id] for child_id in copied_node.children_node_ids
                if child_id in node_id_mapping
            ]
        
        # Add new nodes to graph
        self._current_session_graph.nodes.extend(new_nodes)
        
        # Update step root nodes (nodes without parents)
        for new_node in new_nodes:
            if new_node.parent_node_id is None:
                step_def.root_node_ids.append(new_node.node_id)
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()
        
        QMessageBox.information(self, "Step Pasted", f"Pasted {len(self._step_clipboard)} actions into step '{step_def.step_name or step_def.step_id[:8]}'.")

    def _handle_add_step_above(self, step_def: StepDefinition):
        """Add a new step above the current step."""
        if not self._current_session_graph:
            return
        
        step_name, ok = QInputDialog.getText(self, "Add Step Above", "Enter optional name for the new step:")
        if not ok:
            return
        
        try:
            current_index = self._current_session_graph.steps.index(step_def)
            new_step = StepDefinition(step_name=step_name.strip())
            self._current_session_graph.steps.insert(current_index, new_step)
            
            self.load_session_graph(self._current_session_name, self._current_session_graph)
            self.session_graph_changed.emit()
        except ValueError:
            QMessageBox.critical(self, "Error", "Could not find step in data model.")

    def _handle_add_step_below(self, step_def: StepDefinition):
        """Add a new step below the current step."""
        if not self._current_session_graph:
            return
        
        step_name, ok = QInputDialog.getText(self, "Add Step Below", "Enter optional name for the new step:")
        if not ok:
            return
        
        try:
            current_index = self._current_session_graph.steps.index(step_def)
            new_step = StepDefinition(step_name=step_name.strip())
            self._current_session_graph.steps.insert(current_index + 1, new_step)
            
            self.load_session_graph(self._current_session_name, self._current_session_graph)
            self.session_graph_changed.emit()
        except ValueError:
            QMessageBox.critical(self, "Error", "Could not find step in data model.")

    def _can_move_action_up(self, action_node: ActionNode) -> bool:
        """Check if an action can be moved up in the hierarchy."""
        if not self._current_session_graph or not action_node.parent_node_id:
            return False
        
        parent_node = self._current_session_graph.get_node_by_id(action_node.parent_node_id)
        if not parent_node:
            return False
        
        # Can move up if parent has only one child (this action)
        return len(parent_node.children_node_ids) == 1

    def _can_move_action_down(self, action_node: ActionNode) -> bool:
        """Check if an action can be moved down in the hierarchy."""
        if not self._current_session_graph:
            return False
        
        # Can move down if this action has only one child
        return len(action_node.children_node_ids) == 1

    def _handle_move_action_up(self, action_node: ActionNode):
        """Move action up in hierarchy. A > B > C becomes B > A > C"""
        if not self._current_session_graph or not self._can_move_action_up(action_node):
            return
        
        parent_node = self._current_session_graph.get_node_by_id(action_node.parent_node_id)
        if not parent_node:
            return
        
        # Store action's children before restructuring
        action_children = action_node.children_node_ids.copy()
        
        # Restructure: action takes parent's place
        action_node.parent_node_id = parent_node.parent_node_id
        action_node.children_node_ids = [parent_node.node_id]
        
        # Parent becomes child of action, gets action's original children
        parent_node.parent_node_id = action_node.node_id
        parent_node.children_node_ids = action_children
        
        # Update parent references for action's original children
        for child_id in action_children:
            child_node = self._current_session_graph.get_node_by_id(child_id)
            if child_node:
                child_node.parent_node_id = parent_node.node_id
        
        # Update grandparent's children or step root nodes
        if action_node.parent_node_id:
            grandparent_node = self._current_session_graph.get_node_by_id(action_node.parent_node_id)
            if grandparent_node:
                # Replace parent with action in grandparent's children
                grandparent_node.children_node_ids = [
                    action_node.node_id if child_id == parent_node.node_id else child_id
                    for child_id in grandparent_node.children_node_ids
                ]
        else:
            # Parent was root node, now action becomes root
            for step_def in self._current_session_graph.steps:
                if parent_node.node_id in step_def.root_node_ids:
                    step_def.root_node_ids = [
                        action_node.node_id if root_id == parent_node.node_id else root_id
                        for root_id in step_def.root_node_ids
                    ]
                    break
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_move_action_down(self, action_node: ActionNode):
        """Move action down in hierarchy. A > B > C becomes A > C > B"""
        if not self._current_session_graph or not self._can_move_action_down(action_node):
            return
        
        child_node_id = action_node.children_node_ids[0]
        child_node = self._current_session_graph.get_node_by_id(child_node_id)
        if not child_node:
            return
        
        # Store child's children before restructuring
        child_children = child_node.children_node_ids.copy()
        
        # Restructure: child takes action's place
        child_node.parent_node_id = action_node.parent_node_id
        child_node.children_node_ids = [action_node.node_id]
        
        # Action becomes child of its former child, keeps empty children initially
        action_node.parent_node_id = child_node.node_id
        action_node.children_node_ids = child_children
        
        # Update parent references for child's original children
        for grandchild_id in child_children:
            grandchild_node = self._current_session_graph.get_node_by_id(grandchild_id)
            if grandchild_node:
                grandchild_node.parent_node_id = action_node.node_id
        
        # Update parent's children or step root nodes
        if child_node.parent_node_id:
            parent_node = self._current_session_graph.get_node_by_id(child_node.parent_node_id)
            if parent_node:
                # Replace action with child in parent's children
                parent_node.children_node_ids = [
                    child_node.node_id if child_id == action_node.node_id else child_id
                    for child_id in parent_node.children_node_ids
                ]
        else:
            # Action was root node, now child becomes root
            for step_def in self._current_session_graph.steps:
                if action_node.node_id in step_def.root_node_ids:
                    step_def.root_node_ids = [
                        child_node.node_id if root_id == action_node.node_id else root_id
                        for root_id in step_def.root_node_ids
                    ]
                    break
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()

    def _handle_step_enabled_changed(self, step_def: StepDefinition, enabled: bool):
        """Handle step enabled/disabled state change."""
        if not self._current_session_graph:
            return
        
        step_def.enabled = enabled
        self.session_graph_changed.emit()
        
    def _toggle_step_collapse(self, step_id: str):
        """Toggle the collapsed state of a step."""
        if step_id in self._collapsed_steps:
            self._collapsed_steps.remove(step_id)
        else:
            self._collapsed_steps.add(step_id)
        
        # Refresh the display to update collapse state
        if self._current_session_graph:
            self.load_session_graph(self._current_session_name, self._current_session_graph)

    def _handle_copy_action(self, action_node: ActionNode):
        """Copy a single action to clipboard."""
        if not action_node:
            return
        
        # Deep copy the action node with its custom field values
        self._action_clipboard = copy.deepcopy(action_node)
        self._branch_clipboard = None  # Clear branch clipboard
        
        QMessageBox.information(self, "Action Copied", f"Action '{action_node.action_label_to_execute}' copied to clipboard.")
    
    def _handle_copy_branch(self, action_node: ActionNode):
        """Copy an entire branch starting from this action."""
        if not self._current_session_graph or not action_node:
            return
        
        # Collect all nodes in the branch
        nodes_to_copy = []
        queue = [action_node.node_id]
        processed = set()
        
        while queue:
            node_id = queue.pop(0)
            if node_id in processed:
                continue
            processed.add(node_id)
            
            node = self._current_session_graph.get_node_by_id(node_id)
            if node:
                nodes_to_copy.append(node)
                queue.extend(node.children_node_ids)
        
        # Deep copy the branch
        self._branch_clipboard = copy.deepcopy(nodes_to_copy)
        self._action_clipboard = None  # Clear action clipboard
        
        QMessageBox.information(self, "Branch Copied", f"Branch starting from '{action_node.action_label_to_execute}' with {len(self._branch_clipboard)} actions copied to clipboard.")
    
    def _handle_paste_action_as_child(self, parent_action_node: ActionNode):
        """Paste a single action as child of the selected action."""
        if not self._current_session_graph or not self._action_clipboard:
            return
        
        # Create new action node with new ID but same properties
        new_action_node = ActionNode(
            action_label_to_execute=self._action_clipboard.action_label_to_execute,
            parent_node_id=parent_action_node.node_id,
            instance_label=self._action_clipboard.instance_label,
            custom_field_values=copy.deepcopy(self._action_clipboard.custom_field_values)
        )
        
        self._current_session_graph.nodes.append(new_action_node)
        parent_action_node.children_node_ids.append(new_action_node.node_id)
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()
    
    def _handle_paste_action_as_brother(self, sibling_action_node: ActionNode):
        """Paste a single action as sibling of the selected action."""
        if not self._current_session_graph or not self._action_clipboard:
            return
        
        # Create new action node with same parent as sibling
        new_action_node = ActionNode(
            action_label_to_execute=self._action_clipboard.action_label_to_execute,
            parent_node_id=sibling_action_node.parent_node_id,
            instance_label=self._action_clipboard.instance_label,
            custom_field_values=copy.deepcopy(self._action_clipboard.custom_field_values)
        )
        
        self._current_session_graph.nodes.append(new_action_node)
        
        # Add to same parent or step
        if sibling_action_node.parent_node_id:
            parent_node = self._current_session_graph.get_node_by_id(sibling_action_node.parent_node_id)
            if parent_node:
                parent_node.children_node_ids.append(new_action_node.node_id)
        else:
            # Root node - add to same step
            for step_def in self._current_session_graph.steps:
                if sibling_action_node.node_id in step_def.root_node_ids:
                    step_def.root_node_ids.append(new_action_node.node_id)
                    break
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()
    
    def _handle_paste_branch_as_child(self, parent_action_node: ActionNode):
        """Paste an entire branch as child of the selected action."""
        if not self._current_session_graph or not self._branch_clipboard:
            return
        
        # Map old IDs to new IDs
        node_id_mapping = {}
        new_nodes = []
        
        # Create new nodes with new IDs
        for copied_node in self._branch_clipboard:
            new_node = ActionNode(
                action_label_to_execute=copied_node.action_label_to_execute,
                parent_node_id=None,  # Will be set later
                instance_label=copied_node.instance_label,
                custom_field_values=copy.deepcopy(copied_node.custom_field_values)
            )
            new_nodes.append(new_node)
            node_id_mapping[copied_node.node_id] = new_node.node_id
        
        # Update parent-child relationships
        for i, copied_node in enumerate(self._branch_clipboard):
            new_node = new_nodes[i]
            
            # Set parent - root of branch becomes child of parent_action_node
            if i == 0:  # First node (root of branch)
                new_node.parent_node_id = parent_action_node.node_id
            elif copied_node.parent_node_id in node_id_mapping:
                new_node.parent_node_id = node_id_mapping[copied_node.parent_node_id]
            
            # Update children references
            new_node.children_node_ids = [
                node_id_mapping[child_id] for child_id in copied_node.children_node_ids
                if child_id in node_id_mapping
            ]
        
        # Add new nodes to graph
        self._current_session_graph.nodes.extend(new_nodes)
        
        # Add root of branch to parent's children
        if new_nodes:
            parent_action_node.children_node_ids.append(new_nodes[0].node_id)
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()
    
    def _handle_paste_branch_as_brother(self, sibling_action_node: ActionNode):
        """Paste an entire branch as sibling of the selected action."""
        if not self._current_session_graph or not self._branch_clipboard:
            return
        
        # Map old IDs to new IDs
        node_id_mapping = {}
        new_nodes = []
        
        # Create new nodes with new IDs
        for copied_node in self._branch_clipboard:
            new_node = ActionNode(
                action_label_to_execute=copied_node.action_label_to_execute,
                parent_node_id=None,  # Will be set later
                instance_label=copied_node.instance_label,
                custom_field_values=copy.deepcopy(copied_node.custom_field_values)
            )
            new_nodes.append(new_node)
            node_id_mapping[copied_node.node_id] = new_node.node_id
        
        # Update parent-child relationships
        for i, copied_node in enumerate(self._branch_clipboard):
            new_node = new_nodes[i]
            
            # Set parent - root of branch has same parent as sibling
            if i == 0:  # First node (root of branch)
                new_node.parent_node_id = sibling_action_node.parent_node_id
            elif copied_node.parent_node_id in node_id_mapping:
                new_node.parent_node_id = node_id_mapping[copied_node.parent_node_id]
            
            # Update children references
            new_node.children_node_ids = [
                node_id_mapping[child_id] for child_id in copied_node.children_node_ids
                if child_id in node_id_mapping
            ]
        
        # Add new nodes to graph
        self._current_session_graph.nodes.extend(new_nodes)
        
        # Add root of branch to same parent or step as sibling
        if new_nodes:
            if sibling_action_node.parent_node_id:
                parent_node = self._current_session_graph.get_node_by_id(sibling_action_node.parent_node_id)
                if parent_node:
                    parent_node.children_node_ids.append(new_nodes[0].node_id)
            else:
                # Root node - add to same step
                for step_def in self._current_session_graph.steps:
                    if sibling_action_node.node_id in step_def.root_node_ids:
                        step_def.root_node_ids.append(new_nodes[0].node_id)
                        break
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()
    
    def _handle_rename_step(self, step_def: StepDefinition):
        """Handle renaming a step."""
        if not self._current_session_graph:
            return
        
        current_name = step_def.step_name or ""
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename Step", 
            "Enter new name for the step:",
            text=current_name
        )
        
        if ok:
            step_def.step_name = new_name.strip()
            self.load_session_graph(self._current_session_name, self._current_session_graph)
            self.session_graph_changed.emit()
    
    def _handle_paste_action_as_parent(self, child_action_node: ActionNode):
        """Paste a single action as parent of the selected action."""
        if not self._current_session_graph or not self._action_clipboard:
            return
        
        # Create new action node that will become the parent
        new_parent_node = ActionNode(
            action_label_to_execute=self._action_clipboard.action_label_to_execute,
            parent_node_id=child_action_node.parent_node_id,
            instance_label=self._action_clipboard.instance_label,
            custom_field_values=copy.deepcopy(self._action_clipboard.custom_field_values)
        )
        
        # Add the new parent node to the graph
        self._current_session_graph.nodes.append(new_parent_node)
        
        # Update relationships: new node becomes parent of selected node
        if child_action_node.parent_node_id:
            # Child has a parent - update existing parent's children
            parent_node = self._current_session_graph.get_node_by_id(child_action_node.parent_node_id)
            if parent_node:
                # Replace child_action_node with new_parent_node in parent's children
                parent_node.children_node_ids = [
                    new_parent_node.node_id if child_id == child_action_node.node_id else child_id
                    for child_id in parent_node.children_node_ids
                ]
        else:
            # Child is a root node - update step's root nodes
            for step_def in self._current_session_graph.steps:
                if child_action_node.node_id in step_def.root_node_ids:
                    step_def.root_node_ids = [
                        new_parent_node.node_id if root_id == child_action_node.node_id else root_id
                        for root_id in step_def.root_node_ids
                    ]
                    break
        
        # Set new parent-child relationship
        child_action_node.parent_node_id = new_parent_node.node_id
        new_parent_node.children_node_ids = [child_action_node.node_id]
        
        self._current_session_graph.rebuild_node_lookup()
        self.load_session_graph(self._current_session_name, self._current_session_graph)
        self.session_graph_changed.emit()
    
    def _handle_paste_branch_as_parent(self, child_action_node: ActionNode):
        """Paste an entire branch as parent of the selected action."""
        if not self._current_session_graph or not self._branch_clipboard:
            return
        
        # Map old IDs to new IDs
        node_id_mapping = {}
        new_nodes = []
        
        # Create new nodes with new IDs
        for copied_node in self._branch_clipboard:
            new_node = ActionNode(
                action_label_to_execute=copied_node.action_label_to_execute,
                parent_node_id=None,  # Will be set later
                instance_label=copied_node.instance_label,
                custom_field_values=copy.deepcopy(copied_node.custom_field_values)
            )
            new_nodes.append(new_node)
            node_id_mapping[copied_node.node_id] = new_node.node_id
        
        # Update parent-child relationships within the branch
        for i, copied_node in enumerate(self._branch_clipboard):
            new_node = new_nodes[i]
            
            # Update parent reference within the branch
            if copied_node.parent_node_id in node_id_mapping:
                new_node.parent_node_id = node_id_mapping[copied_node.parent_node_id]
            
            # Update children references
            new_node.children_node_ids = [
                node_id_mapping[child_id] for child_id in copied_node.children_node_ids
                if child_id in node_id_mapping
            ]
        
        # Find the leaf nodes (nodes without children) in the pasted branch
        leaf_nodes = [node for node in new_nodes if not node.children_node_ids]
        
        if not new_nodes:
            return
        
        # The root of the pasted branch takes the place of child_action_node
        branch_root = new_nodes[0]
        branch_root.parent_node_id = child_action_node.parent_node_id
        
        # Update relationships: branch root replaces child_action_node
        if child_action_node.parent_node_id:
            # Child has a parent - update existing parent's children
            parent_node = self._current_session_graph.get_node_by_id(child_action_node.parent_node_id)
            if parent_node:
                parent_node.children_node_ids = [
                    branch_root.node_id if child_id == child_action_node.node_id else child_id
                    for child_id in parent_node.children_node_ids
                ]
        else:
            # Child is a root node - update step's root nodes
            for step_def in self._current_session_graph.steps:
                if child_action_node.node_id in step_def.root_node_ids:
                    step_def.root_node_ids = [
                        branch_root.node_id if root_id == child_action_node.node_id else root_id
                        for root_id in step_def.root_node_ids
                    ]
                    break
        
        # Connect child_action_node to all leaf nodes of the pasted branch
        child_action_node.parent_node_id = None  # Will be set to one of the leaf nodes
        for leaf_node in leaf_nodes:
            leaf_node.children_node_ids.append(child_action_node.node_id)
        
        # Set the parent of child_action_node to the first leaf node
        if leaf_nodes:
            child_action_node.parent_node_id = leaf_nodes[0].node_id
        
        # Add all new nodes to the graph
        self._current_session_graph.nodes.extend(new_nodes)
        
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

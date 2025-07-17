# framework_tool/gui/dialogs/manage_session_actions_dialog.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QDialogButtonBox, QSplitter, QMessageBox, QInputDialog,
    QWidget, QLabel # Added QLabel
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional

from framework_tool.data_models.project_data import ProjectData
from framework_tool.data_models.session_graph import SessionActionsGraph, ActionNode 
from ..widgets.session_flow_editor_widget import SessionFlowEditorWidget # The new flow editor
from ..widgets.action_node_details_widget import ActionNodeDetailsWidget # The new details panel


class ManageSessionActionsDialog(QDialog):
    """
    Dialog for managing all SessionActionsGraphs in a project.
    Uses SessionFlowEditorWidget for editing the flow and ActionNodeDetailsWidget for details.
    """
    project_data_changed = Signal() 

    def __init__(self, project_data: ProjectData, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project_data = project_data 

        self.setWindowTitle("Manage Session Flows") 
        self.setMinimumSize(1200, 750) # Increased size for 3 panels

        self._init_ui()
        self._load_session_names_list()
        
        if self.session_names_list_widget.count() > 0:
            self.session_names_list_widget.setCurrentRow(0)
        else:
            self.flow_editor_widget.load_session_graph("", None)
            self.details_widget.clear_details()


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Main splitter for 3 panels: [Session List] | [Flow Editor] | [Details Panel]
        top_splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # --- Left Panel (List of Session Names) ---
        left_panel = QWidget(self)
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Session Flows:", self))
        self.session_names_list_widget = QListWidget(self)
        self.session_names_list_widget.currentItemChanged.connect(self._on_selected_session_name_changed)
        left_layout.addWidget(self.session_names_list_widget)

        sessions_buttons_layout = QHBoxLayout()
        add_session_button = QPushButton("Add New Session...", self)
        add_session_button.clicked.connect(self._add_new_session)
        sessions_buttons_layout.addWidget(add_session_button)
        remove_session_button = QPushButton("Remove Selected", self) # Shorter text
        remove_session_button.clicked.connect(self._remove_selected_session)
        sessions_buttons_layout.addWidget(remove_session_button)
        left_layout.addLayout(sessions_buttons_layout)
        top_splitter.addWidget(left_panel)

        # --- Center Panel (SessionFlowEditorWidget) ---
        self.flow_editor_widget = SessionFlowEditorWidget(project_data_ref=self.project_data, parent=self)
        self.flow_editor_widget.session_graph_changed.connect(self._on_editor_data_changed)
        self.flow_editor_widget.action_node_selected.connect(self._on_action_node_selected_in_flow)
        top_splitter.addWidget(self.flow_editor_widget)

        # --- Right Panel (ActionNodeDetailsWidget) ---
        self.details_widget = ActionNodeDetailsWidget(project_data_ref=self.project_data, parent=self)
        top_splitter.addWidget(self.details_widget)

        top_splitter.setSizes([200, 550, 250]) # Initial sizes for left, center, right
        main_layout.addWidget(top_splitter)

        # --- Dialog Buttons (Close) ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        button_box.clicked.connect(self.accept) 
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)

    def _load_session_names_list(self):
        self.session_names_list_widget.blockSignals(True)
        self.session_names_list_widget.clear()
        sorted_sessions = sorted(self.project_data.session_actions, key=lambda s: s.session_name)
        for session_graph in sorted_sessions:
            self.session_names_list_widget.addItem(QListWidgetItem(session_graph.session_name))
        self.session_names_list_widget.blockSignals(False)

        if self.session_names_list_widget.count() > 0:
            if not self.session_names_list_widget.currentItem():
                 self.session_names_list_widget.setCurrentRow(0)
            else: 
                 self._on_selected_session_name_changed(self.session_names_list_widget.currentItem(), None)
        else: 
            self.flow_editor_widget.load_session_graph("", None)
            self.details_widget.clear_details()

    @Slot(QListWidgetItem, QListWidgetItem)
    def _on_selected_session_name_changed(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        self.details_widget.clear_details() # Clear details when session changes
        if current:
            session_name_key = current.text()
            selected_graph: Optional[SessionActionsGraph] = None
            for graph in self.project_data.session_actions:
                if graph.session_name == session_name_key:
                    selected_graph = graph
                    break
            if selected_graph:
                self.flow_editor_widget.load_session_graph(session_name_key, selected_graph)
            else:
                QMessageBox.critical(self, "Data Error", f"No graph found for Session name '{session_name_key}'.")
                self.flow_editor_widget.load_session_graph(session_name_key, None) 
        else:
            self.flow_editor_widget.load_session_graph("", None)

    @Slot()
    def _add_new_session(self):
        new_session_name, ok = QInputDialog.getText(self, "Add New Session Flow", "Enter name for the new Session Flow:")
        if ok and new_session_name:
            new_session_name = new_session_name.strip()
            if not new_session_name:
                QMessageBox.warning(self, "Input Error", "Session name cannot be empty."); return
            if any(new_session_name.lower() == sg.session_name.lower() for sg in self.project_data.session_actions):
                QMessageBox.warning(self, "Duplicate Name", f"The Session name '{new_session_name}' already exists."); return

            new_graph = SessionActionsGraph(session_name=new_session_name) 
            self.project_data.session_actions.append(new_graph)
            self._load_session_names_list() 
            items = self.session_names_list_widget.findItems(new_session_name, Qt.MatchFlag.MatchExactly)
            if items: self.session_names_list_widget.setCurrentItem(items[0])
            self.project_data_changed.emit() 
        elif ok and not new_session_name:
             QMessageBox.warning(self, "Input Error", "Session name cannot be empty.")

    @Slot()
    def _remove_selected_session(self):
        current_item = self.session_names_list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a Session to remove."); return
        session_name_to_remove = current_item.text()
        reply = QMessageBox.question(self, "Confirm Removal", f"Remove Session '{session_name_to_remove}' and all its flow data?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            graph_to_remove_obj = next((g for g in self.project_data.session_actions if g.session_name == session_name_to_remove), None)
            if graph_to_remove_obj: self.project_data.session_actions.remove(graph_to_remove_obj)
            self._load_session_names_list() 
            self.project_data_changed.emit()

    @Slot()
    def _on_editor_data_changed(self): # Connected to session_graph_changed from flow_editor
        self.project_data_changed.emit()

    @Slot(object) # Receives ActionNode object or None
    def _on_action_node_selected_in_flow(self, action_node_obj: Optional[ActionNode]):
        if action_node_obj and isinstance(action_node_obj, ActionNode):
            self.details_widget.load_action_node_details(action_node_obj)
        else:
            self.details_widget.clear_details()


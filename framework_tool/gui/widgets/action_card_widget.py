# framework_tool/gui/widgets/action_card_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PySide6.QtGui import QMouseEvent, QColor, QPalette, QFont
from PySide6.QtCore import Qt, Signal
from typing import Optional

# data_models imports are relative to the framework_tool package
from ...data_models.session_graph import ActionNode
from ...data_models.action_definition import ActionDefinition 
from ...data_models.project_data import ProjectData


class ActionCardWidget(QFrame):
    """
    A simple widget to represent an ActionNode as a clickable card.
    Displays the ActionLabel and uses background color for visual grouping.
    """
    clicked = Signal(str) # Emits the node_id when clicked

    def __init__(self, 
                 action_node: ActionNode,
                 project_data: ProjectData, 
                 base_color: QColor, 
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.action_node = action_node
        self.project_data = project_data
        self.base_color = base_color

        self._selected = False
        
        self._init_ui()
        self._apply_style() # Apply initial style

    def _init_ui(self):
        # QFrame settings (less reliant on palette now, more on stylesheet)
        self.setFrameShape(QFrame.Shape.StyledPanel) # Still useful for a basic panel look
        self.setFrameShadow(QFrame.Shadow.Raised)   # Can add a bit of depth
        # self.setLineWidth(1) # Border width will be controlled by stylesheet

        self.setMinimumSize(120, 60) 
        self.setMaximumHeight(80)  

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        display_text = self.action_node.action_label_to_execute
        
        self.action_label_widget = QLabel(display_text)
        self.action_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_label_widget.setWordWrap(True)
        
        font = self.action_label_widget.font()
        font.setBold(True)
        self.action_label_widget.setFont(font)
        
        layout.addWidget(self.action_label_widget)
        self.setLayout(layout)

    def _apply_style(self):
        """Applies styling, including background color and selection highlight using stylesheets."""
        
        current_bg_color_name = self.base_color.name() # Get color name, e.g., "#RRGGBB"
        current_text_color_name = "black" 
        border_width = 1
        border_color_name = self.base_color.darker(130).name() # Default border slightly darker than base

        if self._selected:
            selected_bg_color = self.base_color.darker(120) # Make selected background a bit darker
            current_bg_color_name = selected_bg_color.name()
            
            # Determine text color based on background brightness for selected state
            bg_brightness = (selected_bg_color.redF() * 0.299 + 
                             selected_bg_color.greenF() * 0.587 + 
                             selected_bg_color.blueF() * 0.114)
            if bg_brightness < 0.5: # If background is dark
                current_text_color_name = "white"
            else: # If background is light
                current_text_color_name = "black"
            
            border_width = 2
            border_color_name = QColor(255, 140, 0).name() # Orange selection border
        
        # Apply style using stylesheet for QFrame (self)
        # Note: Using the class name "ActionCardWidget" in the stylesheet selector
        # ensures that only instances of this class are affected if this stylesheet
        # were to be applied more globally. For setStyleSheet on the instance, it's direct.
        self.setStyleSheet(f"""
            ActionCardWidget {{
                background-color: {current_bg_color_name};
                border: {border_width}px solid {border_color_name};
                border-radius: 4px; 
            }}
        """)
        
        # Style the QLabel for text color specifically.
        # QLabel's background should be transparent to show the QFrame's styled background.
        self.action_label_widget.setStyleSheet(f"""
            QLabel {{
                color: {current_text_color_name};
                background-color: transparent;
                border: none; 
            }}
        """)
        
        # self.update() # QWidget::setStyleSheet() calls update() internally.

    def set_selected(self, selected: bool):
        if self._selected != selected:
            self._selected = selected
            self._apply_style() 
            # self.update() is implicitly called by setStyleSheet if style changes

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.action_node.node_id)
        super().mousePressEvent(event)

    def get_background_color(self) -> QColor: # This might be less relevant if colors are hardcoded in style
        return self.base_color


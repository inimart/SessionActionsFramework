# framework_tool/gui/widgets/action_card_widget.py
# All comments and identifiers in English

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QPushButton
)
from PySide6.QtGui import QMouseEvent, QColor, QPalette, QFont, QEnterEvent
from PySide6.QtCore import Qt, Signal, QPoint
from typing import Optional

# data_models imports are relative to the framework_tool package
from framework_tool.data_models.session_graph import ActionNode
from framework_tool.data_models.action_definition import ActionDefinition 
from framework_tool.data_models.project_data import ProjectData


class ActionCardWidget(QFrame):
    """
    A simple widget to represent an ActionNode as a clickable card.
    Displays the ActionLabel and uses background color for visual grouping.
    """
    clicked = Signal(str) # Emits the node_id when clicked
    add_parent_requested = Signal(str) # Emits the node_id when add parent is requested
    add_child_requested = Signal(str) # Emits the node_id when add child is requested
    add_sibling_requested = Signal(str) # Emits the node_id when add sibling is requested
    insert_intermediate_requested = Signal(str) # Emits the node_id when intermediate insertion is requested

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
        self._hover_buttons_visible = False
        
        self._init_ui()
        self._create_hover_buttons()
        self._apply_style() # Apply initial style

    def _init_ui(self):
        # QFrame settings (less reliant on palette now, more on stylesheet)
        self.setFrameShape(QFrame.Shape.StyledPanel) # Still useful for a basic panel look
        self.setFrameShadow(QFrame.Shadow.Raised)   # Can add a bit of depth
        # self.setLineWidth(1) # Border width will be controlled by stylesheet

        self.setMinimumSize(140, 80) 
        self.setMaximumHeight(120)  

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        self.setLayout(layout)
        
        # Build initial content
        self._rebuild_content()
        
        # Set tooltip with NodeID
        self.setToolTip(f"Node ID: {self.action_node.node_id}")

    def _create_hover_buttons(self):
        """Create hover buttons for adding actions."""
        # Add Parent button (top)
        self.add_parent_btn = QPushButton("▲", self)
        self.add_parent_btn.setFixedSize(20, 15)
        self.add_parent_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 180);
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 220);
            }
        """)
        self.add_parent_btn.clicked.connect(lambda: self.add_parent_requested.emit(self.action_node.node_id))
        self.add_parent_btn.hide()
        
        # Add Child button (bottom)
        self.add_child_btn = QPushButton("▼", self)
        self.add_child_btn.setFixedSize(20, 15)
        self.add_child_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 180);
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 220);
            }
        """)
        self.add_child_btn.clicked.connect(self._handle_child_button_click)
        self.add_child_btn.hide()
        
        # Add Sibling button (right)
        self.add_sibling_btn = QPushButton("▶", self)
        self.add_sibling_btn.setFixedSize(15, 20)
        self.add_sibling_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 180);
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 220);
            }
        """)
        self.add_sibling_btn.clicked.connect(lambda: self.add_sibling_requested.emit(self.action_node.node_id))
        self.add_sibling_btn.hide()

    def refresh_content(self):
        """Refresh the card content when action node data changes."""
        # Clear current layout
        for i in reversed(range(self.layout().count())):
            child = self.layout().itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Rebuild content
        self._rebuild_content()
    
    def _rebuild_content(self):
        """Rebuild the card content."""
        layout = self.layout()
        
        # Action Label (bold)
        self.action_label_widget = QLabel(self.action_node.action_label_to_execute)
        self.action_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_label_widget.setWordWrap(True)
        font = self.action_label_widget.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() - 1)
        self.action_label_widget.setFont(font)
        layout.addWidget(self.action_label_widget)

        # Instance Label (if present)
        if self.action_node.instance_label:
            self.instance_label_widget = QLabel(self.action_node.instance_label)
            self.instance_label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.instance_label_widget.setWordWrap(True)
            instance_font = self.instance_label_widget.font()
            instance_font.setItalic(True)
            instance_font.setPointSize(instance_font.pointSize() - 2)
            self.instance_label_widget.setFont(instance_font)
            layout.addWidget(self.instance_label_widget)
        else:
            self.instance_label_widget = None

        # Custom field values (show names and values clearly)
        if self.action_node.custom_field_values:
            field_texts = []
            for field_name, field_value in self.action_node.custom_field_values.items():
                # Format field value based on type
                if isinstance(field_value, bool):
                    value_str = "true" if field_value else "false"
                elif isinstance(field_value, dict):
                    # For Vector/RGBA types, show compact format
                    if len(field_value) == 2:  # Vector2
                        value_str = f"({field_value.get('x', 0):.1f}, {field_value.get('y', 0):.1f})"
                    elif len(field_value) == 3:  # Vector3
                        value_str = f"({field_value.get('x', 0):.1f}, {field_value.get('y', 0):.1f}, {field_value.get('z', 0):.1f})"
                    elif len(field_value) == 4:  # RGBA
                        value_str = f"({field_value.get('r', 1):.1f}, {field_value.get('g', 1):.1f}, {field_value.get('b', 1):.1f}, {field_value.get('a', 1):.1f})"
                    else:
                        # Fallback for other dict types
                        first_key = next(iter(field_value.keys()))
                        value_str = f"{first_key}={field_value[first_key]}"
                elif isinstance(field_value, float):
                    value_str = f"{field_value:.1f}"
                elif isinstance(field_value, str):
                    # Truncate long strings with ellipsis after first few words
                    words = field_value.split()[:3]  # First 3 words
                    value_str = " ".join(words)
                    if len(field_value.split()) > 3:
                        value_str += "..."
                else:
                    value_str = str(field_value)
                    # Limit other types to reasonable length
                    if len(value_str) > 15:
                        value_str = value_str[:12] + "..."
                
                field_texts.append(f"{field_name}: {value_str}")
            
            if field_texts:
                self.custom_fields_widget = QLabel("\n".join(field_texts))
                self.custom_fields_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.custom_fields_widget.setWordWrap(True)
                fields_font = self.custom_fields_widget.font()
                fields_font.setPointSize(fields_font.pointSize() - 2)
                self.custom_fields_widget.setFont(fields_font)
                layout.addWidget(self.custom_fields_widget)
            else:
                self.custom_fields_widget = None
        else:
            self.custom_fields_widget = None

        # Reapply styling
        self._apply_style()

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
        
        # Style all QLabels for text color specifically.
        # QLabel's background should be transparent to show the QFrame's styled background.
        label_style = f"""
            QLabel {{
                color: {current_text_color_name};
                background-color: transparent;
                border: none; 
            }}
        """
        
        self.action_label_widget.setStyleSheet(label_style)
        
        if self.instance_label_widget:
            self.instance_label_widget.setStyleSheet(label_style)
            
        if self.custom_fields_widget:
            self.custom_fields_widget.setStyleSheet(label_style)
        
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

    def enterEvent(self, event):
        """Show hover buttons when mouse enters the widget."""
        self._show_hover_buttons()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hide hover buttons when mouse leaves the widget."""
        self._hide_hover_buttons()
        super().leaveEvent(event)
    
    def resizeEvent(self, event):
        """Position hover buttons when widget is resized."""
        super().resizeEvent(event)
        self._position_hover_buttons()
    
    def _show_hover_buttons(self):
        """Show the appropriate hover buttons based on node level."""
        if not self._hover_buttons_visible:
            self._hover_buttons_visible = True
            self._position_hover_buttons()
            
            # Show different buttons based on node level
            # Level 0 (root) nodes can only have children and siblings
            # Level > 0 nodes can have parent, children, and siblings
            node_level = self._get_node_level()
            
            if node_level > 0:
                self.add_parent_btn.show()
            self.add_child_btn.show()
            self.add_sibling_btn.show()
    
    def _hide_hover_buttons(self):
        """Hide all hover buttons."""
        if self._hover_buttons_visible:
            self._hover_buttons_visible = False
            self.add_parent_btn.hide()
            self.add_child_btn.hide()
            self.add_sibling_btn.hide()
    
    def _position_hover_buttons(self):
        """Position hover buttons on the edges of the card."""
        if not self._hover_buttons_visible:
            return
            
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Position add parent button (top center)
        parent_btn_x = (width - self.add_parent_btn.width()) // 2
        parent_btn_y = -7  # Slightly above the top edge
        self.add_parent_btn.move(parent_btn_x, parent_btn_y)
        
        # Position add child button (bottom center)
        child_btn_x = (width - self.add_child_btn.width()) // 2
        child_btn_y = height - 8  # Slightly below the bottom edge
        self.add_child_btn.move(child_btn_x, child_btn_y)
        
        # Position add sibling button (right center)
        sibling_btn_x = width - 8  # Slightly to the right of the right edge
        sibling_btn_y = (height - self.add_sibling_btn.height()) // 2
        self.add_sibling_btn.move(sibling_btn_x, sibling_btn_y)
    
    def _handle_child_button_click(self):
        """Handle child button click - different behavior based on number of children."""
        if len(self.action_node.children_node_ids) > 1:
            # Node has multiple children - trigger intermediate insertion
            self.insert_intermediate_requested.emit(self.action_node.node_id)
        else:
            # Node has 0 or 1 child - normal child addition
            self.add_child_requested.emit(self.action_node.node_id)

    def _get_node_level(self) -> int:
        """Get the hierarchical level of this node (0 for root, 1+ for children)."""
        # For now, we'll determine level by checking if it has a parent
        # In a more complex implementation, we might need to traverse up the tree
        if hasattr(self.action_node, 'parent_node_id') and self.action_node.parent_node_id:
            return 1  # Has parent, so at least level 1
        return 0  # No parent, so root level

    def get_background_color(self) -> QColor: # This might be less relevant if colors are hardcoded in style
        return self.base_color


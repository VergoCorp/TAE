from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsItem,
                           QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPainterPath

class Engine2DView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Enable antialiasing for smoother drawing
        self.setRenderHint(QPainter.Antialiasing)
        
        # Enable mouse tracking for zoom
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # Set up the view
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(Qt.white))  # White background
        
        # Initialize the drawing
        self.draw_engine()
        
        # Fit the view to the scene
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def draw_dimension_line(self, x1, y1, x2, y2, text, offset=10):
        # Draw main dimension line
        line = QGraphicsLineItem(x1, y1, x2, y2)
        line.setPen(QPen(Qt.black, 1))
        self.scene.addItem(line)
        
        # Draw end caps
        cap_length = 5
        for x, y in [(x1, y1), (x2, y2)]:
            cap = QGraphicsLineItem(x, y - cap_length/2, x, y + cap_length/2)
            cap.setPen(QPen(Qt.black, 1))
            self.scene.addItem(cap)
        
        # Add dimension text
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(Qt.black)
        font = QFont()
        font.setPointSize(8)
        text_item.setFont(font)
        
        # Position text in the middle
        text_width = text_item.boundingRect().width()
        text_x = x1 + (x2 - x1 - text_width) / 2
        text_y = y1 + offset
        text_item.setPos(text_x, text_y)
        self.scene.addItem(text_item)

    def create_cross_hatch_pattern(self, rect, spacing=5, angle=45):
        path = QPainterPath()
        
        # Calculate the diagonal length to ensure full coverage
        width = rect.width()
        height = rect.height()
        diagonal = (width**2 + height**2)**0.5
        
        # Create lines at the specified angle
        num_lines = int(diagonal / spacing) * 2
        
        for i in range(-num_lines, num_lines):
            offset = i * spacing
            path.moveTo(rect.left() - diagonal/2, offset)
            path.lineTo(rect.left() + diagonal/2, offset)
        
        return path
        
    def draw_engine(self):
        # Clear existing items
        self.scene.clear()
        
        # Define colors
        STEEL_COLOR = QColor("#A0A0A0")  # Gray for steel parts
        BLUE_COLOR = QColor("#4169E1")   # Blue for cold parts
        RED_COLOR = QColor("#CD5C5C")    # Red for hot parts
        
        # Define dimensions (in scene coordinates)
        STACK_LENGTH = 85
        HHX_LENGTH = 20
        CHX_LENGTH = 50
        TOTAL_HEIGHT = 60  # Reduced height for better proportions
        
        # Draw main components
        # Stack (center, blue with cross-hatching)
        stack = QGraphicsRectItem(-STACK_LENGTH/2, -TOTAL_HEIGHT/2, STACK_LENGTH, TOTAL_HEIGHT)
        stack.setBrush(QBrush(QColor("#4682B4")))  # Steel blue color
        stack.setPen(QPen(Qt.black, 1))
        self.scene.addItem(stack)
        
        # Add cross-hatching to stack
        hatch_path = self.create_cross_hatch_pattern(stack.rect())
        hatch_item = self.scene.addPath(hatch_path, QPen(Qt.white, 0.5))
        hatch_item.setPos(stack.pos())
        
        # Hot heat exchanger (left, red with internal details)
        hhx = QGraphicsRectItem(-STACK_LENGTH/2 - HHX_LENGTH, -TOTAL_HEIGHT/2, HHX_LENGTH, TOTAL_HEIGHT)
        hhx.setBrush(QBrush(RED_COLOR))
        hhx.setPen(QPen(Qt.black, 1))
        self.scene.addItem(hhx)
        
        # Add heater tubes in HHX
        for y in range(-20, 21, 10):
            tube = QGraphicsRectItem(-STACK_LENGTH/2 - HHX_LENGTH + 5, y, 2, 4)
            tube.setBrush(QBrush(QColor("#FF4500")))
            tube.setPen(QPen(Qt.black, 1))
            self.scene.addItem(tube)
        
        # Cold heat exchanger (right, blue with cooling tubes)
        chx = QGraphicsRectItem(STACK_LENGTH/2, -TOTAL_HEIGHT/2, CHX_LENGTH, TOTAL_HEIGHT)
        chx.setBrush(QBrush(QColor("#90EE90")))  # Light green
        chx.setPen(QPen(Qt.black, 1))
        self.scene.addItem(chx)
        
        # Add cooling tubes in CHX
        for y in range(-25, 26, 10):
            tube = QGraphicsRectItem(STACK_LENGTH/2 + 10, y, 30, 2)
            tube.setBrush(QBrush(QColor("#B87333")))  # Copper color
            tube.setPen(QPen(Qt.black, 1))
            self.scene.addItem(tube)
        
        # Add resonator tubes with flanges
        # Left resonator
        left_res = QGraphicsRectItem(-STACK_LENGTH/2 - HHX_LENGTH - 100, -TOTAL_HEIGHT/4, 100, TOTAL_HEIGHT/2)
        left_res.setBrush(QBrush(STEEL_COLOR))
        left_res.setPen(QPen(Qt.black, 1))
        self.scene.addItem(left_res)
        
        # Right resonator
        right_res = QGraphicsRectItem(STACK_LENGTH/2 + CHX_LENGTH, -TOTAL_HEIGHT/4, 100, TOTAL_HEIGHT/2)
        right_res.setBrush(QBrush(STEEL_COLOR))
        right_res.setPen(QPen(Qt.black, 1))
        self.scene.addItem(right_res)
        
        # Add flanges
        for x in [-STACK_LENGTH/2 - HHX_LENGTH, -STACK_LENGTH/2, STACK_LENGTH/2, STACK_LENGTH/2 + CHX_LENGTH]:
            flange = QGraphicsRectItem(x - 5, -TOTAL_HEIGHT/2 - 5, 10, TOTAL_HEIGHT + 10)
            flange.setBrush(QBrush(QColor("#C0C0C0")))
            flange.setPen(QPen(Qt.black, 1))
            self.scene.addItem(flange)
        
        # Add dimension lines
        # HHX dimension
        self.draw_dimension_line(-STACK_LENGTH/2 - HHX_LENGTH, TOTAL_HEIGHT/2 + 15,
                               -STACK_LENGTH/2, TOTAL_HEIGHT/2 + 15,
                               "20")
        
        # Stack dimension
        self.draw_dimension_line(-STACK_LENGTH/2, TOTAL_HEIGHT/2 + 15,
                               STACK_LENGTH/2, TOTAL_HEIGHT/2 + 15,
                               "85")
        
        # CHX dimension
        self.draw_dimension_line(STACK_LENGTH/2, TOTAL_HEIGHT/2 + 15,
                               STACK_LENGTH/2 + CHX_LENGTH, TOTAL_HEIGHT/2 + 15,
                               "50")
        
        # Set the scene rect to ensure all components are visible
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def wheelEvent(self, event):
        # Handle zoom with mouse wheel
        zoom_factor = 1.15
        
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1/zoom_factor, 1/zoom_factor) 
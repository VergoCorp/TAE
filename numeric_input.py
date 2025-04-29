from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtCore import Qt

class NumericInput(QDoubleSpinBox):
    def __init__(self, min_val=0, max_val=1000, decimals=2, suffix=""):
        super().__init__()
        self.setMinimum(min_val)
        self.setMaximum(max_val)
        self.setDecimals(decimals)
        self.setSuffix(suffix)
        self.setAlignment(Qt.AlignRight)
        # Restore up/down arrow buttons for value adjustment
        self.setButtonSymbols(QDoubleSpinBox.UpDownArrows)
        self.setStyleSheet("""
            QDoubleSpinBox {
                padding: 2px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
        """)

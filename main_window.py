import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QFrame, QStackedWidget,
    QLabel, QMessageBox, QTabWidget, QSplitter, QComboBox, QDoubleSpinBox,
    QTabBar, QFileDialog, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt
from simulation import ThermoacousticSimulation
from cad_import import CADImporter
from engine_2d_view import Engine2DView
from engine_3d_view import Engine3DView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermoacoustic Engine Simulator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create left panel
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        left_panel_layout.setSpacing(0)
        
        # Create tabs navigation at top of left panel
        tab_bar = QTabBar()
        tab_bar.addTab("Parameters")
        tab_bar.addTab("CAD Import")
        tab_bar.setExpanding(False)
        tab_bar.setStyleSheet("""
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                border-bottom: none;
                padding: 8px 20px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: white;
            }
        """)
        tab_bar.currentChanged.connect(self.switch_tab)
        left_panel_layout.addWidget(tab_bar)
        
        # Create stacked widget for tab contents
        self.stack = QStackedWidget()
        left_panel_layout.addWidget(self.stack)
        
        # Create and add pages
        self.parameters_page = QWidget()
        self.cad_page = QWidget()
        self.stack.addWidget(self.parameters_page)
        self.stack.addWidget(self.cad_page)
        
        # Initialize pages
        self.init_parameters_page()
        self.init_cad_page()
        
        # Create main view area with tabs
        self.main_view = QTabWidget()
        self.main_view.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 20px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: none;
            }
        """)
        
        # Create container for 2D view
        view_2d_container = QWidget()
        view_2d_layout = QVBoxLayout(view_2d_container)
        view_2d_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add 2D view
        self.engine_2d_view = Engine2DView()
        view_2d_layout.addWidget(self.engine_2d_view)
        
        # Add 2D view container to tab widget
        self.main_view.addTab(view_2d_container, "2D View")
        
        # Create container for 3D view
        view_3d_container = QWidget()
        view_3d_layout = QVBoxLayout(view_3d_container)
        view_3d_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add 3D view
        self.engine_3d_view = Engine3DView()
        view_3d_layout.addWidget(self.engine_3d_view)
        
        # Add 3D view container to tab widget
        self.main_view.addTab(view_3d_container, "3D View")
        
        # Add analysis tab (placeholder for now)
        self.analysis_view = QWidget()
        self.main_view.addTab(self.analysis_view, "Analysis")
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.main_view)
        
        # Initialize components
        self.sim = None
        self.cad_importer = None

    def switch_tab(self, index):
        """Switch between tab pages"""
        self.stack.setCurrentIndex(index)

    def init_parameters_page(self):
        """Initialize parameters page"""
        layout = QVBoxLayout(self.parameters_page)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Working Fluid
        fluid_group = QGroupBox("Working Fluid")
        fluid_layout = QFormLayout()
        
        # Add controls
        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setRange(0.1, 10.0)
        self.pressure_spin.setValue(0.85)
        fluid_layout.addRow("Pressure (MPa):", self.pressure_spin)
        
        fluid_group.setLayout(fluid_layout)
        layout.addWidget(fluid_group)
        
        # Stack Material Properties
        material_group = QGroupBox("Stack Material Properties")
        material_layout = QFormLayout()
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Steel", "Aluminum", "Copper"])
        material_layout.addRow("Material:", self.material_combo)
        
        material_group.setLayout(material_layout)
        layout.addWidget(material_group)
        
        layout.addStretch()

    def init_cad_page(self):
        """Initialize CAD import page"""
        layout = QVBoxLayout(self.cad_page)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Import controls
        import_btn = QPushButton("Import CAD File...")
        import_btn.clicked.connect(self.import_cad)
        layout.addWidget(import_btn)
        
        self.cad_status = QLabel("No file imported")
        layout.addWidget(self.cad_status)
        
        layout.addStretch()

    def import_cad(self):
        """Open file dialog to select CAD file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Open CAD File", 
            "", 
            "CAD Files (*.stp *.step *.stl *.iges *.igs *.x_t)"
        )
        
        if filename:
            self.cad_status.setText("File imported: " + filename.split('/')[-1])
            if not hasattr(self, 'cad_importer') or not self.cad_importer:
                self.cad_importer = CADImporter()
            
            if self.cad_importer.import_cad(filename):
                QMessageBox.information(self, "Success", "CAD file loaded successfully")
                
                # Update simulation with CAD dimensions if available
                self.update_simulation_with_cad()

    def update_simulation_with_cad(self):
        """Update simulation parameters from CAD dimensions"""
        if self.sim and hasattr(self, 'cad_importer') and self.cad_importer:
            dims = self.cad_importer.get_dimensions()
            if dims:
                # Update relevant simulation parameters
                self.sim.params.stack_length = dims['length'] * 1000  # Convert to mm
                self.sim.params.stack_width = dims['width'] * 1000
                self.sim.params.stack_height = dims['height'] * 1000
                
                # Update UI if parameter controls exist
                if hasattr(self, 'param_controls'):
                    self.update_parameter_controls()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

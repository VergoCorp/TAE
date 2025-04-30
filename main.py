from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt
from config_panel import ConfigPanel
from middle_tabs import MiddleTabs
from results_tabs import ResultsTabs

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermoacoustic Engine Simulator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Create and add config panel
        self.config_panel = ConfigPanel()
        splitter.addWidget(self.config_panel)
        
        # Create and add middle visualization section
        self.middle_tabs = MiddleTabs()
        splitter.addWidget(self.middle_tabs)
        
        # Create and add results tabs
        self.results_tabs = ResultsTabs()
        splitter.addWidget(self.results_tabs)
        
        # Set initial splitter sizes (300px, 700px, 400px)
        splitter.setSizes([300, 700, 400])
        
        # Connect simulation signals
        self.config_panel.simulation_started.connect(self.results_tabs.on_simulation_started)
        self.config_panel.simulation_updated.connect(self.results_tabs.on_simulation_updated)
        self.config_panel.simulation_finished.connect(self.results_tabs.on_simulation_finished)
        
        # Connect visualization signals
        self.config_panel.simulation_started.connect(self.middle_tabs.on_simulation_started)
        self.config_panel.simulation_updated.connect(self.middle_tabs.on_simulation_updated)
        
        # Connect parameter change signals
        self.config_panel.parameter_changed.connect(self.middle_tabs.on_parameter_changed)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    def main():
        app = QApplication(sys.argv)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Proper application exit
        ret = app.exec_()
        
        # Clean up any resources
        if hasattr(window, 'cad_importer') and window.cad_importer:
            window.cad_importer.mesh = None
        
        sys.exit(ret)

    main()

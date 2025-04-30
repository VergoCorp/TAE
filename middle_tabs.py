from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QPushButton,
    QProgressDialog, QMessageBox, QLabel, QDialog,
    QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor  # Only import actually needed QtGui items

import time
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from engine_2d_view import Engine2DView
from engine_3d_view import Engine3DView


class AnalysisThread(QThread):
    """Thread for running thermoacoustic analysis"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(dict)
    
    def __init__(self, params):
        super().__init__()
        self.params = params
        
    def run(self):
        """Run the analysis"""
        try:
            from simulation import ThermoacousticSimulation
            
            # Convert parameters to simulation format
            sim_params = {
                'stack_length': self.params['stack_length'],
                'hhx_length': self.params['hhx_length'],
                'chx_length': self.params['chx_length'],
                'resonator_length': self.params['resonator_length'],
                # Add other required parameters
            }
            
            # Create and run simulation
            simulation = ThermoacousticSimulation(sim_params)
            
            # Run with progress updates
            for progress in range(0, 101, 5):
                self.progress_updated.emit(progress)
                self.msleep(100)  # Simulate work
                
            # Get final results
            results = simulation.run_simulation()
            self.analysis_completed.emit(results)
            
        except Exception as e:
            print(f"Analysis thread error: {str(e)}")
            self.progress_updated.emit(0)


class MiddleTabs(QTabWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize with default values from the image
        self.current_dimensions = {
            'stack_length': 85.0,  # mm
            'stack_position': 265.0,  # mm from left end
            'hhx_length': 20.0,  # mm
            'chx_length': 50.0,  # mm
            'resonator_diameter': 50.0,  # mm
            'resonator_length': 750.0,  # mm
        }

        # Create and add tabs
        self._2d_view = None
        self._3d_view = None
        
        # Create 3D tab first (index 0)
        self.create_3d_tab()
        # Create 2D tab second (index 1)
        self.create_2d_tab()
        
        # Set 3D tab as default
        self.setCurrentIndex(0)

        # Connect signals
        self.currentChanged.connect(self.on_tab_changed)

    def on_parameter_changed(self, param_name: str, value: float):
        """Update the visualization when a parameter changes"""
        print(f"Received parameter change: {param_name} = {value}")  # Debug print
        
        # Map UI parameter names to internal names if needed
        param_mapping = {
            'length_mm': 'stack_length',
            'hot_hx_length_mm': 'hhx_length',
            'cold_hx_length_mm': 'chx_length',
            'diameter_mm': 'resonator_diameter'
        }
        
        # Convert parameter name if needed
        internal_name = param_mapping.get(param_name, param_name)
        
        if internal_name in self.current_dimensions:
            print(f"Updating dimension: {internal_name} = {value}")  # Debug print
            self.current_dimensions[internal_name] = value
            
            # Update both views
            if self._2d_view:
                self._2d_view.draw_engine()
            if self._3d_view:
                self._3d_view.create_engine_model()

    def on_tab_changed(self):
        # No need to do anything special on tab change now
        pass

    def create_2d_tab(self):
        """Create 2D visualization tab with Engine2DView"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create Engine2DView instance
        self._2d_view = Engine2DView()
        layout.addWidget(self._2d_view)
        
        widget.setLayout(layout)
        self.addTab(widget, "2D Sketch")

    def create_3d_tab(self):
        """Create 3D visualization tab with Engine3DView"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create Engine3DView instance
        self._3d_view = Engine3DView()
        layout.addWidget(self._3d_view)
        
        widget.setLayout(layout)
        self.addTab(widget, "3D Sketch")

    def on_simulation_started(self, simulation):
        """Handle start of simulation"""
        self.simulation = simulation

    def on_simulation_updated(self, metrics, arrays):
        """Handle simulation updates"""
        if self.simulation:
            if 'temperature' in arrays:
                t_array = arrays['temperature']
                t_range = np.max(t_array) - np.min(t_array)
                if t_range > 0:
                    # Temperature visualization will be implemented here
                    pass

    def init_ui(self):
        # Add analyze button connection
        self.analyze_btn = QPushButton('Analyze Performance')
        self.analyze_btn.clicked.connect(self.run_analysis)

    def run_analysis(self):
        """Thread-safe analysis execution"""
        try:
            # Ensure only one analysis runs at a time
            if hasattr(self, '_analysis_running') and self._analysis_running:
                return
                
            self._analysis_running = True
            
            # Create and configure progress dialog
            self._create_progress_dialog()
            
            # Run in separate thread
            params = self.config_panel.get_simulation_parameters()
            self.analysis_thread = AnalysisThread(params)
            self.analysis_thread.progress_updated.connect(self._update_progress)
            self.analysis_thread.analysis_completed.connect(self._on_analysis_completed)
            self.analysis_thread.finished.connect(self._on_analysis_finished)
            self.analysis_thread.start()
            
        except Exception as e:
            self._handle_analysis_error(e)
    
    def _create_progress_dialog(self):
        """Create engineering progress dialog"""
        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle("TAE Simulation | Computational Engine")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        
        # Setup UI elements
        self.progress_bar = QProgressBar()
        self.metrics_label = QLabel("Initializing simulation...")
        
        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.metrics_label)
        self.progress_dialog.setLayout(layout)
        
        self.progress_dialog.show()
    
    def _on_analysis_completed(self, results):
        """Handle successful analysis"""
        try:
            if hasattr(self, 'results_tab'):
                self.results_tab.update_results(results)
        except Exception as e:
            self._handle_analysis_error(e)
    
    def _on_analysis_finished(self):
        """Clean up after analysis"""
        self._analysis_running = False
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
    
    def _handle_analysis_error(self, error):
        """Show error message and clean up"""
        self._on_analysis_finished()
        QMessageBox.critical(self, "Analysis Error", 
                           f"Engineering analysis failed:\n{str(error)}")

    def _update_progress(self, progress):
        """Update progress bar"""
        self.progress_bar.setValue(progress)
        if progress == 100:
            self.metrics_label.setText("Simulation completed")
        else:
            self.metrics_label.setText(f"Simulation in progress ({progress}%)")

    def solve_thermoacoustics(self, params):
        """Thermoacoustic PDE solver considering all components and parameters"""
        # Extract parameters
        stack_length = params['stack_length'] * 1e-3  # Convert mm to m
        stack_width = params['stack_width'] * 1e-3
        stack_height = params['stack_height'] * 1e-3
        stack_porosity = params['stack_porosity'] / 100.0
        stack_thermal_conductivity = params['stack_thermal_conductivity']
        fluid_pressure = params['fluid_pressure'] * 1e3  # Convert kPa to Pa
        ambient_temp = params['ambient_temp'] + 273.15  # Convert to Kelvin
        operating_temp = params['operating_temp'] + 273.15  # Convert to Kelvin
        hhx_length = params['hhx_length'] * 1e-3
        chx_length = params['chx_length'] * 1e-3
        resonator_diameter = params['resonator_diameter'] * 1e-3

        # Derived parameters
        alpha = stack_thermal_conductivity / (stack_porosity * stack_length)
        c = 343.0  # Speed of sound in air, m/s

        # Initialize arrays
        nx = 100
        T = np.full(nx, ambient_temp)
        u = np.zeros(nx)

        # Time-stepping parameters
        dt = 1e-5
        dx = stack_length / nx

        # Time-stepping loop
        for _ in range(1000):
            # Update temperature
            T[1:-1] += alpha * dt / dx**2 * (T[2:] - 2*T[1:-1] + T[:-2])

            # Update displacement
            u[1:-1] += c**2 * dt**2 / dx**2 * (u[2:] - 2*u[1:-1] + u[:-2])

            # Incorporate heat exchangers
            T[:int(nx * hhx_length / stack_length)] += 0.1  # Example effect
            T[-int(nx * chx_length / stack_length):] -= 0.1

        # Calculate results
        frequency = np.sqrt(np.mean(u**2)) * c / (2 * np.pi * stack_length)
        power = np.max(u) * fluid_pressure
        efficiency = power / (stack_thermal_conductivity * (operating_temp - ambient_temp))

        return {
            'frequency': frequency,
            'power': power,
            'efficiency': efficiency
        }

    def run_simulation(self):
        """Execute thermoacoustic PDE solver"""
        try:
            # 1. Get parameters
            params = self.config_panel.get_simulation_parameters()
            
            # 2. Run solver (replace with your actual PDE solver)
            results = self.solve_thermoacoustic_pde(params)
            
            # 3. Update visualizations
            self.update_results_tab(results)
            self._2d_view.draw_engine()
            
            return True
            
        except Exception as e:
            print(f"Simulation failed: {str(e)}")
            return False
            
    def solve_thermoacoustic_pde(self, params):
        """Your PDE solver implementation"""
        # Placeholder - replace with your actual solver
        return {
            'frequency': 85.3,  # Hz
            'pressure_amplitude': 15000,  # Pa
            'phase_angle': 0.62,  # radians
            'efficiency': 0.42
        }

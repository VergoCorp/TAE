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
        self._2d_widget = None
        self._2d_canvas = None
        self._2d_ax = None
        self._2d_fig = None
        self._3d_widget = None
        self._3d_plotter = None
        
        # Create 3D tab first (index 0)
        self.create_3d_tab()
        # Create 2D tab second (index 1)
        self.create_2d_tab()
        
        # Set 3D tab as default
        self.setCurrentIndex(0)

        # Connect signals
        self.currentChanged.connect(self.on_tab_changed)

        # Initialize UI
        self.init_ui()

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
            
            try:
                # Update the current view
                if self.currentIndex() == 0:  # 3D tab
                    self.update_3d_model(internal_name)
                else:  # 2D tab
                    self.update_2d_schematic()
            except Exception as e:
                print(f"Error updating view: {e}")
        else:
            print(f"Warning: Parameter {internal_name} not found in current_dimensions")

    def on_tab_changed(self):
        if self.currentIndex() == 0:  # 3D tab
            self.update_3d_model()
        else:  # 2D tab
            self.update_2d_schematic()

    def create_2d_tab(self):
        """Create 2D visualization tab with matplotlib"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create figure and canvas
        self._2d_fig = plt.figure(figsize=(8, 6))
        self._2d_canvas = FigureCanvas(self._2d_fig)
        self._2d_ax = self._2d_fig.add_subplot(111)
        
        layout.addWidget(self._2d_canvas)
        widget.setLayout(layout)
        
        self._2d_widget = widget
        self.addTab(widget, "2D Sketch")
        
        # Initial update after setup
        self.update_2d_schematic()

    def update_2d_schematic(self):
        """Enhanced 2D visualization with velocity vectors"""
        if not hasattr(self, '_2d_ax'):
            return
            
        self._2d_ax.clear()
        
        # Setup professional styling
        self._2d_ax.grid(True, linestyle=':', alpha=0.7)
        self._2d_ax.set_facecolor('#f8f8f8')
        self._2d_fig.patch.set_facecolor('#f0f0f0')
        
        # Dimensions in meters
        res_length = self.current_dimensions['resonator_length'] * 0.001
        res_radius = self.current_dimensions['resonator_diameter'] * 0.0005
        stack_length = self.current_dimensions['stack_length'] * 0.001
        stack_pos = self.current_dimensions['stack_position'] * 0.001
        hhx_length = self.current_dimensions['hhx_length'] * 0.001
        chx_length = self.current_dimensions['chx_length'] * 0.001
        
        # Add velocity vectors (example data - replace with actual simulation results)
        if hasattr(self, 'simulation') and hasattr(self.simulation, 'u'):
            x_positions = np.linspace(0, res_length, len(self.simulation.u))
            y_positions = np.zeros_like(x_positions)
            
            # Normalize velocities for visualization
            max_vel = np.max(np.abs(self.simulation.u))
            if max_vel > 0:
                scaled_vel = 0.8 * res_radius * (self.simulation.u / max_vel)
                
                # Plot vectors with color indicating direction
                for x, y, vel in zip(x_positions, y_positions, scaled_vel):
                    color = '#ff0000' if vel > 0 else '#0000ff'  # Red=positive, Blue=negative
                    self._2d_ax.arrow(x, y, 0, vel, 
                                     head_width=0.01, head_length=0.005, 
                                     fc=color, ec=color, alpha=0.7)
                
                # Add velocity scale legend
                self._2d_ax.plot([0.8*res_length, 0.8*res_length], 
                                [res_radius*1.2, res_radius*1.2 + 0.8*res_radius],
                                color='black', lw=1)
                self._2d_ax.text(0.8*res_length, res_radius*1.5, 
                                f'{max_vel:.2f} m/s\n(peak velocity)', 
                                ha='center', fontsize=8)
        
        # Add detailed annotations
        self._2d_ax.set_title('Thermoacoustic Engine Cross-Section', 
                            fontsize=12, pad=20)
        self._2d_ax.set_xlabel('Position Along Resonator (m)', fontsize=10)
        self._2d_ax.set_ylabel('', fontsize=10)
        self._2d_ax.tick_params(axis='both', which='major', labelsize=8)
        
        # Add component labels with arrows
        def annotate_component(x, y, text, color):
            self._2d_ax.annotate(text, xy=(x, y), xytext=(x, y+res_radius*1.5),
                               ha='center', va='center', fontsize=9,
                               arrowprops=dict(arrowstyle="->", color=color),
                               bbox=dict(boxstyle="round", alpha=0.2, color=color))
        
        # Draw components with enhanced styling
        components = [
            ('HHX', 0.02, '#ff6b6b', hhx_length),
            ('Stack', stack_pos, '#4d96ff', stack_length),
            ('CHX', stack_pos+stack_length, '#6bcb77', chx_length)
        ]
        
        for name, pos, color, length in components:
            rect = patches.Rectangle((pos, -res_radius), length, res_radius*2,
                           facecolor=color, alpha=0.7, edgecolor='black', lw=1)
            self._2d_ax.add_patch(rect)
            annotate_component(pos + length/2, 0, name, color)
        
        # Draw resonator tube
        tube = patches.Rectangle((0, -res_radius), res_length, res_radius*2,
                       facecolor='none', edgecolor='#333333', linestyle='--', lw=1)
        self._2d_ax.add_patch(tube)
        
        # Set proper axis limits
        self._2d_ax.set_xlim(0, res_length)
        self._2d_ax.set_ylim(-res_radius*1.5, res_radius*1.5)
        
        # Add scale bar
        self._2d_ax.plot([0.05, 0.15], [-res_radius*1.3]*2, color='black', lw=2)
        self._2d_ax.text(0.1, -res_radius*1.4, '10 cm', ha='center', fontsize=8)
        
        self._2d_canvas.draw()

    def create_3d_tab(self):
        """Create 3D visualization tab with PyVista"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create PyVista plotter
        self._3d_plotter = QtInteractor(widget)
        layout.addWidget(self._3d_plotter)
        
        widget.setLayout(layout)
        self._3d_widget = widget
        self.addTab(widget, "3D Sketch")
        
        # Initial update
        self.update_3d_model()

    def update_3d_model(self, changed_param=None):
        """Update 3D model with new parameters"""
        self._3d_plotter.clear()
        
        # Convert mm to meters
        res_length = self.current_dimensions['resonator_length'] * 0.001
        res_diameter = self.current_dimensions['resonator_diameter'] * 0.001
        stack_length = self.current_dimensions['stack_length'] * 0.001
        stack_position = self.current_dimensions['stack_position'] * 0.001
        hhx_length = self.current_dimensions['hhx_length'] * 0.001
        chx_length = self.current_dimensions['chx_length'] * 0.001
        
        # Create engine components
        # Engine casing (left and right)
        casing_left = pv.Cylinder(center=[stack_position, 0, 0], direction=[1, 0, 0],
                                radius=res_diameter/2, height=0.05)
        casing_right = pv.Cylinder(center=[stack_position + stack_length + hhx_length + chx_length, 0, 0],
                                 direction=[1, 0, 0], radius=res_diameter/2, height=0.05)
        
        # Stack
        stack = pv.Box(bounds=[stack_position + hhx_length, 
                             stack_position + hhx_length + stack_length,
                             -res_diameter/2, res_diameter/2,
                             -res_diameter/2, res_diameter/2])
        
        # Heat exchangers
        hhx = pv.Cylinder(center=[stack_position + hhx_length/2, 0, 0],
                         direction=[1, 0, 0], radius=res_diameter*0.4, height=hhx_length)
        
        chx = pv.Cylinder(center=[stack_position + hhx_length + stack_length + chx_length/2, 0, 0],
                         direction=[1, 0, 0], radius=res_diameter*0.4, height=chx_length)
        
        # Resonating pipes
        res_pipe_left = pv.Cylinder(center=[stack_position/2, 0, 0],
                                  direction=[1, 0, 0], radius=res_diameter*0.3, height=stack_position)
        
        right_res_start = stack_position + stack_length + hhx_length + chx_length + 0.05
        right_res_length = res_length - right_res_start
        res_pipe_right = pv.Cylinder(center=[right_res_start + right_res_length/2, 0, 0],
                                   direction=[1, 0, 0], radius=res_diameter*0.3, height=right_res_length)
        
        # Add all parts to the plotter with appropriate colors and opacity
        self._3d_plotter.add_mesh(casing_left, color='gray', opacity=0.7)
        self._3d_plotter.add_mesh(casing_right, color='gray', opacity=0.7)
        self._3d_plotter.add_mesh(stack, color='royalblue', opacity=0.7)
        self._3d_plotter.add_mesh(hhx, color='red', opacity=0.7)
        self._3d_plotter.add_mesh(chx, color='blue', opacity=0.7)
        self._3d_plotter.add_mesh(res_pipe_left, color='lightgray')
        self._3d_plotter.add_mesh(res_pipe_right, color='lightgray')
        
        # Set camera position for isometric view
        self._3d_plotter.camera_position = 'iso'
        self._3d_plotter.reset_camera()

    def import_cad_model(self, filepath):
        """Import CAD file into 3D viewer"""
        try:
            # Supported extensions without extra dependencies
            supported = ('.stl', '.obj', '.ply', '.vtk', '.step', '.stp', '.iges', '.igs')
            
            if not filepath.lower().endswith(supported):
                raise ValueError(f"Unsupported file format. Supported: {', '.join(supported)}")
                
            mesh = pv.read(filepath)
            self._3d_plotter.add_mesh(mesh, color='lightgray', show_edges=True)
            self._3d_plotter.reset_camera()
            return True
            
        except Exception as e:
            print(f"CAD import failed: {str(e)}")
            return False

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
            self.update_2d_schematic()
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
        """Your thermoacoustic PDE solver implementation"""
        # Placeholder - replace with your actual solver
        # This should return dict with:
        # - frequency (Hz)
        # - power (W)
        # - efficiency (0-1)
        return {
            'frequency': 85.3,
            'power': 150.2,
            'efficiency': 0.42
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
            self.update_2d_schematic()
            
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

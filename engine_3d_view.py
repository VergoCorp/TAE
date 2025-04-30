from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np

class Engine3DView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create PyVista plotter
        self.plotter = QtInteractor(self)
        self.plotter.set_background('white')
        self.plotter.enable_anti_aliasing()
        self.plotter.enable_eye_dome_lighting()
        layout.addWidget(self.plotter)
        
        # Initialize the 3D model
        self.create_engine_model()
        
    def create_engine_model(self):
        self.plotter.clear()
        
        # Create all components
        self.create_resonating_pipes()
        self.create_engine_casing()
        self.create_stack()
        self.create_heat_exchangers()
        self.create_flanges()
        self.create_adapters()
        
        # Set camera position for isometric view
        self.plotter.camera_position = 'iso'
        self.plotter.camera.zoom(1.5)
        
    def create_resonating_pipes(self):
        # Create threaded pipes on both sides
        for x_pos in [-0.375, 0.375]:  # Adjusted positions for full length
            # Main pipe body
            pipe = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=0.03,
                height=0.265  # Length from dimensions
            )
            self.plotter.add_mesh(pipe, color='#B8B8B8')
            
            # Create thread pattern
            self.create_pipe_threads(x_pos + 0.13 if x_pos < 0 else x_pos - 0.13)
            
            # Create galvanized reducer
            reducer = pv.Cone(
                center=(x_pos + 0.132 if x_pos < 0 else x_pos - 0.132, 0, 0),
                direction=(1 if x_pos < 0 else -1, 0, 0),
                height=0.04,
                radius=0.04,
            )
            self.plotter.add_mesh(reducer, color='#C8C8C8')  # Galvanized finish
            
    def create_pipe_threads(self, x_pos):
        t = np.linspace(0, 8*np.pi, 200)
        radius = 0.031
        pitch = 0.003
        
        for offset in [-0.02, 0.02]:  # Create two sections of threads
            x = x_pos + offset + t * pitch / (2*np.pi)
            y = radius * np.cos(t)
            z = radius * np.sin(t)
            
            points = np.column_stack((x, y, z))
            spline = pv.Spline(points, 1000)
            thread = spline.tube(radius=0.001)
            self.plotter.add_mesh(thread, color='#707070')
            
    def create_engine_casing(self):
        # Main casing cylinders with bolt pattern
        for x_pos in [-0.085, 0.085]:
            # Main casing body
            casing = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=0.075,
                height=0.025
            )
            self.plotter.add_mesh(casing, color='#D0D0D0', opacity=0.8)
            
            # Add bolt pattern
            self.create_casing_bolts(x_pos)
            
            # Add reinforcement ring
            ring = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=0.08,
                height=0.015
            )
            self.plotter.add_mesh(ring, color='#B0B0B0')
            
    def create_casing_bolts(self, x_pos):
        # Create bolt pattern for engine casing
        for i in range(8):
            angle = i * np.pi/4
            radius = 0.07
            y = radius * np.cos(angle)
            z = radius * np.sin(angle)
            
            # Bolt shaft
            bolt = pv.Cylinder(
                center=(x_pos, y, z),
                direction=(1, 0, 0),
                radius=0.003,
                height=0.035
            )
            self.plotter.add_mesh(bolt, color='#404040')
            
            # Bolt head
            head = pv.Cylinder(
                center=(x_pos - 0.015, y, z),
                direction=(1, 0, 0),
                radius=0.005,
                height=0.005
            )
            self.plotter.add_mesh(head, color='#303030')
            
    def create_stack(self):
        # Create main stack with mesh pattern using cylindrical elements
        spacing = 0.005  # Spacing between elements
        radius = 0.001   # Radius of each element
        
        # Create grid of cylindrical elements
        for x in np.arange(-0.04, 0.04, spacing):
            for y in np.arange(-0.04, 0.04, spacing):
                element = pv.Cylinder(
                    center=(x, y, 0),
                    direction=(0, 0, 1),
                    radius=radius,
                    height=0.09
                )
                self.plotter.add_mesh(element, color='#4169E1')
        
    def create_heat_exchangers(self):
        # Create HHX (Hot Heat Exchanger) with multiple cartridge heaters
        hhx_housing = pv.Box(bounds=(-0.0625, -0.0425, -0.05, 0.05, -0.05, 0.05))
        self.plotter.add_mesh(hhx_housing, color='#CD5C5C')
        
        # Add multiple cartridge heaters
        heater_positions = [
            (-0.052, -0.03, 0), (-0.052, -0.01, 0),
            (-0.052, 0.01, 0), (-0.052, 0.03, 0)
        ]
        for pos in heater_positions:
            heater = pv.Cylinder(
                center=pos,
                direction=(0, 0, 1),
                radius=0.004,
                height=0.09
            )
            self.plotter.add_mesh(heater, color='#FF4500')
        
        # Create CHX (Cold Heat Exchanger) with copper tubes
        chx_housing = pv.Box(bounds=(0.0425, 0.0625, -0.05, 0.05, -0.05, 0.05))
        self.plotter.add_mesh(chx_housing, color='#90EE90')
        
        # Add copper tubes in grid pattern
        for y in np.linspace(-0.035, 0.035, 4):
            for z in np.linspace(-0.035, 0.035, 4):
                tube = pv.Cylinder(
                    center=(0.0525, y, z),
                    direction=(0, 0, 1),
                    radius=0.003,
                    height=0.1
                )
                self.plotter.add_mesh(tube, color='#B87333')
                
    def create_flanges(self):
        for x_pos in [-0.065, 0.065]:
            # Main flange body
            flange = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=0.07,
                height=0.02
            )
            self.plotter.add_mesh(flange, color='#C0C0C0')
            
            # Gasket
            gasket = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=0.065,
                height=0.002
            )
            self.plotter.add_mesh(gasket, color='#8B4513')
            
            # Add bolts
            self.create_flange_bolts(x_pos)
            
    def create_flange_bolts(self, x_pos):
        for i in range(8):
            angle = i * np.pi/4
            radius = 0.06
            y = radius * np.cos(angle)
            z = radius * np.sin(angle)
            
            # Bolt shaft
            bolt = pv.Cylinder(
                center=(x_pos, y, z),
                direction=(1, 0, 0),
                radius=0.004,
                height=0.03
            )
            self.plotter.add_mesh(bolt, color='#404040')
            
            # Bolt head
            head = pv.Cylinder(
                center=(x_pos - 0.01, y, z),
                direction=(1, 0, 0),
                radius=0.006,
                height=0.006
            )
            self.plotter.add_mesh(head, color='#303030')
            
    def create_adapters(self):
        # Thermoacoustic adapters between flanges and heat exchangers
        for x_pos in [-0.04, 0.04]:
            adapter = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=0.055,
                height=0.01
            )
            self.plotter.add_mesh(adapter, color='#A0A0A0')
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.plotter.reset_camera() 
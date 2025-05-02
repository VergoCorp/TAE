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
        
        # Scale factor to convert mm to our model units
        # Total length is 750mm, we'll scale it to fit in our coordinate system
        self.scale = 0.001  # 1mm = 0.001 units
        
        # Create all components based on the schematic dimensions
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
        # Based on the schematic, we have:
        # Left pipe: 265mm, Right pipe: 75mm + 105mm
        
        # Left resonating pipe (265mm)
        left_pipe = pv.Cylinder(
            center=(-132.5 * self.scale, 0, 0),  # Center position
            direction=(1, 0, 0),
            radius=30 * self.scale,  # Estimated from drawing
            height=265 * self.scale  # Length from schematic
        )
        self.plotter.add_mesh(left_pipe, color='#B8B8B8')
        
        # Right resonating pipe (75mm + 105mm = 180mm)
        right_pipe = pv.Cylinder(
            center=(90 * self.scale, 0, 0),  # Center position 
            direction=(1, 0, 0),
            radius=30 * self.scale,  # Estimated from drawing
            height=180 * self.scale  # Length from schematic
        )
        self.plotter.add_mesh(right_pipe, color='#B8B8B8')
        
        # Create threaded sections at the ends
        self.create_pipe_threads((-265 * self.scale, 0, 0))
        self.create_pipe_threads((180 * self.scale, 0, 0))
        
        # Create galvanized steel reducers
        left_reducer = pv.Cylinder(
            center=(-265 * self.scale, 0, 0),
            direction=(-1, 0, 0),
            radius=35 * self.scale,
            height=25 * self.scale
        )
        self.plotter.add_mesh(left_reducer, color='#C8C8C8')  # Galvanized finish
        
        right_reducer = pv.Cylinder(
            center=(180 * self.scale, 0, 0),
            direction=(1, 0, 0),
            radius=35 * self.scale,
            height=25 * self.scale
        )
        self.plotter.add_mesh(right_reducer, color='#C8C8C8')  # Galvanized finish
            
    def create_pipe_threads(self, position):
        x_pos, y_pos, z_pos = position
        t = np.linspace(0, 8*np.pi, 200)
        radius = 31 * self.scale
        pitch = 3 * self.scale
        
        # Create thread pattern
        x = x_pos + t * pitch / (2*np.pi)
        y = y_pos + radius * np.cos(t)
        z = z_pos + radius * np.sin(t)
        
        points = np.column_stack((x, y, z))
        spline = pv.Spline(points, 1000)
        thread = spline.tube(radius=1 * self.scale)
        self.plotter.add_mesh(thread, color='#707070')
            
    def create_engine_casing(self):
        # Based on schematic, engine casing is positioned at ±85mm from center
        # with thickness of ~20mm
        
        # Left engine casing
        left_casing = pv.Cylinder(
            center=(-85 * self.scale, 0, 0),
            direction=(1, 0, 0),
            radius=75 * self.scale,  # Based on drawing
            height=20 * self.scale   # Thickness estimate
        )
        self.plotter.add_mesh(left_casing, color='#D0D0D0', opacity=0.8)
        
        # Right engine casing
        right_casing = pv.Cylinder(
            center=(85 * self.scale, 0, 0),
            direction=(1, 0, 0),
            radius=75 * self.scale,  # Based on drawing
            height=20 * self.scale   # Thickness estimate
        )
        self.plotter.add_mesh(right_casing, color='#D0D0D0', opacity=0.8)
        
        # Add bolt patterns
        self.create_casing_bolts(-85 * self.scale)
        self.create_casing_bolts(85 * self.scale)
            
    def create_casing_bolts(self, x_pos):
        # Create bolt pattern for engine casing
        for i in range(8):
            angle = i * np.pi/4
            radius = 70 * self.scale
            y = radius * np.cos(angle)
            z = radius * np.sin(angle)
            
            # Bolt shaft
            bolt = pv.Cylinder(
                center=(x_pos, y, z),
                direction=(1, 0, 0),
                radius=3 * self.scale,
                height=35 * self.scale
            )
            self.plotter.add_mesh(bolt, color='#404040')
            
            # Bolt head
            head = pv.Cylinder(
                center=(x_pos - 15 * self.scale if x_pos < 0 else x_pos + 15 * self.scale, y, z),
                direction=(1, 0, 0),
                radius=5 * self.scale,
                height=5 * self.scale
            )
            self.plotter.add_mesh(head, color='#303030')
            
    def create_stack(self):
        # Based on the drawing, stack is 50mm wide (position ~0)
        # Create a rectangular stack structure with mesh pattern
        
        # Main stack housing
        stack_width = 50 * self.scale
        stack_height = 60 * self.scale  # Estimated from drawing
        stack_depth = 60 * self.scale   # Estimated from drawing
        
        # Create the blue mesh structure
        # Use a grid of thin lines to represent the mesh
        spacing = 3 * self.scale  # Spacing between mesh elements
        
        # Create horizontal mesh lines (x-direction)
        for z in np.linspace(-stack_depth/2, stack_depth/2, 20):
            for y in np.linspace(-stack_height/2, stack_height/2, 20):
                line = pv.Line((-stack_width/2, y, z), (stack_width/2, y, z))
                tube = line.tube(radius=0.5 * self.scale)
                self.plotter.add_mesh(tube, color='#4169E1')
                
        # Create vertical mesh lines (y-direction)
        for x in np.linspace(-stack_width/2, stack_width/2, 20):
            for z in np.linspace(-stack_depth/2, stack_depth/2, 20):
                line = pv.Line((x, -stack_height/2, z), (x, stack_height/2, z))
                tube = line.tube(radius=0.5 * self.scale)
                self.plotter.add_mesh(tube, color='#4169E1')
        
    def create_heat_exchangers(self):
        # From schematic, HHX is positioned before stack (~-20mm from center)
        # and CHX after stack (~20mm from center)
        # HHX width is ~20mm, CHX width is ~20mm
        
        # Create HHX (Hot Heat Exchanger) with cartridge heaters
        hhx_width = 20 * self.scale
        hhx_height = 60 * self.scale  # Estimated
        hhx_depth = 60 * self.scale   # Estimated
        hhx_position = -35 * self.scale  # Position based on schematic
        
        hhx_housing = pv.Box(
            bounds=(
                hhx_position - hhx_width/2, hhx_position + hhx_width/2,
                -hhx_height/2, hhx_height/2,
                -hhx_depth/2, hhx_depth/2
            )
        )
        self.plotter.add_mesh(hhx_housing, color='#CD5C5C')
        
        # Add four cartridge heaters on the left side of HHX
        heater_positions = [
            (hhx_position - hhx_width/2 - 5 * self.scale, -20 * self.scale, 0),
            (hhx_position - hhx_width/2 - 5 * self.scale, -7 * self.scale, 0),
            (hhx_position - hhx_width/2 - 5 * self.scale, 7 * self.scale, 0),
            (hhx_position - hhx_width/2 - 5 * self.scale, 20 * self.scale, 0)
        ]
        
        for pos in heater_positions:
            heater = pv.Cylinder(
                center=pos,
                direction=(0, 0, 1),
                radius=4 * self.scale,
                height=90 * self.scale
            )
            self.plotter.add_mesh(heater, color='#FF4500')
        
        # Create CHX (Cold Heat Exchanger) with copper tubes
        chx_width = 20 * self.scale
        chx_height = 60 * self.scale  # Estimated
        chx_depth = 60 * self.scale   # Estimated
        chx_position = 35 * self.scale  # Position based on schematic
        
        chx_housing = pv.Box(
            bounds=(
                chx_position - chx_width/2, chx_position + chx_width/2,
                -chx_height/2, chx_height/2,
                -chx_depth/2, chx_depth/2
            )
        )
        self.plotter.add_mesh(chx_housing, color='#90EE90')
        
        # Add copper tubes in grid pattern as shown in drawing
        for i in range(4):
            for j in range(4):
                y_offset = -25 * self.scale + i * 17 * self.scale
                z_offset = -25 * self.scale + j * 17 * self.scale
                
                tube = pv.Cylinder(
                    center=(chx_position + chx_width/2 + 5 * self.scale, y_offset, z_offset),
                    direction=(0, 0, 1),
                    radius=3 * self.scale,
                    height=90 * self.scale
                )
                self.plotter.add_mesh(tube, color='#B87333')  # Copper color
                
    def create_flanges(self):
        # Flanges are positioned at around ±65mm from center
        flange_positions = [-65 * self.scale, 65 * self.scale]
        
        for x_pos in flange_positions:
            # Main flange body
            flange = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=70 * self.scale,  # From drawing
                height=10 * self.scale   # Thickness from drawing
            )
            self.plotter.add_mesh(flange, color='#C0C0C0')
            
            # Gasket - thin ring between flanges and other components
            gasket = pv.Cylinder(
                center=(x_pos + 5 * self.scale if x_pos < 0 else x_pos - 5 * self.scale, 0, 0),
                direction=(1, 0, 0),
                radius=65 * self.scale,
                height=2 * self.scale
            )
            self.plotter.add_mesh(gasket, color='#8B4513')  # Brown color for gasket
            
            # Add bolts
            self.create_flange_bolts(x_pos)
            
    def create_flange_bolts(self, x_pos):
        # Create 8 bolts arranged in a circular pattern
        for i in range(8):
            angle = i * np.pi/4
            radius = 60 * self.scale  # Bolt circle diameter from drawing
            y = radius * np.cos(angle)
            z = radius * np.sin(angle)
            
            # Bolt shaft
            bolt = pv.Cylinder(
                center=(x_pos, y, z),
                direction=(1, 0, 0),
                radius=4 * self.scale,
                height=20 * self.scale
            )
            self.plotter.add_mesh(bolt, color='#404040')
            
            # Bolt head
            head = pv.Cylinder(
                center=(x_pos - 10 * self.scale if x_pos < 0 else x_pos + 10 * self.scale, y, z),
                direction=(1, 0, 0),
                radius=6 * self.scale,
                height=6 * self.scale
            )
            self.plotter.add_mesh(head, color='#303030')
            
    def create_adapters(self):
        # Thermoacoustic adapters positioned between flanges and heat exchangers
        # From the drawing, positioned at around ±50mm from center
        adapter_positions = [-50 * self.scale, 50 * self.scale]
        
        for x_pos in adapter_positions:
            adapter = pv.Cylinder(
                center=(x_pos, 0, 0),
                direction=(1, 0, 0),
                radius=55 * self.scale,  # From drawing
                height=10 * self.scale   # Thickness estimate
            )
            self.plotter.add_mesh(adapter, color='#A0A0A0')
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.plotter.reset_camera() 
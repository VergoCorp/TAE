from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QFrame, QGroupBox, 
                           QFormLayout, QComboBox, QLineEdit, QHBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from numeric_input import NumericInput
from simulation import SimulationParams, ThermoacousticSimulation
from functools import partial

class ConfigPanel(QWidget):
    # Signals
    parameter_changed = pyqtSignal(str, float)
    simulation_started = pyqtSignal(object)
    simulation_stopped = pyqtSignal()
    simulation_updated = pyqtSignal(dict, dict)
    simulation_finished = pyqtSignal(dict, dict)

    def __init__(self):
        super().__init__()
        self.simulation = None
        self.running = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Working Fluid Parameters
        fluid_group = QGroupBox("Working Fluid")
        fluid_layout = QFormLayout()
        self.working_fluid_type = QComboBox()
        self.working_fluid_type.addItems(["Air", "Helium", "Argon"])
        self.working_fluid_pressure = NumericInput()
        fluid_layout.addRow("Type:", self.working_fluid_type)
        fluid_layout.addRow("Pressure (kPa):", self.working_fluid_pressure)
        fluid_group.setLayout(fluid_layout)

        # Stack Material Properties
        stack_mat_group = QGroupBox("Stack Material Properties")
        stack_mat_layout = QFormLayout()
        self.stack_specific_heat = NumericInput()
        self.stack_melting_point = NumericInput()
        stack_mat_layout.addRow("Specific Heat (J/kgK):", self.stack_specific_heat)
        stack_mat_layout.addRow("Melting Point (°C):", self.stack_melting_point)
        stack_mat_group.setLayout(stack_mat_layout)

        # Heat Exchanger Material Properties
        hx_mat_group = QGroupBox("Heat Exchanger Material")
        hx_mat_layout = QFormLayout()
        self.hhx_material = QComboBox()
        self.hhx_material.addItems(["Copper", "Aluminum", "Stainless Steel"])
        self.chx_material = QComboBox()
        self.chx_material.addItems(["Copper", "Aluminum", "Stainless Steel"])
        hx_mat_layout.addRow("HHX Material:", self.hhx_material)
        hx_mat_layout.addRow("CHX Material:", self.chx_material)
        hx_mat_group.setLayout(hx_mat_layout)

        # Stack Parameters
        stack_group = QGroupBox("Stack")
        stack_layout = QFormLayout()
        
        # Stack dimensions with predetermined values from the sketch
        self.stack_length = NumericInput(min_val=0, max_val=1000, decimals=1, suffix=" mm")
        self.stack_length.setValue(85.0)  # From sketch
        
        self.stack_position = NumericInput(min_val=0, max_val=1000, decimals=1, suffix=" mm")
        self.stack_position.setValue(265.0)  # Position from left end
        
        self.stack_spacing = NumericInput(min_val=0, max_val=10, decimals=1, suffix=" mm")
        self.stack_spacing.setValue(1.0)
        
        self.stack_width = NumericInput()
        self.stack_height = NumericInput()
        self.stack_porosity = NumericInput()
        self.stack_cell_density = NumericInput()
        self.stack_thermal_conductivity = NumericInput()
        
        stack_layout.addRow("Length (mm):", self.stack_length)
        stack_layout.addRow("Position (mm):", self.stack_position)
        stack_layout.addRow("Spacing (mm):", self.stack_spacing)
        stack_layout.addRow("Width (mm):", self.stack_width)
        stack_layout.addRow("Height (mm):", self.stack_height)
        stack_layout.addRow("Porosity (%):", self.stack_porosity)
        stack_layout.addRow("Cell Density (CPSI):", self.stack_cell_density)
        stack_layout.addRow("Thermal Conductivity (W/mK):", self.stack_thermal_conductivity)
        stack_group.setLayout(stack_layout)
        scroll_layout.addWidget(stack_group)

        # Heat Exchanger Parameters
        hx_group = QGroupBox("Heat Exchangers")
        hx_layout = QFormLayout()
        
        # HX dimensions with predetermined values from the sketch
        self.hhx_length = NumericInput(min_val=0, max_val=100, decimals=1, suffix=" mm")
        self.hhx_length.setValue(20.0)  # From sketch
        
        self.chx_length = NumericInput(min_val=0, max_val=100, decimals=1, suffix=" mm")
        self.chx_length.setValue(20.0)  # From sketch
        
        self.hhx_power_rating = NumericInput()
        self.hhx_supply_voltage = NumericInput()
        self.hhx_diameter = NumericInput()
        
        self.chx_config = QComboBox()
        self.chx_config.addItems(["Internal Only", "Internal + External"])
        self.chx_internal_br = NumericInput()
        self.chx_external_br = NumericInput()
        self.chx_num_pores = NumericInput()
        self.chx_pore_area = NumericInput()
        self.chx_coolant_flow = NumericInput()
        
        hx_layout.addRow("Hot HX Length (mm):", self.hhx_length)
        hx_layout.addRow("Cold HX Length (mm):", self.chx_length)
        hx_layout.addRow("Power Rating (W):", self.hhx_power_rating)
        hx_layout.addRow("Supply Voltage (V):", self.hhx_supply_voltage)
        hx_layout.addRow("Diameter (mm):", self.hhx_diameter)
        hx_layout.addRow("Configuration:", self.chx_config)
        hx_layout.addRow("Internal BR (%):", self.chx_internal_br)
        hx_layout.addRow("External BR (%):", self.chx_external_br)
        hx_layout.addRow("Number of Pores:", self.chx_num_pores)
        hx_layout.addRow("Pore Area (mm²):", self.chx_pore_area)
        hx_layout.addRow("Coolant Flow Rate (L/min):", self.chx_coolant_flow)
        hx_group.setLayout(hx_layout)
        scroll_layout.addWidget(hx_group)

        # Resonator Parameters
        resonator_group = QGroupBox("Resonator")
        resonator_layout = QFormLayout()
        
        self.resonator_length = NumericInput(min_val=0, max_val=2000, decimals=1, suffix=" mm")
        self.resonator_length.setValue(750.0)  # Total length
        
        self.resonator_diameter = NumericInput(min_val=0, max_val=200, decimals=1, suffix=" mm")
        self.resonator_diameter.setValue(50.0)  # From sketch
        
        resonator_layout.addRow("Length (mm):", self.resonator_length)
        resonator_layout.addRow("Diameter (mm):", self.resonator_diameter)
        resonator_group.setLayout(resonator_layout)
        scroll_layout.addWidget(resonator_group)

        # Engine Casing Parameters
        casing_group = QGroupBox("Engine Casing")
        casing_layout = QFormLayout()
        self.casing_material = QComboBox()
        self.casing_material.addItems(["Steel", "Aluminum", "Plastic", "Other"])
        self.casing_thickness = NumericInput()
        self.casing_flange = QLineEdit()
        casing_layout.addRow("Material:", self.casing_material)
        casing_layout.addRow("Thickness (mm):", self.casing_thickness)
        casing_layout.addRow("Flange Details:", self.casing_flange)
        casing_group.setLayout(casing_layout)

        # Coolant Parameters
        coolant_group = QGroupBox("Coolant")
        coolant_layout = QFormLayout()
        self.coolant_type = QComboBox()
        self.coolant_type.addItems(["Water", "Oil", "No Coolant", "Other"])
        self.coolant_temp = NumericInput()
        coolant_layout.addRow("Type:", self.coolant_type)
        coolant_layout.addRow("Temperature (°C):", self.coolant_temp)
        coolant_group.setLayout(coolant_layout)

        # HHX Housing Blockage Ratio
        hhx_housing_group = QGroupBox("HHX Housing")
        hhx_housing_layout = QFormLayout()
        self.hhx_blockage_ratio = NumericInput()
        hhx_housing_layout.addRow("Blockage Ratio (%):", self.hhx_blockage_ratio)
        hhx_housing_group.setLayout(hhx_housing_layout)

        # Analysis Mode Selection
        analysis_group = QGroupBox("Analysis Mode")
        analysis_layout = QFormLayout()
        self.analysis_mode = QComboBox()
        self.analysis_mode.addItems([
            "Design Optimization",
            "Performance Analysis",
            "Parametric Study",
            "Efficiency Analysis"
        ])
        analysis_layout.addRow("Mode:", self.analysis_mode)
        analysis_group.setLayout(analysis_layout)

        # Performance Targets
        perf_group = QGroupBox("Performance Targets")
        perf_layout = QFormLayout()
        self.perf_onset_time = NumericInput()
        self.perf_max_temp = NumericInput()
        self.perf_sound_level = NumericInput()
        self.perf_min_velocity = NumericInput()
        perf_layout.addRow("Target Onset Time (s):", self.perf_onset_time)
        perf_layout.addRow("Max Operating Temp (°C):", self.perf_max_temp)
        perf_layout.addRow("Target Sound Level (dB):", self.perf_sound_level)
        perf_layout.addRow("Min Volumetric Velocity (m/s):", self.perf_min_velocity)
        perf_group.setLayout(perf_layout)

        # Operating Conditions
        op_group = QGroupBox("Operating Conditions")
        op_layout = QFormLayout()
        self.op_ambient_temp = NumericInput()
        self.op_operating_temp = NumericInput()
        self.op_resonant_freq = NumericInput()
        op_layout.addRow("Ambient Temperature (°C):", self.op_ambient_temp)
        op_layout.addRow("Operating Temperature (°C):", self.op_operating_temp)
        op_layout.addRow("Resonant Frequency (Hz):", self.op_resonant_freq)
        op_group.setLayout(op_layout)

        # Add all groups to scroll layout
        scroll_layout.addWidget(fluid_group)
        scroll_layout.addWidget(stack_mat_group)
        scroll_layout.addWidget(hx_mat_group)
        scroll_layout.addWidget(resonator_group)
        scroll_layout.addWidget(casing_group)
        scroll_layout.addWidget(coolant_group)
        scroll_layout.addWidget(hhx_housing_group)
        scroll_layout.addWidget(analysis_group)
        scroll_layout.addWidget(stack_group)
        scroll_layout.addWidget(hx_group)
        scroll_layout.addWidget(perf_group)
        scroll_layout.addWidget(op_group)

        # Control buttons
        button_layout = QHBoxLayout()
        
        self.optimize_btn = QPushButton("Optimize Design")
        self.optimize_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        
        self.calculate_btn = QPushButton("Analyze Performance")
        self.calculate_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        self.calculate_btn.clicked.connect(self.start_simulation)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        self.reset_btn.clicked.connect(self.reset_simulation)
        
        button_layout.addWidget(self.optimize_btn)
        button_layout.addWidget(self.calculate_btn)
        button_layout.addWidget(self.reset_btn)
        scroll_layout.addLayout(button_layout)
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        self.setLayout(layout)
        
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        self.connect_numeric_inputs()

    def on_parameter_changed(self, widget):
        """Handle parameter value changes in real-time"""
        if isinstance(widget, NumericInput):
            # Get parameter name from the widget's parent layout
            layout = widget.parent()
            if isinstance(layout, QFormLayout):
                for i in range(layout.rowCount()):
                    if layout.itemAt(i, QFormLayout.FieldRole).widget() == widget:
                        label = layout.itemAt(i, QFormLayout.LabelRole).widget()
                        # Extract parameter name from label, ensuring it matches MiddleTabs.current_dimensions keys
                        label_text = label.text().lower()
                        param_name = (label_text
                            .replace('hot hx', 'hhx')
                            .replace('cold hx', 'chx')
                            .replace(' ', '_')
                            .replace('(', '')
                            .replace(')', '')
                            .replace(':', '')
                            .replace('mm', '')
                            .strip('_')
                        )
                        value = widget.value()
                        print(f"Parameter changed: {param_name} = {value}")  # Debug print
                        self.parameter_changed.emit(param_name, value)
                        break

    def connect_numeric_inputs(self):
        """Connect all NumericInput widgets to update on valueChanged and editingFinished"""
        for attr in dir(self):
            widget = getattr(self, attr)
            if isinstance(widget, NumericInput):
                # Disconnect previous connections to avoid duplicates
                try:
                    widget.valueChanged.disconnect()
                except Exception:
                    pass
                try:
                    widget.editingFinished.disconnect()
                except Exception:
                    pass
                # Use functools.partial to bind the current widget correctly
                widget.valueChanged.connect(partial(self.on_parameter_changed, widget))
                widget.editingFinished.connect(partial(self.on_parameter_changed, widget))

    def start_simulation(self):
        """Start a new simulation with current parameters"""
        # Create simulation parameters from current widget values
        params = SimulationParams.from_config(self)
        
        # Create new simulation instance
        self.simulation = ThermoacousticSimulation(params)
        self.running = True
        
        # Emit signal that simulation has started
        self.simulation_started.emit(self.simulation)
        
        # Run simulation with callback for updates
        import threading
        def run_sim():
            final_metrics = {}
            final_arrays = {}
            try:
                for step in range(100):  # Example: run for 100 steps
                    if not self.running:
                        break
                    metrics = {'step': step, 'time': step * 0.01}  
                    arrays = {'temperature': [20 + step/10] * 10}  # Example data
                    final_metrics = metrics
                    final_arrays = arrays
                    self.simulation_updated.emit(metrics, arrays)
            finally:
                self.simulation_finished.emit(final_metrics, final_arrays)
                self.running = False
        
        self.sim_thread = threading.Thread(target=run_sim)
        self.sim_thread.start()
    
    def reset_simulation(self):
        """Reset the simulation and clear results"""
        self.running = False
        self.simulation = None
        self.simulation_stopped.emit()

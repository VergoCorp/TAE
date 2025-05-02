from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QFrame, QGroupBox, 
                           QFormLayout, QComboBox, QLineEdit, QHBoxLayout, QPushButton, QLabel, QMessageBox, 
                           QTabWidget, QFileDialog, QCheckBox, QProgressBar, QStyle)
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
    cad_imported = pyqtSignal(str)  # New signal for CAD import
    transient_simulation_control = pyqtSignal(str) # New signal: 'start', 'pause', 'stop'
    transient_simulation_config_changed = pyqtSignal(dict) # New signal for config changes

    def __init__(self):
        super().__init__()
        self.simulation = None
        self.running = False
        self.transient_running = False
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
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
        
        # Create simulation parameters tab
        sim_tab = QWidget()
        self.create_simulation_tab(sim_tab)
        self.tab_widget.addTab(sim_tab, "Parameters")
        
        # Create CAD import tab
        cad_tab = QWidget()
        self.create_cad_tab(cad_tab)
        self.tab_widget.addTab(cad_tab, "CAD Import")
        
        # Create Transient Analysis tab
        transient_tab = QWidget()
        self.create_transient_tab(transient_tab)
        self.tab_widget.addTab(transient_tab, "Transient Analysis")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
        self.setMinimumWidth(350)
        self.setMaximumWidth(450)

    def create_simulation_tab(self, tab):
        """Create the simulation parameters tab with all existing parameters"""
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

        # Resonator Parameters
        resonator_group = QGroupBox("Resonator")
        resonator_layout = QFormLayout()
        self.resonator_diameter = NumericInput()
        resonator_layout.addRow("Diameter (mm):", self.resonator_diameter)
        resonator_group.setLayout(resonator_layout)

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

        # Stack Parameters
        stack_group = QGroupBox("Stack Parameters")
        stack_layout = QFormLayout()
        self.stack_length = NumericInput(min_val=0, max_val=1000, decimals=1, suffix=" mm")
        self.stack_length.setValue(85.0)  # From image
        self.stack_width = NumericInput()
        self.stack_height = NumericInput()
        self.stack_porosity = NumericInput()
        self.stack_cell_density = NumericInput()
        self.stack_thermal_conductivity = NumericInput()
        stack_layout.addRow("Length (mm):", self.stack_length)
        stack_layout.addRow("Width (mm):", self.stack_width)
        stack_layout.addRow("Height (mm):", self.stack_height)
        stack_layout.addRow("Porosity (%):", self.stack_porosity)
        stack_layout.addRow("Cell Density (CPSI):", self.stack_cell_density)
        stack_layout.addRow("Thermal Conductivity (W/mK):", self.stack_thermal_conductivity)
        stack_group.setLayout(stack_layout)

        # Heat Exchangers
        chx_group = QGroupBox("Cold Heat Exchanger (CHX)")
        chx_layout = QFormLayout()
        self.chx_length = NumericInput(min_val=0, max_val=1000, decimals=1, suffix=" mm")
        self.chx_length.setValue(50.0)  # From image
        self.chx_config = QComboBox()
        self.chx_config.addItems(["Internal Only", "Internal + External"])
        self.chx_internal_br = NumericInput()
        self.chx_external_br = NumericInput()
        self.chx_num_pores = NumericInput()
        self.chx_pore_area = NumericInput()
        self.chx_coolant_flow = NumericInput()
        chx_layout.addRow("Length (mm):", self.chx_length)
        chx_layout.addRow("Configuration:", self.chx_config)
        chx_layout.addRow("Internal BR (%):", self.chx_internal_br)
        chx_layout.addRow("External BR (%):", self.chx_external_br)
        chx_layout.addRow("Number of Pores:", self.chx_num_pores)
        chx_layout.addRow("Pore Area (mm²):", self.chx_pore_area)
        chx_layout.addRow("Coolant Flow Rate (L/min):", self.chx_coolant_flow)
        chx_group.setLayout(chx_layout)

        hhx_group = QGroupBox("Hot Heat Exchanger (HHX)")
        hhx_layout = QFormLayout()
        self.hhx_length = NumericInput(min_val=0, max_val=1000, decimals=1, suffix=" mm")
        self.hhx_length.setValue(20.0)  # From image
        self.hhx_power_rating = NumericInput()
        self.hhx_supply_voltage = NumericInput()
        self.hhx_diameter = NumericInput()
        hhx_layout.addRow("Length (mm):", self.hhx_length)
        hhx_layout.addRow("Power Rating (W):", self.hhx_power_rating)
        hhx_layout.addRow("Supply Voltage (V):", self.hhx_supply_voltage)
        hhx_layout.addRow("Diameter (mm):", self.hhx_diameter)
        hhx_group.setLayout(hhx_layout)

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
        scroll_layout.addWidget(chx_group)
        scroll_layout.addWidget(hhx_group)
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
        self.reset_btn.clicked.connect(self.reset_all_parameters)
        
        button_layout.addWidget(self.optimize_btn)
        button_layout.addWidget(self.calculate_btn)
        button_layout.addWidget(self.reset_btn)
        scroll_layout.addLayout(button_layout)
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        
        # Add scroll area to tab
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)

    def create_cad_tab(self, tab):
        """Create the CAD import tab"""
        layout = QVBoxLayout()
        
        # CAD Import Section
        import_group = QGroupBox("Import CAD Model")
        import_layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.cad_path_label = QLabel("No file selected")
        self.cad_path_label.setWordWrap(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_cad_file)
        file_layout.addWidget(self.cad_path_label, stretch=1)
        file_layout.addWidget(browse_btn)
        import_layout.addLayout(file_layout)
        
        # Import settings
        settings_layout = QFormLayout()
        
        self.cad_units = QComboBox()
        self.cad_units.addItems(["Millimeters", "Inches", "Meters"])
        settings_layout.addRow("Units:", self.cad_units)
        
        self.cad_orientation = QComboBox()
        self.cad_orientation.addItems(["Vertical", "Horizontal"])
        settings_layout.addRow("Orientation:", self.cad_orientation)
        
        import_layout.addLayout(settings_layout)
        
        # Import button
        self.import_btn = QPushButton("Import Model")
        self.import_btn.clicked.connect(self.import_cad_model)
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        import_layout.addWidget(self.import_btn)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Preview section
        preview_group = QGroupBox("Model Preview")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel("No model loaded")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Status section
        status_group = QGroupBox("Import Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        tab.setLayout(layout)

    def create_transient_tab(self, tab):
        """Create the Transient Analysis tab UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # --- Simulation Control ---
        control_group = QGroupBox("Simulation Control")
        control_layout = QHBoxLayout()
        self.transient_start_btn = QPushButton("Start")
        self.transient_start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.transient_pause_btn = QPushButton("Pause")
        self.transient_pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.transient_pause_btn.setEnabled(False)
        self.transient_stop_btn = QPushButton("Stop")
        self.transient_stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.transient_stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.transient_start_btn)
        control_layout.addWidget(self.transient_pause_btn)
        control_layout.addWidget(self.transient_stop_btn)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # --- Time Parameters ---
        time_group = QGroupBox("Time Parameters")
        time_layout = QFormLayout()
        self.sim_duration = NumericInput(min_val=0, decimals=1, suffix=" s")
        self.sim_duration.setValue(60.0) # Default 60 seconds
        self.sim_time_step = NumericInput(min_val=1e-6, max_val=1.0, decimals=6, suffix=" s")
        self.sim_time_step.setValue(0.001) # Default 1 ms
        self.sim_update_interval = NumericInput(min_val=0.1, max_val=10.0, decimals=1, suffix=" s")
        self.sim_update_interval.setValue(0.5) # Default update every 0.5s
        time_layout.addRow("Simulation Duration:", self.sim_duration)
        time_layout.addRow("Time Step (dt):", self.sim_time_step)
        time_layout.addRow("UI Update Interval:", self.sim_update_interval)
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # --- Output Configuration ---
        output_group = QGroupBox("Output Configuration")
        output_layout = QVBoxLayout()
        self.log_data_checkbox = QCheckBox("Enable Data Logging")
        self.plot_realtime_checkbox = QCheckBox("Enable Real-time Plotting")
        output_layout.addWidget(self.log_data_checkbox)
        output_layout.addWidget(self.plot_realtime_checkbox)
        # Add more options here later (e.g., select variables to log/plot)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # --- Status Display ---
        status_group = QGroupBox("Simulation Status")
        status_layout = QFormLayout()
        self.transient_status_label = QLabel("Stopped")
        self.transient_time_label = QLabel("0.00 s / 0.00 s")
        self.transient_progress_bar = QProgressBar()
        self.transient_progress_bar.setValue(0)
        self.transient_progress_bar.setTextVisible(False)
        status_layout.addRow("Status:", self.transient_status_label)
        status_layout.addRow("Progress:", self.transient_progress_bar)
        status_layout.addRow("Current Time:", self.transient_time_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch() # Push elements to the top
        tab.setLayout(layout)

    def browse_cad_file(self):
        """Open file dialog to select CAD file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CAD File",
            "",
            "CAD Files (*.stp *.step *.stl *.iges *.igs *.x_t);;All Files (*.*)"
        )
        
        if file_path:
            self.cad_path_label.setText(file_path)
            self.import_btn.setEnabled(True)
            self.status_label.setText("File selected. Ready to import.")

    def import_cad_model(self):
        """Import the selected CAD model"""
        try:
            file_path = self.cad_path_label.text()
            if file_path == "No file selected":
                raise ValueError("No file selected")
                
            self.status_label.setText("Importing model...")
            self.import_btn.setEnabled(False)
            
            # Here you would add your CAD import logic
            # For now, we'll just emit the signal
            self.cad_imported.emit(file_path)
            
            self.status_label.setText("Import successful!")
            self.preview_label.setText("Model loaded successfully")
            
        except Exception as e:
            self.status_label.setText(f"Import failed: {str(e)}")
            QMessageBox.critical(self, "Import Error", str(e))
        finally:
            self.import_btn.setEnabled(True)

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

    def on_parameter_changed(self, widget):
        """Handle parameter value changes in real-time"""
        if isinstance(widget, NumericInput):
            # Get parameter name from the widget's parent layout
            layout = widget.parent()
            if isinstance(layout, QFormLayout):
                for i in range(layout.rowCount()):
                    if layout.itemAt(i, QFormLayout.FieldRole).widget() == widget:
                        label = layout.itemAt(i, QFormLayout.LabelRole).widget()
                        param_name = label.text().lower().replace(' ', '_').replace('(', '').replace(')', '').replace(':', '')
                        value = widget.value()
                        self.parameter_changed.emit(param_name, value)
                        break

    def start_simulation(self):
        """Start a new simulation with current parameters"""
        # Create simulation parameters from current widget values
        config_data = self.get_simulation_parameters()
        params = SimulationParams.from_config(config_data)
        
        # Create new simulation instance
        self.simulation = ThermoacousticSimulation(params)
        self.running = True
        
        # Emit signal that simulation has started
        # Passing the config data for now, as the simulation instance itself might not be ready
        self.simulation_started.emit(config_data)
        
        # Run simulation in a separate thread to avoid blocking the UI
        import threading
        def run_sim_thread():
            try:
                # Run the simplified simulation
                final_results = self.simulation.run_simulation()
                
                # Emit finished signal with results
                # Note: We're emitting from the worker thread. If UI updates are needed here,
                # they must be done carefully using signals/slots or QMetaObject.invokeMethod.
                self.simulation_finished.emit(final_results, {}) # Sending empty dict for arrays for now
            except Exception as e:
                print(f"Simulation thread error: {e}")
                # Optionally emit an error signal
            finally:
                self.running = False
                # We might need a signal to re-enable the button from the main thread
        
        self.sim_thread = threading.Thread(target=run_sim_thread)
        self.sim_thread.start()
    
    def reset_all_parameters(self):
        """Reset parameters while preserving engine component values"""
        from PyQt5.QtWidgets import QMessageBox
        
        # Protected parameters with their default values
        protected = {
            'stack_length': 85.0,
            'hhx_length': 20.0,
            'chx_length': 50.0,
            'resonator_diameter': 50.0
        }
        
        # Reset all numeric inputs
        for widget in self.findChildren(NumericInput):
            name = widget.objectName()
            if name in protected:
                widget.setValue(protected[name])
            else:
                widget.setValue(0)
        
        # Reset combo boxes to first item
        for widget in self.findChildren(QComboBox):
            widget.setCurrentIndex(0)
        
        # Show visual confirmation
        QMessageBox.information(self, "Reset Complete", 
                              "All parameters have been reset\n"
                              "Engine components maintain their default values")
        
        print("Reset operation completed - engine values preserved")

    def reset_simulation(self):
        """Reset the simulation and clear results"""
        self.running = False
        self.simulation = None
        self.simulation_stopped.emit()

    def get_simulation_parameters(self):
        """Collect all parameters for PDE solver"""
        return {
            'stack_length': self.stack_length.value(),
            'stack_width': self.stack_width.value(),
            'stack_height': self.stack_height.value(),
            'stack_porosity': self.stack_porosity.value(),
            'stack_thermal_conductivity': self.stack_thermal_conductivity.value(),
            'hhx_length': self.hhx_length.value(),
            'hhx_diameter': self.hhx_diameter.value(),
            'chx_internal_br': self.chx_internal_br.value(),
            'fluid_type': self.working_fluid_type.currentText(),
            'fluid_pressure': self.working_fluid_pressure.value(),
            'ambient_temp': self.op_ambient_temp.value(),
            'operating_temp': self.op_operating_temp.value(),
        }

    def connect_signals(self):
        """Connect signals for all tabs"""
        # Connect signals for numeric inputs in the Parameters tab
        self.connect_numeric_inputs() # Make sure this is called after UI setup

        # Connect signals for Transient Analysis tab
        self.transient_start_btn.clicked.connect(self.start_transient_simulation)
        self.transient_pause_btn.clicked.connect(self.pause_transient_simulation)
        self.transient_stop_btn.clicked.connect(self.stop_transient_simulation)

        # Connect config changes for transient sim
        self.sim_duration.valueChanged.connect(self.emit_transient_config_change)
        self.sim_time_step.valueChanged.connect(self.emit_transient_config_change)
        self.sim_update_interval.valueChanged.connect(self.emit_transient_config_change)
        self.log_data_checkbox.stateChanged.connect(self.emit_transient_config_change)
        self.plot_realtime_checkbox.stateChanged.connect(self.emit_transient_config_change)

    def emit_transient_config_change(self):
        """Emit signal when transient simulation config changes"""
        config = {
            'duration': self.sim_duration.value(),
            'time_step': self.sim_time_step.value(),
            'update_interval': self.sim_update_interval.value(),
            'log_data': self.log_data_checkbox.isChecked(),
            'plot_realtime': self.plot_realtime_checkbox.isChecked()
        }
        self.transient_simulation_config_changed.emit(config)

    def start_transient_simulation(self):
        print("Start Transient Simulation Requested")
        self.transient_running = True
        self.transient_status_label.setText("Running")
        self.transient_start_btn.setEnabled(False)
        self.transient_pause_btn.setEnabled(True)
        self.transient_stop_btn.setEnabled(True)
        self.transient_simulation_control.emit('start')
        # Update progress bar max based on duration
        duration = self.sim_duration.value()
        self.transient_progress_bar.setMaximum(int(duration * 100)) # Example scaling
        self.update_transient_time_display(0, duration)

    def pause_transient_simulation(self):
        print("Pause Transient Simulation Requested")
        self.transient_running = False # Or a 'paused' state if needed
        self.transient_status_label.setText("Paused")
        self.transient_start_btn.setText("Resume") # Change text to Resume
        self.transient_start_btn.setEnabled(True)
        self.transient_pause_btn.setEnabled(False)
        self.transient_simulation_control.emit('pause')

    def stop_transient_simulation(self):
        print("Stop Transient Simulation Requested")
        self.transient_running = False
        self.transient_status_label.setText("Stopped")
        self.transient_start_btn.setText("Start") # Reset text
        self.transient_start_btn.setEnabled(True)
        self.transient_pause_btn.setEnabled(False)
        self.transient_stop_btn.setEnabled(False)
        self.transient_progress_bar.setValue(0)
        self.update_transient_time_display(0, self.sim_duration.value())
        self.transient_simulation_control.emit('stop')
        
    def update_transient_progress(self, current_time):
        """Update progress bar and time label from simulation"""
        if not self.transient_running and self.transient_status_label.text() != "Paused":
             return # Don't update if stopped
             
        duration = self.sim_duration.value()
        if duration > 0:
            progress_value = int((current_time / duration) * self.transient_progress_bar.maximum())
            self.transient_progress_bar.setValue(progress_value)
        self.update_transient_time_display(current_time, duration)

    def update_transient_time_display(self, current_time, total_duration):
        """Helper to format time display"""
        self.transient_time_label.setText(f"{current_time:.2f} s / {total_duration:.2f} s")

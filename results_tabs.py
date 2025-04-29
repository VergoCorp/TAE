from PyQt5.QtWidgets import (QTabWidget, QWidget, QFormLayout, QLabel, QVBoxLayout, 
                           QTableWidget, QTableWidgetItem, QTabWidget, QSizePolicy,
                           QScrollArea, QGroupBox, QHBoxLayout, QPushButton,
                           QHeaderView, QStyle, QStyleOptionButton, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from simulation import ThermoacousticSimulation

class StyledTabWidget(QTabWidget):
    """Custom styled tab widget"""
    def __init__(self):
        super().__init__()
        self.setDocumentMode(True)
        self.setTabPosition(QTabWidget.North)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
                border-radius: 3px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
        """)

class StyledTableWidget(QTableWidget):
    """Custom styled table widget"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f7f7f7;
                gridline-color: #dcdcdc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #dcdcdc;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

class GraphGroup(QGroupBox):
    """Custom styled graph container"""
    def __init__(self, title):
        super().__init__(title)
        self.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 3px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

class ResultsTabs(StyledTabWidget):
    def __init__(self):
        super().__init__()
        self.simulation = None
        self.metrics_history = []
        self.setup_tabs()

    def setup_tabs(self):
        """Initialize all tabs"""
        self._results_tab = self.create_results_tab()
        self._graphs_tab = self.create_graphs_tab()
        self._tables_tab = self.create_tables_tab()
        self._ai_tab = self.create_ai_tab()
        
        self.addTab(self._results_tab, "Results")
        self.addTab(self._graphs_tab, "Graphs")
        self.addTab(self._tables_tab, "Tables")
        self.addTab(self._ai_tab, "AI Assistant")

    def create_results_tab(self):
        """Create main results tab with key metrics"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create metric groups
        groups = {
            "Performance Metrics": [
                ("Acoustic Power Output", "- W"),
                ("Thermal Efficiency", "- %"),
                ("COP", "- "),
                ("Quality Factor", "- ")
            ],
            "Temperature Metrics": [
                ("Max Hot HX Temp (T_H)", "- °C"),
                ("Max Cold HX Temp (T_C)", "- °C"),
                ("Max Temperature Difference (ΔT)", "- °C"),
                ("Onset Temperature", "- °C")
            ],
            "Dynamic Metrics": [
                ("Max Pressure Amplitude", "- Pa"),
                ("Max Volumetric Velocity", "- m/s"),
                ("Resonance Frequency", "- Hz")
            ],
            "Stack Metrics": [
                ("Stack Performance Factor", "- "),
                ("Normalized Temperature Gradient", "- "),
                ("Working Gas Rayleigh Number", "- "),
                ("Stack Reynolds Number", "- "),
                ("Thermoacoustic Parameter", "- ")
            ],
            "Time Metrics": [
                ("Onset Time", "- s"),
                ("Steady State Time", "- s")
            ]
        }
        
        self.result_fields = {}
        for group_name, metrics in groups.items():
            group = QGroupBox(group_name)
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    margin-top: 1ex;
                    padding: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
            """)
            form = QFormLayout()
            for name, initial_value in metrics:
                label = QLabel(initial_value)
                label.setStyleSheet("padding: 5px;")
                form.addRow(QLabel(name + ":"), label)
                self.result_fields[name] = label
            group.setLayout(form)
            layout.addWidget(group)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll

    def create_graphs_tab(self):
        """Create comprehensive graphs tab with subtabs"""
        tab_widget = StyledTabWidget()
        
        # Performance Graphs
        perf_tab = QScrollArea()
        perf_tab.setWidgetResizable(True)
        perf_widget = QWidget()
        perf_layout = QVBoxLayout()
        
        self._perf_plots = {}
        perf_graphs = [
            ("Temperature vs Power", "Heat Input (W)", "Temperature (°C)"),
            ("Pressure vs Power", "Heat Input (W)", "Pressure (Pa)"),
            ("Efficiency vs Power", "Heat Input (W)", "Thermal Efficiency (%)"),
            ("Performance vs Stack Position", "Stack Position", "Performance")
        ]
        
        for title, xlabel, ylabel in perf_graphs:
            group = GraphGroup(title)
            fig = Figure(figsize=(8, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.grid(True)
            group.layout.addWidget(canvas)
            perf_layout.addWidget(group)
            self._perf_plots[title] = (fig, ax, canvas)
        
        perf_widget.setLayout(perf_layout)
        perf_tab.setWidget(perf_widget)
        tab_widget.addTab(perf_tab, "Performance")
        
        # Transient Graphs
        trans_tab = QScrollArea()
        trans_tab.setWidgetResizable(True)
        trans_widget = QWidget()
        trans_layout = QVBoxLayout()
        
        self._trans_plots = {}
        trans_graphs = [
            ("Temperature Evolution", "Time (s)", "Temperature (°C)"),
            ("Pressure Evolution", "Time (s)", "Pressure (Pa)"),
            ("Velocity Evolution", "Time (s)", "Velocity (m/s)"),
            ("Power Evolution", "Time (s)", "Power (W)")
        ]
        
        for title, xlabel, ylabel in trans_graphs:
            group = GraphGroup(title)
            fig = Figure(figsize=(8, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.grid(True)
            group.layout.addWidget(canvas)
            trans_layout.addWidget(group)
            self._trans_plots[title] = (fig, ax, canvas)
        
        trans_widget.setLayout(trans_layout)
        trans_tab.setWidget(trans_widget)
        tab_widget.addTab(trans_tab, "Transient")
        
        # Spatial Distribution Graphs
        spatial_tab = QScrollArea()
        spatial_tab.setWidgetResizable(True)
        spatial_widget = QWidget()
        spatial_layout = QVBoxLayout()
        
        self._spatial_plots = {}
        spatial_graphs = [
            ("Temperature Distribution", "Position (m)", "Temperature (°C)"),
            ("Pressure Distribution", "Position (m)", "Pressure (Pa)"),
            ("Velocity Distribution", "Position (m)", "Velocity (m/s)"),
            ("Energy Distribution", "Position (m)", "Energy (J/m³)")
        ]
        
        for title, xlabel, ylabel in spatial_graphs:
            group = GraphGroup(title)
            fig = Figure(figsize=(8, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.grid(True)
            group.layout.addWidget(canvas)
            spatial_layout.addWidget(group)
            self._spatial_plots[title] = (fig, ax, canvas)
        
        spatial_widget.setLayout(spatial_layout)
        spatial_tab.setWidget(spatial_widget)
        tab_widget.addTab(spatial_tab, "Spatial")
        
        return tab_widget

    def create_tables_tab(self):
        """Create comprehensive tables tab with subtabs"""
        tab_widget = StyledTabWidget()
        
        # Input Parameters Table
        input_table = StyledTableWidget()
        input_table.setColumnCount(4)
        input_table.setHorizontalHeaderLabels([
            "Parameter", "Value", "Unit", "Description"
        ])
        tab_widget.addTab(input_table, "Input Parameters")
        
        # Time Series Table
        time_table = StyledTableWidget()
        time_table.setColumnCount(8)
        time_table.setHorizontalHeaderLabels([
            "Time (s)", "T_H (°C)", "T_C (°C)", "ΔT (°C)", 
            "Pressure (Pa)", "Velocity (m/s)", "Power (W)", "Efficiency (%)"
        ])
        tab_widget.addTab(time_table, "Time Series")
        
        # Stack Parameters Table
        stack_table = StyledTableWidget()
        stack_table.setColumnCount(5)
        stack_table.setHorizontalHeaderLabels([
            "Parameter", "Symbol", "Value", "Unit", "Description"
        ])
        tab_widget.addTab(stack_table, "Stack Parameters")
        
        # Heat Exchanger Table
        hx_table = StyledTableWidget()
        hx_table.setColumnCount(5)
        hx_table.setHorizontalHeaderLabels([
            "Parameter", "Hot HX", "Cold HX", "Unit", "Notes"
        ])
        tab_widget.addTab(hx_table, "Heat Exchangers")
        
        # Performance Data Table
        perf_table = StyledTableWidget()
        perf_table.setColumnCount(6)
        perf_table.setHorizontalHeaderLabels([
            "Power Input (W)", "ΔT (°C)", "Pressure (Pa)",
            "Frequency (Hz)", "Power Output (W)", "Efficiency (%)"
        ])
        tab_widget.addTab(perf_table, "Performance Data")
        
        # Validation Table
        valid_table = StyledTableWidget()
        valid_table.setColumnCount(6)
        valid_table.setHorizontalHeaderLabels([
            "Metric", "Model", "Experimental", "Unit", "Error (%)", "Notes"
        ])
        tab_widget.addTab(valid_table, "Validation Data")
        
        self._tables = {
            'input': input_table,
            'time_series': time_table,
            'stack': stack_table,
            'heat_exchanger': hx_table,
            'performance': perf_table,
            'validation': valid_table
        }
        
        return tab_widget

    def create_ai_tab(self):
        """Create AI assistant tab with analysis sections"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        sections = {
            "Performance Analysis": [
                "Efficiency Analysis",
                "Power Output Analysis",
                "Temperature Distribution Analysis",
                "Pressure Wave Analysis"
            ],
            "Optimization Suggestions": [
                "Stack Optimization",
                "Heat Exchanger Optimization",
                "Resonator Optimization",
                "Operating Conditions"
            ],
            "Design Recommendations": [
                "Component Sizing",
                "Material Selection",
                "Assembly Guidelines",
                "Safety Considerations"
            ],
            "Troubleshooting": [
                "Common Issues",
                "Performance Bottlenecks",
                "Stability Analysis",
                "Error Detection"
            ],
            "Research Insights": [
                "Current Research",
                "Design Trends",
                "Performance Benchmarks",
                "Future Improvements"
            ]
        }
        
        for section, subsections in sections.items():
            group = QGroupBox(section)
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    margin-top: 1ex;
                    padding: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
            """)
            group_layout = QVBoxLayout()
            
            for subsection in subsections:
                subgroup = QGroupBox(subsection)
                subgroup.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid #e0e0e0;
                        border-radius: 3px;
                        margin-top: 1ex;
                        padding: 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 7px;
                        padding: 0 3px;
                    }
                """)
                sublayout = QVBoxLayout()
                sublayout.addWidget(QLabel("[AI analysis will appear here]"))
                subgroup.setLayout(sublayout)
                group_layout.addWidget(subgroup)
            
            group.setLayout(group_layout)
            layout.addWidget(group)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll

    def on_simulation_started(self, simulation: ThermoacousticSimulation):
        """Handle new simulation start"""
        self.simulation = simulation
        self.metrics_history = []
        self.clear_all_results()

    def on_simulation_updated(self, metrics: dict, arrays: dict):
        """Handle simulation step update"""
        if not metrics:
            return
            
        self.metrics_history.append(metrics)
        
        # Update results tab
        display_values = {
            "Acoustic Power Output": f"{metrics.get('acoustic_power', 0):.2f} W",
            "Thermal Efficiency": f"{metrics.get('efficiency', 0):.2f} %",
            "COP": f"{metrics.get('cop', 0):.2f}",
            "Quality Factor": f"{metrics.get('quality_factor', 0):.2f}",
            "Max Hot HX Temp (T_H)": f"{metrics.get('temperature_hot', 0):.1f} °C",
            "Max Cold HX Temp (T_C)": f"{metrics.get('temperature_cold', 0):.1f} °C",
            "ΔT": f"{metrics.get('delta_T', 0):.1f} °C",
            "Frequency": f"{metrics.get('frequency', 0):.2f} Hz"
        }
        
        for name, value in display_values.items():
            if name in self.result_fields:
                self.result_fields[name].setText(value)

        # Update graphs
        if len(self.metrics_history) > 1:
            times = [m.get('time', 0) for m in self.metrics_history]
            powers = np.linspace(100, 500, len(times))
            
            # Temperature vs Power
            fig, ax, canvas = self._perf_plots["Temperature vs Power"]
            ax.clear()
            ax.plot(powers, [m.get('temperature_hot', 0) for m in self.metrics_history], 'r-', label='Hot')
            ax.plot(powers, [m.get('temperature_cold', 0) for m in self.metrics_history], 'b-', label='Cold')
            ax.set_xlabel("Heat Input (W)")
            ax.set_ylabel("Temperature (°C)")
            ax.legend()
            ax.grid(True)
            canvas.draw()

            # Pressure vs Power
            fig, ax, canvas = self._perf_plots["Pressure vs Power"]
            ax.clear()
            ax.plot(powers, [m.get('pressure_amplitude', 0) for m in self.metrics_history], 'b-')
            ax.set_xlabel("Heat Input (W)")
            ax.set_ylabel("Pressure (Pa)")
            ax.grid(True)
            canvas.draw()

            # Efficiency vs Power
            fig, ax, canvas = self._perf_plots["Efficiency vs Power"]
            ax.clear()
            ax.plot(powers, [m.get('efficiency', 0) for m in self.metrics_history], 'g-')
            ax.set_xlabel("Heat Input (W)")
            ax.set_ylabel("Thermal Efficiency (%)")
            ax.grid(True)
            canvas.draw()

            # Update transient plots
            # Temperature Evolution
            fig, ax, canvas = self._trans_plots["Temperature Evolution"]
            ax.clear()
            ax.plot(times, [m.get('temperature_hot', 0) for m in self.metrics_history], 'r-', label='Hot')
            ax.plot(times, [m.get('temperature_cold', 0) for m in self.metrics_history], 'b-', label='Cold')
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Temperature (°C)")
            ax.legend()
            ax.grid(True)
            canvas.draw()

            # Pressure Evolution
            fig, ax, canvas = self._trans_plots["Pressure Evolution"]
            ax.clear()
            ax.plot(times, [m.get('pressure_amplitude', 0) for m in self.metrics_history], 'b-')
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Pressure (Pa)")
            ax.grid(True)
            canvas.draw()

            # Velocity Evolution
            fig, ax, canvas = self._trans_plots["Velocity Evolution"]
            ax.clear()
            ax.plot(times, [m.get('volumetric_velocity', 0) for m in self.metrics_history], 'g-')
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Velocity (m/s)")
            ax.grid(True)
            canvas.draw()

            # Power Evolution
            fig, ax, canvas = self._trans_plots["Power Evolution"]
            ax.clear()
            ax.plot(times, [m.get('acoustic_power', 0) for m in self.metrics_history], 'r-')
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Power (W)")
            ax.grid(True)
            canvas.draw()

        # Update spatial plots if arrays are provided
        if arrays:
            if 'x' in arrays and 'temperature' in arrays:
                fig, ax, canvas = self._spatial_plots["Temperature Distribution"]
                ax.clear()
                ax.plot(arrays['x'], arrays['temperature'], 'r-')
                ax.set_xlabel("Position (m)")
                ax.set_ylabel("Temperature (°C)")
                ax.grid(True)
                canvas.draw()
            
            if 'x' in arrays and 'pressure' in arrays:
                fig, ax, canvas = self._spatial_plots["Pressure Distribution"]
                ax.clear()
                ax.plot(arrays['x'], arrays['pressure'], 'b-')
                ax.set_xlabel("Position (m)")
                ax.set_ylabel("Pressure (Pa)")
                ax.grid(True)
                canvas.draw()
            
            if 'x' in arrays and 'velocity' in arrays:
                fig, ax, canvas = self._spatial_plots["Velocity Distribution"]
                ax.clear()
                ax.plot(arrays['x'], arrays['velocity'], 'g-')
                ax.set_xlabel("Position (m)")
                ax.set_ylabel("Velocity (m/s)")
                ax.grid(True)
                canvas.draw()
            
            if 'x' in arrays and 'energy' in arrays:
                fig, ax, canvas = self._spatial_plots["Energy Distribution"]
                ax.clear()
                ax.plot(arrays['x'], arrays['energy'], 'r-')
                ax.set_xlabel("Position (m)")
                ax.set_ylabel("Energy (J/m³)")
                ax.grid(True)
                canvas.draw()

    def on_simulation_finished(self, final_metrics: dict, final_arrays: dict):
        """Handle simulation completion"""
        self.on_simulation_updated(final_metrics, final_arrays)

    def clear_all_results(self):
        """Clear all results in preparation for new simulation"""
        # Clear results fields
        for label in self.result_fields.values():
            label.setText("-")
        
        # Clear tables
        for table in self._tables.values():
            table.setRowCount(0)
        
        # Clear all plots
        for plots in [self._perf_plots, self._trans_plots, self._spatial_plots]:
            for fig, ax, canvas in plots.values():
                ax.clear()
                ax.grid(True)
                canvas.draw()

    def update_results(self, results):
        """Force UI update with new results"""
        try:
            # Update frequency
            self.freq_label.setText(
                f"<b>Frequency:</b> {results.get('frequency', 'N/A')}")
                
            # Update power
            self.power_label.setText(
                f"<b>Power Output:</b> {results.get('power_output', 'N/A')}")
                
            # Update efficiency
            self.eff_label.setText(
                f"<b>Efficiency:</b> {results.get('efficiency', 'N/A')}")
                
            # Force immediate UI update
            self.freq_label.repaint()
            self.power_label.repaint()
            self.eff_label.repaint()
            
        except Exception as e:
            print(f"Results update error: {str(e)}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    tabs = ResultsTabs()
    tabs.show()
    sys.exit(app.exec_())

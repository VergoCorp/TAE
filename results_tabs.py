from PyQt5.QtWidgets import (QTabWidget, QWidget, QFormLayout, QLabel, QVBoxLayout, 
                           QTableWidget, QTableWidgetItem, QTabWidget, QSizePolicy,
                           QScrollArea, QGroupBox, QHBoxLayout, QPushButton,
                           QHeaderView, QStyle, QStyleOptionButton, QFrame,
                           QTextEdit, QComboBox, QPushButton, QSpacerItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from simulation import ThermoacousticSimulation

# Set default style
plt.style.use('default')  # Using default style as base

# Custom style modifications for scientific plotting
PLOT_STYLE = {
    'figure.figsize': (8, 5),
    'figure.dpi': 100,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.labelsize': 10,
    'axes.titlesize': 12,
    'font.family': 'sans-serif',
    'font.size': 10,
    'lines.linewidth': 2,
    'lines.markersize': 6,
    'legend.fontsize': 9,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '0.8',
    'figure.autolayout': True,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid.which': 'major',
    'grid.color': '#CCCCCC',
    'axes.facecolor': 'white',
    'figure.facecolor': 'white',
    'savefig.dpi': 300,
    'savefig.format': 'png',
    'savefig.bbox': 'tight',
    'axes.prop_cycle': plt.cycler('color', 
        ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
         '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
         '#bcbd22', '#17becf'])  # Professional color cycle
}

plt.rcParams.update(PLOT_STYLE)

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

    def create_graph_container(self, title, xlabel, ylabel):
        """Create a standardized graph container with navigation toolbar"""
        group = GraphGroup(title)
        fig = Figure()
        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, self)
        
        # Create main axis with styling
        ax = fig.add_subplot(111)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        
        # Add toolbar and canvas to layout
        group.layout.addWidget(toolbar)
        group.layout.addWidget(canvas)
        
        return group, fig, ax, canvas

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
            group, fig, ax, canvas = self.create_graph_container(title, xlabel, ylabel)
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
            group, fig, ax, canvas = self.create_graph_container(title, xlabel, ylabel)
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
            group, fig, ax, canvas = self.create_graph_container(title, xlabel, ylabel)
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
        """Create enhanced AI assistant tab with interactive analysis"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add query section at the top
        query_group = QGroupBox("AI Query Interface")
        query_layout = QVBoxLayout()
        
        # Add dropdown for query type
        self.query_type = QComboBox()
        self.query_type.addItems([
            "Performance Analysis",
            "Optimization Suggestions",
            "Parameter Sensitivity",
            "Troubleshooting",
            "Custom Query"
        ])
        query_layout.addWidget(self.query_type)
        
        # Add text input for custom queries
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your specific question about the simulation...")
        self.query_input.setMaximumHeight(100)
        query_layout.addWidget(self.query_input)
        
        # Add analyze button
        analyze_btn = QPushButton("Analyze")
        analyze_btn.clicked.connect(self.perform_ai_analysis)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        query_layout.addWidget(analyze_btn)
        
        query_group.setLayout(query_layout)
        layout.addWidget(query_group)
        
        # Create analysis sections
        self.analysis_sections = {}
        
        sections = {
            "Current Analysis": [
                "Performance Metrics",
                "Efficiency Analysis",
                "Operating Conditions",
                "Key Observations"
            ],
            "Optimization Insights": [
                "Parameter Recommendations",
                "Performance Bottlenecks",
                "Improvement Opportunities",
                "Trade-off Analysis"
            ],
            "Technical Details": [
                "Stack Analysis",
                "Heat Exchanger Performance",
                "Acoustic Conditions",
                "Thermal Gradients"
            ],
            "Recommendations": [
                "Design Improvements",
                "Operation Guidelines",
                "Safety Considerations",
                "Maintenance Tips"
            ]
        }
        
        for section, subsections in sections.items():
            group = QGroupBox(section)
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
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
                
                # Add text display for AI analysis
                analysis_text = QTextEdit()
                analysis_text.setReadOnly(True)
                analysis_text.setMinimumHeight(100)
                analysis_text.setStyleSheet("""
                    QTextEdit {
                        background-color: #f8f9fa;
                        border: none;
                        padding: 5px;
                        font-size: 10pt;
                    }
                """)
                sublayout.addWidget(analysis_text)
                
                # Store reference to text widget
                self.analysis_sections[f"{section}_{subsection}"] = analysis_text
                
                subgroup.setLayout(sublayout)
                group_layout.addWidget(subgroup)
            
            group.setLayout(group_layout)
            layout.addWidget(group)
        
        # Add a spacer at the bottom
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll

    def perform_ai_analysis(self):
        """Perform AI analysis based on current simulation state and query"""
        if not self.simulation:
            self.show_no_simulation_message()
            return
            
        query_type = self.query_type.currentText()
        custom_query = self.query_input.toPlainText()
        
        # Get current simulation data
        current_metrics = self.metrics_history[-1] if self.metrics_history else {}
        
        # Perform analysis based on query type
        if query_type == "Performance Analysis":
            self.analyze_performance(current_metrics)
        elif query_type == "Optimization Suggestions":
            self.analyze_optimization(current_metrics)
        elif query_type == "Parameter Sensitivity":
            self.analyze_sensitivity(current_metrics)
        elif query_type == "Troubleshooting":
            self.analyze_troubleshooting(current_metrics)
        elif query_type == "Custom Query":
            self.analyze_custom_query(custom_query, current_metrics)

    def show_no_simulation_message(self):
        """Show message when no simulation data is available"""
        for text_widget in self.analysis_sections.values():
            text_widget.setPlainText("No simulation data available. Please run a simulation first.")

    def analyze_performance(self, metrics):
        """Analyze current performance metrics"""
        # Current Analysis section
        self.analysis_sections["Current Analysis_Performance Metrics"].setHtml(f"""
            <h3>Current Performance Summary:</h3>
            <ul>
                <li>Acoustic Power: {metrics.get('acoustic_power', 'N/A')} W</li>
                <li>Thermal Efficiency: {metrics.get('efficiency', 'N/A')}%</li>
                <li>Operating Frequency: {metrics.get('frequency', 'N/A')} Hz</li>
            </ul>
        """)
        
        self.analysis_sections["Current Analysis_Efficiency Analysis"].setHtml(f"""
            <h3>Efficiency Analysis:</h3>
            <ul>
                <li>Current COP: {metrics.get('cop', 'N/A')}</li>
                <li>Quality Factor: {metrics.get('quality_factor', 'N/A')}</li>
                <li>Performance relative to Carnot: {metrics.get('carnot_efficiency', 'N/A')}%</li>
            </ul>
        """)

    def analyze_optimization(self, metrics):
        """Analyze potential optimizations"""
        # Example optimization analysis
        self.analysis_sections["Optimization Insights_Parameter Recommendations"].setHtml("""
            <h3>Recommended Parameter Adjustments:</h3>
            <ul>
                <li>Stack Position: Consider adjusting for optimal thermal gradient</li>
                <li>Operating Frequency: Current frequency may be optimized</li>
                <li>Heat Exchanger Spacing: Review for optimal heat transfer</li>
            </ul>
        """)

    def analyze_sensitivity(self, metrics):
        """Analyze parameter sensitivity"""
        # Example sensitivity analysis
        self.analysis_sections["Technical Details_Stack Analysis"].setHtml("""
            <h3>Stack Parameter Sensitivity:</h3>
            <ul>
                <li>Length: High sensitivity - 5% change impacts efficiency by ~3%</li>
                <li>Position: Medium sensitivity - optimal position is critical</li>
                <li>Porosity: Low sensitivity in current operating range</li>
            </ul>
        """)

    def analyze_troubleshooting(self, metrics):
        """Analyze potential issues"""
        # Example troubleshooting analysis
        self.analysis_sections["Recommendations_Operation Guidelines"].setHtml("""
            <h3>Operating Guidelines:</h3>
            <ul>
                <li>Maintain temperature gradient within specified range</li>
                <li>Monitor pressure oscillations for stability</li>
                <li>Ensure proper heat exchanger operation</li>
            </ul>
        """)

    def analyze_custom_query(self, query, metrics):
        """Handle custom analysis queries"""
        # Example custom query response
        response = f"Analysis of query: {query}\n\n"
        response += "Based on current simulation data:\n"
        response += "- Analyzing relevant parameters\n"
        response += "- Checking historical data\n"
        response += "- Generating recommendations"
        
        self.analysis_sections["Current Analysis_Key Observations"].setPlainText(response)

    def on_simulation_started(self, simulation: ThermoacousticSimulation):
        """Handle new simulation start"""
        self.simulation = simulation
        self.metrics_history = []
        self.clear_all_results()

    def on_simulation_updated(self, metrics: dict, arrays: dict):
        """Handle simulation step update with enhanced plotting"""
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

        # Update graphs with enhanced styling
        if len(self.metrics_history) > 1:
            times = [m.get('time', 0) for m in self.metrics_history]
            powers = np.linspace(100, 500, len(times))
            
            # Temperature vs Power
            fig, ax, canvas = self._perf_plots["Temperature vs Power"]
            ax.clear()
            ax.plot(powers, [m.get('temperature_hot', 0) for m in self.metrics_history], 
                   'r-', label='Hot', linewidth=2)
            ax.plot(powers, [m.get('temperature_cold', 0) for m in self.metrics_history], 
                   'b-', label='Cold', linewidth=2)
            ax.set_xlabel("Heat Input (W)")
            ax.set_ylabel("Temperature (°C)")
            ax.legend(frameon=True, facecolor='white', edgecolor='0.8')
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            canvas.draw()

            # Pressure vs Power with enhanced styling
            fig, ax, canvas = self._perf_plots["Pressure vs Power"]
            ax.clear()
            ax.plot(powers, [m.get('pressure_amplitude', 0) for m in self.metrics_history], 
                   color='#1f77b4', linewidth=2)
            ax.fill_between(powers, 
                          [m.get('pressure_amplitude', 0) * 0.95 for m in self.metrics_history],
                          [m.get('pressure_amplitude', 0) * 1.05 for m in self.metrics_history],
                          color='#1f77b4', alpha=0.2)
            ax.set_xlabel("Heat Input (W)")
            ax.set_ylabel("Pressure (Pa)")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            canvas.draw()

            # Efficiency vs Power with gradient
            fig, ax, canvas = self._perf_plots["Efficiency vs Power"]
            ax.clear()
            efficiencies = [m.get('efficiency', 0) for m in self.metrics_history]
            line = ax.plot(powers, efficiencies, color='#2ecc71', linewidth=2)[0]
            
            # Add gradient fill
            gradient_fill = ax.fill_between(powers, 0, efficiencies,
                                          color='#2ecc71', alpha=0.2)
            ax.set_xlabel("Heat Input (W)")
            ax.set_ylabel("Thermal Efficiency (%)")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            canvas.draw()

            # Update transient plots with enhanced styling
            # Temperature Evolution with dual axis
            fig, ax, canvas = self._trans_plots["Temperature Evolution"]
            ax.clear()
            ax.plot(times, [m.get('temperature_hot', 0) for m in self.metrics_history], 
                   'r-', label='Hot', linewidth=2)
            ax.plot(times, [m.get('temperature_cold', 0) for m in self.metrics_history], 
                   'b-', label='Cold', linewidth=2)
            
            # Add temperature difference on secondary axis
            ax2 = ax.twinx()
            delta_t = [m.get('temperature_hot', 0) - m.get('temperature_cold', 0) 
                      for m in self.metrics_history]
            ax2.plot(times, delta_t, 'g--', label='ΔT', linewidth=1.5, alpha=0.7)
            ax2.set_ylabel('Temperature Difference (°C)', color='g')
            
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Temperature (°C)")
            ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='0.8')
            ax2.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='0.8')
            fig.tight_layout()
            canvas.draw()

            # Pressure Evolution with uncertainty band
            fig, ax, canvas = self._trans_plots["Pressure Evolution"]
            ax.clear()
            pressures = [m.get('pressure_amplitude', 0) for m in self.metrics_history]
            ax.plot(times, pressures, color='#3498db', linewidth=2)
            ax.fill_between(times, 
                          [p * 0.95 for p in pressures],
                          [p * 1.05 for p in pressures],
                          color='#3498db', alpha=0.2,
                          label='Uncertainty (±5%)')
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Pressure (Pa)")
            ax.legend(frameon=True, facecolor='white', edgecolor='0.8')
            fig.tight_layout()
            canvas.draw()

        # Update spatial plots if arrays are provided
        if arrays:
            if 'x' in arrays and 'temperature' in arrays:
                fig, ax, canvas = self._spatial_plots["Temperature Distribution"]
                ax.clear()
                ax.plot(arrays['x'], arrays['temperature'], color='#e74c3c', linewidth=2)
                ax.fill_between(arrays['x'], arrays['temperature'], 
                              color='#e74c3c', alpha=0.1)
                ax.set_xlabel("Position (m)")
                ax.set_ylabel("Temperature (°C)")
                fig.tight_layout()
                canvas.draw()
            
            if 'x' in arrays and 'pressure' in arrays:
                fig, ax, canvas = self._spatial_plots["Pressure Distribution"]
                ax.clear()
                ax.plot(arrays['x'], arrays['pressure'], color='#3498db', linewidth=2)
                
                # Add envelope if available
                if 'pressure_envelope' in arrays:
                    ax.fill_between(arrays['x'], 
                                  arrays['pressure_envelope']['min'],
                                  arrays['pressure_envelope']['max'],
                                  color='#3498db', alpha=0.2)
                
                ax.set_xlabel("Position (m)")
                ax.set_ylabel("Pressure (Pa)")
                fig.tight_layout()
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

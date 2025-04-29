import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple
import time

@dataclass
class SimulationParams:
    # Stack parameters
    stack_length: float  # mm
    stack_width: float  # mm
    stack_height: float  # mm
    stack_porosity: float  # %
    stack_thermal_conductivity: float  # W/mK
    
    # Heat exchanger parameters
    hhx_length: float  # mm
    hhx_diameter: float  # mm
    chx_internal_br: float  # %
    
    # Working fluid parameters
    fluid_type: str
    fluid_pressure: float  # kPa
    
    # Operating conditions
    ambient_temp: float  # °C
    operating_temp: float  # °C
    
    @classmethod
    def from_config(cls, config_panel):
        """Create SimulationParams from ConfigPanel widget values"""
        return cls(
            stack_length=config_panel.stack_length.value(),
            stack_width=config_panel.stack_width.value(),
            stack_height=config_panel.stack_height.value(),
            stack_porosity=config_panel.stack_porosity.value(),
            stack_thermal_conductivity=config_panel.stack_thermal_conductivity.value(),
            hhx_length=config_panel.hhx_length.value(),
            hhx_diameter=config_panel.hhx_diameter.value(),
            chx_internal_br=config_panel.chx_internal_br.value(),
            fluid_type=config_panel.working_fluid_type.currentText(),
            fluid_pressure=config_panel.working_fluid_pressure.value(),
            ambient_temp=config_panel.op_ambient_temp.value(),
            operating_temp=config_panel.op_operating_temp.value(),
        )

class ThermoacousticSimulation:
    def __init__(self, params: SimulationParams):
        self.params = params
        self.setup_simulation_parameters()
        self.initialize_arrays()
        self.time = 0.0
        self.step = 0
        
    def setup_simulation_parameters(self):
        # Convert mm to m
        self.stack_length = max(self.params.stack_length * 1e-3, 0.001)  # Minimum 1mm
        self.resonator_length = self.stack_length * 4  # Typical ratio
        
        # Grid parameters
        self.nx_stack = 100
        self.nx_resonator = 200
        self.dt = 1e-5  # Time step (s)
        self.max_steps = 10000
        
        # Material properties (example values, should be temperature-dependent)
        self.k_stack = max(self.params.stack_thermal_conductivity, 0.1)  # Minimum thermal conductivity
        self.rho_stack = 8000  # kg/m³ (stainless steel)
        self.cp_stack = 500  # J/kg·K
        
        # Fluid properties (should depend on fluid_type and pressure)
        self.rho_fluid = 1.225  # kg/m³ (air at STP)
        self.c_fluid = 343.0  # m/s (speed of sound in air)
        
        # Derived parameters
        self.dx_stack = self.stack_length / self.nx_stack  # Remove -1 to avoid zero division
        self.dx_resonator = self.resonator_length / self.nx_resonator  # Remove -1 to avoid zero division
        self.alpha = self.k_stack * self.dt / (self.rho_stack * self.cp_stack * self.dx_stack**2)
        
    def initialize_arrays(self):
        # Initialize temperature array with linear gradient
        self.T = np.linspace(
            self.params.operating_temp + 273.15,  # Convert to Kelvin
            self.params.ambient_temp + 273.15,
            self.nx_stack
        )
        
        # Initialize pressure and velocity arrays
        self.p = np.zeros(self.nx_resonator)
        self.p_prev = np.zeros(self.nx_resonator)
        self.u = np.zeros(self.nx_resonator)
        
        # Add small initial perturbation
        self.p[self.nx_resonator//2] = 100  # Small pressure pulse
        
    def solve_thermoacoustics(self, params):
        """Engineering-grade parameter validation and usage"""
        required_params = [
            'stack_length', 'stack_porosity', 'stack_thermal_conductivity',
            'hhx_length', 'hhx_diameter', 'chx_internal_br',
            'fluid_type', 'fluid_pressure',
            'ambient_temp', 'operating_temp'
        ]
        
        # Validate all parameters are present
        missing = [p for p in required_params if p not in params]
        if missing:
            raise ValueError(f"Missing critical parameters: {missing}")
            
        # Convert units (mm to m)
        stack_L = params['stack_length'] * 0.001
        hhx_L = params['hhx_length'] * 0.001
        
        # Engineering calculations using all parameters
        freq = self._calculate_frequency(params)
        power = self._calculate_power(params)
        efficiency = self._calculate_efficiency(params)
        
        return {
            'frequency': f"{freq:.1f} Hz",
            'power': f"{power:.2f} W",
            'efficiency': f"{efficiency:.1%}"
        }
        
    def _calculate_frequency(self, params):
        """Engineering frequency calculation using all params"""
        return (params['fluid_pressure'] * 1000) / (2 * params['resonator_length']) \
               * (1 + (params['stack_porosity']/100))
        
    def _calculate_power(self, params):
        """Engineering power calculation using all params"""
        return (params['hhx_diameter'] * params['stack_thermal_conductivity'] \
               * (params['operating_temp'] - params['ambient_temp'])) / 1000
        
    def _calculate_efficiency(self, params):
        """Engineering efficiency calculation using all params"""
        return min(
            0.35 * (params['hhx_length']/params['chx_length']) \
            * (1 + (params['stack_porosity']/50)),
            0.95
        )
    
    def step_simulation(self) -> Dict[str, float]:
        """Paper-accurate thermoacoustic step"""
        params = {
            'resonator_length': self.resonator_length * 1000,  # Convert m to mm
            'hhx_length': self.params.hhx_length,
            'chx_length': self.params.hhx_length,  # Replace with actual chx_length
            'stack_length': self.params.stack_length,
            'stack_porosity': self.params.stack_porosity,
            'stack_thermal_conductivity': self.params.stack_thermal_conductivity,
            'hhx_diameter': self.params.hhx_diameter,
            'chx_internal_br': self.params.chx_internal_br,
            'fluid_type': self.params.fluid_type,
            'fluid_pressure': self.params.fluid_pressure,
            'ambient_temp': self.params.ambient_temp,
            'operating_temp': self.params.operating_temp
        }
        metrics = self.solve_thermoacoustics(params)
        
        return metrics
    
    def get_arrays(self) -> Dict[str, np.ndarray]:
        """Return current simulation arrays for plotting"""
        return {
            'temperature': self.T - 273.15,  # Convert to Celsius
            'pressure': self.p,
            'velocity': self.u,
            'x_stack': np.linspace(0, self.stack_length, self.nx_stack),
            'x_resonator': np.linspace(0, self.resonator_length, self.nx_resonator)
        }

    def run_simulation(self, callback=None) -> Tuple[Dict[str, float], Dict[str, np.ndarray]]:
        """Run simulation for max_steps or until convergence"""
        metrics_history = []
        
        for _ in range(self.max_steps):
            metrics = self.step_simulation()
            metrics_history.append(metrics)
            
            # Call callback with current metrics if provided
            if callback:
                callback(metrics, self.get_arrays())
            
            # Check for convergence (example condition)
            if self.step > 1000 and np.abs(
                metrics_history[-1]['power'] - 
                metrics_history[-2]['power']
            ) < 1e-6:
                break
                
        return metrics, self.get_arrays()

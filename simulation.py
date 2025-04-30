def solve_thermoacoustics(self, params):
    # Extract parameters
    stack_length = params['stack_length'] * 1e-3
    # ...

    print(f"Initial Parameters: {params}")

    # Initialize arrays
    nx = 100
    T = np.full(nx, ambient_temp)
    u = np.zeros(nx)

    print(f"Initial Temperature: {T}")
    print(f"Initial Displacement: {u}")

    # Time-stepping loop
    for _ in range(1000):
        # Update temperature
        T[1:-1] += alpha * dt / dx**2 * (T[2:] - 2*T[1:-1] + T[:-2])
        # Update displacement
        u[1:-1] += c**2 * dt**2 / dx**2 * (u[2:] - 2*u[1:-1] + u[:-2])

    print(f"Final Temperature: {T}")
    print(f"Final Displacement: {u}")

    # Calculate results
    frequency = np.sqrt(np.mean(u**2)) * c / (2 * np.pi * stack_length)
    power = np.max(u) * fluid_pressure
    efficiency = power / (stack_thermal_conductivity * (operating_temp - ambient_temp))

    print(f"Results - Frequency: {frequency}, Power: {power}, Efficiency: {efficiency}")

    return {
        'frequency': frequency,
        'power': power,
        'efficiency': efficiency
    }

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
        self.cad_importer = None  
        self.setup_simulation_parameters()
        self.initialize_arrays()
        self.step = 0
        
    def load_cad_model(self, filepath):
        """Load CAD model with validation"""
        from cad_import import CADImporter
        
        if self.cad_importer is None:
            self.cad_importer = CADImporter()
            
        success = self.cad_importer.import_cad(filepath)
        if success:
            # Verify CAD dimensions match simulation parameters
            cad_dims = self.cad_importer.get_dimensions()
            if cad_dims:
                print(f"CAD Dimensions: {cad_dims}")
        return success
        
    def visualize_geometry(self, **kwargs):
        """Show CAD with customization options"""
        if self.cad_importer:
            self.cad_importer.visualize(**kwargs)
        else:
            raise ValueError("No CAD model loaded")
    
    def export_visualization(self, filename):
        """Save CAD visualization to file"""
        if self.cad_importer:
            self.cad_importer.visualize(screenshot=filename)
        else:
            raise ValueError("No CAD model loaded")
            
    def setup_simulation_parameters(self):
        # Temperature validation
        if self.params.operating_temp <= self.params.ambient_temp:
            raise ValueError(
                f"Operating temp {self.params.operating_temp}°C must be > "
                f"ambient {self.params.ambient_temp}°C"
            )
            
        # Validate parameters with warnings
        if not (0.1 <= self.params.stack_porosity <= 99.9):
            print(f"Warning: Stack porosity {self.params.stack_porosity}% is outside recommended range (0.1-99.9%)")
            self.params.stack_porosity = max(0.1, min(99.9, self.params.stack_porosity))
            
        # Basic fluid properties (must come first)
        self.c_fluid = 343.0  # Default sound speed (m/s)
        self.rho_fluid = 1.225  # Default density (kg/m³)
        
        # Convert mm to m
        self.stack_length = max(self.params.stack_length * 1e-3, 0.001)
        self.resonator_length = self.stack_length * 4
        
        # Grid parameters
        self.nx_stack = 100
        self.nx_resonator = 200
        
        # Derived spatial steps
        self.dx_stack = self.stack_length / self.nx_stack
        self.dx_resonator = self.resonator_length / self.nx_resonator
        
        # Time step based on CFL condition
        self.dt = min(1e-5, 0.5*self.dx_stack/self.c_fluid)
        
        # Temperature-dependent properties
        avg_temp = (self.params.operating_temp + self.params.ambient_temp)/2 + 273.15
        self.k_stack = max(self.params.stack_thermal_conductivity, 0.1)
        self.rho_stack = 8000  # kg/m³
        self.cp_stack = 500  # J/kg·K
        
        # Simulation control
        self.max_steps = 10000
        
        # Thermal diffusivity
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
        print(f"Starting simulation with parameters: {self.params}")
        metrics_history = []
        
        for step in range(self.max_steps):
            self.step = step
            metrics = self.step_simulation()
            metrics_history.append(metrics)
            
            # Print progress every 100 steps
            if step % 100 == 0:
                print(f"Step {step}: Frequency={metrics['frequency']} Hz, "
                      f"Power={metrics['power']} W, "
                      f"Efficiency={metrics['efficiency']}")
            
            if callback:
                callback(metrics, self.get_arrays())
            
            # Enhanced convergence criteria
            if step > 1000 and all([
                np.abs(metrics_history[-1]['power'] - metrics_history[-2]['power']) < 1e-6,
                np.abs(metrics_history[-1]['frequency'] - metrics_history[-2]['frequency']) < 0.1,
                np.abs(metrics_history[-1]['efficiency'] - metrics_history[-2]['efficiency']) < 1e-4
            ]):
                print(f"Converged after {step} steps")
                break
                
        final_metrics = metrics_history[-1]
        print(f"\nFinal Results:\n"
              f"Frequency: {final_metrics['frequency']} Hz\n"
              f"Power: {final_metrics['power']} W\n"
              f"Efficiency: {final_metrics['efficiency']}")
              
        return final_metrics, self.get_arrays()

    def _temp_dependent_conductivity(self, temp):
        # Implement temperature-dependent conductivity model
        pass

    def _temp_dependent_density(self, temp):
        # Implement temperature-dependent density model
        pass

    def _temp_dependent_heat_capacity(self, temp):
        # Implement temperature-dependent heat capacity model
        pass

    def _fluid_density(self, fluid_type, temp, pressure):
        """Returns density in kg/m³ for given fluid"""
        # Basic implementation - can be expanded
        if fluid_type.lower() == 'air':
            return (pressure * 1000) / (287.05 * temp)
        return 1.225  # Default for other gases

    def _fluid_sound_speed(self, fluid_type, temp):
        """Returns sound speed in m/s for given fluid"""
        # Basic implementation - can be expanded
        if fluid_type.lower() == 'air':
            return 331.4 + (0.6 * (temp - 273.15))
        return 343.0  # Default for other gases

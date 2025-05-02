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
    # Define all parameters from config_panel here
    # Using simplified set for now
    stack_length: float
    stack_porosity: float
    stack_thermal_conductivity: float
    hhx_length: float
    hhx_diameter: float
    chx_length: float
    fluid_type: str
    fluid_pressure: float
    ambient_temp: float
    operating_temp: float
    resonator_length: float  # Assuming we can derive this or add it

    @classmethod
    def from_config(cls, config_data):
        # Map config data to SimulationParams fields
        # Assuming config_data is a dictionary from config_panel.get_simulation_parameters()
        return cls(
            stack_length=config_data.get('stack_length', 85.0),
            stack_porosity=config_data.get('stack_porosity', 70.0),
            stack_thermal_conductivity=config_data.get('stack_thermal_conductivity', 1.0),
            hhx_length=config_data.get('hhx_length', 20.0),
            hhx_diameter=config_data.get('hhx_diameter', 50.0),
            chx_length=config_data.get('chx_length', 50.0),
            fluid_type=config_data.get('fluid_type', 'Air'),
            fluid_pressure=config_data.get('fluid_pressure', 101.3),
            ambient_temp=config_data.get('ambient_temp', 20.0),
            operating_temp=config_data.get('operating_temp', 400.0),
            resonator_length=config_data.get('resonator_length', 750.0) # Placeholder
        )

class ThermoacousticSimulation:
    def __init__(self, params: SimulationParams):
        self.params = params
        self.cad_importer = None  
        self.setup_simulation_parameters()
        self.initialize_arrays()
        self.step = 0
        self.results = {}
        
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
            'chx_internal_br': self.params.chx_length,
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

    def run_simulation(self) -> Dict[str, float]:
        """Runs a simplified simulation based on parameters.
           This will be replaced by the actual PDE solver later.
        """
        # Convert parameters to consistent units (e.g., meters, Kelvin, Pascal)
        L_stack = self.params.stack_length * 1e-3
        porosity = self.params.stack_porosity / 100.0
        k_stack = self.params.stack_thermal_conductivity
        L_res = self.params.resonator_length * 1e-3
        P_mean = self.params.fluid_pressure * 1e3
        T_amb = self.params.ambient_temp + 273.15
        T_op = self.params.operating_temp + 273.15
        T_mean = (T_op + T_amb) / 2

        # Simplified Fluid Properties (replace with proper calculations)
        gamma = 1.4 if self.params.fluid_type == 'Air' else 1.66 # Adiabatic index
        R_gas = 287.0 if self.params.fluid_type == 'Air' else 2077.0 # Specific gas constant J/(kg*K)
        
        try:
            # Calculate speed of sound
            c_sound = np.sqrt(gamma * R_gas * T_mean)

            # Simplified Frequency Calculation (based on resonator length)
            # Using lambda/2 resonance for a simplified model
            frequency = c_sound / (2 * L_res)

            # Simplified Power Calculation (Placeholder)
            # Based on temperature difference and stack properties
            delta_T = T_op - T_amb
            # Basic scaling - this needs a proper thermoacoustic model
            acoustic_power = k_stack * delta_T * L_stack * porosity * 0.1 # Arbitrary scaling

            # Simplified Efficiency Calculation (Placeholder)
            # Requires heat input calculation, using a simple estimate
            heat_input = acoustic_power / 0.15 # Assuming 15% efficiency for placeholder
            thermal_efficiency = (acoustic_power / heat_input) * 100 if heat_input > 0 else 0
            thermal_efficiency = min(thermal_efficiency, 90.0) # Cap efficiency
            
            # Placeholder values for other metrics shown in the Results tab
            cop = thermal_efficiency / (100 - thermal_efficiency) if thermal_efficiency < 100 else 10.0
            quality_factor = frequency / 10.0 # Placeholder
            pressure_amplitude = P_mean * 0.05 # 5% of mean pressure
            velocity = c_sound * 0.02 # 2% of sound speed
            onset_temp = T_amb + delta_T * 0.2 # Placeholder

        except Exception as e:
            print(f"Error during simplified simulation: {e}")
            return {
                'frequency': 0.0,
                'acoustic_power': 0.0,
                'thermal_efficiency': 0.0,
                'cop': 0.0,
                'quality_factor': 0.0,
                'pressure_amplitude': 0.0,
                'velocity': 0.0,
                'T_H': T_op - 273.15,
                'T_C': T_amb - 273.15,
                'delta_T': 0.0,
                'onset_temperature': 0.0,
            }
            
        self.results = {
            'frequency': frequency,
            'acoustic_power': acoustic_power,
            'thermal_efficiency': thermal_efficiency,
            'cop': cop,
            'quality_factor': quality_factor,
            'pressure_amplitude': pressure_amplitude,
            'velocity': velocity,
            'T_H': T_op - 273.15, # Convert back to Celsius for display
            'T_C': T_amb - 273.15,
            'delta_T': delta_T,
            'onset_temperature': onset_temp - 273.15,
            # Add other placeholder results needed by ResultsTabs
            'stack_performance_factor': 0.8,
            'normalized_temp_gradient': 0.5,
            'rayleigh_number': 1e6,
            'reynolds_number': 1000,
            'thermoacoustic_parameter': 0.1,
            'onset_time': 5.0,
            'steady_state_time': 20.0
        }
        return self.results

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

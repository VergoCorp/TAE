import pyvista as pv
import meshio
import numpy as np
from pathlib import Path

class CADImporter:
    SUPPORTED_FORMATS = ['.step', '.stp', '.stl', '.iges', '.igs', '.x_t']
    
    def __init__(self):
        self.mesh = None
        self.filepath = None
        
    def import_cad(self, filepath):
        """Import CAD file with format validation"""
        try:
            path = Path(filepath)
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported file format: {path.suffix}")
                
            # Try pyvista first (better for visualization)
            try:
                self.mesh = pv.read(filepath)
            except:
                # Fallback to meshio if pyvista fails
                mesh_data = meshio.read(filepath)
                self.mesh = pv.wrap(mesh_data)
                
            self.filepath = str(path.absolute())
            print(f"Successfully imported {path.name}")
            self._print_mesh_stats()
            return True
            
        except Exception as e:
            print(f"CAD import error: {str(e)}")
            return False
    
    def _print_mesh_stats(self):
        """Display basic mesh information"""
        if self.mesh:
            print(f"Mesh stats - Points: {self.mesh.n_points:,}" 
                  f" Cells: {self.mesh.n_cells:,}")
    
    def visualize(self, show_edges=True, screenshot=None):
        """Show 3D visualization with options"""
        if not self.mesh:
            raise ValueError("No CAD model loaded")
            
        plotter = pv.Plotter()
        plotter.add_mesh(
            self.mesh, 
            color='lightgrey', 
            show_edges=show_edges,
            opacity=0.9
        )
        plotter.add_axes()
        plotter.add_title(f"CAD Model: {Path(self.filepath).name}")
        
        if screenshot:
            plotter.screenshot(screenshot)
        plotter.show()
    
    def get_dimensions(self):
        """Return model bounding box dimensions"""
        if self.mesh:
            bounds = self.mesh.bounds
            return {
                'length': abs(bounds[1] - bounds[0]),
                'width': abs(bounds[3] - bounds[2]),
                'height': abs(bounds[5] - bounds[4])
            }
        return None

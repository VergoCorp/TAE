from cad_import import CADImporter

# Initialize and test CAD import
def main():
    importer = CADImporter()
    
    # Replace with your actual CAD file path
    cad_file = "engine_model.step"  # or .stl, .iges, etc.
    
    if importer.import_cad(cad_file):
        print("CAD import successful!")
        
        # View the model with edges visible
        importer.visualize(show_edges=True)
        
        # Get dimensions
        dims = importer.get_dimensions()
        print(f"Model dimensions (mm): {dims}")
    else:
        print("CAD import failed")

if __name__ == "__main__":
    main()

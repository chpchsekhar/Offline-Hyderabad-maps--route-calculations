import json
import geojson
from shapely.geometry import shape, Point, LineString
import numpy as np

def convert_hyderabad_geojson(input_file):
    """
    Convert Hyderabad GeoJSON data to the format required by our offline maps application.
    """
    # Read the GeoJSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = geojson.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find the file {input_file}")
        return [], []
    except json.JSONDecodeError:
        print(f"Error: The file {input_file} is not valid JSON")
        return [], []

    # Initialize our data structures
    roads = []
    locations = []
    
    # Debug information
    print(f"Total features found: {len(data['features'])}")
    
    # Count different types of geometries
    geometry_types = {}
    
    # Process each feature in the GeoJSON
    for feature in data['features']:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        
        # Count geometry types
        geom_type = geometry.get('type', 'Unknown')
        geometry_types[geom_type] = geometry_types.get(geom_type, 0) + 1
        
        try:
            if geometry['type'] == 'LineString':
                # Process roads
                coordinates = geometry['coordinates']
                if len(coordinates) >= 2:  # Make sure we have at least 2 points
                    for i in range(len(coordinates) - 1):
                        roads.append({
                            'start': [coordinates[i][1], coordinates[i][0]],
                            'end': [coordinates[i+1][1], coordinates[i+1][0]],
                            'name': properties.get('name', ''),
                            'type': properties.get('highway', 'road')
                        })
                        
            elif geometry['type'] == 'Point':
                # Process locations/points of interest
                if 'name' in properties:
                    locations.append({
                        'name': properties['name'],
                        'area': properties.get('area', ''),
                        'lat': geometry['coordinates'][1],
                        'lng': geometry['coordinates'][0],
                        'type': properties.get('amenity', 'landmark')
                    })
            
            elif geometry['type'] == 'Polygon':
                # Process areas/neighborhoods
                # Use centroid as the location point
                try:
                    poly = shape(geometry)
                    centroid = poly.centroid
                    if 'name' in properties:
                        locations.append({
                            'name': properties['name'],
                            'area': properties.get('area', properties.get('name', '')),
                            'lat': centroid.y,
                            'lng': centroid.x,
                            'type': 'area'
                        })
                except Exception as e:
                    print(f"Error processing polygon: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error processing feature: {str(e)}")
            continue

    # Print debug information
    print("\nGeometry types found:")
    for gtype, count in geometry_types.items():
        print(f"{gtype}: {count} features")
    
    print(f"\nProcessed {len(roads)} road segments")
    print(f"Processed {len(locations)} locations")

    # Only save files if we have data
    if roads:
        with open('data/hyderabad_roads.json', 'w', encoding='utf-8') as f:
            json.dump({'roads': roads}, f, indent=2, ensure_ascii=False)
    else:
        print("Warning: No road data was processed!")

    if locations:
        with open('data/hyderabad_locations.json', 'w', encoding='utf-8') as f:
            json.dump(locations, f, indent=2, ensure_ascii=False)
    else:
        print("Warning: No location data was processed!")
    
    return roads, locations

def generate_static_map(roads, locations, width=800, height=600):
    """
    Generate a static map image using the processed data
    """
    if not roads and not locations:
        print("Error: No data available to generate map")
        return

    import cairo
    
    # Create a new surface and context
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)
    
    # Set background
    ctx.set_source_rgb(0.95, 0.95, 0.95)
    ctx.paint()
    
    # Get coordinate bounds
    lats = []
    lons = []
    
    # Collect coordinates from roads
    for road in roads:
        lats.extend([road['start'][0], road['end'][0]])
        lons.extend([road['start'][1], road['end'][1]])
    
    # Collect coordinates from locations
    for location in locations:
        lats.append(location['lat'])
        lons.append(location['lng'])
    
    if not lats or not lons:
        print("Error: No coordinates found to generate map")
        return
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Function to convert coordinates to pixels
    def coord_to_pixel(lat, lon):
        x = (lon - min_lon) / (max_lon - min_lon) * width if max_lon != min_lon else width/2
        y = height - (lat - min_lat) / (max_lat - min_lat) * height if max_lat != min_lat else height/2
        return x, y
    
    # Draw roads
    if roads:
        ctx.set_source_rgb(0.7, 0.7, 0.7)
        ctx.set_line_width(1)
        
        for road in roads:
            start_x, start_y = coord_to_pixel(road['start'][0], road['start'][1])
            end_x, end_y = coord_to_pixel(road['end'][0], road['end'][1])
            
            ctx.move_to(start_x, start_y)
            ctx.line_to(end_x, end_y)
            ctx.stroke()
    
    # Draw locations
    if locations:
        ctx.set_source_rgb(0.8, 0.2, 0.2)
        for location in locations:
            x, y = coord_to_pixel(location['lat'], location['lng'])
            ctx.arc(x, y, 2, 0, 2 * np.pi)
            ctx.fill()
    
    # Save the map
    surface.write_to_png('static/hyderabad_map.png')
    print("Generated static map: hyderabad_map.png")

if __name__ == "__main__":
    # Make sure the output directories exist
    import os
    os.makedirs('data', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Let user input the filename if it's not 'hyderabad.geojson'
    filename = input("Enter the name of your GeoJSON file (or press Enter for default 'hyderabad.geojson'): ").strip()
    if not filename:
        filename = 'hyderabad.geojson'
    
    # Convert the data
    roads, locations = convert_hyderabad_geojson(filename)
    
    # Only generate map if we have data
    if roads or locations:
        generate_static_map(roads, locations)
    else:
        print("No data available to generate map")

    # Print a sample of the data for verification
    print("\nSample of processed data:")
    if roads:
        print("\nFirst road:", roads[0])
    if locations:
        print("\nFirst location:", locations[0])
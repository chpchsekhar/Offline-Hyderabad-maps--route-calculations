import os
import osmnx as ox
import pickle
import json
import requests
import time
from pathlib import Path
import math

def download_map_tiles(min_lat, max_lat, min_lon, max_lon, zoom_levels):
    """Download map tiles for specified region and zoom levels"""
    os.makedirs('offline_data/tiles', exist_ok=True)
    
    for zoom in zoom_levels:
        print(f"Downloading tiles for zoom level {zoom}...")
        
        # Calculate tile coordinates
        min_x, min_y = deg2num(max_lat, min_lon, zoom)
        max_x, max_y = deg2num(min_lat, max_lon, zoom)
        
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                try:
                    # Create directories
                    tile_dir = Path(f'offline_data/tiles/{zoom}/{x}')
                    tile_dir.mkdir(parents=True, exist_ok=True)
                    
                    tile_path = tile_dir / f'{y}.png'
                    
                    # Skip if tile already exists
                    if tile_path.exists():
                        continue
                    
                    # Download tile
                    url = f"https://a.tile.openstreetmap.org/{zoom}/{x}/{y}.png"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        with open(tile_path, 'wb') as f:
                            f.write(response.content)
                    
                    # Be nice to the OSM servers
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error downloading tile {zoom}/{x}/{y}: {e}")

def deg2num(lat_deg, lon_deg, zoom):
    """Convert latitude/longitude to tile coordinates"""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def get_place_coordinates(place_name):
    """Get the coordinates for a place using OSM Nominatim"""
    location = ox.geocode(place_name)
    return location[0], location[1]  # Returns (lat, lon)

def setup_offline_data(region):
    """Download and prepare all necessary offline data"""
    try:
        # Create offline_data directory
        os.makedirs('offline_data', exist_ok=True)
        
        print(f"Getting coordinates for {region}...")
        center_lat, center_lon = get_place_coordinates(region)
        
        print("Downloading road network...")
         
        G = ox.graph_from_point((center_lat, center_lon), 
                               dist=20000,  # 20km radius
                               network_type='drive')
        
       
        with open('offline_data/road_network.pkl', 'wb') as f:
            pickle.dump(G, f)
        
        print("Creating geocoding database...")
        
        geocoding_db = []
        
       
        geocoding_db.append({
            'name': region,
            'latitude': center_lat,
            'longitude': center_lon
        })
        
        
        for node, data in G.nodes(data=True):
            if 'name' in data:
                geocoding_db.append({
                    'name': data['name'],
                    'latitude': data['y'],
                    'longitude': data['x']
                })
        
        with open('offline_data/geocoding.json', 'w') as f:
            json.dump(geocoding_db, f)
        
        print("Downloading map tiles...")
         
        padding = 0.1   
        download_map_tiles(
            min_lat=center_lat - padding,
            max_lat=center_lat + padding,
            min_lon=center_lon - padding,
            max_lon=center_lon + padding,
            zoom_levels=range(10, 16)  
        )
        
        print("Setup complete!")
        
    except Exception as e:
        print(f"Error during setup: {e}")
        raise

if __name__ == '__main__':
    
    region = "Hyderabad, India"   
    setup_offline_data(region)
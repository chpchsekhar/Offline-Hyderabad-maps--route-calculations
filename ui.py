# File: main.py
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import folium
import sqlite3
import osmnx as ox
import networkx as nx
from pathlib import Path
import json
import pickle
import base64

class OfflineMapsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Maps")
        self.setGeometry(100, 100, 800, 600)
        
        # Check if offline data exists
        if not self.check_offline_data():
            QMessageBox.critical(self, "Error", 
                               "Offline data not found. Please run setup_offline_data.py first.")
            sys.exit(1)
        
        # Initialize offline data
        self.load_offline_data()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Create search bar and buttons
        search_layout = QHBoxLayout()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter location to search...")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_location)
        
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(search_button)
        
        # Route planning widgets
        route_layout = QHBoxLayout()
        
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Enter source location...")
        
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Enter destination...")
        
        route_button = QPushButton("Show Route")
        route_button.clicked.connect(self.show_route)
        
        route_layout.addWidget(QLabel("From:"))
        route_layout.addWidget(self.source_input)
        route_layout.addWidget(QLabel("To:"))
        route_layout.addWidget(self.dest_input)
        route_layout.addWidget(route_button)
        
        # Create map view
        self.map_view = QWebEngineView()
        
        # Add widgets to main layout
        layout.addLayout(search_layout)
        layout.addLayout(route_layout)
        layout.addWidget(self.map_view)
        
        main_widget.setLayout(layout)
        
        # Initialize map
        self.initialize_map()

    def check_offline_data(self):
        """Check if required offline data exists"""
        required_files = [
            'offline_data/road_network.pkl',
            'offline_data/geocoding.json'
        ]
        return all(Path(f).exists() for f in required_files) and Path('offline_data/tiles').exists()

    def load_offline_data(self):
        """Load offline data"""
        try:
            # Load road network
            with open('offline_data/road_network.pkl', 'rb') as f:
                self.G = pickle.load(f)
            
            # Load geocoding database
            with open('offline_data/geocoding.json', 'r') as f:
                self.geocoding_db = json.load(f)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load offline data: {str(e)}")
            sys.exit(1)

    def create_map_html(self, center_lat, center_lon, zoom=12, markers=None, route=None):
        """Create HTML for the map with embedded tile data"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <style>
                #map {{ height: 100vh; width: 100%; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([{center_lat}, {center_lon}], {zoom});
                
                // Add tile layer using local tiles
                L.tileLayer('file://{str(Path("offline_data/tiles").absolute())}/{{z}}/{{x}}/{{y}}.png', {{
                    minZoom: 10,
                    maxZoom: 15,
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);
        """
        
        # Add markers if provided
        if markers:
            for marker in markers:
                html += f"""
                L.marker([{marker['lat']}, {marker['lon']}])
                    .bindPopup('{marker['popup']}')
                    .addTo(map);
                """
        
        # Add route if provided
        if route:
            html += f"""
            L.polyline({route},
                {{color: 'blue', weight: 2, opacity: 0.8}}).addTo(map);
            """
        
        html += """
            </script>
        </body>
        </html>
        """
        
        # Save to temporary file
        temp_path = Path('temp_map.html')
        with open(temp_path, 'w') as f:
            f.write(html)
        return temp_path

    def initialize_map(self):
        """Initialize the map"""
        try:
            initial_location = self.geocoding_db[0]
            temp_path = self.create_map_html(
                initial_location['latitude'],
                initial_location['longitude']
            )
            self.map_view.setUrl(QUrl.fromLocalFile(str(temp_path.absolute())))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize map: {str(e)}")

    def find_location(self, search_text):
        """Find location in offline database"""
        search_text_lower = search_text.lower()
        for entry in self.geocoding_db:
            if search_text_lower in entry['name'].lower():
                return entry['latitude'], entry['longitude']
        return None, None

    def search_location(self):
        """Search for a location"""
        search_text = self.search_bar.text()
        
        latitude, longitude = self.find_location(search_text)
        
        if latitude is None or longitude is None:
            QMessageBox.warning(self, "Not Found", 
                              "Location not found in offline database")
            return
        
        # Create marker
        markers = [{
            'lat': latitude,
            'lon': longitude,
            'popup': search_text
        }]
        
        # Update map
        temp_path = self.create_map_html(
            latitude, longitude,
            zoom=14,
            markers=markers
        )
        self.map_view.setUrl(QUrl.fromLocalFile(str(temp_path.absolute())))

    def show_route(self):
        """Show route between two locations"""
        source = self.source_input.text()
        destination = self.dest_input.text()
        
        try:
            # Get coordinates
            source_lat, source_lon = self.find_location(source)
            dest_lat, dest_lon = self.find_location(destination)
            
            if None in (source_lat, source_lon, dest_lat, dest_lon):
                QMessageBox.warning(self, "Not Found", 
                                  "One or both locations not found in offline database")
                return
            
            # Calculate center point
            center_lat = (source_lat + dest_lat) / 2
            center_lon = (source_lon + dest_lon) / 2
            
            # Create markers
            markers = [
                {
                    'lat': source_lat,
                    'lon': source_lon,
                    'popup': source
                },
                {
                    'lat': dest_lat,
                    'lon': dest_lon,
                    'popup': destination
                }
            ]
            
            # Find route
            source_node = ox.nearest_nodes(self.G, source_lon, source_lat)
            dest_node = ox.nearest_nodes(self.G, dest_lon, dest_lat)
            
            try:
                route = nx.shortest_path(self.G, source_node, dest_node, weight='length')
                
                # Get route coordinates
                route_coords = []
                for node in route:
                    route_coords.append([self.G.nodes[node]['y'], self.G.nodes[node]['x']])
                
                # Update map
                temp_path = self.create_map_html(
                    center_lat, center_lon,
                    zoom=12,
                    markers=markers,
                    route=route_coords
                )
                self.map_view.setUrl(QUrl.fromLocalFile(str(temp_path.absolute())))
                
            except nx.NetworkXNoPath:
                QMessageBox.warning(self, "No Route", 
                                  "No route found between these locations")
                return
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error showing route: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OfflineMapsApp()
    window.show()
    sys.exit(app.exec_())
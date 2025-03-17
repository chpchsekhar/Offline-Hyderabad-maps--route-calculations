import sqlite3
import math
import folium
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLineEdit, QPushButton, QLabel, 
                            QCompleter, QProgressBar)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import networkx as nx
import osmnx as ox
import numpy as np
from rtree import index
from shapely.geometry import Point, LineString
import geopandas as gpd
import osmium
import json

class AddressDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.setup_database()
        
    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY,
                street TEXT,
                city TEXT,
                lat REAL,
                lon REAL,
                UNIQUE(street, city)
            )
        ''')
        self.conn.commit()
        
    def add_address(self, street, city, lat, lon):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO addresses (street, city, lat, lon)
                VALUES (?, ?, ?, ?)
            ''', (street, city, lat, lon))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding address: {e}")
            
    def search_address(self, query):
        try:
            self.cursor.execute('''
                SELECT street, city, lat, lon FROM addresses
                WHERE street LIKE ? OR city LIKE ?
            ''', (f'%{query}%', f'%{query}%'))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error searching address: {e}")
            return []

class MapTileProvider:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def get_tile(self, zoom, x, y):
        try:
            self.cursor.execute('''
                SELECT tile_data FROM tiles 
                WHERE zoom_level=? AND tile_column=? AND tile_row=?
            ''', (zoom, x, y))
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error retrieving tile: {e}")
            return None

class RoutingEngine:
    def __init__(self, graph_path):
        self.G = ox.load_graphml(graph_path)
        self.nodes = np.array([[node[1]['y'], node[1]['x']] 
                             for node in self.G.nodes(data=True)])
        self.idx = index.Index()
        for i, node in enumerate(self.G.nodes(data=True)):
            self.idx.insert(i, (node[1]['y'], node[1]['x'], 
                               node[1]['y'], node[1]['x']))
    
    def nearest_node(self, lat, lon):
        point = Point(lat, lon)
        nearest = list(self.idx.nearest((lat, lon, lat, lon), 1))[0]
        return list(self.G.nodes())[nearest]
    
    def calculate_route(self, start_lat, start_lon, end_lat, end_lon):
        start_node = self.nearest_node(start_lat, start_lon)
        end_node = self.nearest_node(end_lat, end_lon)
        
        try:
            route = nx.shortest_path(self.G, start_node, end_node, 
                                   weight='length')
            route_coords = []
            for node in route:
                route_coords.append([
                    self.G.nodes[node]['y'],
                    self.G.nodes[node]['x']
                ])
            return route_coords
        except nx.NetworkXNoPath:
            return None

class OfflineMapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline Route Mapping")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.db_path = r"C:\Users\chpch\Downloads\Mobile Atlas Creator 2.3.3\atlases\hyd.sqlitedb"
        self.address_db = AddressDatabase(self.db_path)
        self.tile_provider = MapTileProvider(self.db_path)
        self.routing_engine = RoutingEngine("hyderabad_graph.graphml")  # You'll need to create this
        
        self.setup_ui()
        self.setup_autocomplete()
        
    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Search bar container
        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        
        # Source input
        source_layout = QHBoxLayout()
        source_label = QLabel("From:")
        self.source_input = QLineEdit()
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_input)
        
        # Destination input
        dest_layout = QHBoxLayout()
        dest_label = QLabel("To:")
        self.dest_input = QLineEdit()
        dest_layout.addWidget(dest_label)
        dest_layout.addWidget(self.dest_input)
        
        # Add inputs to search container
        search_layout.addLayout(source_layout)
        search_layout.addLayout(dest_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Find Route")
        self.search_button.clicked.connect(self.calculate_route)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_route)
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.clear_button)
        search_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        search_layout.addWidget(self.progress_bar)
        
        # Add search container to main layout
        layout.addWidget(search_container)
        
        # Map view
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # Initialize map
        self.display_initial_map()
        
    def setup_autocomplete(self):
        # Load address list for autocomplete
        addresses = self.address_db.search_address("")
        address_list = [f"{addr[0]}, {addr[1]}" for addr in addresses]
        
        # Set up autocomplete for both inputs
        completer = QCompleter(address_list)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.source_input.setCompleter(completer)
        self.dest_input.setCompleter(completer)
        
    def display_initial_map(self):
        # Center on Hyderabad
        m = folium.Map(
            location=[17.3850, 78.4867],
            zoom_start=12,
            tiles='OpenStreetMap'  # We'll replace this with our offline tiles
        )
        
        # Convert to HTML and display
        data = m._repr_html_()
        self.web_view.setHtml(data)
        
    def get_coordinates_from_address(self, address):
        # Search address in local database
        results = self.address_db.search_address(address)
        if results:
            return results[0][2], results[0][3]  # lat, lon
        return None, None
        
    def calculate_route(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Get coordinates
        source_addr = self.source_input.text()
        dest_addr = self.dest_input.text()
        
        start_lat, start_lon = self.get_coordinates_from_address(source_addr)
        end_lat, end_lon = self.get_coordinates_from_address(dest_addr)
        
        if not all([start_lat, start_lon, end_lat, end_lon]):
            self.progress_bar.setVisible(False)
            return
            
        self.progress_bar.setValue(50)
        
        # Calculate route
        route_coords = self.routing_engine.calculate_route(
            start_lat, start_lon, end_lat, end_lon
        )
        
        if route_coords:
            self.display_route(route_coords, (start_lat, start_lon), 
                             (end_lat, end_lon))
            
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
    def display_route(self, route_coords, start_coords, end_coords):
        # Create new map centered on route
        center_lat = (start_coords[0] + end_coords[0]) / 2
        center_lon = (start_coords[1] + end_coords[1]) / 2
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
        
        # Add markers
        folium.Marker(
            start_coords,
            popup='Start',
            icon=folium.Icon(color='green')
        ).add_to(m)
        
        folium.Marker(
            end_coords,
            popup='End',
            icon=folium.Icon(color='red')
        ).add_to(m)
        
        # Add route line
        folium.PolyLine(
            route_coords,
            weight=4,
            color='blue',
            opacity=0.8
        ).add_to(m)
        
        # Update map
        data = m._repr_html_()
        self.web_view.setHtml(data)
        
    def clear_route(self):
        self.source_input.clear()
        self.dest_input.clear()
        self.display_initial_map()

def main():
    app = QApplication(sys.argv)
    window = OfflineMapApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
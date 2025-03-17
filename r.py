# Script to create address database and road network
import osmnx as ox
import osmium
import sqlite3

# Download Hyderabad data (do this once)
area = ox.geocode_to_gdf("Hyderabad, India")
G = ox.graph_from_polygon(area.geometry.iloc[0], network_type='drive')
ox.save_graphml(G, "hyderabad_graph.graphml")

# Create database connection
conn = sqlite3.connect('addresses.db')
cursor = conn.cursor()

# Ensure the table exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        street TEXT,
        city TEXT,
        lat REAL,
        lon REAL
    )
''')
conn.commit()

# Create address handler
class AddressHandler(osmium.SimpleHandler):
    def __init__(self, db_conn):
        super().__init__()
        self.conn = db_conn
        self.cursor = self.conn.cursor()

    def node(self, n):
        if 'addr:street' in n.tags:
            self.cursor.execute('''
                INSERT OR IGNORE INTO addresses (street, city, lat, lon)
                VALUES (?, ?, ?, ?)
            ''', (
                n.tags.get('addr:street'),
                'Hyderabad',
                n.location.lat,
                n.location.lon
            ))
            self.conn.commit()

# Process OSM file
handler = AddressHandler(conn)
handler.apply_file("hyd.osm.pbf")  # Ensure you have this file

# Close database connection
conn.close()

import sqlite3
import os
import gzip
import io
from PIL import Image
import magic  # Install via: pip install python-magic

MBTILES_FILE = "osm-2020-02-10-v3.11_india_hyderabad (1).mbtiles"
OUTPUT_DIR = "offline_tiles"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Connect to .mbtiles database
conn = sqlite3.connect(MBTILES_FILE)
cursor = conn.cursor()
cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles")

for zoom, col, row, data in cursor.fetchall():
    if data:
        print(f"Processing Tile {zoom}_{col}_{row} - Size: {len(data)} bytes")

        try:
            # Detect file type
            file_type = magic.from_buffer(data, mime=True)
            print(f"Detected MIME type: {file_type}")

            # Handle gzip-compressed tiles
            if file_type == "application/gzip":
                data = gzip.decompress(data)

            # Open image
            tile_image = Image.open(io.BytesIO(data))
            
            # Save as PNG or JPEG
            ext = "png" if tile_image.format == "PNG" else "jpg"
            tile_filename = os.path.join(OUTPUT_DIR, f"{zoom}_{col}_{row}.{ext}")
            tile_image.save(tile_filename)
            print(f"Saved: {tile_filename}")

        except Exception as e:
            print(f"Error processing tile {zoom}_{col}_{row}: {e}")
    else:
        print(f"Skipping empty tile {zoom}_{col}_{row}")

print("✅ Tile extraction complete.")

# Offline Maps Application

This is an offline maps application built using Python, PyQt5, Folium, and OSMnx. The application allows users to search for locations and plan routes using offline data.

## Features

- Search for locations using offline geocoding data
- Display maps with offline tiles
- Plan routes between two locations using offline road network data

## Requirements

- Python 3.6+
- PyQt5
- Folium
- OSMnx
- NetworkX
- SQLite3

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/offline-maps-app.git
    cd offline-maps-app
    ```

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

3. Ensure you have the required offline data files in the `offline_data` directory:

    - `road_network.pkl`
    - `geocoding.json`
    - `tiles/` directory with map tiles

## Usage

1. Run the application:

    ```sh
    python ui.py
    ```

2. Use the search bar to find locations and the route planning inputs to plan routes.

## Offline Data Setup

To set up the offline data, run the `setup_offline_data.py` script. This script will download and prepare the necessary data files.

```sh
python setup_offline_data.py
```

## Project Structure

```
offline-maps-app/
│
├── abc/
│   ├── geocoding.json
│   ├── map_tiles.db
│   ├── road_network.pkl
│   └── tiles/
│
├── cache/
│   ├── 3d625b55c19b0865e601950d6489e579b55e30b5.json
│   ├── 4937bc25f1de64e021cf52193c6eb13aa418c064.json
│   └── 678ba0c4c4b61294a087e4eddf64233c7e5865d0.json
│
├── data/
│   └── hyderabad_locations.json
│
├── hyderabad_map_data/
│
├── offline_tiles/
│
├── static/
│
├── templates/
│
├── a.py
├── addresses.db
├── app.py
├── convert.py
├── hyd.osm.pbf
├── hyderabad_graph.graphml
├── hyderabad.graphml
├── offline.py
├── osm-2020-02-10-v3.11_india_hyderabad (1).mbtiles
├── r.py
├── temp_map.html
├── test.py
├── ui.py
└── requirements.txt
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

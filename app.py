from flask import Flask, request, jsonify
import osmnx as ox
import networkx as nx

app = Flask(__name__)

# Load the GraphML file
GRAPHML_FILE = "hyderabad.graphml"
graph = ox.load_graphml(GRAPHML_FILE)

@app.route("/route", methods=["GET"])
def get_route():
    """Calculate the shortest path between two points (offline)."""
    try:
        lat1, lon1 = float(request.args.get("lat1")), float(request.args.get("lon1"))
        lat2, lon2 = float(request.args.get("lat2")), float(request.args.get("lon2"))

        # Find nearest nodes
        node1 = ox.distance.nearest_nodes(graph, X=lon1, Y=lat1)
        node2 = ox.distance.nearest_nodes(graph, X=lon2, Y=lat2)

        # Compute shortest path
        route = nx.shortest_path(graph, node1, node2, weight="length")

        # Convert route to coordinates
        route_coords = [(graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in route]

        return jsonify({"route": route_coords})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)

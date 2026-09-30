import json
import os

DATA_FILE = "dashboard_nodes.json"


def _load_nodes():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_nodes(nodes):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(nodes, file, indent=4)


def add_node(node):
    name = node.get("name")

    if not name:
        return

    nodes = _load_nodes()

    nodes[name] = {
        "name": name,
        "host": node.get("host", ""),
        "port": node.get("port", ""),
        "node_id": node.get("node_id", ""),
        "consensus": node.get("consensus", "Unknown"),
        "status": "Online",
        "role": node.get("role", "Normal"),
        "peers": 0
    }

    _save_nodes(nodes)


def remove_node(node):
    name = node.get("name")

    if not name:
        return

    nodes = _load_nodes()

    if name in nodes:
        del nodes[name]

    _save_nodes(nodes)


def get_nodes():
    return _load_nodes()


def update_peers(name, peers):
    nodes = _load_nodes()

    if name in nodes:
        nodes[name]["peers"] = peers
        _save_nodes(nodes)


def update_blockchain_stats(name, block_count, transaction_count):
    nodes = _load_nodes()

    if name in nodes:
        nodes[name]["blocks"] = block_count
        nodes[name]["transactions"] = transaction_count
        _save_nodes(nodes)

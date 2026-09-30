import asyncio
import json
import websockets

from dashboard_state import update_peers, update_blockchain_stats

from consensus.poa.p2p import Peer as PoAPeer
from consensus.pos.p2p import Peer as PoSPeer
from consensus.pow.p2p import Peer as PoWPeer

from consensus.poa.mal_node import Peer as PoaMalPeer
from consensus.pos.mal_node import Peer as PosMalPeer
from consensus.pow.mal_node import Peer as PowMalPeer


SIGNALLING_SERVER = "ws://localhost:8765"


async def connect_to_room(peer, room_id):
    node_info = {
        "name": peer.name,
        "host": peer.host,
        "port": peer.port,
        "node_id": getattr(peer, "node_id", ""),
        "consensus": getattr(peer, "consensus", "Unknown"),
        "role": getattr(peer, "role", "Normal"),
    }

    try:
        async with websockets.connect(SIGNALLING_SERVER) as websocket:

            await websocket.send(json.dumps({
                "type": "join_room",
                "room_id": room_id,
                "node": node_info
            }))

            print(f"[SIGNAL] Joined room '{room_id}'")

            async for message in websocket:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    continue

                message_type = data.get("type")

                if message_type == "room_peers":
                    peers = data.get("peers", [])

                    for remote_peer in peers:
                        await connect_discovered_peer(peer, remote_peer)

                elif message_type == "peer_joined":
                    remote_peer = data.get("node", {})

                    print(
                        f"[SIGNAL] New peer joined: "
                        f"{remote_peer.get('name', 'Unknown')}"
                    )

                    await connect_discovered_peer(peer, remote_peer)

                elif message_type == "peer_left":
                    remote_peer = data.get("node", {})

                    print(
                        f"[SIGNAL] Peer left: "
                        f"{remote_peer.get('name', 'Unknown')}"
                    )

                elif message_type == "error":
                    print(
                        f"[SIGNAL] Error: "
                        f"{data.get('message', 'Unknown error')}"
                    )

    except asyncio.CancelledError:
        raise

    except Exception as e:
        print(f"[SIGNAL] Connection error: {e}")


async def connect_discovered_peer(peer, remote_peer):
    remote_name = remote_peer.get("name")
    remote_host = remote_peer.get("host")
    remote_port = remote_peer.get("port")
    remote_node_id = remote_peer.get("node_id")

    if (
        remote_node_id
        and getattr(peer, "node_id", None) == remote_node_id
    ):
        return

    if not remote_host or not remote_port:
        print(
            f"[P2P] Invalid peer information for "
            f"{remote_name or 'Unknown'}"
        )
        return

    try:
        await peer.connect_to_peer(
            remote_host,
            int(remote_port)
        )

        print(
            f"[P2P] Connecting to "
            f"{remote_name or remote_host} "
            f"at {remote_host}:{remote_port}"
        )

    except Exception as e:
        print(
            f"[P2P] Could not connect to "
            f"{remote_name or remote_host}: {e}"
        )


async def update_dashboard_peers(peer):
    while True:
        try:
            peer_count = len(peer.known_peers)

            update_peers(
                peer.name,
                peer_count
            )

            block_count = 0
            transaction_count = 0

            if peer.chain and hasattr(peer.chain, "chain"):
                block_count = len(peer.chain.chain)

                transaction_count = sum(
                    len(block.transactions)
                    for block in peer.chain.chain
                    if hasattr(block, "transactions")
                )

            update_blockchain_stats(
                peer.name,
                block_count,
                transaction_count
            )

        except Exception:
            pass

        await asyncio.sleep(2)


async def run_peer(peer, room_id):

    peer_task = asyncio.create_task(
        peer.start(None, None)
    )

    await asyncio.sleep(1.5)

    signalling_task = asyncio.create_task(
        connect_to_room(peer, room_id)
    )

    dashboard_task = asyncio.create_task(
        update_dashboard_peers(peer)
    )

    try:
        await peer_task

    finally:

        if not signalling_task.done():
            signalling_task.cancel()

        if not dashboard_task.done():
            dashboard_task.cancel()

        try:
            await signalling_task
        except asyncio.CancelledError:
            pass

        try:
            await dashboard_task
        except asyncio.CancelledError:
            pass


def start_peer():

    print("========================================")
    print("     TATHACK BLOCKCHAIN SIMULATOR")
    print("========================================")
    print()

    host = input(
        "Enter Host (example: localhost): "
    ).strip()

    port = int(
        input(
            "Enter Port (example: 5001): "
        ).strip()
    )

    name = input(
        "Enter Name: "
    ).strip()

    consensus = input(
        "Enter Consensus[poa/pos/pow] "
        "(default: pow): "
    ).strip().lower()

    if not consensus:
        consensus = "pow"

    room_id = input(
        "Enter Room ID: "
    ).strip()

    activate_disk_load = input(
        "Do you like to load saved data if any(y/n): "
    ).strip().lower()

    activate_disk_save = input(
        "Do you like to continuously backup data "
        "to disk(y/n): "
    ).strip().lower()

    peer = None
    mal = False

    # =========================
    # PROOF OF AUTHORITY
    # =========================

    if consensus == "poa":

        mal_raw_input = input(
            "Malicious? (y/n): "
        ).strip().lower()

        mal = mal_raw_input == "y"

        if not mal:

            peer = PoAPeer(
                host,
                port,
                name,
                activate_disk_load,
                activate_disk_save
            )

        else:

            peer = PoaMalPeer(
                host,
                port,
                name,
                activate_disk_load,
                activate_disk_save
            )

        peer.name_to_node_id_dict[
            peer.name.lower()
        ] = peer.node_id

        peer.node_id_to_name_dict[
            peer.node_id
        ] = peer.name.lower()

    # =========================
    # PROOF OF STAKE
    # =========================

    elif consensus == "pos":

        mal_raw_input = input(
            "Malicious? (y/n): "
        ).strip().lower()

        mal = mal_raw_input == "y"

        if not mal:

            staker_raw_input = input(
                "Staker? (y/n): "
            ).strip().lower()

            staker = staker_raw_input != "n"

            peer = PoSPeer(
                host,
                port,
                name,
                staker,
                activate_disk_load,
                activate_disk_save
            )

        else:

            peer = PosMalPeer(
                host,
                port,
                name,
                True,
                activate_disk_load,
                activate_disk_save
            )

    # =========================
    # PROOF OF WORK
    # =========================

    else:

        mal_raw_input = input(
            "Malicious? (y/n): "
        ).strip().lower()

        mal = mal_raw_input == "y"

        if not mal:

            miner_raw_input = input(
                "Miner? (y/n): "
            ).strip().lower()

            miner = miner_raw_input != "n"

            peer = PoWPeer(
                host,
                port,
                name,
                miner,
                activate_disk_load,
                activate_disk_save
            )

        else:

            peer = PowMalPeer(
                host,
                port,
                name,
                True,
                activate_disk_load,
                activate_disk_save
            )

    # =========================
    # NODE INFORMATION
    # =========================

    peer.consensus = consensus.upper()

    peer.role = (
        "Malicious"
        if mal
        else "Normal"
    )

    print()
    print("========================================")
    print(" Starting Blockchain Node")
    print("========================================")
    print(f"Node : {name}")
    print(f"Port : {port}")
    print(f"Room : {room_id}")
    print(f"Consensus : {peer.consensus}")
    print(f"Role : {peer.role}")
    print()

    try:

        asyncio.run(
            run_peer(
                peer,
                room_id
            )
        )

    except KeyboardInterrupt:

        print("\nShutting Down...")


if __name__ == "__main__":
    start_peer()
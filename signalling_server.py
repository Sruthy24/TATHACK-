import asyncio
import json
import websockets

from dashboard_state import add_node, remove_node

# room_id -> {websocket: node_info}
rooms = {}


async def signalling_handler(websocket):
    room_id = None
    node_info = None

    try:
        async for raw_message in websocket:
            message = json.loads(raw_message)
            message_type = message.get("type")

            # -----------------------------
            # CREATE / JOIN ROOM
            # -----------------------------
            if message_type in ("create_room", "join_room"):
                room_id = message.get("room_id")
                node_info = message.get("node")

                if not room_id or not node_info:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "room_id and node information are required"
                    }))
                    continue

                if room_id not in rooms:
                    rooms[room_id] = {}

                # Get the nodes already inside this room
                existing_nodes = list(rooms[room_id].values())

                # Add this node
                rooms[room_id][websocket] = node_info
                add_node(node_info)

                # Tell the new node about existing nodes
                await websocket.send(json.dumps({
                    "type": "room_peers",
                    "peers": existing_nodes
                }))

                # Tell existing nodes about the new node
                notification = json.dumps({
                    "type": "peer_joined",
                    "peer": node_info
                })

                for peer_ws in list(rooms[room_id]):
                    if peer_ws != websocket:
                        try:
                            await peer_ws.send(notification)
                        except Exception:
                            pass

                print(
                    f"[ROOM] {node_info.get('name')} "
                    f"joined room '{room_id}'"
                )

            # -----------------------------
            # LEAVE ROOM
            # -----------------------------
            elif message_type == "leave_room":
                break

    except websockets.exceptions.ConnectionClosed:
        pass

    finally:
        # Remove node from room when disconnected
        if room_id and room_id in rooms and websocket in rooms[room_id]:
            leaving_node = rooms[room_id].pop(websocket)
            remove_node(leaving_node)


            print(
                f"[ROOM] {leaving_node.get('name')} "
                f"left room '{room_id}'"
            )

            # Notify remaining nodes
            notification = json.dumps({
                "type": "peer_left",
                "peer": leaving_node
            })

            for peer_ws in list(rooms[room_id]):
                try:
                    await peer_ws.send(notification)
                except Exception:
                    pass

            if not rooms[room_id]:
                del rooms[room_id]


async def main():
    print("========================================")
    print("   TATHACK BLOCKCHAIN SIGNALLING SERVER")
    print("========================================")
    print("Server running on ws://localhost:8765")
    print()

    async with websockets.serve(
        signalling_handler,
        "localhost",
        8765
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSignalling server stopped.")
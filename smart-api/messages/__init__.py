from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect
router = APIRouter(prefix="/messages", tags=["messages"])



class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, booking_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(booking_id, []).append(websocket)

    def disconnect(self, booking_id: int, websocket: WebSocket):
        self.active_connections[booking_id].remove(websocket)

    async def broadcast(self, booking_id: int, message: dict):
        for ws in self.active_connections.get(booking_id, []):
            await ws.send_json(message)

# manager = ConnectionManager()



# ### front end stuff  #####
# const socket = new WebSocket(
#   `ws://localhost:8000/ws/chat/${bookingId}?token=${token}`
# );

# socket.onmessage = (event) => {
#   const msg = JSON.parse(event.data);
#   setMessages(prev => [...prev, msg]);
# };

# socket.send(JSON.stringify({
#   content: "Hello 👋",
#   receiver_id: workerUserId
# }));

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
import json

app = FastAPI()

latest_message = None
clients = []

# WebSocket connection management
async def notify_clients(message: dict):
    if clients:
        for client in clients:
            await client.send_json(message)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            # Wait for a message and keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

# Receive data from the webhook and store it
@app.post("/ql-webhook")
async def receive_ql_result(request: Request):
    global latest_message
    data = await request.json()
    title = data.get("title", "No title")
    content = data.get("content", "No content")

    # Log the received message
    print(f"Received task result: {title} - {content}")

    # Attempt to parse content as JSON and take the first entry
    try:
        if isinstance(content, str):
            content = content.replace("'", '"')  # Replace single quotes with double quotes
        content_dict = json.loads(content)
        first_key = next(iter(content_dict))  # Get the first key
        first_value = content_dict[first_key]  # Get the corresponding value
        processed_content = {first_key: first_value}
    except (json.JSONDecodeError, StopIteration, TypeError):
        processed_content = "Parsing failed"

    latest_message = {"title": title, "content": processed_content}

    # Notify all connected WebSocket clients
    await notify_clients(latest_message)

    return {"status": "ok"}

@app.get("/latest-message")
async def get_latest_message():
    return latest_message if latest_message else {"title": "No new messages", "content": ""}

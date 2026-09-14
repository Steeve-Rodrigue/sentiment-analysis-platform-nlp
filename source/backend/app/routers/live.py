"""
source/backend/app/routers/live.py

WS /api/live -- section "live" de la page principale. S'abonne au
diffuseur (broadcast.py), qui recoit ses messages de la tache de
fond Kafka -- ne consomme jamais Kafka directement, aucune
persistance.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.broadcast import broadcaster

router = APIRouter(prefix="/api/live", tags=["live"])


@router.websocket("")
async def live_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = broadcaster.subscribe()
    try:
        while True:
            message = await queue.get()
            await websocket.send_json(message.model_dump())
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe(queue)

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from pyrogram import Client

app = FastAPI()

API_ID = int(os.getenv("API_ID", "30900388"))
API_HASH = os.getenv("API_HASH", "28d5e5fc5ab1d20b575b951917b8871b")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "pelis_rolo_family")

bot = None

@app.on_event("startup")
async def startup_event():
    global bot
    bot = Client("family_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
    await bot.start()

@app.on_event("shutdown")
async def shutdown_event():
    if bot:
        await bot.stop()

@app.get("/")
async def root():
    return {"status": "Servidor Familiar Activo"}

@app.get("/stream/{message_id}")
async def stream_video(message_id: int, request: Readout := None, request: Request = None):
    try:
        message = await bot.get_messages(CHANNEL_NAME, message_id)
        if not message or not message.video:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        file_size = message.video.file_size
        range_header = request.headers.get("range")
        
        start = 0
        end = file_size - 1
        
        if range_header:
            range_match = range_header.replace("bytes=", "").split("-")
            if range_match[0]:
                start = int(range_match[0])
            if len(range_match) > 1 and range_match[1]:
                end = int(range_match[1])
        
        async def file_stream():
            async for chunk in bot.stream_media(message, offset=start, limit=end - start + 1):
                yield chunk
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": message.video.mime_type or "video/mp4",
        }
        
        return StreamingResponse(file_stream(), status_code=206, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

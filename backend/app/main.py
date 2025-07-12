import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .fish.server import routes
from .fish.utils.logs import CustomLogFormatter

load_dotenv()

ch = logging.StreamHandler()
ch.setFormatter(CustomLogFormatter())

logger = logging.getLogger()
logger.addHandler(ch)

if os.getenv("DEBUG") == "True":
    logger.setLevel(logging.DEBUG)

app = FastAPI(debug=os.getenv("DEBUG") == "True")
app.include_router(routes.router)

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="assets")
templates = Jinja2Templates(directory="templates")

@app.get("/health")
def health():
    return { "Hello": "World", "timestamp": datetime.now(timezone.utc) }

@app.get("/")
async def serve_spa(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

import asyncio
from contextlib import asynccontextmanager
import json
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
import RootAdministrator.endpoints
import Authentication.endpoints
import GroupObjects.endpoints
import Object.endpoints
import RecordObject.endpoints
import FieldObject.endpoints
import MailService.endpoints
import InboundRule.endpoints
import DatasetAI.endpoints
import Workflow.endpoints
import Action.endpoints
import CustomViewRecord.endpoints
import os
import platform
from dotenv import load_dotenv

from app.tasks import monitor_tasks

load_dotenv()

if platform.system() == 'Windows':
    print("TRUE")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run at startup
    # asyncio.create_task(monitor_tasks(clients))
    # yield
    print('Shutting down...')

app = FastAPI(lifespan=lifespan)

origins = [
    'http://localhost:3000',
    'http://localhost:8000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
#     if isinstance(exc.detail, dict):
#         content = {
#             'error_code': exc.detail['error_code'],
#             'description': exc.detail['description']
#         }
#     else:
#         content = {
#             'error_code': None,
#             'description': exc.detail
#         }
        
#     return JSONResponse(
#         content=content,
#         status_code=exc.status_code
#     )

# app.add_exception_handler(HTTPException, http_error_handler)

clients = []

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url=os.environ.get("DOCS_ROUTE"))

@app.websocket("/ws") # ws://127.0.0.1:8000/ws
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)

# Include Routers
app.include_router(Authentication.endpoints.router, prefix="/api/authen", tags=["Authentication"])
app.include_router(RootAdministrator.endpoints.router, prefix="/api/root", tags=["Root Administrator"])
app.include_router(GroupObjects.endpoints.router, prefix="/api/group-objects", tags=["Group Objects"])
app.include_router(Object.endpoints.router, prefix="/api/object", tags=["Object"])
app.include_router(RecordObject.endpoints.router, prefix="/api/record", tags=["Record"])
app.include_router(FieldObject.endpoints.router, prefix="/api/field-object", tags=["Field Object"])
app.include_router(MailService.endpoints.router, prefix="/api/mail", tags=["Mail"])
app.include_router(InboundRule.endpoints.router, prefix="/api/inbound-rule", tags=["Inbound Rule"])
app.include_router(Workflow.endpoints.router, prefix="/api/workflow", tags=["Workflow"])
app.include_router(Action.endpoints.router, prefix="/api/action", tags=["Action"])
app.include_router(DatasetAI.endpoints.router, prefix="/api/ai-dataset", tags=["AI Dataset"])
app.include_router(CustomViewRecord.endpoints.router, prefix="/api/view-record", tags=["Custom View Record"])
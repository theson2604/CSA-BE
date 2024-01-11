from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from app.settings.config import ServerConfig
import RootAdministrator.endpoints
import Authentication.endpoints
import GroupObjects.endpoints

app = FastAPI()

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

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url=ServerConfig.DOCS_ROUTE)

# Include Routers
app.include_router(Authentication.endpoints.router, prefix="/api/authen", tags=["Authentication"])
app.include_router(RootAdministrator.endpoints.router, prefix="/api/root", tags=["Root Administrator"])
app.include_router(GroupObjects.endpoints.router, prefix="/api/group-objects", tags=["Group Objects"]) 
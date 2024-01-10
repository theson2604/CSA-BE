from fastapi import FastAPI
from starlette.responses import RedirectResponse
from app.settings.config import ServerConfig
import RootAdministrator.endpoints
import Authentication.endpoints

app = FastAPI()

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url=ServerConfig.DOCS_ROUTE)

# Include Routers
app.include_router(Authentication.endpoints.router, prefix="/api/authen", tags=["Authentication"])
app.include_router(RootAdministrator.endpoints.router, prefix="/api/root", tags=["Root Administrator"]) 
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from app.settings.config import ServerConfig
import RootAdministrator.endpoints
import Authentication.endpoints
import GroupObjects.endpoints
import Object.endpoints

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

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url=ServerConfig.DOCS_ROUTE)

# Include Routers
app.include_router(Authentication.endpoints.router, prefix="/api/authen", tags=["Authentication"])
app.include_router(RootAdministrator.endpoints.router, prefix="/api/root", tags=["Root Administrator"])
app.include_router(GroupObjects.endpoints.router, prefix="/api/group-objects", tags=["Group Objects"])
app.include_router(Object.endpoints.router, prefix="/api/object", tags=["Object"])
app.include_router(Object.endpoints.router, prefix="/api/record", tags=["Record"])
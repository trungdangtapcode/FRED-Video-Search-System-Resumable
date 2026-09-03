from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path

app = FastAPI()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(os.getenv("STATIC_ROOT", PROJECT_ROOT / "data")).resolve()

# --- CORS settings ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or ["http://localhost:3000"] if you want to restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Example API route ---
@app.post("/search")
async def search(request: Request):
    body = await request.json()
    # Do something with the request payload
    return JSONResponse({"message": "Search received", "data": body})

# --- Static files ---
class CORSEnabledStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        return response

app.mount(
    "/",
    CORSEnabledStaticFiles(directory=str(ROOT_DIR), html=True, follow_symlink=True),
    name="static",
)

if __name__ == "__main__":
    uvicorn.run(
        "static_server.run:app",
        host=os.getenv("STATIC_HOST", "127.0.0.1"),
        port=int(os.getenv("STATIC_PORT", "8069")),
        reload=False,
    )

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

ROOT_DIR = "/data/root"

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
    CORSEnabledStaticFiles(directory=ROOT_DIR, html=True, follow_symlink=True),
    name="static",
)

if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8069, reload=True)
    uvicorn.run("static_server.run:app", host="0.0.0.0", port=8069, reload=True)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# Serve symlinks too
app.mount(
    "/", 
    StaticFiles(directory="/home/root", html=True, follow_symlink=True), 
    name="static"
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8069, reload=True)

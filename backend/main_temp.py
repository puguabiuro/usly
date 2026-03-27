from fastapi import FastAPI
from fastapi.responses import FileResponse
app = FastAPI()

@app.get("/api/legal/terms_pl")
def get_terms_pl():
    return FileResponse("legal/terms_pl.md")

@app.get("/api/legal/terms_en")
def get_terms_en():
    return FileResponse("legal/terms_en.md")

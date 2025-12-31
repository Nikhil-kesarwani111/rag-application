from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from starlette.staticfiles import StaticFiles
import os
import shutil
import subprocess

from app.rag_chain import final_chain

app = FastAPI()

# -----------------------------------------
# CORS FOR FRONTEND
# -----------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------
# FIX PATHS (GLOBAL)
# -----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.abspath(os.path.join(BASE_DIR, "../pdf-documents"))
SCRIPT_PATH = os.path.abspath(os.path.join(BASE_DIR, "../rag-data-loader/rag_load_and_process.py"))

print("📂 PDF Directory:", PDF_DIR)
print("📜 Script Path:", SCRIPT_PATH)

# Make sure pdf directory exists
os.makedirs(PDF_DIR, exist_ok=True)

# Serve static PDFs
app.mount("/rag/static", StaticFiles(directory=PDF_DIR), name="static")


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


# -----------------------------------------
# UPLOAD PDF API
# -----------------------------------------
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        try:
            save_path = os.path.join(PDF_DIR, file.filename)
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            saved_files.append(file.filename)
            print("📥 Saved file:", save_path)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"❌ Could not save file: {e}")

    return {"message": "Files uploaded successfully", "filenames": saved_files}


# -----------------------------------------
# LOAD + PROCESS PDFS (run ingestion script)
# -----------------------------------------
@app.post("/load-and-process-pdfs")
async def load_and_process_pdfs():
    try:
        # ✔ Use Poetry venv Python
        VENV_PYTHON = r"C:\Users\nikhi\AppData\Local\pypoetry\Cache\virtualenvs\rag-application-hxf4MHVb-py3.11\Scripts\python.exe"

        script_path = os.path.join(os.getcwd(), "rag-data-loader", "rag_load_and_process.py")

        print("▶ Running ingestion with:", VENV_PYTHON)
        print("📜 Script Path:", script_path)

        result = subprocess.run(
            [VENV_PYTHON, script_path], 
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("❌ Script Error:", result.stderr)
            return {"error": "Script failed", "details": result.stderr}

        print("✅ Script Output:", result.stdout)
        return {"message": "PDFs loaded and processed successfully"}

    except Exception as e:
        print("🔥 Unexpected Error:", e)
        return {"error": str(e)}

# -----------------------------------------
# ADD LANGSERVE RAG ROUTE
# -----------------------------------------
add_routes(app, final_chain, path="/rag")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

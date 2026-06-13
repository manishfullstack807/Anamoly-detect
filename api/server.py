import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agent.memory import memory
from agent.main import run_agent
from agent.verify import verify

Path("data").mkdir(exist_ok=True)

app = FastAPI(title="Supply Chain CLAW API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def root():
    return {"status": "Supply Chain CLAW is running"}


@app.get("/decisions")
def get_decisions():
    return memory.get_all()


@app.post("/run")
def trigger_run(payload: dict = {}):
    api_key = payload.get("api_key") or None
    model = payload.get("model") or None
    result = run_agent(api_key=api_key, model=model)
    return {
        "anomalies": result["anomalies"],
        "reasoning": result["reasoning"],
        "action": result["action"],
        "model_used": model or "meta/llama-3.1-8b-instruct"
    }


@app.get("/health")
def health():
    return {"status": "ok", "memory_count": memory.collection.count()}


@app.post("/verify")
def verify_agent(payload: dict):
    return verify(payload.get("anomalies", ""))


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".xlsx")):
        return {"error": "Only CSV or Excel files allowed"}
    
    file_path = f"data/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "uploaded"}

from dotenv import load_dotenv
import sys
import os
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest, ChatResponse
from orchestrator import process_query

app = FastAPI(
    title="FinOps Local Cost Chatbot",
    version="0.2.0",
)

# Allow frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # consider restricting later
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.on_event("startup")
async def startup_event():
    # Read environment variable in ALL uvicorn worker processes
    app.state.cli_arg = os.getenv("CLI_ARG")
    if not app.state.cli_arg:
        raise Exception("Please provide model")
    print("→ Server started with CLI_ARG =", app.state.cli_arg)

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Read CLI argument passed during python3 main.py XYZ
    model_name = app.state.cli_arg

    # Attach to request (optional)
    req.model = model_name

    return await process_query(data=req)


if __name__ == '__main__':
     # Read the argument passed → python3 main.py XYZ
    arg_value = sys.argv[1] if len(sys.argv) > 1 else None

    print("Argument received:", arg_value)
    # Store into environment (survives reload mode)
    os.environ["CLI_ARG"] = arg_value
    import uvicorn
    uvicorn.run(app = 'main:app',host = '0.0.0.0',port = 8000,reload = True)
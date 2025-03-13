# Standard libraries
import logging
import threading
from contextlib import asynccontextmanager

# FastAPI libraries
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Pydantic library
from pydantic import BaseModel

# Uvicorn library
import uvicorn

logging.basicConfig(
    filename=r'logs\errors.log',  
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Variáveis de configuração
SERVER_HOST = "localhost"
SERVER_PORT = 5000

# Estrutura de comunicação thread-safe
class ApprovalState:
    def __init__(self):
        self.event = threading.Event()
        self.value = None
        self.data = ""
        self.lock = threading.Lock()

    def update_value(self, new_value: bool, data: str = ""):
        with self.lock:
            self.value = new_value
            self.data = data
            self.event.set()

    def aguardar_valor(self):
        self.event.wait()
        with self.lock:
            self.event.clear()
            return self.value, self.data

state = ApprovalState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização do servidor
    yield
    # Limpeza ao encerrar
    print("\nServer shutting down normally...")

def create_application():
    app = FastAPI(lifespan=lifespan)

    # Configuração CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # Ajuste para seus domínios
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

    return app

app = create_application()

class RequestData(BaseModel):
    Approved: bool
    Data: str

@app.post('/approve_changes')
async def receive_approval(data: RequestData):
    try:
        state.update_value(data.Approved, data.Data)
        return {"status": "success", "code": 200}
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_server():
    config = uvicorn.Config(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        timeout_keep_alive=600,
        timeout_graceful_shutdown=30
    )
    server = uvicorn.Server(config)
    server.run()

def server_init():
    # Inicialização do servidor em thread separada
    server_thread = threading.Thread(
        target=run_server,
        daemon=True
    )
    server_thread.start()

def approve_changes():
    try:
        approved, data = state.aguardar_valor()            
    except KeyboardInterrupt:
        print("\nInterruption received, closing...")
    finally:
        print("Processing completed.")
        return approved, data

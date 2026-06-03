import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from .database import init_db
from .ingest import router as ingest_router
from .health import router as health_router
from .metrics import router as metrics_router
from .funnel import router as funnel_router
from .anomalies import router as anomalies_router
from .heatmap import router as heatmap_router
from .frontend import router as frontend_router
from .pos import router as pos_router
from .stream import router as stream_router

logger = logging.getLogger("store_api")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        print("\n" + "="*60)
        print("🚀 STORE INTELLIGENCE SYSTEM IS LIVE!")
        print("="*60)
        print("👉 Live Dashboard: http://localhost:8000/dashboard")
        print("👉 API Docs:       http://localhost:8000/docs")
        print("="*60 + "\n")
    except Exception as e:
        logger.error(f"DB Init error: {e}")
    yield

app = FastAPI(title='Store Intelligence API', lifespan=lifespan)

@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    response = None
    event_count = None
    try:
        if request.url.path == '/events/ingest' and request.method == 'POST':
            # read body to count events
            try:
                body = await request.json()
                event_count = len(body.get('events', []))
            except Exception:
                pass
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        store_id = request.path_params.get("id", "N/A")
        if event_count is not None:
            logger.info(f"trace_id={trace_id} store_id={store_id} endpoint={request.url.path} latency_ms={latency_ms} event_count={event_count} status_code={status_code}")
        else:
            logger.info(f"trace_id={trace_id} store_id={store_id} endpoint={request.url.path} latency_ms={latency_ms} status_code={status_code}")

    if response:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content={"error": "Database unavailable", "detail": "Service is experiencing degradation."}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=503,
        content={"error": "Service unavailable", "detail": "An internal error occurred."}
    )

@app.get('/', include_in_schema=False)
async def root():
    return RedirectResponse(url='/dashboard')

from sqlmodel import Session
from sqlalchemy import text
from .database import engine

@app.post('/api/reset_db')
def reset_db():
    with Session(engine) as session:
        session.execute(text("DELETE FROM event"))
        session.execute(text("DELETE FROM visitorsession"))
        session.execute(text("DELETE FROM posrecord"))
        session.commit()
    return {"status": "Database cleared"}

app.include_router(frontend_router)
app.include_router(ingest_router, prefix='/events')
app.include_router(pos_router, prefix='/pos')
app.include_router(health_router, prefix='/health')
app.include_router(metrics_router, prefix='/stores')
app.include_router(funnel_router, prefix='/stores')
app.include_router(heatmap_router, prefix='/stores')
app.include_router(anomalies_router, prefix='/stores')
app.include_router(stream_router, prefix='/stores')

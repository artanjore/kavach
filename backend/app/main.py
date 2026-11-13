import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine
from .models import ScamNumber
from .risk.phone import normalize
from .routers import admin, bank, protect, users, whatsapp

logging.basicConfig(level=logging.INFO)
SEED = Path(__file__).resolve().parent.parent / "data" / "scam_numbers_seed.json"


def seed(db: Session) -> None:
    if not SEED.exists():
        return
    for item in json.loads(SEED.read_text())["numbers"]:
        n = normalize(item["number"])
        if not db.get(ScamNumber, n):
            db.add(ScamNumber(number=n, category=item.get("category", ""), source="seed"))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # use Alembic migrations once the schema settles
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="Kavach API", version="0.1.0", lifespan=lifespan)
for r in (users.router, protect.router, whatsapp.router, bank.router, admin.router):
    app.include_router(r)


@app.get("/healthz")
def health():
    return {"ok": True}

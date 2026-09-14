import os, pathlib, aiosqlite

DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent / "smcpe.db"))

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA foreign_keys=ON;")
    return db

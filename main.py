

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from database import database, sensor_readings, create_tables
from schemas import SensorReadingIn, SensorReadingOut


# Startup & shutdown logic

@asynccontextmanager
async def lifespan(app: FastAPI):
  
    create_tables()             # 1: synchronous, runs once
    await database.connect()    # 2: opens the async pool
    yield                       # app is running 
    await database.disconnect() # 3: clean teardown


# App Instance
app = FastAPI(
    title="Sensor Ingestion Service",
    description=(
        "A lightweight FastAPI service that ingests environmental sensor "
        "readings and stores them in SQLite."
    ),
    version="1.0.0",
    lifespan=lifespan,
)



# POST /readings  Add a new sensor reading
@app.post(
    "/readings",
    response_model=SensorReadingOut,
    status_code=201,            
    summary="Submit a sensor reading",
)
async def create_reading(payload: SensorReadingIn):
    """
    Accept a JSON body with sensor_id, timestamp, and reading.

    """
    # Convert the datetime object to an ISO string for storage.
    timestamp_str = payload.timestamp.isoformat()

    # Build and execute the INSERT statement.
    insert_query = sensor_readings.insert().values(
        sensor_id=payload.sensor_id,
        timestamp=timestamp_str,
        reading=payload.reading,
    )

    try:
        last_id = await database.execute(insert_query)
    except Exception as exc:
        # Catch any unexpected DB errors and send error 500
        raise HTTPException(
            status_code=500,
            detail=f"Database write failed: {str(exc)}",
        )

    # Fetch the newly created row to include server-generated columns.
    select_query = sensor_readings.select().where(sensor_readings.c.id == last_id)
    row = await database.fetch_one(select_query)

    return SensorReadingOut(
        id=row["id"],
        sensor_id=row["sensor_id"],
        timestamp=row["timestamp"],
        reading=row["reading"],
        ingested_at=row["ingested_at"],
    )


# GET /readings  Retrieve stored readings (with optional filters)
@app.get(
    "/readings",
    response_model=list[SensorReadingOut],
    summary="List sensor readings",
)
async def list_readings(
    sensor_id: str | None = Query(default=None, description="Filter by sensor ID"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max rows to return"),
):
   
    query = sensor_readings.select().order_by(sensor_readings.c.id.desc()).limit(limit)

    if sensor_id:
        query = query.where(sensor_readings.c.sensor_id == sensor_id)

    rows = await database.fetch_all(query)

    return [
        SensorReadingOut(
            id=row["id"],
            sensor_id=row["sensor_id"],
            timestamp=row["timestamp"],
            reading=row["reading"],
            ingested_at=row["ingested_at"],
        )
        for row in rows
    ]


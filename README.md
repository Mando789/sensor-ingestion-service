# Sensor Ingestion Service

A lightweight FastAPI service that acts as the main entry point for environmental metrics collected from multiple external sensors. It accepts JSON payloads containing sensor readings and persists them to a SQLite database.
 
## Project Structure
 
```
sensor-ingestion-service/
├── main.py            # FastAPI app, endpoints, lifespan events
├── database.py        # DB connection, table schema (SQLAlchemy Core)
├── schemas.py         # Pydantic models for request/response validation
├── requirements.txt   # Python dependencies
└── README.md
```

## Prerequisites
 
- Python 3.10 or higher
 
## How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mando789/sensor-ingestion-service.git
   cd sensor-ingestion-service
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   venv\Scripts\activate           # Windows
   ```
 
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
 
4. **Start the server with Uvicorn:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Test the endpoint:**

**Interactive API Docs** Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to explore and test all endpoints via Swagger UI.

OR

   ```bash
   curl -X POST http://localhost:8000/readings \
     -H "Content-Type: application/json" \
     -d '{"sensor_id": "sensor-42", "timestamp": "2025-03-29T14:30:00Z", "reading": 23.7}'
   ```

## API Endpoints
 
| Method | Path        | Description                        |
|--------|-------------|------------------------------------|
| POST   | `/readings` | Submit a new sensor reading        |
| GET    | `/readings` | List stored readings (with filters)|



### POST /readings – Request Body
 
```json
{
  "sensor_id": "sensor-42",
  "timestamp": "2025-03-29T14:30:00Z",
  "reading": 23.7
}
```
 
### POST /readings – Response (201 Created)
 
```json
{
  "id": 1,
  "sensor_id": "sensor-42",
  "timestamp": "2025-03-29T14:30:00Z",
  "reading": 23.7,
  "ingested_at": "2025-03-29 14:30:05"
}
```


## The Scaling Question

Scaling from 10 to 10,000 would be problem while using SQLite due to the file-level lock that orders writes. Below are some solutions I'd use to solve such an issue:

### 1. Replace SQLite with a Production Database
Switch to PostgreSQL, AWS RDS, or any equivalent. Such databases can manage thousands writes concurrently.

### 2. Introduce Asynchronous Message Queue
Endpoint would send each reading to a message broker such Apache Kafka instead of writing right away in the DB inside the HTTP request. Workers would then batch insert from the queue to the database. If the database is temporarily slow, messages would accumulate in the queue rather than causing HTTP timeouts. This will provide back pressure handling and separate ingestion throughput from database write speed.

### 3. Batch Inserts
Batch inserts are faster than individual ones as they reduce the number of round trips and transaction commits. Workers would collect readings into batches and insert them as a single transaction.

### 4. Horizontal Scaling of the API layer
Run multiple instances of the FastAPI service behind a load balancer. Since the endpoint is stateless, just publish to the queue, such a solution will be straightforward and scales linearly with incoming traffic.

### 5. Time-series Optimised Storage (Optional)
For analytical queries at this volume, consider a time-series database such as TimescaleDB (a PostgreSQL extension) or InfluxDB. They are mainly designed for append-heavy workloads and offer automatic partitioning by time, efficient compression, and built-in downsampling.


## Assumptions
1. **Timestamps are provided in ISO 8601 format** and can include timezone information. The service stores them as strings to preserve the original format sent by the sensor.
2. **A single reading per request.** The current endpoint accepts one reading at a time. For the scaled architecture, a batch endpoint (accepting an array of readings) would reduce HTTP overhead.
3. **The `reading` field is a generic float.** The service does not enforce domain-specific bounds (e.g. temperature between -50 and 60) because different sensor types measure different things. Domain validation could be added per sensor type. 4. **No authentication.** This prototype does not implement API keys or tokens. In production, each sensor would authenticate via an API key or mutual TLS.
4. **No authentication.** This prototype does not implement API keys or tokens.
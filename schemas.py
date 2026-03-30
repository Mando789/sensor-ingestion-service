"""
Pydantic models for request and response validation.

"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SensorReadingIn(BaseModel):
    """
    Schema for the incoming JSON payload.

    Example valid JSON:
    {
        "sensor_id": "sensor-42",
        "timestamp": "2025-03-29T14:30:00Z",
        "reading": 23.7
    }
    """

    sensor_id: str = Field(
        ...,                        
        min_length=1,              
        max_length=64,             
        description="Unique identifier of the sensor",
        examples=["sensor-42"],
    )

    timestamp: datetime = Field(
        ...,
        description="Measurement time in ISO 8601 format",
        examples=["2025-03-29T14:30:00Z"],
    )

    reading: float = Field(
        ...,
        description="The measured environmental value",
        examples=[23.7],
    )

 
    # Custom validator
    @field_validator("timestamp")
    @classmethod
    def timestamp_not_in_future(cls, value: datetime) -> datetime:
    
        # Make the comparison timezone-naive for simplicity.
        now = datetime.utcnow()
        naive_value = value.replace(tzinfo=None) if value.tzinfo else value
        if naive_value > now:
            raise ValueError("Timestamp cannot be in the future")
        return value


class SensorReadingOut(BaseModel):
    """
    Schema for the response we send back after a successful insert.

    Mirrors the input fields plus the server-generated 'id' and 'ingested_at'.
    Returning the 'id' lets the caller confirm the record was stored and
    reference it later if needed.
    """

    id: int
    sensor_id: str
    timestamp: str
    reading: float
    ingested_at: str
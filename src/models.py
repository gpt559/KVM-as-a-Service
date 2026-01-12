from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

class SwitchRequest(BaseModel):
    """
    Request model for switching KVM ports.
    """
    port: int = Field(..., ge=1, le=8, description="Target Port ID (1-8)")

class BuzzerRequest(BaseModel):
    """
    Request model for controlling the buzzer.
    """
    state: Literal["on", "off"]

class ConfigRequest(BaseModel):
    """
    Request model for updating KVM configuration.
    """
    protocol: Optional[Literal["enterprise", "consumer_a", "consumer_b", "matrix", "dual_monitor_hex"]] = None
    baudrate: Optional[Literal[9600, 38400, 115200]] = None
    terminator: Optional[Literal["none", "cr", "lf", "crlf"]] = None

class SuccessResponse(BaseModel):
    """
    Standard success response model.
    """
    status: str = "success"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """
    Standard error response model.
    """
    status: str = "error"
    code: str
    detail: str

class TestLog(BaseModel):
    """
    Log entry for a manual test step.
    """
    action: str
    status: Literal["success", "failed", "skipped"]
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TestResponse(BaseModel):
    """
    Response model for the manual test run.
    """
    status: str = "completed"
    logs: list[TestLog]

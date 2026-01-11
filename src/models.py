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
    terminator: Optional[Literal["none", "cr", "crlf"]] = None

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

from fastapi import FastAPI, HTTPException, Request, Depends, status as http_status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from src.serial_manager import SerialManager
from src.controller_service import ControllerService
from src.models import (
    SwitchRequest,
    BuzzerRequest,
    ConfigRequest,
    SuccessResponse,
    ErrorResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for services
serial_manager = None
controller_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the FastAPI application.
    Initializes the serial connection and controller service on startup.
    Clean up is handled automatically when the process exits.
    """
    global serial_manager, controller_service
    
    # Startup
    logger.info("Starting up KVM Service...")
    try:
        # Initialize Serial Manager (using default port/baud from SerialManager defaults or env vars)
        serial_manager = SerialManager()
        if serial_manager.connect():
            logger.info(f"Serial connection established on {serial_manager.port}")
        else:
            logger.warning(f"Could not establish initial serial connection on {serial_manager.port}. Will retry on first command.")
        
        # Initialize Controller Service
        controller_service = ControllerService(serial_manager)
        logger.info("Controller Service initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # We don't raise here to allow the API to start even if hardware is offline,
        # but endpoints will fail gracefully or return 503.
    
    yield
    
    # Shutdown
    logger.info("Shutting down KVM Service...")
    if serial_manager:
        serial_manager.disconnect()
        logger.info("Serial connection closed")


app = FastAPI(
    title="KVM-as-a-Service API",
    description="API for controlling TESmart KVM Switch via Serial",
    version="1.0.0",
    lifespan=lifespan
)

# Dependency to get controller service
def get_controller() -> ControllerService:
    if controller_service is None:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Controller service not initialized (Hardware offline?)"
        )
    return controller_service

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            code="INTERNAL_ERROR",
            detail=str(exc)
        ).dict()
    )

@app.post(
    "/api/v1/config",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
async def update_config(
    request: ConfigRequest,
    controller: ControllerService = Depends(get_controller)
):
    """
    Update KVM configuration (Protocol, Baudrate, Terminator).
    """
    try:
        controller.update_config(
            protocol=request.protocol,
            baudrate=request.baudrate,
            terminator=request.terminator
        )
        
        msg_parts = []
        if request.protocol:
            msg_parts.append(f"Protocol set to {request.protocol}")
        if request.baudrate:
            msg_parts.append(f"Baudrate set to {request.baudrate}")
        if request.terminator:
            msg_parts.append(f"Terminator set to {request.terminator}")
            
        return SuccessResponse(
            message=", ".join(msg_parts) if msg_parts else "No changes made"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Configuration failed: {str(e)}"
        )

@app.post(
    "/api/v1/switch",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
async def switch_port(
    request: SwitchRequest,
    controller: ControllerService = Depends(get_controller)
):
    """
    Switch the KVM to a specific port (1-8).
    """
    try:
        controller.switch_port(request.port)
        return SuccessResponse(
            message=f"Switched to Port {request.port}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotImplementedError as e:
         raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e)
        )
    except Exception as e:
        # Hardware/Serial errors
        logger.error(f"Switch port failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Hardware communication failed: {str(e)}"
        )

@app.post(
    "/api/v1/buzzer",
    response_model=SuccessResponse,
    responses={
        503: {"model": ErrorResponse}
    }
)
async def control_buzzer(
    request: BuzzerRequest,
    controller: ControllerService = Depends(get_controller)
):
    """
    Turn the KVM buzzer on or off.
    """
    try:
        controller.control_buzzer(request.state)
        return SuccessResponse(
            message=f"Buzzer turned {request.state}"
        )
    except NotImplementedError as e:
         raise HTTPException(
            status_code=http_status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Buzzer control failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Hardware communication failed: {str(e)}"
        )

@app.get(
    "/api/v1/status",
    responses={
        503: {"model": ErrorResponse}
    }
)
async def get_status(
    controller: ControllerService = Depends(get_controller)
):
    """
    Get the health status of the KVM service.
    """
    status_info = controller.check_status()
    
    if status_info["status"] != "healthy":
        # We can return 503 if unhealthy, or 200 with status="unhealthy"
        # Design choice: Let's return 200 with status info so client can see details,
        # unless the controller itself is completely broken.
        pass
        
    return status_info

# Mount static files (Frontend UI)
# Mount at root "/" but be careful not to override API routes. 
# FastAPI checks routes in order, but StaticFiles on "/" acts as a catch-all.
# A common pattern is to mount static on "/static" or "/ui", but to serve index.html at root,
# we can mount it at root and it will serve index.html for "/".
# However, explicit API routes defined above/below will take precedence if they match specific paths.
# Since our API is at /api/v1, there is no conflict.
app.mount("/", StaticFiles(directory="static", html=True), name="static")

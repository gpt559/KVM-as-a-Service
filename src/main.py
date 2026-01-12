from fastapi import FastAPI, HTTPException, Request, Depends, status as http_status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import asyncio

from src.serial_manager import SerialManager
from src.controller_service import ControllerService
from src.constants import Protocol
from src.models import (
    SwitchRequest,
    BuzzerRequest,
    ConfigRequest,
    LightModeRequest,
    FanModeRequest,
    AudioSourceRequest,
    AudioFollowRequest,
    UsbFocusRequest,
    NetworkControlRequest,
    FeatureToggleRequest,
    SuccessResponse,
    ErrorResponse,
    TestResponse,
    TestLog
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

@app.post("/api/v1/light", response_model=SuccessResponse)
async def set_light_mode(request: LightModeRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_light_mode(request.mode)
        return SuccessResponse(message=f"Light mode set to {request.mode}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/fan", response_model=SuccessResponse)
async def set_fan_mode(request: FanModeRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_fan_mode(request.mode)
        return SuccessResponse(message=f"Fan mode set to {request.mode}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/audio/source", response_model=SuccessResponse)
async def set_audio_source(request: AudioSourceRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_audio_source(request.port)
        return SuccessResponse(message=f"Audio source set to PC{request.port}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/audio/follow", response_model=SuccessResponse)
async def set_audio_follow(request: AudioFollowRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_audio_follow(request.enabled)
        return SuccessResponse(message=f"Audio follow {'enabled' if request.enabled else 'disabled'}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/network", response_model=SuccessResponse)
async def set_network_power(request: NetworkControlRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_network_power(request.port, request.enabled)
        return SuccessResponse(message=f"Network for PC{request.port} {'enabled' if request.enabled else 'disabled'}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/usb/focus", response_model=SuccessResponse)
async def set_usb_focus(request: UsbFocusRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_usb_focus(request.target)
        return SuccessResponse(message=f"USB focus switched to {request.target}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/system/autodetect", response_model=SuccessResponse)
async def set_autodetect(request: FeatureToggleRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_feature_state("AUTODETECT", request.enabled, "Auto-detect")
        return SuccessResponse(message=f"Auto-detect {'enabled' if request.enabled else 'disabled'}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/system/autoscan", response_model=SuccessResponse)
async def set_autoscan(request: FeatureToggleRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_feature_state("AUTOSCAN", request.enabled, "Auto-scan")
        return SuccessResponse(message=f"Auto-scan {'enabled' if request.enabled else 'disabled'}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/usb/compatibility", response_model=SuccessResponse)
async def set_usb_compatibility(request: FeatureToggleRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_feature_state("USB_COMPAT", request.enabled, "USB Compatibility Mode")
        return SuccessResponse(message=f"USB Compatibility Mode {'enabled' if request.enabled else 'disabled'}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/v1/usb/mouse-middle", response_model=SuccessResponse)
async def set_mouse_middle(request: FeatureToggleRequest, controller: ControllerService = Depends(get_controller)):
    try:
        controller.set_feature_state("MOUSE_MIDDLE", request.enabled, "Mouse Middle Button")
        return SuccessResponse(message=f"Mouse Middle Button {'enabled' if request.enabled else 'disabled'}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

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

@app.post(
    "/api/v1/test/permutations",
    response_model=TestResponse,
    responses={
        503: {"model": ErrorResponse}
    }
)
async def run_test_permutations(
    controller: ControllerService = Depends(get_controller)
):
    """
    Manual Test: Run all permutations of configurations (Protocol, Baudrate, Terminator).
    For each configuration, attempts to switch between Port 1 and Port 2.
    """
    logs = []

    # Save original config to restore later
    status = controller.check_status()
    original_protocol = status.get('protocol')
    original_baud = status.get('baudrate')
    original_terminator = status.get('terminator')
    
    # Define permutations
    protocols = [p.value for p in Protocol]
    baudrates = [115200, 9600, 38400]
    terminators = ["none", "cr", "lf", "crlf"]
    
    # Total permutations = 5 * 3 * 3 = 45.
    # Each has 2 switches + delays. 45 * 1.5s approx = ~70 seconds.
    # This is long, but acceptable for a manual "Run All" test.

    try:
        for baud in baudrates:
            for protocol in protocols:
                for terminator in terminators:
                    
                    config_desc = f"Baud={baud}, Proto={protocol}, Term={terminator}"
                    
                    # 1. Update Configuration
                    try:
                        controller.update_config(protocol=protocol, baudrate=baud, terminator=terminator)
                    except Exception as e:
                        logs.append(TestLog(
                            action=f"Config: {config_desc}",
                            status="failed",
                            detail=f"Failed to set config: {str(e)}"
                        ))
                        continue

                    # 2. Test Port 1
                    try:
                        controller.switch_port(1)
                        logs.append(TestLog(
                            action=f"Switch Port 1",
                            status="success",
                            detail=f"Sent (No HW Feedback) - {config_desc}"
                        ))
                    except Exception as e:
                        logs.append(TestLog(
                            action=f"Switch Port 1",
                            status="failed",
                            detail=f"{config_desc}: {str(e)}"
                        ))
                    
                    await asyncio.sleep(0.2)

                    # 3. Test Port 2
                    try:
                        controller.switch_port(2)
                        logs.append(TestLog(
                            action=f"Switch Port 2",
                            status="success",
                            detail=f"Sent (No HW Feedback) - {config_desc}"
                        ))
                    except Exception as e:
                        logs.append(TestLog(
                            action=f"Switch Port 2",
                            status="failed",
                            detail=f"{config_desc}: {str(e)}"
                        ))

                    await asyncio.sleep(0.2)
                    
    finally:
        # Always attempt to restore original configuration
        try:
            if original_protocol and original_baud and original_terminator:
                controller.update_config(
                    protocol=original_protocol,
                    baudrate=original_baud,
                    terminator=original_terminator
                )
                logs.append(TestLog(
                    action="Restore Config",
                    status="success",
                    detail="Restored original configuration"
                ))
        except Exception as e:
            logs.append(TestLog(
                action="Restore Config",
                status="failed",
                detail=f"Failed to restore: {str(e)}"
            ))

    return TestResponse(logs=logs)

# Mount static files (Frontend UI)
# Mount at root "/" but be careful not to override API routes. 
# FastAPI checks routes in order, but StaticFiles on "/" acts as a catch-all.
# A common pattern is to mount static on "/static" or "/ui", but to serve index.html at root,
# we can mount it at root and it will serve index.html for "/".
# However, explicit API routes defined above/below will take precedence if they match specific paths.
# Since our API is at /api/v1, there is no conflict.
app.mount("/", StaticFiles(directory="static", html=True), name="static")

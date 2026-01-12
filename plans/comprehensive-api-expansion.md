# Comprehensive API Expansion Plan for HDC202-X24

## Objective
Expand the KVM Service API to support the full range of controls provided in the `External_Button_Board_Command_Test_EN_CSV.csv` file for the HDC202-X24 model. This includes lighting, fan control, network switching, audio management, and advanced USB settings.

## 1. Constants Update (`src/constants.py`)

Expand `HDC202X24Commands` with the following groups:

### 1.1 Switching
*   `SWITCH_ALL_PC1` - `SWITCH_ALL_PC4` (Existing as `SWITCH_PORT_X`)
*   `SWITCH_ALL_NEXT`: `AA BB 03 FF 00 67`
*   `SWITCH_OUT1_PC1`, `SWITCH_OUT1_PC2`
*   `SWITCH_OUT2_PC1`, `SWITCH_OUT2_PC2`

### 1.2 Audio/Video Features
*   `BUZZER_ON`, `BUZZER_OFF` (Existing)
*   `LIGHT_OFF`: `AA BB 05 02 00 6C`
*   `LIGHT_BASIC`: `AA BB 05 02 01 6D`
*   `LIGHT_FLOW`: `AA BB 05 02 02 6E`
*   `LIGHT_BREATHING`: `AA BB 05 02 03 6F`
*   `AUDIO_FOLLOW_ON`: `AA BB 0C 00 01 72`
*   `AUDIO_FOLLOW_OFF`: `AA BB 0C 00 00 71`
*   `AUDIO_PC1` - `AUDIO_PC4`
*   `AUDIO_NEXT`: `AA BB 0D FF 00 71`

### 1.3 System & Hardware
*   `FAN_OFF`: `AA BB 0B 00 00 70`
*   `FAN_AUTO`: `AA BB 0B 00 01 71`
*   `FAN_LOW`: `AA BB 0B 00 02 72`
*   `FAN_HIGH`: `AA BB 0B 00 03 73`
*   `AUTODETECT_ON`, `AUTODETECT_OFF`
*   `AUTOSCAN_ON`, `AUTOSCAN_OFF`

### 1.4 USB & Input
*   `USB_FOCUS_PC1`, `USB_FOCUS_PC2`, `USB_FOCUS_NEXT`
*   `USB_COMPAT_ON`, `USB_COMPAT_OFF`
*   `MOUSE_MIDDLE_ON`, `MOUSE_MIDDLE_OFF`

### 1.5 Network Control
*   `NET_PC1_ON`, `NET_PC1_OFF` through `NET_PC4_ON`, `NET_PC4_OFF`

---

## 2. Models Update (`src/models.py`)

Create Pydantic models for the new endpoints:

```python
class LightModeRequest(BaseModel):
    mode: Literal["off", "basic", "flow", "breathing"]

class FanModeRequest(BaseModel):
    mode: Literal["off", "auto", "low", "high"]

class AudioSourceRequest(BaseModel):
    port: int  # 1-4

class AudioFollowRequest(BaseModel):
    enabled: bool

class UsbFocusRequest(BaseModel):
    target: Literal["pc1", "pc2", "next"]

class NetworkControlRequest(BaseModel):
    port: int # 1-4
    enabled: bool

class FeatureToggleRequest(BaseModel):
    enabled: bool
```

---

## 3. Controller Service Update (`src/controller_service.py`)

Add methods to `ControllerService` to handle the new command groups.
*   `set_light_mode(mode: str)`
*   `set_fan_mode(mode: str)`
*   `set_audio_source(port: int)`
*   `set_audio_follow(enabled: bool)`
*   `set_network_power(port: int, enabled: bool)`
*   `set_usb_focus(target: str)`
*   `toggle_feature(feature: str, enabled: bool)` (for autodetect, autoscan, usb_compat, mouse_middle)

Each method will check `hasattr(commands, COMMAND_NAME)` before sending to ensure protocol compatibility.

---

## 4. API Endpoints (`src/main.py`)

Add the following routes:

*   `POST /api/v1/light` -> `set_light_mode`
*   `POST /api/v1/fan` -> `set_fan_mode`
*   `POST /api/v1/audio/source` -> `set_audio_source`
*   `POST /api/v1/audio/follow` -> `set_audio_follow`
*   `POST /api/v1/network` -> `set_network_power`
*   `POST /api/v1/usb/focus` -> `set_usb_focus`
*   `POST /api/v1/system/autodetect`
*   `POST /api/v1/system/autoscan`
*   `POST /api/v1/usb/compatibility`
*   `POST /api/v1/usb/mouse-middle`

## 5. Documentation
*   Update `README.md` to list new endpoints.
*   Ensure OpenAPI docs (Swagger) are auto-generated correctly via Pydantic models.

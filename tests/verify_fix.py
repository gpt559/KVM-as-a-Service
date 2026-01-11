from src.models import ConfigRequest
from pydantic import ValidationError
import sys

try:
    config = ConfigRequest(protocol="matrix")
    print("SUCCESS: 'matrix' protocol accepted.")
except ValidationError as e:
    print(f"FAILURE: Validation failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAILURE: Unexpected error: {e}")
    sys.exit(1)

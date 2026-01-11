import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from controller_service import ControllerService

class TestTerminatorLogic(unittest.TestCase):
    def test_terminator_application(self):
        mock_serial = MagicMock()
        controller = ControllerService(mock_serial)
        
        # Test 1: None (Default)
        controller.current_terminator = "none"
        cmd = b'TEST'
        self.assertEqual(controller._apply_terminator(cmd), b'TEST')
        
        # Test 2: CR
        controller.current_terminator = "cr"
        self.assertEqual(controller._apply_terminator(cmd), b'TEST\r')
        
        # Test 3: CRLF
        controller.current_terminator = "crlf"
        self.assertEqual(controller._apply_terminator(cmd), b'TEST\r\n')
        
        print("\n✅ Verification Successful: Terminator logic works correctly.")

if __name__ == '__main__':
    unittest.main()

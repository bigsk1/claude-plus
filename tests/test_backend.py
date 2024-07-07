import pytest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_import_backend():
    try:
        import backend
        assert True, "Import of backend successful"
    except ImportError:
        pytest.fail("Failed to import backend module")

def test_import_automode_logic():
    try:
        import automode_logic
        assert True, "Import of automode_logic successful"
    except ImportError:
        pytest.fail("Failed to import automode_logic module")

def test_import_shared_utils():
    try:
        import shared_utils
        assert True, "Import of shared_utils successful"
    except ImportError:
        pytest.fail("Failed to import shared_utils module")

# You can add more basic tests here as needed
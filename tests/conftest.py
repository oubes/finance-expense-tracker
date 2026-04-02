import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

import pytest
from fastapi.testclient import TestClient

from src.bootstrap.app_factory import create_app
from src.core.config.loader import load_settings


@pytest.fixture
def test_settings():
    return Settings(APP_NAME="test-app") # type: ignore


@pytest.fixture
def client(test_settings):
    app = create_app()

    def override_get_settings():
        return test_settings

    app.dependency_overrides[load_settings] = override_get_settings

    return TestClient(app)
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def predictor(client):
    assert app.state.predictor is not None, app.state.model_error
    return app.state.predictor

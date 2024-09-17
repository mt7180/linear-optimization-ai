import pytest

def test_app_start(app):
    assert not app.exception

def test_title(app):
    assert "Linear Optimization Assistant" in app.title[0].value
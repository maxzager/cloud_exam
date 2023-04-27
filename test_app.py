import app

def test_app_creation():
    assert hasattr(app, 'app'), "app object should be created in app.py"
    assert app.app is not None, "app object should not be None"
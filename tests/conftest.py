import pytest


@pytest.fixture(autouse=True)
def _reset_usegolib_loaded_modules():
    # Tests run in one Python process; clear process-global cache between tests.
    import usegolib.handle

    usegolib.handle._LOADED_MODULES.clear()
    yield
    usegolib.handle._LOADED_MODULES.clear()


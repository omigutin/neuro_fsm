import pytest


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    """ Писатели истории пишут в ./fsm_logs — каждый тест работает в своём каталоге. """
    monkeypatch.chdir(tmp_path)

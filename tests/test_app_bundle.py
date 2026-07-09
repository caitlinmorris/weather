import os

from presence.render.app import PID_FILE, another_instance_running
from presence.render.make_app import make_app


def test_make_app_writes_valid_bundle(tmp_path):
    bundle = make_app(tmp_path, repo=tmp_path / "fake-repo")
    launcher = bundle / "Contents" / "MacOS" / "weather"
    plist = bundle / "Contents" / "Info.plist"
    assert launcher.is_file() and os.access(launcher, os.X_OK)
    assert 'cd "' + str(tmp_path / "fake-repo") + '"' in launcher.read_text()
    assert "<string>we.ather</string>" in plist.read_text()


def test_instance_guard(tmp_path, monkeypatch):
    import presence.render.app as app_mod

    fake_pid = tmp_path / "app.pid"
    monkeypatch.setattr(app_mod, "PID_FILE", fake_pid)
    assert not another_instance_running()          # no pid file
    fake_pid.write_text(str(os.getpid()))
    assert another_instance_running()              # our own live pid
    fake_pid.write_text("999999999")
    assert not another_instance_running()          # dead pid ignored
    fake_pid.write_text("not-a-pid")
    assert not another_instance_running()          # garbage ignored

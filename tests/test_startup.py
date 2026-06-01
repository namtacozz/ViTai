from vitai import startup


def test_restart_as_admin_quotes_arguments(monkeypatch):
    calls = []

    class Shell32:
        def IsUserAnAdmin(self):
            return False

        def ShellExecuteW(self, hwnd, verb, file, params, directory, show):
            calls.append((verb, file, params))
            return 42

    class Windll:
        shell32 = Shell32()

    monkeypatch.setattr(startup.sys, "platform", "win32")
    monkeypatch.setattr(startup.sys, "executable", r"C:\Program Files\ViTai\ViTai.exe")
    monkeypatch.setattr(startup.sys, "argv", ["vitai", "--name", "a b", "quote\"x"])
    monkeypatch.setattr(startup.ctypes, "windll", Windll())

    try:
        startup.restart_as_admin()
    except SystemExit:
        pass

    assert calls[0][2] == '--name "a b" quote\\\"x'

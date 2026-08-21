import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from vitai.color_wheel import (
    hsv_to_rgb,
    rgb_to_hex,
    rgb_to_hsv,
    extract_hex,
)
from vitai.hotkey import (
    HotkeyManager,
    _canonical_mouse_button,
    format_key_display,
)
from vitai.user_store import (
    User,
    UserStore,
    clear_session,
    get_current_session,
    get_mac_address,
    hash_password,
    save_session,
    verify_password,
)
from pynput import mouse


class TestPasswordAndMacSecurity:
    def test_mac_address_format(self):
        mac = get_mac_address()
        assert isinstance(mac, str)
        assert len(mac) == 17
        parts = mac.split(":")
        assert len(parts) == 6
        for p in parts:
            assert len(p) == 2
            int(p, 16)  # Valid hex

    def test_password_hashing_and_salting(self):
        pwd = "SecretPassword123!"
        salt1, hash1 = hash_password(pwd)
        salt2, hash2 = hash_password(pwd)

        assert salt1 != salt2  # Unique salt per hash
        assert hash1 != hash2

        assert verify_password(pwd, salt1, hash1) is True
        assert verify_password(pwd, salt2, hash2) is True
        assert verify_password("WrongPassword", salt1, hash1) is False


class TestUserStoreAndHardwareLock:
    @pytest.fixture
    def temp_store(self, tmp_path):
        from vitai.user_store import CloudConfig
        store_file = tmp_path / "users.json"
        local_cfg = CloudConfig(is_enabled=False)
        return UserStore(store_path=store_file, cloud_config=local_cfg)

    def test_default_admin_created(self, temp_store):
        admin = temp_store.get_user("vinguoitai")
        assert admin is not None
        assert admin.role == "admin"
        assert admin.bound_mac is None

    def test_create_and_delete_user(self, temp_store):
        ok, msg = temp_store.create_user("alice", "pass123", role="user")
        assert ok is True

        user = temp_store.get_user("alice")
        assert user is not None
        assert user.role == "user"

        # Duplicate check
        ok2, _ = temp_store.create_user("alice", "anotherpass")
        assert ok2 is False

        # Delete check
        ok_del, _ = temp_store.delete_user("alice")
        assert ok_del is True
        assert temp_store.get_user("alice") is None

    def test_mac_binding_on_first_login(self, temp_store):
        temp_store.create_user("bob", "secret123", role="user")
        machine_mac = "AA:BB:CC:DD:EE:01"

        # First login binds MAC
        ok, user, err = temp_store.authenticate("bob", "secret123", machine_mac)
        assert ok is True
        assert user is not None
        assert user.bound_mac == machine_mac

        # Subsequent login on same MAC succeeds
        ok2, user2, err2 = temp_store.authenticate("bob", "secret123", machine_mac)
        assert ok2 is True

        # Login from different computer is REJECTED
        alien_mac = "FF:EE:DD:CC:BB:99"
        ok3, user3, err3 = temp_store.authenticate("bob", "secret123", alien_mac)
        assert ok3 is False
        assert user3 is None
        assert "thiết bị khác" in err3

    def test_admin_reset_mac(self, temp_store):
        temp_store.create_user("charlie", "secret123", role="user")
        old_mac = "AA:11:22:33:44:55"
        temp_store.authenticate("charlie", "secret123", old_mac)

        u = temp_store.get_user("charlie")
        assert u.bound_mac == old_mac

        # Admin resets MAC
        ok, msg = temp_store.reset_mac("charlie")
        assert ok is True
        assert temp_store.get_user("charlie").bound_mac is None

        # User can now login on new MAC
        new_mac = "BB:66:77:88:99:00"
        ok_new, u_new, _ = temp_store.authenticate("charlie", "secret123", new_mac)
        assert ok_new is True
        assert u_new.bound_mac == new_mac

    def test_admin_unrestricted_mac_access(self, temp_store):
        # Admin can login from machine 1
        mac1 = "11:22:33:44:55:66"
        ok1, admin1, _ = temp_store.authenticate("vinguoitai", "vit24052005", mac1)
        assert ok1 is True
        assert admin1.role == "admin"
        assert admin1.bound_mac is None  # Admin MAC is never permanently locked

        # Admin can also login from machine 2, 3 without being rejected
        mac2 = "AA:BB:CC:DD:EE:FF"
        ok2, admin2, _ = temp_store.authenticate("vinguoitai", "vit24052005", mac2)
        assert ok2 is True
        assert admin2.role == "admin"

    def test_session_lifecycle(self, tmp_path, temp_store):
        session_file = tmp_path / "session.json"
        temp_store.create_user("david", "passDavid", role="user")
        david = temp_store.get_user("david")

        save_session(david, session_path=session_file)
        restored = get_current_session(temp_store, session_path=session_file)
        assert restored is not None
        assert restored.username == "david"

        clear_session(session_path=session_file)
        assert get_current_session(temp_store, session_path=session_file) is None


class TestMouseHotkeyAndFormatting:
    def test_mouse_button_canonicalization(self):
        assert _canonical_mouse_button(mouse.Button.right) == "mouse_right"
        assert _canonical_mouse_button(mouse.Button.middle) == "mouse_middle"
        assert _canonical_mouse_button(mouse.Button.left) == "mouse_left"

    def test_format_key_display(self):
        assert "Chuột Phải" in format_key_display("mouse_right")
        assert "Chuột Giữa" in format_key_display("mouse_middle")
        assert "Nút Chuột Phụ 1" in format_key_display("mouse_x1")
        assert "Nút Chuột Phụ 2" in format_key_display("mouse_x2")
        assert format_key_display("v") == "V"

    def test_hotkey_manager_display_text(self):
        hm = HotkeyManager("alt", "mouse_right", lambda: None)
        assert "Chuột Phải" in hm.display_text

        hm_ctrl = HotkeyManager("ctrl+shift", "mouse_middle", lambda: None)
        assert "Ctrl+Shift" in hm_ctrl.display_text
        assert "Chuột Giữa" in hm_ctrl.display_text


class TestColorWheelMath:
    def test_rgb_hsv_conversions(self):
        # Pure Red
        h, s, v = rgb_to_hsv(255, 0, 0)
        assert round(h) == 0
        assert s == 1.0
        assert v == 1.0

        r, g, b = hsv_to_rgb(0, 1.0, 1.0)
        assert (r, g, b) == (255, 0, 0)

        # Pure Green
        h, s, v = rgb_to_hsv(0, 255, 0)
        assert round(h) == 120

        # Pure Blue
        h, s, v = rgb_to_hsv(0, 0, 255)
        assert round(h) == 240

    def test_hex_conversion(self):
        hex_code = rgb_to_hex(224, 159, 94)
        assert hex_code.upper() == "#E09F5E"
        assert extract_hex("#e09f5e") == "#E09F5E"
        assert extract_hex("invalid text", default="#FFFFFF") == "#FFFFFF"


class TestCloudSync:
    def test_cloud_config_serde(self, tmp_path):
        from vitai.user_store import CloudConfig, load_cloud_config, save_cloud_config

        cfg_file = tmp_path / "cloud_config.json"
        cfg = CloudConfig(
            provider="supabase",
            supabase_url="https://test.supabase.co",
            supabase_key="secret-anon-key-123",
            table_name="vitai_users",
            is_enabled=True,
        )
        save_cloud_config(cfg, config_path=cfg_file)
        loaded = load_cloud_config(config_path=cfg_file)

        assert loaded.is_enabled is True
        assert loaded.provider == "supabase"
        assert loaded.supabase_url == "https://test.supabase.co"
        assert loaded.supabase_key == "secret-anon-key-123"

    def test_cloud_auth_client_supabase_mock(self):
        from vitai.user_store import CloudAuthClient, CloudConfig

        cfg = CloudConfig(
            provider="supabase",
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            is_enabled=True,
        )
        client = CloudAuthClient(cfg)

        with patch.object(client, "_http_request") as mock_req:
            # Test connection
            mock_req.return_value = (True, [{"count": 1}], "HTTP 200")
            ok, msg = client.test_connection()
            assert ok is True
            assert "thành công" in msg

            # Test get user
            mock_req.return_value = (
                True,
                [
                    {
                        "username": "emma",
                        "password_hash": "hash123",
                        "salt": "salt123",
                        "role": "user",
                        "bound_mac": "11:22:33:44:55:66",
                        "created_at": "2026-08-21 12:00:00",
                        "is_active": True,
                    }
                ],
                "HTTP 200",
            )
            ok_u, user_obj, _ = client.get_user("emma")
            assert ok_u is True
            assert user_obj is not None
            assert user_obj.username == "emma"
            assert user_obj.bound_mac == "11:22:33:44:55:66"

    def test_user_store_hybrid_cloud_authenticate(self, tmp_path):
        from vitai.user_store import CloudConfig, UserStore, hash_password

        store_file = tmp_path / "users.json"
        cfg = CloudConfig(
            provider="supabase",
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            is_enabled=True,
        )
        store = UserStore(store_path=store_file, cloud_config=cfg)

        salt, pwd_hash = hash_password("pass123")
        remote_user = User(
            username="frank",
            password_hash=pwd_hash,
            salt=salt,
            role="user",
            bound_mac=None,  # Chưa bind MAC
            created_at="2026-08-21 12:00:00",
            is_active=True,
        )

        with patch.object(store.cloud_client, "get_user", return_value=(True, remote_user, "OK")):
            with patch.object(store.cloud_client, "update_fields", return_value=(True, "OK")) as mock_update:
                my_mac = "AA:11:22:33:44:99"
                ok, user, msg = store.authenticate("frank", "pass123", client_mac=my_mac)
                assert ok is True
                assert user is not None
                assert user.bound_mac == my_mac

                # Đảm bảo lệnh update MAC được gửi lên Cloud
                mock_update.assert_called_once_with("frank", {"bound_mac": my_mac})


class TestLoginGateBarrier:
    def test_settings_window_login_gate_overlay_state(self, tmp_path):
        from PyQt6.QtWidgets import QApplication
        from vitai.config import AppConfig
        from vitai.settings import SettingsWindow
        from vitai.user_store import CloudConfig, UserStore, save_session, clear_session

        app = QApplication.instance() or QApplication([])

        store_file = tmp_path / "users.json"
        local_cfg = CloudConfig(is_enabled=False)
        store = UserStore(store_path=store_file, cloud_config=local_cfg)

        cfg = AppConfig()

        # 1. Khi chưa đăng nhập (no session)
        clear_session(session_path=tmp_path / "session.json")
        with patch("vitai.settings.get_user_store", return_value=store):
            with patch("vitai.settings.get_current_session", return_value=None):
                win = SettingsWindow(cfg)
                assert win.current_user is None
                assert win.login_gate_overlay.isHidden() is False
                assert win.login_gate_overlay.objectName() == "loginGateOverlay"

                # 2. Đăng nhập thành công qua Login Gate
                win.gate_user_input.setText("vinguoitai")
                win.gate_pass_input.setText("vit24052005")
                with patch("vitai.settings.save_session") as mock_save:
                    win._on_gate_login()
                    assert win.current_user is not None
                    assert win.current_user.username == "vinguoitai"
                    assert win.login_gate_overlay.isHidden() is True
                    mock_save.assert_called_once()



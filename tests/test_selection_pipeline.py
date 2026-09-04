from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from vitai.config import AppConfig
from vitai.user_store import User, CloudConfig, UserStore


def test_full_selection_to_overlay_pipeline(tmp_path):
    from vitai.main import ViTaiApp

    app = QApplication.instance() or QApplication([])

    # Mock user store with logged in user
    store = UserStore(store_path=tmp_path / "users.json", cloud_config=CloudConfig(is_enabled=False))
    admin_user = store.get_user("vinguoitai")

    with patch("vitai.main.default_config_path", return_value=tmp_path / "config.json"), \
         patch("vitai.user_store.get_current_session", return_value=admin_user), \
         patch("vitai.main.install_linux_desktop_file"), \
         patch("vitai.main.install_ui_logging"), \
         patch("vitai.main.configure_logging"):

        vitai_app = ViTaiApp()
        try:
            vitai_app.user_store = store
            vitai_app.selection_anchor = (450, 320)

            # 1. Mock text selection & AI response
            question = "Thủ đô của Việt Nam là gì?\nA. Hà Nội\nB. TP. Hồ Chí Minh"
            
            with patch("vitai.main.get_selected_text", return_value=question), \
                 patch("vitai.llm.LlmClient.ask", return_value="A") as mock_ask:
                
                # Execute selection processing
                vitai_app._process_selection()

                # Process Qt events to flush signals
                QApplication.processEvents()

                # Verify AI was called
                mock_ask.assert_called_once()

                # Verify AnswerOverlay was created and populated
                assert vitai_app.overlay is not None
                assert vitai_app.overlay.label.text() == "A"
                assert vitai_app.overlay.isVisible() is True

                # Verify anchor positioning
                pos = vitai_app.overlay.pos()
                assert pos.x() >= 450

                # Verify cache was populated
                assert question in vitai_app.text_cache
                assert vitai_app.text_cache[question] == "A"

                # 2. Test cache hit on repeated selection (should NOT call AI again)
                mock_ask.reset_mock()
                vitai_app._process_selection()
                QApplication.processEvents()
                mock_ask.assert_not_called()

                # 3. Test click outside hides overlay
                vitai_app.hide_overlay_if_outside(10, 10)
                assert vitai_app.overlay.isVisible() is False
        finally:
            vitai_app.quit()


def test_selection_blocked_when_locked(tmp_path):
    from vitai.main import ViTaiApp

    app = QApplication.instance() or QApplication([])
    store = UserStore(store_path=tmp_path / "users.json", cloud_config=CloudConfig(is_enabled=False))

    with patch("vitai.main.default_config_path", return_value=tmp_path / "config.json"), \
         patch("vitai.user_store.get_current_session", return_value=None), \
         patch("vitai.main.install_linux_desktop_file"), \
         patch("vitai.main.install_ui_logging"), \
         patch("vitai.main.configure_logging"):

        vitai_app = ViTaiApp()
        try:
            vitai_app.user_store = store

            # Trigger request while unauthenticated
            emitted = []
            vitai_app.bridge.show_settings_requested.connect(lambda: emitted.append(True))
            with patch.object(vitai_app, "_process_selection") as mock_process:
                vitai_app._start_answer_request()
                
                # Must emit thread-safe signal to show settings and NOT process selection
                assert len(emitted) == 1
                mock_process.assert_not_called()
        finally:
            vitai_app.quit()

SUPPORTED_UI_LANGUAGES = ("vi", "en")

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "vi": {
        "app_name": "ViTai",
        "auto": "Auto",
        "close": "Đóng",
        "english": "English",
        "history": "Lịch sử",
        "no_translation_yet": "Chưa có bản dịch",
        "settings_title": "Cài đặt ViTai",
        "translation_group": "Dịch thuật",
        "source_language": "Ngôn ngữ nguồn",
        "target_language": "Ngôn ngữ đích",
        "transtyle": "Transtyle",
        "transtyle_tab": "Transtyle",
        "translation_style": "Phong cách dịch",
        "advanced_group": "Nâng cao",
        "capture_engine": "Engine capture",
        "ocr_engine": "Engine OCR",
        "hotkey_backend": "Backend phím tắt",
        "edit_transtyle": "Sửa Transtyle",
        "translator_provider": "Dịch vụ dịch",
        "translator_google": "Google Translate",
        "translator_deepl": "DeepL",
        "translator_ai": "AI Translate (LLM)",
        "translator_failover": "Fallback Google khi lỗi",
        "transtyle_rules_summary": "Glossary, quy tắc xưng hô, regex và correction đi theo phong cách đang chọn.",
        "transtyle_mvp_summary": "MVP lưu rule theo từng style trong config và lưu correction từ overlay.",
        "basic_group": "Cơ bản",
        "overlay_color": "Màu overlay",
        "hotkey": "Phím tắt",
        "auto_translate_default": "Tự động dịch mặc định",
        "auto_interval": "Khoảng lặp Auto",
        "system_group": "Hệ thống",
        "run_as_admin": "Chạy với quyền Admin",
        "start_with_windows": "Khởi động cùng Windows",
        "save": "Lưu",
        "reset": "Đặt lại",
        "exit": "Thoát",
        "admin_warning_title": "Chạy với quyền Admin",
        "admin_warning_message": "Ứng dụng sẽ cần khởi động lại với quyền Admin.\nBạn có muốn tiếp tục?",
        "hotkey_display": "để bắt đầu dịch",
        "speak": "Đọc",
        "tts_unavailable": "Không thể đọc bản dịch",
        "ui_language": "Ngôn ngữ giao diện",
        "vietnamese": "Tiếng Việt",
    },
    "en": {
        "app_name": "ViTai",
        "auto": "Auto",
        "close": "Close",
        "english": "English",
        "history": "History",
        "no_translation_yet": "No translation yet",
        "settings_title": "ViTai Settings",
        "translation_group": "Translation",
        "source_language": "Source language",
        "target_language": "Target language",
        "transtyle": "Transtyle",
        "transtyle_tab": "Transtyle",
        "translation_style": "Translation style",
        "advanced_group": "Advanced",
        "capture_engine": "Capture engine",
        "ocr_engine": "OCR engine",
        "hotkey_backend": "Hotkey backend",
        "edit_transtyle": "Edit Transtyle",
        "translator_provider": "Translator provider",
        "translator_google": "Google Translate",
        "translator_deepl": "DeepL",
        "translator_ai": "AI Translate (LLM)",
        "translator_failover": "Fallback to Google on failure",
        "transtyle_rules_summary": "Glossary, pronoun rules, regex toggles, and corrections follow the selected style.",
        "transtyle_mvp_summary": "MVP stores rules per style in config and saves corrections from the overlay.",
        "basic_group": "Basic",
        "overlay_color": "Overlay color",
        "hotkey": "Hotkey",
        "auto_translate_default": "Auto translate by default",
        "auto_interval": "Auto interval",
        "system_group": "System",
        "run_as_admin": "Run as administrator",
        "start_with_windows": "Start with Windows",
        "save": "Save",
        "reset": "Reset",
        "exit": "Exit",
        "admin_warning_title": "Run as administrator",
        "admin_warning_message": "The application will need to restart with administrator privileges.\nDo you want to continue?",
        "hotkey_display": "to start translating",
        "speak": "Speak",
        "tts_unavailable": "Cannot speak translation",
        "ui_language": "UI language",
        "vietnamese": "Vietnamese",
    },
}


def normalize_ui_language(language: str) -> str:
    return language if language in SUPPORTED_UI_LANGUAGES else "vi"


def tr(key: str, language: str = "vi") -> str:
    normalized = normalize_ui_language(language)
    return _TRANSLATIONS[normalized][key]


def assert_complete_translations() -> None:
    expected_keys = set(_TRANSLATIONS["vi"])
    for language in SUPPORTED_UI_LANGUAGES:
        actual_keys = set(_TRANSLATIONS[language])
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            raise AssertionError(f"{language} translation keys mismatch: missing={missing}, extra={extra}")

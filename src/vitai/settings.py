from __future__ import annotations

# ==============================================================================
# ViTai Settings Module (Backward-Compatibility Facade)
# All UI implementations are cleanly modularized under `vitai.ui`.
# ==============================================================================

from vitai.ui import (
    AddUserDialog,
    ChangeUserPasswordDialog,
    CloudConfigDialog,
    COLOR_CHOICES,
    extract_hex_color,
    get_stylesheet,
    HotkeyInputButton,
    LoginDialog,
    PROVIDER_GUIDES,
    PROVIDER_PRESETS,
    ProviderHelpDialog,
    RegisterPaymentDialog,
    SettingsWindow,
    SIZE_CHOICES,
    UnsavedChangesDialog,
)
from vitai.user_store import (
    CloudAuthClient,
    CloudConfig,
    User,
    UserStore,
    clear_session,
    get_current_session,
    get_mac_address,
    get_user_store,
    load_cloud_config,
    save_cloud_config,
    save_session,
    verify_password,
)

__all__ = [
    "get_stylesheet",
    "PROVIDER_PRESETS",
    "PROVIDER_GUIDES",
    "SIZE_CHOICES",
    "COLOR_CHOICES",
    "extract_hex_color",
    "HotkeyInputButton",
    "ProviderHelpDialog",
    "LoginDialog",
    "AddUserDialog",
    "ChangeUserPasswordDialog",
    "CloudConfigDialog",
    "UnsavedChangesDialog",
    "RegisterPaymentDialog",
    "SettingsWindow",
    "User",
    "UserStore",
    "CloudConfig",
    "CloudAuthClient",
    "get_user_store",
    "get_current_session",
    "save_session",
    "clear_session",
    "get_mac_address",
    "verify_password",
    "load_cloud_config",
    "save_cloud_config",
]

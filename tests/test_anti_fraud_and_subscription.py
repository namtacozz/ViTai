import hashlib
import time
from datetime import datetime, timedelta
from vitai.user_store import (
    CloudConfig,
    User,
    UserStore,
    hash_password,
    verify_password,
)
from vitai.token_store import (
    _obfuscate_token_data,
    _deobfuscate_token_data,
)


def test_pbkdf2_and_legacy_sha256_compatibility():
    pwd = "MySuperSecretPassword@2026"
    salt, pbkdf2_hash = hash_password(pwd)

    # 1. PBKDF2 verify
    assert verify_password(pwd, salt, pbkdf2_hash) is True
    assert verify_password("WrongPassword", salt, pbkdf2_hash) is False

    # 2. Legacy SHA-256 verify
    legacy_sha256 = hashlib.sha256((salt + pwd).encode("utf-8")).hexdigest()
    assert verify_password(pwd, salt, legacy_sha256) is True
    assert verify_password("WrongPassword", salt, legacy_sha256) is False


def test_bruteforce_lockout_after_5_failures(tmp_path):
    store = UserStore(store_path=tmp_path / "users.json", cloud_config=CloudConfig(is_enabled=False))
    store.create_user("victim", "correct_pass_123")

    # 4 consecutive wrong passwords: rejected with incorrect password
    for i in range(4):
        ok, u, msg = store.authenticate("victim", "wrong_pass")
        assert ok is False
        assert "Mật khẩu không chính xác" in msg

    # 5th wrong password: still incorrect password, but locks account
    ok5, u5, msg5 = store.authenticate("victim", "wrong_pass")
    assert ok5 is False

    # 6th attempt (even with correct password!): blocked by anti-bruteforce
    ok6, u6, msg6 = store.authenticate("victim", "correct_pass_123")
    assert ok6 is False
    assert "tạm khóa do nhập sai mật khẩu 5 lần" in msg6


def test_subscription_expiration_logic(tmp_path):
    store = UserStore(store_path=tmp_path / "users.json", cloud_config=CloudConfig(is_enabled=False))

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. Expired user
    store.create_user(
        "expired_user",
        "pass123",
        role="user",
        subscription_type="90d",
        subscription_expires=yesterday,
    )
    ok, u, msg = store.authenticate("expired_user", "pass123")
    assert ok is False
    assert "hết hạn bản quyền" in msg

    # 2. Active subscription user
    store.create_user(
        "active_user",
        "pass123",
        role="user",
        subscription_type="90d",
        subscription_expires=tomorrow,
    )
    ok, u, msg = store.authenticate("active_user", "pass123")
    assert ok is True
    assert u is not None

    # 3. Lifetime user (no expiry)
    store.create_user(
        "lifetime_user",
        "pass123",
        role="user",
        subscription_type="lifetime",
        subscription_expires="",
    )
    ok, u, msg = store.authenticate("lifetime_user", "pass123")
    assert ok is True


def test_token_storage_hardware_encryption():
    raw_tokens = '{"openai": {"access_token": "sk-secret-12345"}}'
    encrypted = _obfuscate_token_data(raw_tokens)

    assert encrypted.startswith("__VITAI_SEC__:")
    assert "sk-secret-12345" not in encrypted  # Plaintext is completely hidden

    decrypted = _deobfuscate_token_data(encrypted)
    assert decrypted == raw_tokens

    # Test backward compatibility: unencrypted data passes through unchanged
    unencrypted = '{"legacy": "data"}'
    assert _deobfuscate_token_data(unencrypted) == unencrypted

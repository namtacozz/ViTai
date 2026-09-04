from vitai.device_fingerprint import (
    get_mac_address,
    get_machine_id,
    get_cpu_signature,
    get_device_fingerprint,
)


def test_device_fingerprint_generation():
    fp1 = get_device_fingerprint()
    fp2 = get_device_fingerprint()

    assert isinstance(fp1, str)
    assert len(fp1) == 32
    assert fp1 == fp2  # Deterministic on the same hardware

    mid = get_machine_id()
    assert isinstance(mid, str)
    assert len(mid) > 0

    cpu = get_cpu_signature()
    assert isinstance(cpu, str)
    assert len(cpu) > 0


def test_mac_address_format():
    mac = get_mac_address()
    assert isinstance(mac, str)
    parts = mac.split(":")
    assert len(parts) == 6
    for p in parts:
        assert len(p) == 2
        int(p, 16)

from vitai.transaction_ledger import TransactionLedger


def test_transaction_ledger_anti_replay(tmp_path):
    ledger_file = tmp_path / "used_tx.json"
    ledger = TransactionLedger(ledger_path=ledger_file)

    ref_no = "FT987654321"

    # Initially not consumed
    assert ledger.is_consumed(ref_no) is False

    # Mark consumed first time: succeeds
    ok1 = ledger.mark_consumed(ref_no, "VITAI123456", 50000, "user1")
    assert ok1 is True
    assert ledger.is_consumed(ref_no) is True

    # Attempt replay with same transaction: rejected
    ok2 = ledger.mark_consumed(ref_no, "VITAI999999", 50000, "user2")
    assert ok2 is False

    # Check persistence across instance reload
    ledger2 = TransactionLedger(ledger_path=ledger_file)
    assert ledger2.is_consumed(ref_no) is True

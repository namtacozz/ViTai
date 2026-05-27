from vitai.mcq import is_mcq, normalize_mcq_answer


def test_detects_lettered_options_with_periods():
    text = "Capital of France?\nA. London\nB. Paris\nC. Rome\nD. Berlin"

    assert is_mcq(text) is True


def test_detects_lettered_options_with_parentheses():
    text = "2 + 2 = ?\nA) 3\nB) 4"

    assert is_mcq(text) is True


def test_requires_at_least_two_unique_options():
    text = "A. This is one bullet only"

    assert is_mcq(text) is False


def test_general_question_is_not_mcq():
    assert is_mcq("Explain database connection pooling.") is False


def test_normalize_mcq_answer_extracts_first_label():
    assert normalize_mcq_answer("Answer: b") == "B"


def test_normalize_mcq_answer_returns_stripped_text_when_no_label():
    assert normalize_mcq_answer("Không chắc chắn") == "Không chắc chắn"

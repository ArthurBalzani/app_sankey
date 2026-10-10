from src.text_processing import extract_words, get_portuguese_stopwords


def test_extract_words_drops_portuguese_stopwords():
    words = extract_words("O atendimento foi excelente para todos como sempre")
    assert "atendimento" in words
    assert "excelente" in words
    assert "para" not in words
    assert "como" not in words


def test_custom_stopwords_are_included():
    stop_words = get_portuguese_stopwords({"atendimento"})
    assert "para" in stop_words
    assert "atendimento" in stop_words
    assert "pra" in stop_words

import pytest
from unittest.mock import patch
import analyzer

def test_analyze_sentiment_mock():
    with patch("analyzer.pipeline") as mock_pipe:
        mock_pipe.return_value.return_value = [{"label": "NEGATIVE", "score": 0.12}]
        result = analyzer.analyze_sentiment("bad")
        assert result["label"] == "NEGATIVE"
        assert 0 <= result["score"] <= 1

def test_check_toxicity():
    # Should be non-toxic for empty or neutral
    assert analyzer.check_toxicity("") == {"is_toxic": False, "score": 0.0}
    res = analyzer.check_toxicity("hello")
    assert "is_toxic" in res and "score" in res

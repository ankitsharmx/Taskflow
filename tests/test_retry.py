import pytest
from app.services.retry import calculate_backoff

def test_first_attempt_backoff():
    assert calculate_backoff(1) == 1

def test_second_attempt_backoff():
    assert calculate_backoff(2) == 2

def test_third_attempt_backoff():
    assert calculate_backoff(3) == 4

def test_fourth_attempt_backoff():
    assert calculate_backoff(4) == 8

def test_custom_base_delay():
    assert calculate_backoff(1, base_delay=5) == 5
    assert calculate_backoff(2, base_delay=5) == 10
    assert calculate_backoff(3, base_delay=5) == 20

def test_invalid_attempts_number():
    with pytest.raises(
        ValueError,
        match="Attempts must be at least 1",
    ):
        calculate_backoff(0)
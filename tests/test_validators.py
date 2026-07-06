from src.validators import Validator


def test_username_empty():
    valid, err = Validator.validate_username("")
    assert not valid
    assert "empty" in err


def test_username_leading_trailing_spaces():
    valid, err = Validator.validate_username(" user123 ")
    assert not valid
    assert "leading or trailing" in err


def test_username_internal_spaces():
    valid, err = Validator.validate_username("user 123")
    assert not valid
    assert "internal spaces" in err


def test_username_too_long():
    long_username = "a" * 65
    valid, err = Validator.validate_username(long_username)
    assert not valid
    assert "length" in err


def test_username_invalid_chars():
    valid, err = Validator.validate_username("user$123")
    assert not valid
    assert "invalid characters" in err


def test_username_valid():
    valid, err = Validator.validate_username("user_name.123-test")
    assert valid
    assert err is None


def test_batch_file_parsing():
    lines = ["user1\n", "# comment line\n", "  \n", "user_2\n", "invalid$user\n"]
    valid, errors = Validator.validate_batch_file(lines)
    assert valid == ["user1", "user_2"]
    assert len(errors) == 1
    assert "Line 5" in errors[0]

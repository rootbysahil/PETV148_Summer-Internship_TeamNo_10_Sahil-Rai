import re


class UsernameValidationError(Exception):
    """Custom exception raised during validation errors."""

    pass


class Validator:
    """Validates inputs for digital footprint scanners."""

    @staticmethod
    def validate_username(username: str, max_length: int = 64) -> tuple[bool, str | None]:
        """Checks target username format, length, and safe character set.

        Args:
            username: Target username.
            max_length: Maximum allowed length.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_reason)
        """
        if not username:
            return False, "Username cannot be empty."

        # Strip whitespaces
        if username.strip() != username:
            return False, "Username cannot contain leading or trailing whitespaces."

        if " " in username:
            return False, "Username cannot contain internal spaces."

        # Verify length
        if len(username) > max_length:
            return False, f"Username exceeds maximum length of {max_length} characters."

        # Sherlock standard safe charset rules: alphanumeric, dot, underscore, dash
        # We allow a standard regex pattern
        pattern = r"^[a-zA-Z0-9._-]+$"
        if not re.match(pattern, username):
            return (
                False,
                "Username contains invalid characters. Only alphanumeric, '.', '_', and '-' are allowed.",
            )

        return True, None

    @classmethod
    def validate_batch_file(cls, lines: list[str]) -> tuple[list[str], list[str]]:
        """Filters list of batch usernames, returning valid and skipped entries.

        Args:
            lines: Raw lines read from a text file.

        Returns:
            Tuple[List[str], List[str]]: (valid_usernames, error_details)
        """
        valid = []
        errors = []
        for index, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                # Ignore empty lines and comments
                continue

            is_valid, error = cls.validate_username(line)
            if is_valid:
                valid.append(line)
            else:
                errors.append(f"Line {index} ('{line}'): {error}")

        return valid, errors

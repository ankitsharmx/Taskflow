def calculate_backoff(
    attempts: int,
    base_delay: int = 1,
) -> int:
    if attempts < 1:
        raise ValueError("Attempts must be at least 1")
    return base_delay * (2 ** (attempts - 1))

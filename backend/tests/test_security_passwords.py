from app.core.security import get_password_hash, verify_password


def test_long_password_hash_and_verify():
    long_password = "x" * 200
    hashed = get_password_hash(long_password)

    assert hashed
    assert verify_password(long_password, hashed)


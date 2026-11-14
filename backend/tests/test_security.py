import bcrypt

from app.core.security import get_password_hash, verify_password


def test_password_hashes_use_argon2id():
    hashed_password = get_password_hash("CampusPassword123!")

    assert hashed_password.startswith("$argon2id$")
    assert verify_password("CampusPassword123!", hashed_password)
    assert not verify_password("WrongPassword123!", hashed_password)


def test_legacy_bcrypt_hashes_remain_verifiable_for_login_migration():
    hashed_password = bcrypt.hashpw(
        b"LegacyPassword123!",
        bcrypt.gensalt(),
    ).decode("utf-8")

    assert verify_password("LegacyPassword123!", hashed_password)
    assert not verify_password("WrongPassword123!", hashed_password)

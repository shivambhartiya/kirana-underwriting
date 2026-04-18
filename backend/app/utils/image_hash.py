import hashlib


def hash_object_key(object_key: str) -> str:
    return hashlib.sha256(object_key.encode("utf-8")).hexdigest()


def duplicate_hint(keys: list[str]) -> bool:
    digests = [hash_object_key(key)[:16] for key in keys]
    return len(digests) != len(set(digests))


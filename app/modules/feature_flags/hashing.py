import hashlib

def compute_user_bucket(user_id: str, feature_name: str) -> float:
    """
    Computes a deterministic bucket score between 0.0 and 100.0 (exclusive upper bound)
    based on the MD5 hash of (user_id + ":" + feature_name).

    :param user_id: Unique identifier for the user
    :param feature_name: Unique feature flag identifier
    :return: Float value in range [0.0, 100.0)
    """
    key = f"{user_id}:{feature_name}".encode("utf-8")
    hash_bytes = hashlib.md5(key).hexdigest()
    # Take the first 8 hex characters (32-bit int) for high precision bucket computation
    hash_int = int(hash_bytes[:8], 16)
    bucket = (hash_int % 10000) / 100.0
    return bucket

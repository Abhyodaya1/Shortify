"""Token Encryption & Secure Key Management Service.
Provides authenticated symmetric encryption (AES-256-GCM) for OAuth tokens at rest,
Windows DPAPI key protection, protected SQLite online backups, and migration utilities.
"""

from __future__ import annotations
import os
import sys
import base64
import secrets
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

logger = logging.getLogger("token_encryption")

KEYS_DIR = Path("backend/storage/keys")
BACKUPS_DIR = Path("backend/storage/backups")
DB_PATH = Path("backend/storage/scheduler.db")


class TokenDecryptionError(Exception):
    """Raised when an encrypted token cannot be decrypted due to key mismatch or corruption."""
    pass


# ---------------------------------------------------------------------------
# Windows DPAPI Helpers (using ctypes.windll.crypt32)
# ---------------------------------------------------------------------------
def _is_windows() -> bool:
    return sys.platform == "win32"


if _is_windows():
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    def _dpapi_encrypt(data: bytes) -> bytes:
        blob_in = DATA_BLOB(
            len(data),
            ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)),
        )
        blob_out = DATA_BLOB()
        if not crypt32.CryptProtectData(
            ctypes.byref(blob_in), "ShortifyMasterKey", None, None, None, 0, ctypes.byref(blob_out)
        ):
            raise RuntimeError("Windows DPAPI CryptProtectData failed")
        res = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        kernel32.LocalFree(blob_out.pbData)
        return res

    def _dpapi_decrypt(cipher: bytes) -> bytes:
        blob_in = DATA_BLOB(
            len(cipher),
            ctypes.cast(ctypes.create_string_buffer(cipher), ctypes.POINTER(ctypes.c_byte)),
        )
        blob_out = DATA_BLOB()
        if not crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        ):
            raise RuntimeError("Windows DPAPI CryptUnprotectData failed")
        res = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        kernel32.LocalFree(blob_out.pbData)
        return res
else:
    def _dpapi_encrypt(data: bytes) -> bytes:
        return data

    def _dpapi_decrypt(cipher: bytes) -> bytes:
        return cipher


class TokenEncryptionService:
    """Manages AES-256-GCM authenticated encryption for OAuth tokens and database backups."""

    _cached_key: Optional[bytes] = None

    @classmethod
    def get_or_create_master_key(cls) -> bytes:
        """Retrieves or initializes the 256-bit AES master key protected by DPAPI."""
        if cls._cached_key is not None:
            return cls._cached_key

        KEYS_DIR.mkdir(parents=True, exist_ok=True)
        key_file_dpapi = KEYS_DIR / "master.key.dpapi"
        key_file_plain = KEYS_DIR / "master.key"

        # 1. Environment variable override
        env_key = os.getenv("SHORTIFY_ENCRYPTION_KEY")
        if env_key:
            try:
                key_bytes = base64.urlsafe_b64decode(env_key.encode("utf-8"))
                if len(key_bytes) == 32:
                    cls._cached_key = key_bytes
                    return key_bytes
            except Exception:
                pass

        # 2. Windows DPAPI protected key file
        if _is_windows() and key_file_dpapi.exists():
            try:
                protected_bytes = key_file_dpapi.read_bytes()
                key_bytes = _dpapi_decrypt(protected_bytes)
                if len(key_bytes) == 32:
                    cls._cached_key = key_bytes
                    return key_bytes
            except Exception as e:
                logger.warning(f"Could not read DPAPI key file ({e}), checking plain fallback...")

        # 3. Plain key file (Linux / CI fallback)
        if key_file_plain.exists():
            try:
                key_bytes = key_file_plain.read_bytes()
                if len(key_bytes) == 32:
                    cls._cached_key = key_bytes
                    return key_bytes
            except Exception:
                pass

        # 4. Generate new cryptographically secure 256-bit key
        new_key = secrets.token_bytes(32)

        if _is_windows():
            try:
                encrypted_key = _dpapi_encrypt(new_key)
                key_file_dpapi.write_bytes(encrypted_key)
            except Exception as e:
                logger.warning(f"DPAPI save failed ({e}), saving with standard permissions")
                key_file_plain.write_bytes(new_key)
        else:
            key_file_plain.write_bytes(new_key)
            try:
                os.chmod(key_file_plain, 0o600)
            except Exception:
                pass

        cls._cached_key = new_key
        return new_key

    @classmethod
    def encrypt_token(cls, token: Optional[str]) -> Optional[str]:
        """Encrypts a plaintext token string with AES-256-GCM.
        Returns: 'enc:v1:<base64_nonce>:<base64_ciphertext>'
        """
        if not token:
            return token
        if token.startswith("enc:v1:"):
            return token  # Already encrypted

        key = cls.get_or_create_master_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit unique nonce

        ciphertext = aesgcm.encrypt(nonce, token.encode("utf-8"), None)
        nonce_b64 = base64.urlsafe_b64encode(nonce).decode("utf-8")
        ct_b64 = base64.urlsafe_b64encode(ciphertext).decode("utf-8")

        return f"enc:v1:{nonce_b64}:{ct_b64}"

    @classmethod
    def decrypt_token(cls, enc_token: Optional[str], channel_id: str = "unknown") -> Optional[str]:
        """Decrypts a token string.
        Raises TokenDecryptionError if corrupt or key mismatch. NEVER falls back silently.
        """
        if not enc_token:
            return enc_token

        if not enc_token.startswith("enc:v1:"):
            # Legacy unmigrated token - return it for migration pass
            return enc_token

        parts = enc_token.split(":")
        if len(parts) != 4:
            raise TokenDecryptionError(f"Malformed token format for channel {channel_id}")

        _, version, nonce_b64, ct_b64 = parts
        if version != "v1":
            raise TokenDecryptionError(f"Unsupported token version '{version}' for channel {channel_id}")

        try:
            nonce = base64.urlsafe_b64decode(nonce_b64.encode("utf-8"))
            ciphertext = base64.urlsafe_b64decode(ct_b64.encode("utf-8"))
            key = cls.get_or_create_master_key()
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except InvalidTag:
            logger.error(f"[Security] Token decryption failed for channel {channel_id}: authentication tag mismatch.")
            raise TokenDecryptionError(f"Decryption authentication failed for channel {channel_id}")
        except Exception as e:
            logger.error(f"[Security] Token decryption failed for channel {channel_id}: {str(e)}")
            raise TokenDecryptionError(f"Decryption error for channel {channel_id}: {str(e)}")

    @classmethod
    def perform_protected_sqlite_backup(cls, source_db: Path) -> Path:
        """Performs a transaction-consistent SQLite online backup and encrypts the backup file."""
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        tmp_backup = BACKUPS_DIR / f"temp_{now_str}.db"
        final_backup_enc = BACKUPS_DIR / f"scheduler.db.bak_{now_str}.dpapi"

        if not source_db.exists():
            return final_backup_enc

        # 1. Transaction-consistent SQLite online backup
        with sqlite3.connect(str(source_db.resolve())) as src, sqlite3.connect(str(tmp_backup.resolve())) as dst:
            src.backup(dst)

        # 2. Read bytes and encrypt with DPAPI or AESGCM
        raw_db_bytes = tmp_backup.read_bytes()
        if _is_windows():
            encrypted_db_bytes = _dpapi_encrypt(raw_db_bytes)
        else:
            key = cls.get_or_create_master_key()
            aesgcm = AESGCM(key)
            nonce = os.urandom(12)
            encrypted_db_bytes = nonce + aesgcm.encrypt(nonce, raw_db_bytes, None)

        # 3. Write encrypted backup and clean up plaintext temp file
        final_backup_enc.write_bytes(encrypted_db_bytes)
        try:
            tmp_backup.unlink()
        except Exception:
            pass

        logger.info(f"[Security] Created protected encrypted database backup: {final_backup_enc.name}")
        return final_backup_enc

    @classmethod
    def migrate_scheduler_db(cls, db_path: Optional[Path] = None) -> int:
        """Migrates any existing plaintext tokens in connected_channels to encrypted format.
        Creates a protected backup before modifying any data.
        Returns the count of tokens migrated.
        """
        target_db = db_path or DB_PATH
        if not target_db.exists():
            return 0

        # Step 1: Protected online backup
        cls.perform_protected_sqlite_backup(target_db)

        # Step 2: Atomic migration transaction
        migrated_count = 0
        with sqlite3.connect(str(target_db.resolve())) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Ensure table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='connected_channels'")
            if not cur.fetchone():
                return 0

            cur.execute("SELECT channel_id, refresh_token, access_token FROM connected_channels")
            rows = cur.fetchall()

            for row in rows:
                ch_id = row["channel_id"]
                rf_token = row["refresh_token"]
                ac_token = row["access_token"]

                needs_update = False
                enc_rf = rf_token
                enc_ac = ac_token

                if rf_token and not rf_token.startswith("enc:v1:"):
                    enc_rf = cls.encrypt_token(rf_token)
                    needs_update = True
                    migrated_count += 1

                if ac_token and not ac_token.startswith("enc:v1:"):
                    enc_ac = cls.encrypt_token(ac_token)
                    needs_update = True
                    migrated_count += 1

                if needs_update:
                    cur.execute(
                        "UPDATE connected_channels SET refresh_token = ?, access_token = ? WHERE channel_id = ?",
                        (enc_rf, enc_ac, ch_id),
                    )

            conn.commit()

        logger.info(f"[Security] Migrated {migrated_count} tokens to AES-256-GCM encryption.")
        return migrated_count

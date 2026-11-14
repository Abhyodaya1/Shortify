"""Unit and integration tests for TokenEncryptionService and encrypted token persistence."""

import os
import sqlite3
import pytest
from pathlib import Path
from backend.app.services.token_encryption_service import (
    TokenEncryptionService,
    TokenDecryptionError,
)
from backend.app.services.persistent_scheduler import PersistentScheduler


def test_token_encrypt_decrypt_roundtrip():
    token = "ya29.a0AfH6SMA_TEST_TOKEN_12345_SECRET"
    enc = TokenEncryptionService.encrypt_token(token)
    assert enc is not None
    assert enc.startswith("enc:v1:")
    assert enc != token

    dec = TokenEncryptionService.decrypt_token(enc, channel_id="test_channel")
    assert dec == token


def test_idempotent_encryption():
    token = "sample_secret_token"
    enc1 = TokenEncryptionService.encrypt_token(token)
    enc2 = TokenEncryptionService.encrypt_token(enc1)
    assert enc1 == enc2  # Does not double-encrypt


def test_decryption_tamper_detection():
    token = "secret_youtube_refresh_token_xyz"
    enc = TokenEncryptionService.encrypt_token(token)
    parts = enc.split(":")
    # Tamper with the ciphertext payload
    ct = parts[3]
    tampered_ct = ct[:-2] + ("AA" if ct[-2:] != "AA" else "BB")
    tampered_enc = f"{parts[0]}:{parts[1]}:{parts[2]}:{tampered_ct}"

    with pytest.raises(TokenDecryptionError):
        TokenEncryptionService.decrypt_token(tampered_enc, channel_id="test_channel")


def test_protected_online_sqlite_backup(tmp_path):
    db_file = tmp_path / "test_scheduler.db"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("CREATE TABLE sample (id INT, secret TEXT)")
        conn.execute("INSERT INTO sample VALUES (1, 'sensitive_token')")
        conn.commit()

    backup_path = TokenEncryptionService.perform_protected_sqlite_backup(db_file)
    assert backup_path.exists()
    assert backup_path.stat().st_size > 0
    # Ensure raw plaintext SQLite header "SQLite format 3" is NOT present in the encrypted backup file
    raw_content = backup_path.read_bytes()
    assert b"SQLite format 3" not in raw_content


def test_token_migration_preserves_tokens(tmp_path):
    test_db = tmp_path / "migration_test.db"
    with sqlite3.connect(str(test_db)) as conn:
        conn.execute("""
        CREATE TABLE connected_channels (
            channel_id TEXT PRIMARY KEY,
            user_id TEXT,
            channel_title TEXT,
            custom_url TEXT,
            thumbnail_url TEXT,
            subscriber_count INT,
            video_count INT,
            is_sandbox INT,
            refresh_token TEXT,
            access_token TEXT,
            created_at TEXT
        )
        """)
        conn.execute("""
        INSERT INTO connected_channels VALUES (
            'UC_plain_1', 'user_1', 'My Channel', '@mychan', 'thumb', 100, 10, 0,
            'plaintext_refresh_token_123', 'plaintext_access_token_456', '2026-01-01'
        )
        """)
        conn.commit()

    # Run migration
    migrated = TokenEncryptionService.migrate_scheduler_db(test_db)
    assert migrated == 2

    # Verify on-disk format is now encrypted
    with sqlite3.connect(str(test_db)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT refresh_token, access_token FROM connected_channels WHERE channel_id = 'UC_plain_1'")
        row = cur.fetchone()
        assert row[0].startswith("enc:v1:")
        assert row[1].startswith("enc:v1:")

        # Decrypt and verify equality
        dec_rf = TokenEncryptionService.decrypt_token(row[0])
        dec_ac = TokenEncryptionService.decrypt_token(row[1])
        assert dec_rf == "plaintext_refresh_token_123"
        assert dec_ac == "plaintext_access_token_456"

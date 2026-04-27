from __future__ import annotations

import base64
import binascii
import html
import hashlib
import hmac
import io
import json
import math
import mimetypes
import os
import re
import secrets
import uuid

import sqlite3
import threading
import time
import urllib.request

from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
except Exception:  # pragma: no cover - fallback local sin PostgreSQL
    psycopg2 = None

# Pool de conexiones PostgreSQL (inicializado en main())
_pg_pool: Optional[Any] = None
_pg_pool_lock = threading.Lock()


BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_FALLBACK_PATH = Path(os.environ.get("SQLITE_FALLBACK_PATH", str(BASE_DIR / "data" / "enturnamiento.db")))
FCM_SERVER_KEY = os.environ.get("FCM_SERVER_KEY", "")
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@enturnamiento.com")
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", str(BASE_DIR / "data" / "uploads")))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
SESSION_COOKIE = "ev_session"
SESSION_HOURS = 16

ROLE_ADMIN = "ADMIN"
ROLE_LOGISTICS = "LOGISTICA"
ROLE_QUALITY = "CALIDAD"
ROLE_VIEWER = "VISUALIZADOR"
VALID_ROLES = {ROLE_ADMIN, ROLE_LOGISTICS, ROLE_QUALITY, ROLE_VIEWER}
CATALOG_ADD_ONLY_IDENTITIES = {
    "samantalozano",
    "samanta lozano",
    "katherindelgado",
    "katherin delgado",
    "katerindelgado",
    "katerin delgado",
    "auxfacturacion",
    "aux facturacion",
    "auxdistribucion",
    "aux distribucion",
}
QUEUE_STATUS_ACTIVE = "QUEUED"
QUEUE_STATUS_ASSIGNED = "ASSIGNED"
QUEUE_STATUS_REJECTED = "REJECTED"
QUALITY_PENDING = "PENDING"
QUALITY_IN_PROGRESS = "IN_REVIEW"
QUALITY_APPROVED = "APPROVED"
QUALITY_REWORK = "REWORK"
QUALITY_REJECTED = "REJECTED"
QUEUE_GROUP_GENERAL = "GENERAL"
QUEUE_GROUP_DIANA = "DIANA_AGRICOLA"
DIANA_AGRICOLA_CODE = "4000801"
LOCAL_TIMEZONE = timezone(timedelta(hours=-5))

INITIAL_DESTINATIONS = [
    ("Bogota", "Cundinamarca"),
    ("Medellin", "Antioquia"),
    ("Bucaramanga", "Santander"),
    ("Barranquilla", "Costa"),
    ("Cartagena", "Costa"),
    ("Pereira", "Eje Cafetero"),
]

INITIAL_CARRIERS = [
    ("4005739", "ADISPETROL"),
    ("4000856", "CARGAS DE COLOMBIA SAS."),
    ("4002879", "CETER (COOPERATIVA MULTIACTIVA Y DE TRANSPORTE)"),
    ("14000800", "CLIENTE RECOGE"),
    ("4006144", "CONALTRA"),
    ("4006141", "CONDOR ANDINO"),
    ("4001457", "COTRASUR (COOPERATIVA DE TRANSPORTADORES DEL SUR)"),
    ("4000801", "DIANA AGRICOLA S.A.S"),
    ("4005207", "EDUARDO BOTERO SOTO S.A."),
    ("4006136", "FL COLOMBIA"),
    ("4006121", "FLETX COLOMBIA"),
    ("4005771", "GAYCO"),
    ("4002308", "GLOBAL LOGISTIC SERVICES"),
    ("4001312", "IMPOCOMA S.A.S"),
    ("4005790", "LOGISTICA Y OPERADORA DE TRANSPORTES LOPERTRANS SAS"),
    ("4006080", "LOGISTICA Y TRASPORTE DEL LLANO EXPRESS LTS"),
    ("4006169", "MBLS"),
    ("4005715", "NUTRITRANS"),
    ("4005447", "OKENDO S.A.S"),
    ("4005520", "OLT ( ORGANIZACION LOGISTICA TRANSPORTADORA)"),
    ("4002551", "OPL (OPERADORES LOGISTICOS DE CARGA S.A.)"),
    ("14000005", "PROPIO"),
    ("4006040", "RECISERVICIOS CIRCULAR"),
    ("4005226", "TRANSER S."),
    ("4005815", "TRANSOLICAR S.A.S"),
    ("4001185", "TRANSPORTES TERRESTRES DE CARGA LTD"),
    ("4006213", "TRASURCAR"),
    ("4003859", "TRT (TRANSPORTADORA REGIONAL DEL TOLIMA)"),
    ("4005641", "TSC (TANQUES Y SERVICIOS DEL CASANARE S)"),
    ("4005880", "VECOBA"),
    ("4001207", "VIACARGO SAS"),
    ("4005705", "VIGIA"),
]

DEFAULT_USERS = [
    ("admin", "Administrador General", ROLE_ADMIN, "Admin2026!"),
    ("logistica", "Logistica Principal", ROLE_LOGISTICS, "Logistica2026!"),
    ("calidad", "Inspector Calidad", ROLE_QUALITY, "Calidad2026!"),
]

DEFAULT_SETTINGS = {
    "site_name": "Planta principal",
    "site_lat": "5.286142",
    "site_lng": "-72.402228",
    "site_radius_m": "180",
    "geofence_enabled": "1",
}

DEFAULT_CENTER_ID = "1010"
INITIAL_CENTERS = [
    ("1010", "1010", "Yopal centro 1010", "5.286142", "-72.402228", "180", "1"),
    ("1000", "1000", "Espinal centro 1000", "4.158676", "-74.900485", "180", "1"),
]

PDF_TEMPLATE_PATH = BASE_DIR / "assets" / "Formato_FO-CL-021_AJUSTADO.pdf"
PDF_LOGO_PATH = BASE_DIR / "assets" / "logo-diana-corporativo.png"
CHECKLIST_EXPORT_ROWS = [
    ("foodLegend", 'Cuenta con leyenda visible "Transporte de alimentos"'),
    ("cleanliness", "Libre de suciedad"),
    ("strangeSmells", "Libre de olores extraños"),
    ("stains", "Libre de manchas"),
    ("damage", "Libre de orificios y averías"),
    ("humidity", "Libre de humedad"),
    ("infestation", "Libre de infestación"),
    ("bulkWallsFloor", "Granel en paredes y piso"),
    ("containerHoles", "Trompos limpios y protegidos"),
    ("woodenStakesPestFree", "Estacas de madera libres de plagas"),
    ("fumigationIn", "Fumigación ingreso"),
    ("fumigationOut", "Fumigación salida"),
]
DATABASE_DRIVER_ERRORS = (psycopg2.Error,) if psycopg2 else (RuntimeError,)


class AppError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_local() -> datetime:
    return datetime.now(LOCAL_TIMEZONE)


def iso_to_local(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(LOCAL_TIMEZONE)


def is_same_local_day(value: Optional[str], reference: Optional[datetime] = None) -> bool:
    local_value = iso_to_local(value)
    if not local_value:
        return False
    base = reference or now_local()
    return local_value.date() == base.date()


def create_id() -> str:
    return uuid.uuid4().hex


def clean_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_plate(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", clean_text(value).upper())


def parse_float(value: object) -> Optional[float]:
    raw = clean_text(value).replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise AppError("El valor numerico recibido no es valido.", 400) from exc


def queue_group_for_carrier_code(carrier_code: Optional[str]) -> str:
    return QUEUE_GROUP_DIANA if clean_text(carrier_code) == DIANA_AGRICOLA_CODE else QUEUE_GROUP_GENERAL


def queue_group_label(queue_group: str) -> str:
    return "Diana Agricola" if queue_group == QUEUE_GROUP_DIANA else "Otras transportadoras"


class _Row(dict):
    """Dict que soporta acceso por índice entero (compatibilidad con sqlite3.Row)."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _Cursor:
    def __init__(self, cur):
        self._cur = cur

    def fetchone(self):
        row = self._cur.fetchone()
        return _Row(row) if row else None

    def fetchall(self):
        return [_Row(r) for r in (self._cur.fetchall() or [])]


class _Conn:
    """Wrapper de psycopg2 que expone la misma API que sqlite3.Connection."""

    def __init__(self, raw):
        self._raw = raw
        self._cur = raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    @staticmethod
    def _adapt(sql: str) -> str:
        return sql.replace("?", "%s")

    def execute(self, sql: str, params=None) -> _Cursor:
        self._cur.execute(self._adapt(sql), params)
        return _Cursor(self._cur)

    def executemany(self, sql: str, seq) -> None:
        self._cur.executemany(self._adapt(sql), seq)

    def executescript(self, script: str) -> None:
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                self._cur.execute(stmt)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        self._raw.close()


class _PooledConn(_Conn):
    """Igual que _Conn pero devuelve la conexión al pool en vez de cerrarla."""

    def __init__(self, raw, pool):
        super().__init__(raw)
        self._pool = pool

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self._raw.commit()
        else:
            try:
                self._raw.rollback()
            except Exception:
                self._pool.putconn(self._raw, close=True)
                return
        self._pool.putconn(self._raw)


def get_vapid_keys() -> Tuple[str, str]:
    try:
        conn = get_connection()
        with conn as db:
            priv = db.execute("SELECT value FROM settings WHERE key = 'vapid_private_key'").fetchone()
            pub = db.execute("SELECT value FROM settings WHERE key = 'vapid_public_key'").fetchone()
        if priv and pub and priv["value"] and pub["value"]:
            return priv["value"], pub["value"]
        from py_vapid import Vapid
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        v = Vapid()
        v.generate_keys()
        private_pem = v.private_pem().decode()
        pub_bytes = v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        import base64
        pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()
        with get_connection() as db:
            for k, val in [("vapid_private_key", private_pem), ("vapid_public_key", pub_b64)]:
                db.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    (k, val),
                )
        return private_pem, pub_b64
    except Exception as exc:
        print(f"VAPID key error: {exc}")
        return "", ""


def send_notification(title: str, body: str, tag: str = "update") -> None:
    threading.Thread(target=_dispatch_notifications, args=(title, body, tag), daemon=True).start()


def _dispatch_notifications(title: str, body: str, tag: str) -> None:
    payload = json.dumps({"title": title, "body": body, "tag": tag}).encode()
    # Web Push
    try:
        private_key, _ = get_vapid_keys()
        if private_key:
            from pywebpush import webpush, WebPushException
            with get_connection() as db:
                subs = db.execute("SELECT * FROM push_subscriptions").fetchall()
            expired = []
            for sub in subs:
                try:
                    webpush(
                        subscription_info={
                            "endpoint": sub["endpoint"],
                            "keys": {"auth": sub["auth"], "p256dh": sub["p256dh"]},
                        },
                        data=payload,
                        vapid_private_key=private_key,
                        vapid_claims={"sub": VAPID_SUBJECT},
                    )
                except WebPushException as exc:
                    if exc.response and exc.response.status_code in (404, 410):
                        expired.append(sub["id"])
                except Exception:
                    pass
            if expired:
                with get_connection() as db:
                    for sid in expired:
                        db.execute("DELETE FROM push_subscriptions WHERE id = ?", (sid,))
    except Exception as exc:
        print(f"Web push error: {exc}")
    # FCM
    if FCM_SERVER_KEY:
        try:
            with get_connection() as db:
                tokens = [r["token"] for r in db.execute("SELECT token FROM fcm_tokens").fetchall()]
            if tokens:
                fcm_body = json.dumps({
                    "registration_ids": tokens,
                    "notification": {"title": title, "body": body, "sound": "default"},
                    "data": {"title": title, "body": body},
                }).encode()
                req = urllib.request.Request(
                    "https://fcm.googleapis.com/fcm/send",
                    data=fcm_body,
                    headers={
                        "Authorization": f"key={FCM_SERVER_KEY}",
                        "Content-Type": "application/json",
                    },
                )
                urllib.request.urlopen(req, timeout=10)
        except Exception as exc:
            print(f"FCM error: {exc}")


def get_connection() -> _Conn:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    SQLITE_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATABASE_URL and psycopg2:
        global _pg_pool
        pool = _pg_pool
        if pool:
            for attempt in range(3):
                try:
                    raw = pool.getconn()
                    # Verificar que la conexión esté viva
                    try:
                        raw.cursor().execute("SELECT 1")
                        raw.rollback()
                    except Exception:
                        pool.putconn(raw, close=True)
                        raw = pool.getconn()
                    return _PooledConn(raw, pool)
                except Exception as err:
                    print(f"Pool.getconn intento {attempt + 1}/3: {err}")
                    if attempt < 2:
                        time.sleep(0.5)
        # Fallback: conexión directa si el pool no está listo
        try:
            return _Conn(psycopg2.connect(DATABASE_URL))
        except Exception as error:
            print(f"PostgreSQL no disponible, se activa contingencia SQLite: {error}")
    elif DATABASE_URL and not psycopg2:
        print("psycopg2 no está disponible; se activa contingencia SQLite.")
    sqlite_conn = sqlite3.connect(SQLITE_FALLBACK_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_conn.execute("PRAGMA foreign_keys = ON")
    return sqlite_conn


def is_postgres_connection(db: Any) -> bool:
    return isinstance(db, _Conn)


def list_table_columns(db: Any, table_name: str) -> set[str]:
    if is_postgres_connection(db):
        return {
            row["name"]
            for row in db.execute(
                "SELECT column_name AS name FROM information_schema.columns "
                "WHERE table_name = ? AND table_schema = current_schema()",
                (table_name,),
            ).fetchall()
        }
    return {
        row["name"]
        for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def add_column_if_missing(db: Any, table_name: str, column_name: str, column_type: str) -> None:
    if column_name in list_table_columns(db, table_name):
        return
    if is_postgres_connection(db):
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
        return
    db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260000)
    return hmac.compare_digest(candidate, expected)


def init_db() -> None:
    with get_connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS destinations (
                id TEXT PRIMARY KEY,
                city TEXT NOT NULL,
                zone TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_destinations_city_zone
            ON destinations (LOWER(city), LOWER(zone));

            CREATE TABLE IF NOT EXISTS carriers (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_carriers_name
            ON carriers (LOWER(name));

            CREATE TABLE IF NOT EXISTS centers (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                site_lat TEXT NOT NULL,
                site_lng TEXT NOT NULL,
                site_radius_m TEXT NOT NULL,
                geofence_enabled TEXT NOT NULL DEFAULT '1',
                created_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_centers_name
            ON centers (LOWER(name));

            CREATE TABLE IF NOT EXISTS vehicles (
                id TEXT PRIMARY KEY,
                plate TEXT NOT NULL,
                carrier_code TEXT,
                carrier TEXT NOT NULL,
                driver_name TEXT NOT NULL,
                driver_id TEXT NOT NULL,
                destination_id TEXT NOT NULL,
                city TEXT NOT NULL,
                zone TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('QUEUED', 'ASSIGNED', 'REJECTED')),
                queue_position INTEGER,
                created_at TEXT NOT NULL,
                assigned_at TEXT,
                rejected_at TEXT,
                rejection_reason TEXT,
                FOREIGN KEY (destination_id) REFERENCES destinations(id)
            );
            CREATE INDEX IF NOT EXISTS idx_vehicles_status_queue
            ON vehicles (status, queue_position);

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('ADMIN', 'LOGISTICA', 'CALIDAD')),
                password_hash TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quality_inspections (
                id TEXT PRIMARY KEY,
                vehicle_id TEXT NOT NULL,
                inspector_user_id TEXT NOT NULL,
                inspector_name TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                final_decision TEXT NOT NULL CHECK(final_decision IN ('APPROVED', 'REWORK', 'REJECTED')),
                suitability_json TEXT NOT NULL,
                observations_text TEXT NOT NULL,
                checklist_json TEXT NOT NULL,
                findings_summary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                FOREIGN KEY (inspector_user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_quality_vehicle_review
            ON quality_inspections (vehicle_id, reviewed_at DESC);

            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL UNIQUE,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fcm_tokens (
                id TEXT PRIMARY KEY,
                token TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            """
        )
        ensure_vehicle_columns(db)
        ensure_user_roles_schema(db)
        ensure_center_columns(db)
        seed_settings(db)
        seed_centers(db)
        seed_destinations(db)
        seed_carriers(db)
        seed_users(db)
        seed_tracking_tokens(db)


def ensure_vehicle_columns(db: sqlite3.Connection) -> None:
    columns = list_table_columns(db, "vehicles")
    extra_columns = {
        "carrier_id": "TEXT",
        "driver_phone": "TEXT",
        "empty_weight_kg": "REAL",
        "driver_selfie_url": "TEXT",
        "driver_signature_url": "TEXT",
        "destination_ids_json": "TEXT",
        "registration_channel": "TEXT DEFAULT 'DESK'",
        "gps_lat": "REAL",
        "gps_lng": "REAL",
        "gps_distance_m": "REAL",
        "queue_group": f"TEXT DEFAULT '{QUEUE_GROUP_GENERAL}'",
        "quality_status": "TEXT DEFAULT 'PENDING'",
        "public_tracking_token": "TEXT",
        "last_quality_at": "TEXT",
        "center_id": "TEXT",
        "center_code": "TEXT",
        "center_name": "TEXT",
    }
    for column_name, column_type in extra_columns.items():
        add_column_if_missing(db, "vehicles", column_name, column_type)
    db.execute(
        "UPDATE vehicles SET quality_status = ? WHERE quality_status IS NULL OR quality_status = ''",
        (QUALITY_PENDING,),
    )
    db.execute(
        "UPDATE vehicles SET registration_channel = 'DESK' WHERE registration_channel IS NULL OR registration_channel = ''"
    )
    db.execute(
        "UPDATE vehicles SET queue_group = ? WHERE queue_group IS NULL OR queue_group = ''",
        (QUEUE_GROUP_GENERAL,),
    )
    if is_postgres_connection(db):
        db.execute(
            """
            UPDATE vehicles
            SET destination_ids_json = json_build_array(destination_id)::text
            WHERE (destination_ids_json IS NULL OR destination_ids_json = '')
              AND destination_id IS NOT NULL AND destination_id != ''
            """
        )
    else:
        rows_missing_destinations = db.execute(
            """
            SELECT id, destination_id FROM vehicles
            WHERE (destination_ids_json IS NULL OR destination_ids_json = '')
              AND destination_id IS NOT NULL AND destination_id != ''
            """
        ).fetchall()
        for row in rows_missing_destinations:
            db.execute(
                "UPDATE vehicles SET destination_ids_json = ? WHERE id = ?",
                (json.dumps([row["destination_id"]], ensure_ascii=False), row["id"]),
            )
    rows = db.execute("SELECT id, carrier_code FROM vehicles").fetchall()
    for row in rows:
        db.execute(
            "UPDATE vehicles SET queue_group = ? WHERE id = ?",
            (queue_group_for_carrier_code(row["carrier_code"]), row["id"]),
        )
    db.execute(
        "UPDATE vehicles SET public_tracking_token = ? WHERE public_tracking_token IS NULL OR public_tracking_token = ''",
        (create_id(),),
    )
    db.execute(
        "UPDATE vehicles SET center_id = ?, center_code = ?, center_name = ? WHERE center_id IS NULL OR center_id = ''",
        (DEFAULT_CENTER_ID, DEFAULT_CENTER_ID, "Yopal centro 1010"),
    )
    compact_queue(db)


def ensure_user_roles_schema(db: _Conn) -> None:
    pass  # PostgreSQL crea las tablas con los constraints correctos desde el inicio


def ensure_center_columns(db: sqlite3.Connection) -> None:
    user_columns = list_table_columns(db, "users")
    for column_name, column_type in {
        "center_id": "TEXT",
        "center_code": "TEXT",
        "center_name": "TEXT",
    }.items():
        if column_name not in user_columns:
            add_column_if_missing(db, "users", column_name, column_type)
    db.execute(
        "UPDATE users SET center_id = ?, center_code = ?, center_name = ? WHERE center_id IS NULL OR center_id = ''",
        (DEFAULT_CENTER_ID, DEFAULT_CENTER_ID, "Yopal centro 1010"),
    )


def seed_settings(db: sqlite3.Connection) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        exists = db.execute("SELECT key FROM settings WHERE key = ?", (key,)).fetchone()
        if not exists:
            db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
        elif key in {"site_lat", "site_lng"}:
            current = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            if current and not clean_text(current["value"]):
                db.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))


def seed_centers(db: sqlite3.Connection) -> None:
    if db.execute("SELECT COUNT(*) FROM centers").fetchone()[0]:
        return
    db.executemany(
        """
        INSERT INTO centers (id, code, name, site_lat, site_lng, site_radius_m, geofence_enabled, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(center_id, code, name, lat, lng, radius, enabled, now_iso()) for center_id, code, name, lat, lng, radius, enabled in INITIAL_CENTERS],
    )


def seed_destinations(db: sqlite3.Connection) -> None:
    if db.execute("SELECT COUNT(*) FROM destinations").fetchone()[0]:
        return
    db.executemany(
        "INSERT INTO destinations (id, city, zone, created_at) VALUES (?, ?, ?, ?)",
        [(create_id(), city, zone, now_iso()) for city, zone in INITIAL_DESTINATIONS],
    )


def seed_carriers(db: sqlite3.Connection) -> None:
    if db.execute("SELECT COUNT(*) FROM carriers").fetchone()[0]:
        return
    db.executemany(
        "INSERT INTO carriers (id, code, name, created_at) VALUES (?, ?, ?, ?)",
        [(create_id(), code, name, now_iso()) for code, name in INITIAL_CARRIERS],
    )


def seed_users(db: sqlite3.Connection) -> None:
    existing = {
        row["username"]: row["id"]
        for row in db.execute("SELECT id, username FROM users").fetchall()
    }
    for username, full_name, role, password in DEFAULT_USERS:
        if username in existing:
            continue
        db.execute(
            """
            INSERT INTO users (id, username, full_name, role, password_hash, created_at, center_id, center_code, center_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                create_id(),
                username,
                full_name,
                role,
                hash_password(password),
                now_iso(),
                DEFAULT_CENTER_ID,
                DEFAULT_CENTER_ID,
                "Yopal centro 1010",
            ),
        )


def seed_tracking_tokens(db: sqlite3.Connection) -> None:
    rows = db.execute(
        "SELECT id FROM vehicles WHERE public_tracking_token IS NULL OR public_tracking_token = ''"
    ).fetchall()
    for row in rows:
        db.execute(
            "UPDATE vehicles SET public_tracking_token = ? WHERE id = ?",
            (create_id(), row["id"]),
        )


def clear_expired_sessions(db: sqlite3.Connection) -> None:
    db.execute("DELETE FROM sessions WHERE expires_at < ?", (now_iso(),))


def get_settings_map(db: sqlite3.Connection) -> Dict[str, str]:
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_settings_values(db: sqlite3.Connection, values: Dict[str, str]) -> None:
    for key, value in values.items():
        db.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )


def create_session(db: sqlite3.Connection, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    created_at = now_iso()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)).isoformat()
    db.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, created_at, expires_at),
    )
    return token


def build_auth_payload(user: sqlite3.Row, origin: str, token: str) -> Dict[str, Any]:
    state = get_user_state(user, origin)
    state["sessionToken"] = token
    return state


def build_mobile_auth_payload(user: sqlite3.Row, token: str) -> Dict[str, Any]:
    state = build_mobile_quality_state(user)
    state["sessionToken"] = token
    return state


def get_authenticated_user_by_token(db: sqlite3.Connection, token: str) -> Optional[sqlite3.Row]:
    clear_expired_sessions(db)
    return db.execute(
        """
        SELECT users.* FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ? AND sessions.expires_at >= ? AND users.active = 1
        """,
        (token, now_iso()),
    ).fetchone()


def serialize_destination(row: sqlite3.Row) -> Dict[str, Any]:
    return {"id": row["id"], "city": row["city"], "zone": row["zone"]}


def serialize_carrier(row: sqlite3.Row) -> Dict[str, Any]:
    return {"id": row["id"], "code": row["code"], "name": row["name"]}


def serialize_center(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "code": row["code"],
        "name": row["name"],
        "siteLat": row["site_lat"],
        "siteLng": row["site_lng"],
        "siteRadiusM": row["site_radius_m"],
        "geofenceEnabled": clean_text(row["geofence_enabled"]) == "1",
    }


def load_centers(db: sqlite3.Connection) -> List[Dict[str, Any]]:
    return [serialize_center(row) for row in db.execute("SELECT * FROM centers ORDER BY code").fetchall()]


def build_center_lookup(centers: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {item["id"]: item for item in centers}


def visible_center_ids_for_user(user: sqlite3.Row, centers: List[Dict[str, Any]]) -> List[str]:
    if user["role"] == ROLE_ADMIN:
        return [center["id"] for center in centers]
    center_id = clean_text(user.get("center_id")) if isinstance(user, dict) else clean_text(user["center_id"])
    return [center_id or DEFAULT_CENTER_ID]


def normalize_identity(value: Any) -> str:
    return clean_text(value).lower().replace(" ", "")


def can_add_catalogs(user: sqlite3.Row) -> bool:
    if user["role"] == ROLE_ADMIN:
        return True
    username = normalize_identity(user["username"])
    full_name = normalize_identity(user["full_name"])
    allowed = {item.replace(" ", "") for item in CATALOG_ADD_ONLY_IDENTITIES}
    return username in allowed or full_name in allowed


def preferred_center_for_user(user: sqlite3.Row, centers: List[Dict[str, Any]]) -> Dict[str, Any]:
    center_lookup = build_center_lookup(centers)
    center_id = clean_text(user.get("center_id")) if isinstance(user, dict) else clean_text(user["center_id"])
    return center_lookup.get(center_id) or (centers[0] if centers else {
        "id": DEFAULT_CENTER_ID,
        "code": DEFAULT_CENTER_ID,
        "name": "Yopal centro 1010",
        "siteLat": DEFAULT_SETTINGS["site_lat"],
        "siteLng": DEFAULT_SETTINGS["site_lng"],
        "siteRadiusM": DEFAULT_SETTINGS["site_radius_m"],
        "geofenceEnabled": True,
    })


def parse_json_field(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _sanitize_checklist_for_client(checklist: Dict[str, Any], include_media: bool) -> Dict[str, Any]:
    if include_media:
        return checklist
    sanitized: Dict[str, Any] = {}
    for key, item in checklist.items():
        if not isinstance(item, dict):
            sanitized[key] = item
            continue
        copied = dict(item)
        evidences = copied.get("evidences") or []
        copied["evidences"] = ["" for _ in evidences]
        sanitized[key] = copied
    return sanitized


def serialize_inspection(row: sqlite3.Row, include_media: bool = True) -> Dict[str, Any]:
    checklist = _sanitize_checklist_for_client(parse_json_field(row["checklist_json"], {}), include_media)
    return {
        "id": row["id"],
        "vehicleId": row["vehicle_id"],
        "inspectorUserId": row["inspector_user_id"],
        "inspectorName": row["inspector_name"],
        "reviewedAt": row["reviewed_at"],
        "finalDecision": row["final_decision"],
        "suitability": parse_json_field(row["suitability_json"], []),
        "observationsText": row["observations_text"],
        "checklist": checklist,
        "findingsSummary": row["findings_summary"],
    }


def compact_inspection_for_history(inspection: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not inspection:
        return {}
    return {
        "id": inspection.get("id"),
        "inspectorName": inspection.get("inspectorName"),
        "reviewedAt": inspection.get("reviewedAt"),
        "finalDecision": inspection.get("finalDecision"),
        "suitability": inspection.get("suitability") or [],
        "findingsSummary": inspection.get("findingsSummary") or "",
        "observationsText": inspection.get("observationsText") or "",
    }


def count_checklist_evidences(checklist: Dict[str, Any]) -> int:
    total = 0
    if not isinstance(checklist, dict):
        return total
    for item in checklist.values():
        if not isinstance(item, dict):
            continue
        total += len([evidence for evidence in (item.get("evidences") or []) if evidence])
    return total


def summarize_inspection_for_vehicle(inspection: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not inspection:
        return None
    return {
        "id": inspection.get("id"),
        "inspectorUserId": inspection.get("inspectorUserId"),
        "inspectorName": inspection.get("inspectorName"),
        "reviewedAt": inspection.get("reviewedAt"),
        "finalDecision": inspection.get("finalDecision"),
        "suitability": inspection.get("suitability") or [],
        "observationsText": inspection.get("observationsText") or "",
        "findingsSummary": inspection.get("findingsSummary") or "",
        "evidenceCount": count_checklist_evidences(inspection.get("checklist") or {}),
    }


def load_inspections_by_vehicle(db: sqlite3.Connection, include_media: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    rows = db.execute(
        "SELECT * FROM quality_inspections ORDER BY reviewed_at DESC, created_at DESC"
    ).fetchall()
    for row in rows:
        grouped.setdefault(row["vehicle_id"], []).append(serialize_inspection(row, include_media=include_media))
    return grouped


def load_latest_inspections(db: sqlite3.Connection, include_media: bool = True) -> Dict[str, Dict[str, Any]]:
    inspections: Dict[str, Dict[str, Any]] = {}
    rows = db.execute(
        "SELECT * FROM quality_inspections ORDER BY reviewed_at DESC, created_at DESC"
    ).fetchall()
    for row in rows:
        if row["vehicle_id"] in inspections:
            continue
        inspections[row["vehicle_id"]] = serialize_inspection(row, include_media=include_media)
    return inspections


def calculate_turn_positions(queued_rows: List[sqlite3.Row]) -> Dict[str, int]:
    positions: Dict[str, int] = {}
    grouped_rows: Dict[str, List[sqlite3.Row]] = {
        QUEUE_GROUP_GENERAL: [],
        QUEUE_GROUP_DIANA: [],
    }
    for row in queued_rows:
        grouped_rows.setdefault(row["queue_group"] or QUEUE_GROUP_GENERAL, []).append(row)
    for group_rows in grouped_rows.values():
        for index, row in enumerate(group_rows, start=1):
            positions[row["id"]] = index
    return positions


def parse_destination_ids(row: sqlite3.Row) -> List[str]:
    parsed = parse_json_field(row["destination_ids_json"], [])
    if isinstance(parsed, list) and parsed:
        return [clean_text(item) for item in parsed if clean_text(item)]
    destination_id = clean_text(row["destination_id"])
    return [destination_id] if destination_id else []


def build_destination_lookup(destinations: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {item["id"]: item for item in destinations}


def build_destination_options(row: sqlite3.Row, lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    options: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for destination_id in parse_destination_ids(row):
        destination = lookup.get(destination_id)
        if not destination:
            continue
        key = f"{destination['city']}::{destination['zone']}"
        if key in seen:
            continue
        seen.add(key)
        options.append(destination)
    if not options and clean_text(row["city"]) and clean_text(row["zone"]):
        options.append({"id": clean_text(row["destination_id"]), "city": row["city"], "zone": row["zone"]})
    return options


def build_city_turn_maps(
    queued_rows: List[sqlite3.Row],
    destination_lookup: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, int]], Dict[str, List[Dict[str, Any]]]]:
    position_map: Dict[str, Dict[str, int]] = {}
    city_lists: Dict[str, List[Dict[str, Any]]] = {}
    counters: Dict[str, int] = {}
    for row in queued_rows:
        destination_options = build_destination_options(row, destination_lookup)
        if not destination_options:
            continue
        for option in destination_options:
            city_key = option["city"]
            counters[city_key] = counters.get(city_key, 0) + 1
            queue_group = row["queue_group"] or queue_group_for_carrier_code(row["carrier_code"])
            position_map.setdefault(row["id"], {})[city_key] = counters[city_key]
            city_lists.setdefault(city_key, []).append(
                {
                    "vehicleId": row["id"],
                    "plate": row["plate"],
                    "carrier": row["carrier"],
                    "carrierCode": row["carrier_code"],
                    "queueGroup": queue_group,
                    "queueGroupLabel": queue_group_label(queue_group),
                    "driverName": row["driver_name"],
                    "qualityStatus": row["quality_status"] or QUALITY_PENDING,
                    "turnPosition": counters[city_key],
                    "zone": option["zone"],
                }
            )
    return position_map, city_lists


def serialize_vehicle(
    row: sqlite3.Row,
    turn_positions: Dict[str, int],
    latest_inspections: Dict[str, Dict[str, Any]],
    destination_lookup: Dict[str, Dict[str, Any]],
    city_turn_map: Dict[str, Dict[str, int]],
    include_media: bool = True,
    inspection_summary_only: bool = False,
) -> Dict[str, Any]:
    latest_inspection = latest_inspections.get(row["id"])
    if inspection_summary_only:
        latest_inspection = summarize_inspection_for_vehicle(latest_inspection)
    created_local = iso_to_local(row["created_at"])
    reviewed_local = iso_to_local(latest_inspection["reviewedAt"]) if latest_inspection else None
    review_lead_minutes = None
    if created_local and reviewed_local:
        review_lead_minutes = max(int((reviewed_local - created_local).total_seconds() // 60), 0)
    return {
        "id": row["id"],
        "plate": row["plate"],
        "carrierId": row["carrier_id"],
        "carrierCode": row["carrier_code"],
        "carrier": row["carrier"],
        "centerId": row["center_id"],
        "centerCode": row["center_code"],
        "centerName": row["center_name"],
        "queueGroup": row["queue_group"] or queue_group_for_carrier_code(row["carrier_code"]),
        "queueGroupLabel": queue_group_label(row["queue_group"] or queue_group_for_carrier_code(row["carrier_code"])),
        "driverName": row["driver_name"],
        "driverId": row["driver_id"],
        "driverPhone": row["driver_phone"],
        "emptyWeightKg": row["empty_weight_kg"],
        "hasDriverSelfie": bool(row["driver_selfie_url"]),
        "hasDriverSignature": bool(row["driver_signature_url"]),
        "driverSelfieUrl": row["driver_selfie_url"] if include_media else None,
        "driverSignatureUrl": row["driver_signature_url"] if include_media else None,
        "destinationId": row["destination_id"],
        "destinationIds": parse_destination_ids(row),
        "destinationOptions": build_destination_options(row, destination_lookup),
        "city": row["city"],
        "zone": row["zone"],
        "cityTurns": city_turn_map.get(row["id"], {}),
        "status": row["status"],
        "qualityStatus": row["quality_status"] or QUALITY_PENDING,
        "turnPosition": turn_positions.get(row["id"]),
        "createdAt": row["created_at"],
        "assignedAt": row["assigned_at"],
        "rejectedAt": row["rejected_at"],
        "rejectionReason": row["rejection_reason"],
        "registrationChannel": row["registration_channel"] or "DESK",
        "gpsLat": row["gps_lat"],
        "gpsLng": row["gps_lng"],
        "gpsDistanceM": row["gps_distance_m"],
        "publicTrackingToken": row["public_tracking_token"],
        "lastQualityAt": row["last_quality_at"],
        "latestInspection": latest_inspection,
        "reviewLeadMinutes": review_lead_minutes,
    }


def serialize_authenticated_user(user: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "fullName": user["full_name"],
        "role": user["role"],
        "centerId": user["center_id"],
        "centerCode": user["center_code"],
        "centerName": user["center_name"],
    }


def sort_count_map(items: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"label": key, "count": value}
        for key, value in sorted(items.items(), key=lambda item: (-item[1], item[0]))
    ]


def build_analytics(rejected: List[Dict[str, Any]], inspections: List[Dict[str, Any]]) -> Dict[str, Any]:
    rejected_by_carrier: Dict[str, int] = {}
    reasons: Dict[str, int] = {}
    suitability_counts = {
        "Cadenas": 0,
        "Mayoristas": 0,
        "Bodegas y operadores": 0,
        "Subproductos": 0,
    }
    quality_decisions = {"Apto": 0, "Requiere arreglos": 0, "No apto / rechazado": 0}

    for vehicle in rejected:
        carrier = vehicle["carrier"] or "Sin transportadora"
        rejected_by_carrier[carrier] = rejected_by_carrier.get(carrier, 0) + 1
        reason = clean_text(vehicle["rejectionReason"]) or "No informado"
        reasons[reason] = reasons.get(reason, 0) + 1

    for inspection in inspections:
        decision = inspection["finalDecision"]
        decision_label = {
            QUALITY_APPROVED: "Apto",
            QUALITY_REWORK: "Requiere arreglos",
            QUALITY_REJECTED: "No apto / rechazado",
        }.get(decision, decision)
        quality_decisions[decision_label] = quality_decisions.get(decision_label, 0) + 1
        for item in inspection["suitability"]:
            if item in suitability_counts:
                suitability_counts[item] += 1

    return {
        "rejectedByCarrier": sort_count_map(rejected_by_carrier),
        "topRejectionReasons": sort_count_map(reasons),
        "suitabilityCounts": [{"label": key, "count": value} for key, value in suitability_counts.items()],
        "qualityDecisionCounts": [{"label": key, "count": value} for key, value in quality_decisions.items()],
    }


def build_history_rows(
    vehicles: List[Dict[str, Any]],
    inspections_by_vehicle: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    history: List[Dict[str, Any]] = []
    for vehicle in vehicles:
        inspections = inspections_by_vehicle.get(vehicle["id"], [])
        latest = inspections[0] if inspections else vehicle.get("latestInspection")
        created_local = iso_to_local(vehicle.get("createdAt"))
        reviewed_local = iso_to_local(latest.get("reviewedAt")) if latest else None
        lead_minutes = vehicle.get("reviewLeadMinutes")
        compact_inspections = [compact_inspection_for_history(item) for item in inspections]
        history.append(
            {
                "id": vehicle["id"],
                "plate": vehicle["plate"],
                "carrier": vehicle["carrier"],
                "carrierCode": vehicle["carrierCode"],
                "queueGroup": vehicle["queueGroup"],
                "queueGroupLabel": vehicle["queueGroupLabel"],
                "driverName": vehicle["driverName"],
                "driverId": vehicle["driverId"],
                "driverPhone": vehicle["driverPhone"],
                "emptyWeightKg": vehicle["emptyWeightKg"],
                "hasDriverSelfie": vehicle.get("hasDriverSelfie", False),
                "hasDriverSignature": vehicle.get("hasDriverSignature", False),
                "destinations": vehicle.get("destinationOptions", []),
                "cityTurns": vehicle.get("cityTurns", {}),
                "status": vehicle["status"],
                "qualityStatus": vehicle["qualityStatus"],
                "createdAt": vehicle["createdAt"],
                "createdDate": created_local.strftime("%Y-%m-%d") if created_local else "",
                "createdTime": created_local.strftime("%H:%M") if created_local else "",
                "assignedAt": vehicle["assignedAt"],
                "rejectedAt": vehicle["rejectedAt"],
                "rejectionReason": vehicle["rejectionReason"],
                "driverSelfieUrl": vehicle.get("driverSelfieUrl"),
                "driverSignatureUrl": vehicle.get("driverSignatureUrl"),
                "qualityReviewedAt": latest.get("reviewedAt") if latest else None,
                "qualityReviewedDate": reviewed_local.strftime("%Y-%m-%d") if reviewed_local else "",
                "qualityReviewedTime": reviewed_local.strftime("%H:%M") if reviewed_local else "",
                "qualityInspectorName": latest.get("inspectorName") if latest else "",
                "qualityDecision": latest.get("finalDecision") if latest else "",
                "qualityChecklist": latest.get("checklist") if latest else {},
                "qualityFindingsSummary": latest.get("findingsSummary") if latest else "",
                "qualityObservations": latest.get("observationsText") if latest else "",
                "reviewLeadMinutes": lead_minutes,
                "reviewLeadLabel": f"{lead_minutes} min" if isinstance(lead_minutes, int) else "",
                "inspectionHistory": compact_inspections,
            }
        )
    history.sort(key=lambda item: item["createdAt"], reverse=True)
    return history


def translate_checklist_status(status: str, poison: str = "") -> str:
    normalized = clean_text(status).upper()
    if normalized == "CUMPLE":
        return "Cumple"
    if normalized == "NO_CUMPLE":
        return "No cumple"
    if normalized == "NO_APLICA":
        return "No aplica"
    if normalized == "SI":
        return f"Sí ({poison})" if poison else "Sí"
    if normalized == "NO":
        return "No"
    return "Pendiente"


def truncate_text(value: Any, limit: int) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return f"{text[: max(limit - 3, 0)]}..."


def draw_fit_text(pdf: Any, text: str, x: float, y: float, max_width: float, font_name: str = "Helvetica", font_size: float = 8) -> None:
    content = clean_text(text)
    if not content:
        return
    size = font_size
    while size >= 5:
        pdf.setFont(font_name, size)
        if pdf.stringWidth(content, font_name, size) <= max_width:
            pdf.drawString(x, y, content)
            return
        size -= 0.4
    pdf.setFont(font_name, 5)
    clipped = content
    while clipped and pdf.stringWidth(f"{clipped}...", font_name, 5) > max_width:
        clipped = clipped[:-1]
    pdf.drawString(x, y, f"{clipped}..." if clipped else "")


def draw_center_mark(pdf: Any, mark: str, x: float, y: float, font_name: str = "Helvetica-Bold", font_size: float = 9) -> None:
    pdf.setFont(font_name, font_size)
    width = pdf.stringWidth(mark, font_name, font_size)
    pdf.drawString(x - (width / 2), y, mark)


def _escape_pdf_text(value: Any) -> str:
    return html.escape(clean_text(value or "-"))


def _history_check_short(checklist: Dict[str, Any], key: str) -> str:
    item = checklist.get(key) or {}
    status = clean_text(item.get("status")).upper()
    return {
        "CUMPLE": "C",
        "NO_CUMPLE": "NC",
        "NO_APLICA": "NA",
        "SI": "SI",
        "NO": "NO",
    }.get(status, "-")


def _history_decision_marks(record: Dict[str, Any]) -> Tuple[str, str]:
    decision = clean_text(record.get("qualityDecision") or record.get("qualityStatus")).upper()
    if decision == QUALITY_APPROVED:
        return "X", ""
    if decision in {QUALITY_REJECTED, QUALITY_REWORK}:
        return "", "X"
    return "", ""


def build_history_pdf(records: List[Dict[str, Any]]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, legal
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception as exc:
        raise AppError(f"No se pudo cargar el generador PDF: {exc}", 500) from exc

    output = io.BytesIO()
    page_width, page_height = landscape(legal)
    margin = 8 * mm
    doc = SimpleDocTemplate(
        output,
        pagesize=(page_width, page_height),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=7 * mm,
        bottomMargin=7 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PdfTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=12, alignment=1)
    subtitle_style = ParagraphStyle("PdfSubtitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=9.4, alignment=1)
    cell_style = ParagraphStyle("PdfCell", parent=styles["Normal"], fontName="Helvetica", fontSize=5.1, leading=5.8, alignment=1)
    cell_left_style = ParagraphStyle("PdfCellLeft", parent=cell_style, alignment=0)
    header_cell_style = ParagraphStyle("PdfHeader", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=5.4, leading=6, alignment=1)
    section_style = ParagraphStyle("PdfSection", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.4, leading=8.4)
    note_style = ParagraphStyle("PdfNote", parent=styles["Normal"], fontName="Helvetica", fontSize=6.1, leading=7)

    def p(value: Any, style: ParagraphStyle) -> Paragraph:
        return Paragraph(_escape_pdf_text(value), style)

    def build_header() -> Table:
        logo_flowable: Any = ""
        if PDF_LOGO_PATH.exists():
            logo_flowable = Image(str(PDF_LOGO_PATH), width=30 * mm, height=12 * mm, kind="proportional")
        center_width = page_width - (margin * 2) - (38 * mm) - (24 * mm)
        title_block = Table(
            [
                [Paragraph("DIANA CORPORACIÓN S.A.S", title_style)],
                [Paragraph("ASEGURAR CALIDAD DEL PRODUCTO", subtitle_style)],
                [Paragraph("INSPECCIÓN, DESINFECCIÓN Y FUMIGACIÓN DE VEHÍCULOS", subtitle_style)],
            ],
            colWidths=[center_width],
        )
        title_block.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.55, colors.black)]))
        right_box = Table(
            [[Paragraph("FO-CL-021", subtitle_style)], [Paragraph("V.7 Octubre 2024", note_style)]],
            colWidths=[24 * mm],
        )
        right_box.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.55, colors.black)]))
        header = Table([[logo_flowable, title_block, right_box]], colWidths=[38 * mm, center_width, 24 * mm])
        header.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.65, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return header

    for index, record in enumerate(records, start=1):
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        destinations_text = ", ".join(
            [
                f"{item.get('city', '')} - {item.get('zone', '')}".strip(" -")
                for item in record.get("destinations", [])
                if item.get("city") or item.get("zone")
            ]
        ) or "-"
        carrier_text = f"{record.get('carrierCode') or ''} {record.get('carrier') or '-'}".strip()
        checklist = record.get("qualityChecklist") or {}
        row_y = 307
        date_y = 352
        field_font = 7.4

        # Campos superiores
        draw_fit_text(pdf, record.get("qualityReviewedDate") or record.get("createdDate") or "-", 36, date_y, 120, font_size=9)
        draw_fit_text(pdf, record.get("qualityReviewedTime") or record.get("createdTime") or "-", 8, row_y, 28, font_size=7)
        draw_fit_text(pdf, record.get("driverName") or "-", 44, row_y, 54, font_size=6.5)
        draw_fit_text(pdf, record.get("plate") or "-", 104, row_y, 44, font_size=7.5)
        draw_fit_text(pdf, destinations_text, 154, row_y, 54, font_size=6.4)

        # Columnas del checklist
        column_map = {
            "foodLegend": 226,
            "cleanliness": 266,
            "strangeSmells": 306,
            "stains": 346,
            "damage": 386,
            "humidity": 426,
            "infestation": 471,
            "bulkWallsFloor": 518,
            "containerHoles": 563,
            "fumigationIn": 603,
            "fumigationOut": 638,
        }
        for key, center_x in column_map.items():
            item = checklist.get(key) or {}
            status = clean_text(item.get("status")).upper()
            if status == "CUMPLE":
                draw_center_mark(pdf, "C", center_x, row_y, font_size=8)
            elif status == "NO_CUMPLE":
                draw_center_mark(pdf, "NC", center_x, row_y, font_size=7)
            elif status == "NO_APLICA":
                draw_center_mark(pdf, "NA", center_x, row_y, font_size=7)
            elif status == "SI":
                draw_center_mark(pdf, "SI", center_x, row_y, font_size=7)
            elif status == "NO":
                draw_center_mark(pdf, "NO", center_x, row_y, font_size=7)

        decision = clean_text(record.get("qualityDecision") or record.get("qualityStatus")).upper()
        if decision == QUALITY_APPROVED:
            draw_center_mark(pdf, "X", 673, row_y, font_size=10)
        else:
            draw_center_mark(pdf, "X", 708, row_y, font_size=10)

        observations = clean_text(record.get("qualityObservations") or record.get("qualityFindingsSummary") or record.get("rejectionReason") or "")
        draw_fit_text(pdf, observations, 732, row_y + 8, 72, font_size=5.8)
        draw_fit_text(pdf, record.get("qualityInspectorName") or "-", 809, row_y + 8, 28, font_size=5.6)

        # Bloque inferior de decisiones
        bottom_y = 92
        decision_label = {
            QUALITY_APPROVED: "ACEPTADO",
            QUALITY_REWORK: "REQUIERE ARREGLOS",
            QUALITY_REJECTED: "RECHAZADO",
            "PENDING": "PENDIENTE",
        }.get(decision or "PENDING", decision or "PENDIENTE")
        draw_fit_text(pdf, decision_label, 18, bottom_y + 16, 120, font_name="Helvetica-Bold", font_size=8)
        draw_fit_text(pdf, observations or "-", 170, bottom_y + 16, 300, font_size=7)
        draw_fit_text(pdf, record.get("qualityInspectorName") or "-", 490, bottom_y + 16, 190, font_size=7)

        # Producto de fumigación
        fumigation_values = []
        for key in ("fumigationIn", "fumigationOut"):
            poison = clean_text((checklist.get(key) or {}).get("poison"))
            if poison:
                fumigation_values.append(poison)
        product_text = ", ".join(dict.fromkeys(fumigation_values)) or "-"
        draw_fit_text(pdf, product_text, 18, 38, 180, font_size=7)
        draw_fit_text(pdf, "-", 210, 38, 88, font_size=7)
        draw_fit_text(pdf, "-", 312, 38, 134, font_size=7)
        draw_fit_text(pdf, "-", 462, 38, 92, font_size=7)

        # Responsable de verificación y leyenda
        draw_fit_text(pdf, record.get("qualityInspectorName") or "-", 120, 2, 200, font_size=8)
        draw_fit_text(pdf, f"Registro {index} de {len(records)}", 640, 2, 120, font_size=7)
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        overlay_reader = PdfReader(buffer)
        overlay_page = overlay_reader.pages[0]
        if template_page is not None:
            page = template_page.clone(writer)
            page.merge_page(overlay_page)
            writer.add_page(page)
        else:
            writer.add_page(overlay_page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def build_history_pdf(records: List[Dict[str, Any]]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, legal
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception as exc:
        raise AppError(f"No se pudo cargar el generador PDF: {exc}", 500) from exc

    output = io.BytesIO()
    page_width, page_height = landscape(legal)
    margin = 8 * mm
    doc = SimpleDocTemplate(
        output,
        pagesize=(page_width, page_height),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=7 * mm,
        bottomMargin=7 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PdfTitleModern", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10.5, leading=12, alignment=1)
    subtitle_style = ParagraphStyle("PdfSubtitleModern", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=9.4, alignment=1)
    cell_style = ParagraphStyle("PdfCellModern", parent=styles["Normal"], fontName="Helvetica", fontSize=4.9, leading=5.5, alignment=1)
    cell_left_style = ParagraphStyle("PdfCellLeftModern", parent=cell_style, alignment=0)
    header_cell_style = ParagraphStyle("PdfHeaderModern", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=4.4, leading=5, alignment=1)
    section_style = ParagraphStyle("PdfSectionModern", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.4, leading=8.4)
    note_style = ParagraphStyle("PdfNoteModern", parent=styles["Normal"], fontName="Helvetica", fontSize=6.1, leading=7)

    def p(value: Any, style: ParagraphStyle) -> Paragraph:
        return Paragraph(_escape_pdf_text(value), style)

    def build_header() -> Table:
        logo_flowable: Any = ""
        if PDF_LOGO_PATH.exists():
            logo_flowable = Image(str(PDF_LOGO_PATH), width=30 * mm, height=12 * mm, kind="proportional")
        center_width = page_width - (margin * 2) - (38 * mm) - (24 * mm)
        title_block = Table(
            [
                [Paragraph("DIANA CORPORACIÓN S.A.S", title_style)],
                [Paragraph("ASEGURAR CALIDAD DEL PRODUCTO", subtitle_style)],
                [Paragraph("INSPECCIÓN, DESINFECCIÓN Y FUMIGACIÓN DE VEHÍCULOS", subtitle_style)],
            ],
            colWidths=[center_width],
        )
        title_block.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.55, colors.black)]))
        right_box = Table(
            [[Paragraph("FO-CL-021", subtitle_style)], [Paragraph("V.7 Octubre 2024", note_style)]],
            colWidths=[24 * mm],
        )
        right_box.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.55, colors.black)]))
        header = Table([[logo_flowable, title_block, right_box]], colWidths=[38 * mm, center_width, 24 * mm])
        header.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.65, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return header

    rows: List[List[Any]] = [[
        p("Hora", header_cell_style),
        p("Conductor", header_cell_style),
        p("Placas", header_cell_style),
        p("Destino", header_cell_style),
        p('Cuenta con leyenda visible "Transporte de alimentos"', header_cell_style),
        p("Libre de suciedad", header_cell_style),
        p("Libre de olores extraños", header_cell_style),
        p("Libre de manchas", header_cell_style),
        p("Libre de orificios y averías", header_cell_style),
        p("Libre de humedad", header_cell_style),
        p("Libre de infestación (plagas, roedores y/o contaminación biológica)", header_cell_style),
        p("Granel en paredes y piso limpio y en buen estado", header_cell_style),
        p("Trompos (agujeros de ensamble del contenedor) limpios y con la debida protección de parche", header_cell_style),
        p("Estacas de madera del vehículo libres de plagas (paredes y pisos)", header_cell_style),
        p("Fumigación ingreso", header_cell_style),
        p("Fumigación salida", header_cell_style),
        p("Aceptado", header_cell_style),
        p("Rech./Arr.", header_cell_style),
        p("Medida correctiva", header_cell_style),
        p("Responsable de la inspección", header_cell_style),
    ]]
    fumigation_rows: List[List[Any]] = [[
        p("Producto aplicado", header_cell_style),
        p("Lote", header_cell_style),
        p("Fecha de vencimiento", header_cell_style),
        p("Dosis (ml o g)", header_cell_style),
        p("Nombre responsable", header_cell_style),
    ]]

    for record in records:
        checklist = record.get("qualityChecklist") or {}
        destinations_text = ", ".join(
            f"{item.get('city', '')} - {item.get('zone', '')}".strip(" -")
            for item in record.get("destinations", [])
            if item.get("city") or item.get("zone")
        ) or "-"
        reviewed_local = iso_to_local(record.get("qualityReviewedAt") or record.get("createdAt"))
        accepted_mark, rejected_mark = _history_decision_marks(record)
        observations = clean_text(record.get("qualityObservations") or record.get("qualityFindingsSummary") or record.get("rejectionReason") or "-")
        rows.append([
            p(reviewed_local.strftime("%H:%M") if reviewed_local else "-", cell_style),
            p(record.get("driverName"), cell_left_style),
            p(record.get("plate"), cell_style),
            p(destinations_text, cell_left_style),
            p(_history_check_short(checklist, "foodLegend"), cell_style),
            p(_history_check_short(checklist, "cleanliness"), cell_style),
            p(_history_check_short(checklist, "strangeSmells"), cell_style),
            p(_history_check_short(checklist, "stains"), cell_style),
            p(_history_check_short(checklist, "damage"), cell_style),
            p(_history_check_short(checklist, "humidity"), cell_style),
            p(_history_check_short(checklist, "infestation"), cell_style),
            p(_history_check_short(checklist, "bulkWallsFloor"), cell_style),
            p(_history_check_short(checklist, "containerHoles"), cell_style),
            p(_history_check_short(checklist, "woodenStakesPestFree"), cell_style),
            p(_history_check_short(checklist, "fumigationIn"), cell_style),
            p(_history_check_short(checklist, "fumigationOut"), cell_style),
            p(accepted_mark or "-", cell_style),
            p(rejected_mark or "-", cell_style),
            p(observations, cell_left_style),
            p(record.get("qualityInspectorName"), cell_left_style),
        ])
    fumigation_rows.append([p("", cell_left_style), p("", cell_style), p("", cell_style), p("", cell_style), p("", cell_left_style)])

    col_widths_mm = [11, 22, 14, 18, 12, 10, 10, 10, 10, 10, 15, 14, 15, 14, 10, 10, 10, 11, 24, 18]
    raw_widths = [item * mm for item in col_widths_mm]
    scaled_widths = [value * ((page_width - (margin * 2)) / sum(raw_widths)) for value in raw_widths]
    main_table = Table(rows, colWidths=scaled_widths, repeatRows=1)
    main_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3fb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.6),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    fumigation_table = Table(fumigation_rows, colWidths=[65 * mm, 35 * mm, 42 * mm, 32 * mm, 50 * mm], repeatRows=1)
    fumigation_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f7fb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
    ]))
    story: List[Any] = [
        build_header(),
        Spacer(1, 2.5 * mm),
        Paragraph(f"Fecha de impresión: {now_local().strftime('%Y-%m-%d %H:%M')} · Registros: {len(records)}", note_style),
        Spacer(1, 2 * mm),
        main_table,
        Spacer(1, 3 * mm),
        Paragraph("INFORMACIÓN DEL PRODUCTO UTILIZADO PARA FUMIGACIÓN", section_style),
        Spacer(1, 1.2 * mm),
        fumigation_table,
        Spacer(1, 2 * mm),
        Paragraph("C: Cumple · NC: No cumple · NA: No aplica · Rech./Arr.: rechazado o requiere arreglos", note_style),
    ]
    doc.build(story)
    return output.getvalue()


def build_history_pdf(records: List[Dict[str, Any]]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch, mm
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception as exc:
        raise AppError(f"No se pudo cargar el generador PDF: {exc}", 500) from exc

    output = io.BytesIO()
    page_width, page_height = landscape((17 * inch, 11 * inch))
    margin = 7 * mm
    doc = SimpleDocTemplate(
        output,
        pagesize=(page_width, page_height),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=6 * mm,
        bottomMargin=6 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PdfTitleStrong", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=14, leading=15.5, alignment=1)
    subtitle_style = ParagraphStyle("PdfSubtitleStrong", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.7, leading=9.6, alignment=1)
    note_style = ParagraphStyle("PdfNoteStrong", parent=styles["Normal"], fontName="Helvetica", fontSize=6.6, leading=7.4, alignment=0)
    header_cell_style = ParagraphStyle("PdfHeaderCellStrong", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=5.2, leading=5.8, alignment=1)
    cell_style = ParagraphStyle("PdfCellStrong", parent=styles["Normal"], fontName="Helvetica", fontSize=5.35, leading=6.1, alignment=1)
    cell_left_style = ParagraphStyle("PdfCellLeftStrong", parent=cell_style, alignment=0)
    section_style = ParagraphStyle("PdfSectionStrong", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.2, leading=9, alignment=0)

    def p(value: Any, style: ParagraphStyle) -> Paragraph:
        return Paragraph(_escape_pdf_text(value), style)

    def build_header() -> Table:
        logo_flowable: Any = ""
        if PDF_LOGO_PATH.exists():
            logo_flowable = Image(str(PDF_LOGO_PATH), width=34 * mm, height=14 * mm, kind="proportional")
        center_width = page_width - (margin * 2) - (40 * mm) - (28 * mm)
        title_block = Table(
            [
                [Paragraph("DIANA CORPORACION S.A.S", title_style)],
                [Paragraph("ASEGURAR CALIDAD DEL PRODUCTO", subtitle_style)],
                [Paragraph("INSPECCION, DESINFECCION Y FUMIGACION DE VEHICULOS", subtitle_style)],
            ],
            colWidths=[center_width],
        )
        title_block.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, colors.black)]))
        right_box = Table(
            [[Paragraph("FO-CL-021", subtitle_style)], [Paragraph("V.7 Octubre de 2024", note_style)]],
            colWidths=[28 * mm],
        )
        right_box.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, colors.black)]))
        header = Table([[logo_flowable, title_block, right_box]], colWidths=[40 * mm, center_width, 28 * mm])
        header.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.7, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return header

    def build_destination_text(items: List[Dict[str, Any]]) -> str:
        labels: List[str] = []
        for item in items:
            city = clean_text(item.get("city"))
            zone = clean_text(item.get("zone"))
            label = " - ".join(part for part in [city, zone] if part)
            if label:
                labels.append(label)
        return "<br/>".join(labels) if labels else "-"

    def build_observation_text(record: Dict[str, Any]) -> str:
        raw = clean_text(record.get("qualityObservations") or record.get("qualityFindingsSummary") or record.get("rejectionReason") or "-")
        if raw == "-":
            return raw
        return raw.replace(". ", ".<br/>")

    def build_sort_key(record: Dict[str, Any]) -> datetime:
        local_value = iso_to_local(record.get("qualityReviewedAt") or record.get("createdAt"))
        return local_value or datetime(2000, 1, 1, tzinfo=LOCAL_TIMEZONE)

    ordered_records = sorted(records, key=build_sort_key)

    rows: List[List[Any]] = [[
        p("Hora", header_cell_style),
        p("Conductor", header_cell_style),
        p("Placa", header_cell_style),
        p("Destino", header_cell_style),
        p('Cuenta con leyenda visible<br/>"Transporte de alimentos"', header_cell_style),
        p("Libre de<br/>suciedad", header_cell_style),
        p("Libre de olores<br/>extranos", header_cell_style),
        p("Libre de<br/>manchas", header_cell_style),
        p("Libre de orificios<br/>y averias", header_cell_style),
        p("Libre de<br/>humedad", header_cell_style),
        p("Libre de infestacion<br/>(plagas, roedores y/o<br/>contaminacion biologica)", header_cell_style),
        p("Granel en paredes y piso<br/>limpio y en buen estado", header_cell_style),
        p("Trompos (agujeros de ensamble del contenedor)<br/>limpios y con la debida proteccion de parche", header_cell_style),
        p("Estacas de madera del vehiculo<br/>libres de plagas (paredes y pisos)", header_cell_style),
        p("Fumigacion<br/>ING", header_cell_style),
        p("Fumigacion<br/>SAL", header_cell_style),
        p("Aceptado", header_cell_style),
        p("Rech./Arr.", header_cell_style),
        p("Medida correctiva", header_cell_style),
        p("Responsable de la inspeccion", header_cell_style),
    ]]
    fumigation_rows: List[List[Any]] = [[
        p("PRODUCTO APLICADO", header_cell_style),
        p("LOTE", header_cell_style),
        p("FECHA DE VENCIMIENTO", header_cell_style),
        p("DOSIS (ml o g)", header_cell_style),
        p("NOMBRE DE RESPONSABLE", header_cell_style),
    ]]

    for record in ordered_records:
        checklist = record.get("qualityChecklist") or {}
        reviewed_local = iso_to_local(record.get("qualityReviewedAt") or record.get("createdAt"))
        accepted_mark, rejected_mark = _history_decision_marks(record)
        rows.append([
            p(reviewed_local.strftime("%H:%M") if reviewed_local else "-", cell_style),
            p(record.get("driverName") or "-", cell_left_style),
            p(record.get("plate") or "-", cell_style),
            p(build_destination_text(record.get("destinations", [])), cell_left_style),
            p(_history_check_short(checklist, "foodLegend"), cell_style),
            p(_history_check_short(checklist, "cleanliness"), cell_style),
            p(_history_check_short(checklist, "strangeSmells"), cell_style),
            p(_history_check_short(checklist, "stains"), cell_style),
            p(_history_check_short(checklist, "damage"), cell_style),
            p(_history_check_short(checklist, "humidity"), cell_style),
            p(_history_check_short(checklist, "infestation"), cell_style),
            p(_history_check_short(checklist, "bulkWallsFloor"), cell_style),
            p(_history_check_short(checklist, "containerHoles"), cell_style),
            p(_history_check_short(checklist, "woodenStakesPestFree"), cell_style),
            p(_history_check_short(checklist, "fumigationIn"), cell_style),
            p(_history_check_short(checklist, "fumigationOut"), cell_style),
            p(accepted_mark or "-", cell_style),
            p(rejected_mark or "-", cell_style),
            p(build_observation_text(record), cell_left_style),
            p(record.get("qualityInspectorName") or "-", cell_left_style),
        ])
    fumigation_rows.append([p("", cell_left_style), p("", cell_style), p("", cell_style), p("", cell_style), p("", cell_left_style)])

    col_widths_mm = [11, 30, 16, 29, 24, 13, 16, 13, 18, 14, 23, 20, 25, 23, 12, 12, 12, 13, 26, 23]
    raw_widths = [item * mm for item in col_widths_mm]
    available_width = page_width - (margin * 2)
    scaled_widths = [value * (available_width / sum(raw_widths)) for value in raw_widths]
    main_table = Table(rows, colWidths=scaled_widths, repeatRows=1)
    main_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.42, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3fb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fbff")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.6),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))

    fumigation_table = Table(fumigation_rows, colWidths=[72 * mm, 38 * mm, 48 * mm, 38 * mm, 62 * mm], repeatRows=1)
    fumigation_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.42, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f7fb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    story: List[Any] = [
        build_header(),
        Spacer(1, 2.4 * mm),
        Paragraph(f"Fecha de impresion: {now_local().strftime('%Y-%m-%d %H:%M')} | Registros incluidos: {len(ordered_records)}", note_style),
        Spacer(1, 2 * mm),
        main_table,
        Spacer(1, 3 * mm),
        Paragraph("INFORMACION DEL PRODUCTO UTILIZADO PARA LA FUMIGACION", section_style),
        Spacer(1, 1.3 * mm),
        fumigation_table,
        Spacer(1, 2 * mm),
        Paragraph("C: Cumple | NC: No cumple | NA: No aplica | Rech./Arr.: rechazado o requiere arreglos", note_style),
    ]
    doc.build(story)
    return output.getvalue()


def get_user_state(user: sqlite3.Row, origin: str) -> Dict[str, Any]:
    with get_connection() as db:
        centers = load_centers(db)
        center_lookup = build_center_lookup(centers)
        visible_center_ids = visible_center_ids_for_user(user, centers)
        preferred_center = preferred_center_for_user(user, centers)
        destinations = [
            serialize_destination(row)
            for row in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
        ]
        destination_lookup = build_destination_lookup(destinations)
        carriers = [
            serialize_carrier(row)
            for row in db.execute("SELECT * FROM carriers ORDER BY name").fetchall()
        ]
        placeholders = ",".join("?" for _ in visible_center_ids)
        vehicles = db.execute(
            f"SELECT * FROM vehicles WHERE center_id IN ({placeholders}) ORDER BY CASE status WHEN 'QUEUED' THEN 0 WHEN 'ASSIGNED' THEN 1 ELSE 2 END, queue_position, created_at DESC",
            visible_center_ids,
        ).fetchall()
        queued_rows = [row for row in vehicles if row["status"] == QUEUE_STATUS_ACTIVE]
        turn_positions = calculate_turn_positions(queued_rows)
        city_turn_map, city_queue_lists = build_city_turn_maps(queued_rows, destination_lookup)
        latest_inspections = load_latest_inspections(db, include_media=False)
        inspections_by_vehicle = load_inspections_by_vehicle(db, include_media=False)

        queued = [
            serialize_vehicle(row, turn_positions, latest_inspections, destination_lookup, city_turn_map, include_media=False, inspection_summary_only=True)
            for row in queued_rows
        ]
        assigned = [
            serialize_vehicle(row, turn_positions, latest_inspections, destination_lookup, city_turn_map, include_media=False, inspection_summary_only=True)
            for row in vehicles
            if row["status"] == QUEUE_STATUS_ASSIGNED
        ]
        rejected = [
            serialize_vehicle(row, turn_positions, latest_inspections, destination_lookup, city_turn_map, include_media=False, inspection_summary_only=True)
            for row in vehicles
            if row["status"] == QUEUE_STATUS_REJECTED
        ]

        users = [
            {
                "id": row["id"],
                "username": row["username"],
                "fullName": row["full_name"],
                "role": row["role"],
                "active": bool(row["active"]),
                "centerId": row["center_id"],
                "centerCode": row["center_code"],
                "centerName": row["center_name"],
            }
            for row in db.execute("SELECT * FROM users ORDER BY role, full_name").fetchall()
        ]
        inspection_rows = db.execute(
            "SELECT * FROM quality_inspections ORDER BY reviewed_at DESC, created_at DESC"
        ).fetchall()
        visible_vehicle_ids = {vehicle["id"] for vehicle in queued + assigned + rejected}
        inspections = [serialize_inspection(row, include_media=False) for row in inspection_rows if row["vehicle_id"] in visible_vehicle_ids]

    quality_pending = [vehicle for vehicle in queued if vehicle["qualityStatus"] in {QUALITY_PENDING, QUALITY_IN_PROGRESS}]
    today_local = now_local()
    approved_today = [
        item for item in inspections
        if item["finalDecision"] == QUALITY_APPROVED and is_same_local_day(item["reviewedAt"], today_local)
    ]
    rejected_today = [
        item for item in inspections
        if item["finalDecision"] == QUALITY_REJECTED and is_same_local_day(item["reviewedAt"], today_local)
    ]
    history_rows = build_history_rows(queued + assigned + rejected, inspections_by_vehicle)
    site_config = {
        "siteName": preferred_center["name"],
        "siteLat": preferred_center["siteLat"],
        "siteLng": preferred_center["siteLng"],
        "siteRadiusM": preferred_center["siteRadiusM"],
        "geofenceEnabled": preferred_center["geofenceEnabled"],
        "centerId": preferred_center["id"],
        "centerCode": preferred_center["code"],
    }
    registration_url = f"{origin}/driver.html?center={preferred_center['id']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&data={registration_url}"

    return {
        "user": serialize_authenticated_user(user),
        "centers": centers,
        "destinations": destinations,
        "carriers": carriers,
        "queued": queued,
        "cityQueues": [
            {"city": city, "vehicles": rows}
            for city, rows in sorted(city_queue_lists.items(), key=lambda item: item[0])
        ],
        "assigned": assigned,
        "rejected": rejected,
        "history": [],
        "quality": {
            "dailyApprovedCount": len(approved_today),
            "dailyRejectedCount": len(rejected_today),
            "pendingCount": len(quality_pending),
        },
        "users": users if user["role"] == ROLE_ADMIN else [],
        "settings": site_config,
        "analytics": {
            **build_analytics(rejected, inspections),
            "dailyApprovedCount": len(approved_today),
            "dailyRejectedCount": len(rejected_today),
            "queuedCount": len(queued),
            "qualityPendingCount": len(quality_pending),
        },
        "permissions": {
            "isAdmin": user["role"] == ROLE_ADMIN,
            "canManageCatalogs": can_add_catalogs(user),
            "canAddCatalogs": can_add_catalogs(user),
            "canEditCatalogs": user["role"] == ROLE_ADMIN,
            "canDeleteCatalogs": user["role"] == ROLE_ADMIN,
            "canManageUsers": user["role"] == ROLE_ADMIN,
            "canViewCatalogs": user["role"] in {ROLE_ADMIN, ROLE_VIEWER} or can_add_catalogs(user),
            "canViewUsers": user["role"] in {ROLE_ADMIN, ROLE_VIEWER},
            "canConfigureSite": user["role"] == ROLE_ADMIN,
            "canOperateLogistics": user["role"] in {ROLE_ADMIN, ROLE_LOGISTICS},
            "canOperateQuality": user["role"] in {ROLE_ADMIN, ROLE_QUALITY},
            "canViewDashboard": user["role"] in {ROLE_ADMIN, ROLE_LOGISTICS, ROLE_VIEWER},
        },
        "publicRegistrationUrl": registration_url,
        "publicQrUrl": qr_url,
    }


def get_history_rows_for_user(user: sqlite3.Row) -> List[Dict[str, Any]]:
    with get_connection() as db:
        centers = load_centers(db)
        visible_center_ids = visible_center_ids_for_user(user, centers)
        destination_lookup = build_destination_lookup(
            [
                serialize_destination(row)
                for row in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
            ]
        )
        placeholders = ",".join("?" for _ in visible_center_ids)
        vehicles = db.execute(
            f"SELECT * FROM vehicles WHERE center_id IN ({placeholders}) ORDER BY CASE status WHEN 'QUEUED' THEN 0 WHEN 'ASSIGNED' THEN 1 ELSE 2 END, queue_position, created_at DESC",
            visible_center_ids,
        ).fetchall()
        queued_rows = [row for row in vehicles if row["status"] == QUEUE_STATUS_ACTIVE]
        turn_positions = calculate_turn_positions(queued_rows)
        city_turn_map, _city_queue_lists = build_city_turn_maps(queued_rows, destination_lookup)
        latest_inspections = load_latest_inspections(db, include_media=False)
        inspections_by_vehicle = load_inspections_by_vehicle(db, include_media=False)
        serialized = [
            serialize_vehicle(row, turn_positions, latest_inspections, destination_lookup, city_turn_map, include_media=False, inspection_summary_only=True)
            for row in vehicles
        ]
    return build_history_rows(serialized, inspections_by_vehicle)


def build_public_city_turn_counts(city_queue_lists: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for city, vehicles in sorted(city_queue_lists.items(), key=lambda item: item[0]):
        counts = {
            QUEUE_GROUP_GENERAL: 0,
            QUEUE_GROUP_DIANA: 0,
        }
        for vehicle in vehicles:
            queue_group = vehicle.get("queueGroup") or QUEUE_GROUP_GENERAL
            counts[queue_group] = counts.get(queue_group, 0) + 1
        rows.append({
            "city": city,
            "counts": counts,
        })
    return rows


def get_vehicle_detail_for_user(user: sqlite3.Row, vehicle_id: str) -> Dict[str, Any]:
    with get_connection() as db:
        centers = load_centers(db)
        visible_center_ids = set(visible_center_ids_for_user(user, centers))
        row = db.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        if not row:
            raise AppError("No se encontró el vehículo solicitado.", 404)
        if clean_text(row["center_id"]) not in visible_center_ids:
            raise AppError("No tienes permiso para ver ese vehículo.", 403)
        destinations = [
            serialize_destination(item)
            for item in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
        ]
        destination_lookup = build_destination_lookup(destinations)
        queued_rows = db.execute(
            "SELECT * FROM vehicles WHERE status = 'QUEUED' AND center_id = ? ORDER BY queue_position, created_at",
            (row["center_id"],),
        ).fetchall()
        turn_positions = calculate_turn_positions(queued_rows)
        city_turn_map, _city_queue_lists = build_city_turn_maps(queued_rows, destination_lookup)
        latest_inspections = load_latest_inspections(db, include_media=True)
        inspections_by_vehicle = load_inspections_by_vehicle(db, include_media=True)
        vehicle = serialize_vehicle(row, turn_positions, latest_inspections, destination_lookup, city_turn_map, include_media=True, inspection_summary_only=False)
        vehicle["inspectionHistory"] = inspections_by_vehicle.get(vehicle_id, [])
        return vehicle


def build_mobile_quality_state(user: sqlite3.Row) -> Dict[str, Any]:
    with get_connection() as db:
        centers = load_centers(db)
        visible_center_ids = visible_center_ids_for_user(user, centers)
        placeholders = ",".join("?" for _ in visible_center_ids)
        destinations = [
            serialize_destination(row)
            for row in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
        ]
        destination_lookup = build_destination_lookup(destinations)
        queued_rows = db.execute(
            f"SELECT * FROM vehicles WHERE center_id IN ({placeholders}) AND status = 'QUEUED' ORDER BY queue_position, created_at",
            visible_center_ids,
        ).fetchall()
        rejected_rows = db.execute(
            f"SELECT * FROM vehicles WHERE center_id IN ({placeholders}) AND status = 'REJECTED' ORDER BY rejected_at DESC, created_at DESC",
            visible_center_ids,
        ).fetchall()
        latest_inspections = load_latest_inspections(db, include_media=False)

    turn_positions = calculate_turn_positions(queued_rows)
    city_turn_map, _city_queue_lists = build_city_turn_maps(queued_rows, destination_lookup)
    queued = [
        serialize_vehicle(
            row,
            turn_positions,
            latest_inspections,
            destination_lookup,
            city_turn_map,
            include_media=False,
        )
        for row in queued_rows
    ]
    rejected = [
        serialize_vehicle(
            row,
            turn_positions,
            latest_inspections,
            destination_lookup,
            city_turn_map,
            include_media=False,
        )
        for row in rejected_rows
    ]
    quality_pending = [vehicle for vehicle in queued if vehicle["qualityStatus"] in {QUALITY_PENDING, QUALITY_IN_PROGRESS}]
    quality_rework = [vehicle for vehicle in queued if vehicle["qualityStatus"] == QUALITY_REWORK]
    quality_approved = [vehicle for vehicle in queued if vehicle["qualityStatus"] == QUALITY_APPROVED]
    quality_rejected = [vehicle for vehicle in rejected if vehicle["qualityStatus"] == QUALITY_REJECTED]
    today_local = now_local()
    approved_today = [
        item for item in quality_approved
        if item.get("latestInspection") and is_same_local_day(item["latestInspection"].get("reviewedAt"), today_local)
    ]
    rejected_today = [
        item for item in quality_rejected
        if item.get("latestInspection") and is_same_local_day(item["latestInspection"].get("reviewedAt"), today_local)
    ]
    return {
        "user": serialize_authenticated_user(user),
        "quality": {
            "pending": quality_pending,
            "rework": quality_rework,
            "approved": quality_approved,
            "rejected": quality_rejected,
            "inspections": [],
            "dailyApprovedCount": len(approved_today),
            "dailyRejectedCount": len(rejected_today),
        },
    }


def compact_queue(db: sqlite3.Connection) -> None:
    for queue_group in (QUEUE_GROUP_GENERAL, QUEUE_GROUP_DIANA):
        queued = db.execute(
            """
            SELECT id FROM vehicles
            WHERE status = 'QUEUED' AND COALESCE(queue_group, ?) = ?
            ORDER BY queue_position, created_at
            """,
            (QUEUE_GROUP_GENERAL, queue_group),
        ).fetchall()
        for index, row in enumerate(queued, start=1):
            db.execute("UPDATE vehicles SET queue_position = ? WHERE id = ?", (index, row["id"]))


def find_plate_registration_block(db: Any, plate: str, center_id: str) -> Optional[str]:
    rows = db.execute(
        """
        SELECT plate, status, quality_status, assigned_at, created_at
        FROM vehicles
        WHERE center_id = ? AND status IN ('QUEUED', 'ASSIGNED')
        ORDER BY created_at DESC
        """,
        (center_id,),
    ).fetchall()
    normalized_plate = normalize_plate(plate)
    today_local = now_local().date()
    for row in rows:
        if normalize_plate(row["plate"]) != normalized_plate:
            continue
        if row["status"] == QUEUE_STATUS_ACTIVE:
            return f"La placa {normalized_plate} ya tiene un proceso abierto de turno o revisión de calidad."
        assigned_local = iso_to_local(row["assigned_at"] or row["created_at"])
        if row["status"] == QUEUE_STATUS_ASSIGNED and assigned_local and assigned_local.date() >= today_local:
            next_day = (assigned_local + timedelta(days=1)).strftime("%Y-%m-%d")
            return (
                f"La placa {normalized_plate} ya tuvo viaje asignado hoy. "
                f"Solo podrá volver a enturnarse a partir del día siguiente ({next_day})."
            )
    return None


def create_vehicle(
    payload: Dict[str, Any],
    registration_channel: str,
    gps_lat: Optional[float],
    gps_lng: Optional[float],
    gps_distance_m: Optional[float],
    center_id: Optional[str],
) -> Dict[str, Any]:
    plate = normalize_plate(payload.get("plate"))
    carrier_id = clean_text(payload.get("carrierId"))
    driver_name = clean_text(payload.get("driverName"))
    driver_id = clean_text(payload.get("driverId"))
    driver_phone = clean_text(payload.get("driverPhone"))
    destination_id = clean_text(payload.get("destinationId"))
    destination_ids_payload = payload.get("destinationIds")
    empty_weight = parse_float(payload.get("emptyWeightKg"))
    driver_selfie_data_url = payload.get("driverSelfieDataUrl")
    driver_signature_data_url = payload.get("driverSignatureDataUrl")
    destination_ids = [clean_text(destination_id)] if destination_id else []
    if isinstance(destination_ids_payload, list):
        destination_ids = [clean_text(item) for item in destination_ids_payload if clean_text(item)]
    if destination_id and destination_id not in destination_ids:
        destination_ids.insert(0, destination_id)
    destination_ids = list(dict.fromkeys(destination_ids))
    destination_id = destination_ids[0] if destination_ids else destination_id

    if not all([plate, carrier_id, driver_name, driver_id, driver_phone, destination_id]):
        raise AppError("Todos los campos del enturnamiento son obligatorios.", 400)
    if empty_weight is None:
        raise AppError("El peso vacio del vehiculo es obligatorio.", 400)
    if registration_channel == "QR":
        if not isinstance(driver_selfie_data_url, str) or not driver_selfie_data_url.startswith("data:image/"):
            raise AppError("Debes tomar una selfie del conductor para registrarte.", 400)
        if not isinstance(driver_signature_data_url, str) or not driver_signature_data_url.startswith("data:image/"):
            raise AppError("Debes firmar en pantalla para completar el registro.", 400)

    with get_connection() as db:
        center = db.execute("SELECT * FROM centers WHERE id = ?", (clean_text(center_id) or DEFAULT_CENTER_ID,)).fetchone()
        if not center:
            raise AppError("El centro seleccionado no existe.", 404)
        destination = db.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()
        if not destination:
            raise AppError("El destino seleccionado no existe.", 404)
        destination_rows = []
        if destination_ids:
            placeholders = ",".join("?" for _ in destination_ids)
            destination_rows = db.execute(
                f"SELECT * FROM destinations WHERE id IN ({placeholders})",
                destination_ids,
            ).fetchall()
        if len(destination_rows) != len(destination_ids):
            raise AppError("Uno o mas destinos seleccionados no existen.", 404)

        carrier = db.execute("SELECT * FROM carriers WHERE id = ?", (carrier_id,)).fetchone()
        if not carrier:
            raise AppError("La transportadora seleccionada no existe.", 404)
        queue_group = queue_group_for_carrier_code(carrier["code"])

        plate_block_reason = find_plate_registration_block(db, plate, center["id"])
        if plate_block_reason:
            raise AppError(plate_block_reason, 409)

        next_position = db.execute(
            """
            SELECT COALESCE(MAX(queue_position), 0) + 1
            FROM vehicles
            WHERE status = 'QUEUED' AND COALESCE(queue_group, ?) = ?
            """,
            (QUEUE_GROUP_GENERAL, queue_group),
        ).fetchone()[0]
        vehicle_id = create_id()
        tracking_token = create_id()
        driver_selfie_url = (
            save_data_url_image(vehicle_id, "registro", "selfie", 1, driver_selfie_data_url)
            if isinstance(driver_selfie_data_url, str) and driver_selfie_data_url.startswith("data:image/")
            else None
        )
        driver_signature_url = (
            save_data_url_image(vehicle_id, "registro", "firma", 1, driver_signature_data_url)
            if isinstance(driver_signature_data_url, str) and driver_signature_data_url.startswith("data:image/")
            else None
        )
        db.execute(
            """
            INSERT INTO vehicles (
                id, plate, carrier_id, carrier_code, carrier, driver_name, driver_id, driver_phone,
                empty_weight_kg, driver_selfie_url, driver_signature_url, destination_ids_json, destination_id, city, zone,
                center_id, center_code, center_name, queue_group, status, quality_status, queue_position, created_at, registration_channel, gps_lat, gps_lng,
                gps_distance_m, public_tracking_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vehicle_id,
                plate,
                carrier["id"],
                carrier["code"],
                carrier["name"],
                driver_name,
                driver_id,
                driver_phone,
                empty_weight,
                driver_selfie_url,
                driver_signature_url,
                json.dumps(destination_ids, ensure_ascii=False),
                destination["id"],
                destination["city"],
                destination["zone"],
                center["id"],
                center["code"],
                center["name"],
                queue_group,
                QUEUE_STATUS_ACTIVE,
                QUALITY_PENDING,
                next_position,
                now_iso(),
                registration_channel,
                gps_lat,
                gps_lng,
                gps_distance_m,
                tracking_token,
            ),
        )
    cities = ", ".join(r["city"] for r in destination_rows) if destination_rows else destination["city"]
    send_notification(
        "🚛 Vehículo enturnaado",
        f"Placa {plate} · {driver_name} · {cities}",
        tag="enturnar",
    )
    return {"trackingToken": tracking_token}


def add_destination(payload: Dict[str, Any]) -> None:
    city = clean_text(payload.get("city"))
    zone = clean_text(payload.get("zone"))
    if not city or not zone:
        raise AppError("La ciudad y la zona son obligatorias.", 400)
    with get_connection() as db:
        exists = db.execute(
            "SELECT id FROM destinations WHERE LOWER(city) = LOWER(?) AND LOWER(zone) = LOWER(?)",
            (city, zone),
        ).fetchone()
        if exists:
            raise AppError("Ese destino ya existe en la base de datos.", 409)
        db.execute(
            "INSERT INTO destinations (id, city, zone, created_at) VALUES (?, ?, ?, ?)",
            (create_id(), city, zone, now_iso()),
        )


def delete_destination(destination_id: str) -> None:
    with get_connection() as db:
        destination = db.execute("SELECT id FROM destinations WHERE id = ?", (destination_id,)).fetchone()
        if not destination:
            raise AppError("El destino no existe.", 404)
        active_rows = db.execute(
            "SELECT id, destination_id, destination_ids_json FROM vehicles WHERE status = 'QUEUED'"
        ).fetchall()
        in_use = any(destination_id in parse_destination_ids(row) for row in active_rows)
        if in_use:
            raise AppError("No se puede borrar un destino usado por vehiculos enturnados.", 409)
        db.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))


def update_destination(destination_id: str, payload: Dict[str, Any]) -> None:
    city = clean_text(payload.get("city"))
    zone = clean_text(payload.get("zone"))
    if not city or not zone:
        raise AppError("La ciudad y la zona son obligatorias.", 400)
    with get_connection() as db:
        destination = db.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()
        if not destination:
            raise AppError("El destino no existe.", 404)
        exists = db.execute(
            "SELECT id FROM destinations WHERE LOWER(city) = LOWER(?) AND LOWER(zone) = LOWER(?) AND id != ?",
            (city, zone, destination_id),
        ).fetchone()
        if exists:
            raise AppError("Ya existe otro destino con esa ciudad y zona.", 409)
        db.execute("UPDATE destinations SET city = ?, zone = ? WHERE id = ?", (city, zone, destination_id))
        db.execute("UPDATE vehicles SET city = ?, zone = ? WHERE destination_id = ?", (city, zone, destination_id))


def add_carrier(payload: Dict[str, Any]) -> None:
    code = clean_text(payload.get("code"))
    name = clean_text(payload.get("name")).upper()
    if not code or not name:
        raise AppError("El codigo y el nombre de la transportadora son obligatorios.", 400)
    with get_connection() as db:
        exists = db.execute(
            "SELECT id FROM carriers WHERE code = ? OR LOWER(name) = LOWER(?)",
            (code, name),
        ).fetchone()
        if exists:
            raise AppError("Esa transportadora ya existe en la base de datos.", 409)
        db.execute(
            "INSERT INTO carriers (id, code, name, created_at) VALUES (?, ?, ?, ?)",
            (create_id(), code, name, now_iso()),
        )


def delete_carrier(carrier_id: str) -> None:
    with get_connection() as db:
        carrier = db.execute("SELECT * FROM carriers WHERE id = ?", (carrier_id,)).fetchone()
        if not carrier:
            raise AppError("La transportadora no existe.", 404)
        in_use = db.execute(
            "SELECT id FROM vehicles WHERE carrier_id = ? AND status = 'QUEUED' LIMIT 1",
            (carrier_id,),
        ).fetchone()
        if in_use:
            raise AppError("No se puede borrar una transportadora usada por vehiculos enturnados.", 409)
        db.execute("DELETE FROM carriers WHERE id = ?", (carrier_id,))


def update_carrier(carrier_id: str, payload: Dict[str, Any]) -> None:
    code = clean_text(payload.get("code"))
    name = clean_text(payload.get("name")).upper()
    if not code or not name:
        raise AppError("El código y el nombre de la transportadora son obligatorios.", 400)
    with get_connection() as db:
        carrier = db.execute("SELECT * FROM carriers WHERE id = ?", (carrier_id,)).fetchone()
        if not carrier:
            raise AppError("La transportadora no existe.", 404)
        exists = db.execute(
            "SELECT id FROM carriers WHERE (code = ? OR LOWER(name) = LOWER(?)) AND id != ?",
            (code, name, carrier_id),
        ).fetchone()
        if exists:
            raise AppError("Ya existe otra transportadora con ese código o nombre.", 409)
        queue_group = queue_group_for_carrier_code(code)
        db.execute("UPDATE carriers SET code = ?, name = ? WHERE id = ?", (code, name, carrier_id))
        db.execute(
            "UPDATE vehicles SET carrier_code = ?, carrier = ?, queue_group = ? WHERE carrier_id = ?",
            (code, name, queue_group, carrier_id),
        )
        compact_queue(db)


def add_user(payload: Dict[str, Any]) -> None:
    username = clean_text(payload.get("username")).lower()
    full_name = clean_text(payload.get("fullName"))
    role = clean_text(payload.get("role")).upper()
    password = str(payload.get("password") or "").strip()
    center_id = clean_text(payload.get("centerId")) or DEFAULT_CENTER_ID
    if not all([username, full_name, role, password, center_id]):
        raise AppError("Usuario, nombre, rol, centro y clave son obligatorios.", 400)
    if role not in VALID_ROLES:
        raise AppError("El rol indicado no es valido.", 400)
    if len(password) < 8:
        raise AppError("La clave debe tener al menos 8 caracteres.", 400)
    with get_connection() as db:
        center = db.execute("SELECT * FROM centers WHERE id = ?", (center_id,)).fetchone()
        if not center:
            raise AppError("El centro seleccionado no existe.", 404)
        exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            raise AppError("Ese usuario ya existe.", 409)
        db.execute(
            """
            INSERT INTO users (id, username, full_name, role, password_hash, created_at, center_id, center_code, center_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                create_id(),
                username,
                full_name,
                role,
                hash_password(password),
                now_iso(),
                center["id"],
                center["code"],
                center["name"],
            ),
        )


def update_user(user_id: str, payload: Dict[str, Any]) -> None:
    username = clean_text(payload.get("username")).lower()
    full_name = clean_text(payload.get("fullName"))
    role = clean_text(payload.get("role")).upper()
    password = str(payload.get("password") or "").strip()
    active = bool(payload.get("active", True))
    center_id = clean_text(payload.get("centerId")) or DEFAULT_CENTER_ID
    if not all([username, full_name, role, center_id]):
        raise AppError("Usuario, nombre, rol y centro son obligatorios.", 400)
    if role not in VALID_ROLES:
        raise AppError("El rol indicado no es válido.", 400)
    if password and len(password) < 8:
        raise AppError("La clave debe tener al menos 8 caracteres.", 400)
    with get_connection() as db:
        center = db.execute("SELECT * FROM centers WHERE id = ?", (center_id,)).fetchone()
        if not center:
            raise AppError("El centro seleccionado no existe.", 404)
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise AppError("El usuario no existe.", 404)
        exists = db.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id)).fetchone()
        if exists:
            raise AppError("Ya existe otro usuario con ese nombre.", 409)
        password_hash = user["password_hash"]
        if password:
            password_hash = hash_password(password)
        db.execute(
            """
            UPDATE users
            SET username = ?, full_name = ?, role = ?, password_hash = ?, active = ?, center_id = ?, center_code = ?, center_name = ?
            WHERE id = ?
            """,
            (
                username,
                full_name,
                role,
                password_hash,
                1 if active else 0,
                center["id"],
                center["code"],
                center["name"],
                user_id,
            ),
        )


def assign_vehicle(vehicle_id: str) -> None:
    with get_connection() as db:
        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ? AND status = 'QUEUED'", (vehicle_id,)).fetchone()
        if not vehicle:
            raise AppError("El vehiculo no esta enturnado o no existe.", 404)
        db.execute(
            "UPDATE vehicles SET status = 'ASSIGNED', assigned_at = ?, queue_position = NULL WHERE id = ?",
            (now_iso(), vehicle_id),
        )
        compact_queue(db)
    send_notification(
        "✅ Viaje asignado",
        f"Placa {vehicle['plate']} · {vehicle['driver_name']} fue asignado a viaje",
        tag="asignar",
    )


def reject_vehicle(vehicle_id: str, reason: str) -> None:
    reason_text = clean_text(reason) or "No informado"
    with get_connection() as db:
        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ? AND status = 'QUEUED'", (vehicle_id,)).fetchone()
        if not vehicle:
            raise AppError("El vehiculo no esta enturnado o no existe.", 404)
        db.execute(
            """
            UPDATE vehicles
            SET status = 'REJECTED', rejected_at = ?, rejection_reason = ?, queue_position = NULL
            WHERE id = ?
            """,
            (now_iso(), reason_text, vehicle_id),
        )
        compact_queue(db)
    send_notification(
        "❌ Vehículo rechazado",
        f"Placa {vehicle['plate']} · {vehicle['driver_name']} — {reason_text}",
        tag="rechazar",
    )


def update_vehicle(vehicle_id: str, payload: Dict[str, Any]) -> None:
    plate = normalize_plate(payload.get("plate"))
    carrier_id = clean_text(payload.get("carrierId"))
    driver_name = clean_text(payload.get("driverName"))
    driver_id = clean_text(payload.get("driverId"))
    driver_phone = clean_text(payload.get("driverPhone"))
    destination_id = clean_text(payload.get("destinationId"))
    destination_ids_payload = payload.get("destinationIds")
    empty_weight = parse_float(payload.get("emptyWeightKg"))
    new_status = clean_text(payload.get("status")).upper()
    quality_status = clean_text(payload.get("qualityStatus")).upper()
    rejection_reason = clean_text(payload.get("rejectionReason"))
    center_id = clean_text(payload.get("centerId"))

    destination_ids = [clean_text(destination_id)] if destination_id else []
    if isinstance(destination_ids_payload, list):
        destination_ids = [clean_text(item) for item in destination_ids_payload if clean_text(item)]
    if destination_id and destination_id not in destination_ids:
        destination_ids.insert(0, destination_id)
    destination_ids = list(dict.fromkeys(destination_ids))
    destination_id = destination_ids[0] if destination_ids else destination_id

    if not all([plate, carrier_id, driver_name, driver_id, driver_phone, destination_id]):
        raise AppError("Todos los datos base del vehículo son obligatorios.", 400)
    if empty_weight is None:
        raise AppError("El peso vacío del vehículo es obligatorio.", 400)
    if new_status not in {QUEUE_STATUS_ACTIVE, QUEUE_STATUS_ASSIGNED, QUEUE_STATUS_REJECTED}:
        raise AppError("El estado logístico no es válido.", 400)
    if quality_status not in {QUALITY_PENDING, QUALITY_IN_PROGRESS, QUALITY_APPROVED, QUALITY_REWORK, QUALITY_REJECTED}:
        raise AppError("El estado de calidad no es válido.", 400)

    with get_connection() as db:
        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        if not vehicle:
            raise AppError("El vehículo no existe.", 404)
        center = db.execute(
            "SELECT * FROM centers WHERE id = ?",
            (center_id or clean_text(vehicle["center_id"]) or DEFAULT_CENTER_ID,),
        ).fetchone()
        if not center:
            raise AppError("El centro seleccionado no existe.", 404)

        destination = db.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()
        if not destination:
            raise AppError("El destino seleccionado no existe.", 404)
        placeholders = ",".join("?" for _ in destination_ids)
        destination_rows = db.execute(
            f"SELECT * FROM destinations WHERE id IN ({placeholders})",
            destination_ids,
        ).fetchall()
        if len(destination_rows) != len(destination_ids):
            raise AppError("Uno o más destinos seleccionados no existen.", 404)

        carrier = db.execute("SELECT * FROM carriers WHERE id = ?", (carrier_id,)).fetchone()
        if not carrier:
            raise AppError("La transportadora seleccionada no existe.", 404)

        duplicate = db.execute(
            "SELECT id FROM vehicles WHERE plate = ? AND status = 'QUEUED' AND id != ? LIMIT 1",
            (plate, vehicle_id),
        ).fetchone()
        if duplicate and new_status == QUEUE_STATUS_ACTIVE:
            raise AppError(f"La placa {plate} ya está enturnada en otro registro.", 409)

        queue_group = queue_group_for_carrier_code(carrier["code"])
        current_queue_group = vehicle["queue_group"] or queue_group_for_carrier_code(vehicle["carrier_code"])
        queue_position = None
        assigned_at = vehicle["assigned_at"]
        rejected_at = vehicle["rejected_at"]
        last_quality_at = vehicle["last_quality_at"]

        if new_status == QUEUE_STATUS_ACTIVE:
            if vehicle["status"] == QUEUE_STATUS_ACTIVE and current_queue_group == queue_group and vehicle["queue_position"] is not None:
                queue_position = vehicle["queue_position"]
            else:
                queue_position = db.execute(
                    """
                    SELECT COALESCE(MAX(queue_position), 0) + 1
                    FROM vehicles
                    WHERE id != ? AND status = 'QUEUED' AND COALESCE(queue_group, ?) = ?
                    """,
                    (vehicle_id, QUEUE_GROUP_GENERAL, queue_group),
                ).fetchone()[0]
            assigned_at = None
            if quality_status != QUALITY_REJECTED:
                rejected_at = None
                if not rejection_reason:
                    rejection_reason = ""
        elif new_status == QUEUE_STATUS_ASSIGNED:
            queue_position = None
            assigned_at = vehicle["assigned_at"] or now_iso()
            rejected_at = None
            if quality_status != QUALITY_REJECTED and not rejection_reason:
                rejection_reason = ""
        elif new_status == QUEUE_STATUS_REJECTED:
            queue_position = None
            rejected_at = vehicle["rejected_at"] or now_iso()
            rejection_reason = rejection_reason or vehicle["rejection_reason"] or "Corregido por administrador"

        if quality_status == QUALITY_REJECTED and not rejection_reason:
            rejection_reason = vehicle["rejection_reason"] or "Rechazo registrado"
        if quality_status != QUALITY_REJECTED and new_status != QUEUE_STATUS_REJECTED and not clean_text(payload.get("rejectionReason")):
            rejection_reason = ""

        if quality_status in {QUALITY_PENDING, QUALITY_IN_PROGRESS}:
            last_quality_at = None
        elif not last_quality_at:
            last_quality_at = now_iso()

        db.execute(
            """
            UPDATE vehicles
            SET plate = ?, carrier_id = ?, carrier_code = ?, carrier = ?, driver_name = ?, driver_id = ?, driver_phone = ?,
                empty_weight_kg = ?, destination_ids_json = ?, destination_id = ?, city = ?, zone = ?, center_id = ?, center_code = ?, center_name = ?, queue_group = ?,
                status = ?, quality_status = ?, queue_position = ?, assigned_at = ?, rejected_at = ?, rejection_reason = ?,
                last_quality_at = ?
            WHERE id = ?
            """,
            (
                plate,
                carrier["id"],
                carrier["code"],
                carrier["name"],
                driver_name,
                driver_id,
                driver_phone,
                empty_weight,
                json.dumps(destination_ids, ensure_ascii=False),
                destination["id"],
                destination["city"],
                destination["zone"],
                center["id"],
                center["code"],
                center["name"],
                queue_group,
                new_status,
                quality_status,
                queue_position,
                assigned_at,
                rejected_at,
                rejection_reason,
                last_quality_at,
                vehicle_id,
            ),
        )
        compact_queue(db)


def delete_vehicle_record(vehicle_id: str) -> None:
    with get_connection() as db:
        vehicle = db.execute("SELECT id FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        if not vehicle:
            raise AppError("El vehículo no existe.", 404)
        db.execute("DELETE FROM quality_inspections WHERE vehicle_id = ?", (vehicle_id,))
        db.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        compact_queue(db)


def update_site_settings(payload: Dict[str, Any], user: sqlite3.Row) -> None:
    site_name = clean_text(payload.get("siteName")) or "Planta principal"
    site_lat = clean_text(payload.get("siteLat")) or DEFAULT_SETTINGS["site_lat"]
    site_lng = clean_text(payload.get("siteLng")) or DEFAULT_SETTINGS["site_lng"]
    radius_value = parse_float(payload.get("siteRadiusM"))
    geofence_enabled = "1" if payload.get("geofenceEnabled", True) else "0"
    center_id = clean_text(payload.get("centerId")) or clean_text(user["center_id"]) or DEFAULT_CENTER_ID

    if site_lat:
        parse_float(site_lat)
    if site_lng:
        parse_float(site_lng)
    if radius_value is None or radius_value <= 0:
        raise AppError("El radio GPS debe ser mayor a cero.", 400)

    with get_connection() as db:
        center = db.execute("SELECT * FROM centers WHERE id = ?", (center_id,)).fetchone()
        if not center:
            raise AppError("El centro seleccionado no existe.", 404)
        db.execute(
            """
            UPDATE centers
            SET name = ?, site_lat = ?, site_lng = ?, site_radius_m = ?, geofence_enabled = ?
            WHERE id = ?
            """,
            (site_name, site_lat, site_lng, str(int(radius_value)), geofence_enabled, center_id),
        )


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def detect_center_by_coordinates(
    gps_lat: float,
    gps_lng: float,
    preferred_center_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], float]:
    with get_connection() as db:
        centers = load_centers(db)
    ordered_centers = centers
    if preferred_center_id:
        ordered_centers = sorted(centers, key=lambda item: 0 if item["id"] == preferred_center_id else 1)
    matches: List[Tuple[Dict[str, Any], float]] = []
    for center in ordered_centers:
        if not center["geofenceEnabled"]:
            continue
        distance = haversine_distance_m(
            gps_lat,
            gps_lng,
            parse_float(center["siteLat"]) or 0.0,
            parse_float(center["siteLng"]) or 0.0,
        )
        radius = parse_float(center["siteRadiusM"]) or 180.0
        if distance <= radius:
            matches.append((center, distance))
    if not matches:
        raise AppError("Estas fuera del radio permitido de los centros configurados.", 409)
    matches.sort(key=lambda item: item[1])
    return matches[0]


def validate_geofence(payload: Dict[str, Any], preferred_center_id: Optional[str] = None) -> Tuple[Optional[float], Optional[float], Optional[float], Dict[str, Any]]:
    gps_lat = parse_float(payload.get("gpsLat"))
    gps_lng = parse_float(payload.get("gpsLng"))
    if gps_lat is None or gps_lng is None:
        raise AppError("Debes habilitar el GPS para registrarte en planta.", 409)
    center, distance = detect_center_by_coordinates(gps_lat, gps_lng, preferred_center_id)
    return gps_lat, gps_lng, distance, center


def public_register(payload: Dict[str, Any], preferred_center_id: Optional[str] = None) -> Dict[str, Any]:
    gps_lat, gps_lng, gps_distance, center = validate_geofence(payload, preferred_center_id)
    created = create_vehicle(payload, "QR", gps_lat, gps_lng, gps_distance, center["id"])
    return build_public_tracking(created["trackingToken"])


def build_public_tracking(token: str) -> Dict[str, Any]:
    with get_connection() as db:
        vehicle = db.execute(
            "SELECT * FROM vehicles WHERE public_tracking_token = ?",
            (token,),
        ).fetchone()
        if not vehicle:
            raise AppError("No se encontro el turno solicitado.", 404)
        destination_lookup = build_destination_lookup(
            [
                serialize_destination(row)
                for row in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
            ]
        )
        queued_rows = db.execute(
            "SELECT * FROM vehicles WHERE status = 'QUEUED' AND center_id = ? ORDER BY queue_position, created_at",
            (vehicle["center_id"],),
        ).fetchall()
        queue_group = vehicle["queue_group"] or queue_group_for_carrier_code(vehicle["carrier_code"])
        queue_group_rows = [
            row for row in queued_rows
            if (row["queue_group"] or queue_group_for_carrier_code(row["carrier_code"])) == queue_group
        ]
        turn_positions = calculate_turn_positions(queued_rows)
        city_turn_map, _city_queue_lists = build_city_turn_maps(queued_rows, destination_lookup)
        latest_inspections = load_latest_inspections(db, include_media=False)
        front_vehicle = queue_group_rows[0] if queue_group_rows else None
    return {
        "vehicle": serialize_vehicle(vehicle, turn_positions, latest_inspections, destination_lookup, city_turn_map, include_media=False, inspection_summary_only=True),
        "queueSize": len(queue_group_rows),
        "currentTurnPosition": turn_positions.get(vehicle["id"]),
        "frontOfQueue": (
            serialize_vehicle(front_vehicle, turn_positions, latest_inspections, destination_lookup, city_turn_map, include_media=False, inspection_summary_only=True)
            if front_vehicle
            else None
        ),
        "centerName": vehicle["center_name"],
    }


def get_public_config(origin: str, center_id: Optional[str] = None) -> Dict[str, Any]:
    with get_connection() as db:
        centers = load_centers(db)
        center_lookup = build_center_lookup(centers)
        center = center_lookup.get(clean_text(center_id) or DEFAULT_CENTER_ID) or preferred_center_for_user(_Row({"center_id": DEFAULT_CENTER_ID}), centers)
        carriers = [
            serialize_carrier(row)
            for row in db.execute("SELECT * FROM carriers ORDER BY name").fetchall()
        ]
        destinations = [
            serialize_destination(row)
            for row in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
        ]
        destination_lookup = build_destination_lookup(destinations)
        queued_rows = db.execute(
            "SELECT * FROM vehicles WHERE status = 'QUEUED' AND center_id = ? ORDER BY queue_position, created_at",
            (center["id"],),
        ).fetchall()
        _turn_positions = calculate_turn_positions(queued_rows)
        _city_turn_map, city_queue_lists = build_city_turn_maps(queued_rows, destination_lookup)
    return {
        "siteName": center["name"],
        "centerId": center["id"],
        "centerCode": center["code"],
        "geofenceEnabled": center["geofenceEnabled"],
        "siteConfigured": bool(center["siteLat"] and center["siteLng"]),
        "siteRadiusM": center["siteRadiusM"],
        "registrationUrl": f"{origin}/driver.html?center={center['id']}",
        "carriers": carriers,
        "destinations": destinations,
        "defaultSiteLat": center["siteLat"],
        "defaultSiteLng": center["siteLng"],
        "centers": centers,
        "cityTurnCounts": build_public_city_turn_counts(city_queue_lists),
    }


def build_findings_summary(checklist: Dict[str, Any]) -> str:
    findings = []
    for key, item in checklist.items():
        status = clean_text(item.get("status")).upper() if isinstance(item, dict) else ""
        if status in {"NO_CUMPLE", "NO"}:
            findings.append(clean_text(item.get("label")) or key)
    return ", ".join(findings[:6]) or "Inspeccion registrada"


def save_data_url_image(vehicle_id: str, inspection_id: str, item_key: str, index: int, data_url: str) -> str:
    try:
        _header, encoded = data_url.split(",", 1)
    except ValueError as exc:
        raise AppError("Una evidencia enviada no tiene formato valido.", 400) from exc
    try:
        base64.b64decode(encoded)
    except (binascii.Error, ValueError) as exc:
        raise AppError("No se pudo decodificar una evidencia fotografica.", 400) from exc
    # Las imágenes se guardan como data URL directamente en PostgreSQL (sin disco)
    return data_url


def save_checklist_evidence(vehicle_id: str, inspection_id: str, checklist: Dict[str, Any]) -> Dict[str, Any]:
    saved: Dict[str, Any] = {}
    for item_key, item in checklist.items():
        if not isinstance(item, dict):
            continue
        copied = dict(item)
        evidences = item.get("evidences") or []
        saved_urls = []
        for index, data_url in enumerate(evidences, start=1):
            if isinstance(data_url, str) and data_url.startswith("data:image/"):
                saved_urls.append(save_data_url_image(vehicle_id, inspection_id, item_key, index, data_url))
        copied["evidences"] = saved_urls
        saved[item_key] = copied
    return saved


def save_quality_inspection(vehicle_id: str, user: sqlite3.Row, payload: Dict[str, Any]) -> None:
    decision = clean_text(payload.get("finalDecision")).upper()
    if decision not in {QUALITY_APPROVED, QUALITY_REWORK, QUALITY_REJECTED}:
        raise AppError("Debes indicar si el vehiculo queda apto, en arreglos o rechazado.", 400)
    checklist = payload.get("checklist") or {}
    suitability = payload.get("suitability") or []
    if not isinstance(checklist, dict):
        raise AppError("La lista de chequeo no tiene un formato valido.", 400)
    if not isinstance(suitability, list):
        raise AppError("La observacion 1 debe enviarse como lista.", 400)

    reviewed_at = now_iso()
    inspection_id = create_id()
    findings_summary = build_findings_summary(checklist)
    observations_text = clean_text(payload.get("observationsText"))
    checklist_saved = save_checklist_evidence(vehicle_id, inspection_id, checklist)

    with get_connection() as db:
        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        if not vehicle:
            raise AppError("El vehiculo ya no esta disponible para revision.", 404)

        db.execute(
            """
            INSERT INTO quality_inspections (
                id, vehicle_id, inspector_user_id, inspector_name, reviewed_at, final_decision,
                suitability_json, observations_text, checklist_json, findings_summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inspection_id,
                vehicle_id,
                user["id"],
                user["full_name"],
                reviewed_at,
                decision,
                json.dumps(suitability, ensure_ascii=False),
                observations_text,
                json.dumps(checklist_saved, ensure_ascii=False),
                findings_summary,
                now_iso(),
            ),
        )

        new_status = vehicle["status"]
        new_queue_position = vehicle["queue_position"]
        rejected_at = vehicle["rejected_at"]
        rejection_reason = vehicle["rejection_reason"]
        if decision == QUALITY_REJECTED:
            new_status = QUEUE_STATUS_REJECTED
            new_queue_position = None
            rejected_at = reviewed_at
            rejection_reason = findings_summary or "Rechazo por calidad"
        else:
            if vehicle["status"] == QUEUE_STATUS_REJECTED:
                new_status = QUEUE_STATUS_ACTIVE
                new_queue_position = db.execute(
                    """
                    SELECT COALESCE(MAX(queue_position), 0) + 1
                    FROM vehicles
                    WHERE id != ? AND status = 'QUEUED' AND COALESCE(queue_group, ?) = ?
                    """,
                    (vehicle_id, QUEUE_GROUP_GENERAL, vehicle["queue_group"] or QUEUE_GROUP_GENERAL),
                ).fetchone()[0]
            elif vehicle["status"] == QUEUE_STATUS_ASSIGNED:
                new_status = QUEUE_STATUS_ASSIGNED
                new_queue_position = None
            else:
                new_status = QUEUE_STATUS_ACTIVE
                if new_queue_position is None:
                    new_queue_position = db.execute(
                        """
                        SELECT COALESCE(MAX(queue_position), 0) + 1
                        FROM vehicles
                        WHERE id != ? AND status = 'QUEUED' AND COALESCE(queue_group, ?) = ?
                        """,
                        (vehicle_id, QUEUE_GROUP_GENERAL, vehicle["queue_group"] or QUEUE_GROUP_GENERAL),
                    ).fetchone()[0]
            rejected_at = None
            rejection_reason = ""

        db.execute(
            """
            UPDATE vehicles
            SET quality_status = ?, last_quality_at = ?, status = ?, queue_position = ?, rejected_at = ?, rejection_reason = ?
            WHERE id = ?
            """,
            (decision, reviewed_at, new_status, new_queue_position, rejected_at, rejection_reason, vehicle_id),
        )
        compact_queue(db)

    quality_labels = {
        QUALITY_APPROVED: ("Vehículo APTO", "apto"),
        QUALITY_REWORK: ("Vehículo en ARREGLOS", "arreglos"),
        QUALITY_REJECTED: ("Vehículo RECHAZADO por calidad", "rechazo-calidad"),
    }
    label, ntag = quality_labels.get(decision, ("Calidad actualizada", "calidad"))
    with get_connection() as db:
        v = db.execute("SELECT plate, driver_name FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
    if v:
        send_notification(label, f"Placa {v['plate']} · {v['driver_name']}", tag=ntag)


class Handler(BaseHTTPRequestHandler):
    server_version = "EnturnamientoVehiculos/2.0"

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self.send_response(200)
            self.add_common_headers("application/json; charset=utf-8")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(200)
        self.add_common_headers("text/plain; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/healthz":
                self.send_json({"status": "ok", "time": now_iso()})
                return
            if parsed.path == "/api/mobile/quality-state":
                user = self.require_user()
                if not user:
                    return
                self.send_json(build_mobile_quality_state(user))
                return
            if parsed.path == "/api/auth/me":
                user = self.require_user()
                if not user:
                    return
                self.send_json({"user": self.serialize_user(user)})
                return
            if parsed.path == "/api/app-state":
                user = self.require_user()
                if not user:
                    return
                self.send_json(get_user_state(user, self.request_origin()))
                return
            if parsed.path == "/api/history":
                user = self.require_user()
                if not user:
                    return
                self.send_json(get_history_rows_for_user(user))
                return
            if parsed.path.startswith("/api/vehicles/") and parsed.path.endswith("/detail"):
                user = self.require_user()
                if not user:
                    return
                vehicle_id = unquote(parsed.path.split("/")[3])
                self.send_json(get_vehicle_detail_for_user(user, vehicle_id))
                return
            if parsed.path == "/api/public/config":
                self.send_json(get_public_config(self.request_origin(), first_query_value(query, "center")))
                return
            if parsed.path.startswith("/api/public/tracking/"):
                token = parsed.path.rsplit("/", 1)[-1]
                self.send_json(build_public_tracking(unquote(token)))
                return
            if parsed.path == "/api/push/vapid-key":
                _, pub = get_vapid_keys()
                self.send_json({"publicKey": pub})
                return
            if parsed.path in {"", "/"}:
                self.serve_static("/index.html")
                return
            if parsed.path == "/driver":
                self.serve_static("/driver.html")
                return
            self.serve_static(parsed.path)
        except AppError as error:
            self.send_error_json(error.message, error.status)
        except DATABASE_DRIVER_ERRORS as error:
            self.send_error_json(f"Error de base de datos: {error}", 500)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            payload = self.read_json()

            if parsed.path == "/api/mobile/auth/login":
                self.login(payload, mobile=True)
                return
            if parsed.path == "/api/auth/login":
                self.login(payload)
                return
            if parsed.path == "/api/auth/logout":
                self.logout()
                return
            if parsed.path == "/api/push/subscribe":
                endpoint = clean_text(payload.get("endpoint"))
                keys = payload.get("keys") or {}
                p256dh = clean_text(keys.get("p256dh"))
                auth = clean_text(keys.get("auth"))
                if endpoint and p256dh and auth:
                    with get_connection() as db:
                        db.execute(
                            "INSERT INTO push_subscriptions (id, endpoint, p256dh, auth, created_at) "
                            "VALUES (?, ?, ?, ?, ?) ON CONFLICT (endpoint) DO UPDATE SET p256dh=EXCLUDED.p256dh, auth=EXCLUDED.auth",
                            (create_id(), endpoint, p256dh, auth, now_iso()),
                        )
                self.send_json({"ok": True})
                return
            if parsed.path == "/api/fcm/register":
                token = clean_text(payload.get("token"))
                if token:
                    with get_connection() as db:
                        db.execute(
                            "INSERT INTO fcm_tokens (id, token, created_at) VALUES (?, ?, ?) "
                            "ON CONFLICT (token) DO NOTHING",
                            (create_id(), token, now_iso()),
                        )
                self.send_json({"ok": True})
                return
            if parsed.path == "/api/public/register":
                self.send_json(public_register(payload, first_query_value(query, "center")), 201)
                return

            user = self.require_user()
            if not user:
                return

            if parsed.path == "/api/settings/site":
                self.require_role(user, ROLE_ADMIN)
                update_site_settings(payload, user)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            if parsed.path == "/api/destinations":
                if not can_add_catalogs(user):
                    raise AppError("No tienes permisos para crear destinos.", 403)
                add_destination(payload)
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return
            if parsed.path == "/api/carriers":
                if not can_add_catalogs(user):
                    raise AppError("No tienes permisos para crear transportadoras.", 403)
                add_carrier(payload)
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return
            if parsed.path == "/api/users":
                self.require_role(user, ROLE_ADMIN)
                add_user(payload)
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return
            if parsed.path == "/api/history/pdf":
                record_ids = [clean_text(item) for item in (payload.get("recordIds") or []) if clean_text(item)]
                visible_history = get_history_rows_for_user(user)
                if record_ids:
                    visible_history = [item for item in visible_history if item["id"] in set(record_ids)]
                if not visible_history:
                    raise AppError("No hay registros visibles para imprimir en PDF.", 404)
                pdf_content = build_history_pdf(visible_history)
                self.send_binary(
                    pdf_content,
                    "application/pdf",
                    f"historial-fo-cl-021-{now_local().strftime('%Y%m%d-%H%M')}.pdf",
                )
                return
            if parsed.path == "/api/vehicles":
                self.require_any_role(user, {ROLE_ADMIN, ROLE_LOGISTICS})
                create_vehicle(payload, "DESK", None, None, None, user["center_id"])
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return

            vehicle_id, action = parse_vehicle_action(parsed.path)
            if action == "assign":
                self.require_any_role(user, {ROLE_ADMIN, ROLE_LOGISTICS})
                assign_vehicle(vehicle_id)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            if action == "reject":
                self.require_any_role(user, {ROLE_ADMIN, ROLE_LOGISTICS})
                reject_vehicle(vehicle_id, clean_text(payload.get("reason")))
                self.send_json(get_user_state(user, self.request_origin()))
                return

            if parsed.path.startswith("/api/quality/") and parsed.path.endswith("/inspect"):
                self.require_any_role(user, {ROLE_ADMIN, ROLE_QUALITY})
                quality_vehicle_id = parsed.path.split("/")[3]
                save_quality_inspection(quality_vehicle_id, user, payload)
                self.send_json(get_user_state(self.get_fresh_user(user["id"]), self.request_origin()))
                return
            if parsed.path.startswith("/api/mobile/quality/") and parsed.path.endswith("/inspect"):
                self.require_any_role(user, {ROLE_ADMIN, ROLE_QUALITY})
                quality_vehicle_id = parsed.path.split("/")[4]
                save_quality_inspection(quality_vehicle_id, user, payload)
                self.send_json(build_mobile_quality_state(self.get_fresh_user(user["id"])))
                return

            self.send_error_json("Ruta no encontrada.", 404)
        except AppError as error:
            self.send_error_json(error.message, error.status)
        except DATABASE_DRIVER_ERRORS as error:
            self.send_error_json(f"Error de base de datos: {error}", 500)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        try:
            user = self.require_user()
            if not user:
                return
            self.require_role(user, ROLE_ADMIN)
            payload = self.read_json()

            vehicle_id = parse_entity_id(parsed.path, "vehicles")
            if vehicle_id:
                update_vehicle(vehicle_id, payload)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            destination_id = parse_entity_id(parsed.path, "destinations")
            if destination_id:
                update_destination(destination_id, payload)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            carrier_id = parse_entity_id(parsed.path, "carriers")
            if carrier_id:
                update_carrier(carrier_id, payload)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            user_id = parse_entity_id(parsed.path, "users")
            if user_id:
                update_user(user_id, payload)
                self.send_json(get_user_state(self.get_fresh_user(user["id"]), self.request_origin()))
                return

            self.send_error_json("Ruta no encontrada.", 404)
        except AppError as error:
            self.send_error_json(error.message, error.status)
        except DATABASE_DRIVER_ERRORS as error:
            self.send_error_json(f"Error de base de datos: {error}", 500)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        try:
            user = self.require_user()
            if not user:
                return
            self.require_role(user, ROLE_ADMIN)

            destination_id = parse_entity_delete(parsed.path, "destinations")
            if destination_id:
                delete_destination(destination_id)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            carrier_id = parse_entity_delete(parsed.path, "carriers")
            if carrier_id:
                delete_carrier(carrier_id)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            vehicle_id = parse_entity_delete(parsed.path, "vehicles")
            if vehicle_id:
                delete_vehicle_record(vehicle_id)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            self.send_error_json("Ruta no encontrada.", 404)
        except AppError as error:
            self.send_error_json(error.message, error.status)
        except DATABASE_DRIVER_ERRORS as error:
            self.send_error_json(f"Error de base de datos: {error}", 500)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.add_common_headers()
        self.end_headers()

    def login(self, payload: Dict[str, Any], mobile: bool = False) -> None:
        username = clean_text(payload.get("username")).lower()
        password = str(payload.get("password") or "")
        if not username or not password:
            raise AppError("Usuario y clave son obligatorios.", 400)
        with get_connection() as db:
            user = db.execute("SELECT * FROM users WHERE username = ? AND active = 1", (username,)).fetchone()
            if not user or not verify_password(password, user["password_hash"]):
                raise AppError("Credenciales invalidas.", 401)
            token = create_session(db, user["id"])
            state = build_mobile_auth_payload(user, token) if mobile else build_auth_payload(user, self.request_origin(), token)
        self.send_json(
            state,
            headers={"Set-Cookie": f"{SESSION_COOKIE}={token}; HttpOnly; Path=/; SameSite=Lax"},
        )

    def logout(self) -> None:
        token = self.get_session_token()
        if token:
            with get_connection() as db:
                db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self.send_json(
            {"ok": True},
            headers={"Set-Cookie": f"{SESSION_COOKIE}=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax"},
        )

    def require_user(self) -> Optional[sqlite3.Row]:
        token = self.get_session_token()
        if not token:
            self.send_error_json("Debes iniciar sesion.", 401)
            return None
        with get_connection() as db:
            user = get_authenticated_user_by_token(db, token)
        if not user:
            self.send_error_json("Tu sesion expiro. Ingresa nuevamente.", 401)
            return None
        return user

    def require_role(self, user: sqlite3.Row, role: str) -> None:
        if user["role"] != role:
            raise AppError("No tienes permisos para esta accion.", 403)

    def require_any_role(self, user: sqlite3.Row, roles: set[str]) -> None:
        if user["role"] not in roles:
            raise AppError("No tienes permisos para esta accion.", 403)

    def get_fresh_user(self, user_id: str) -> sqlite3.Row:
        with get_connection() as db:
            user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise AppError("No se pudo refrescar la sesion del usuario.", 500)
        return user

    def get_session_token(self) -> Optional[str]:
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip() or None
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return None
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        morsel = cookie.get(SESSION_COOKIE)
        return morsel.value if morsel else None

    def request_origin(self) -> str:
        forwarded_proto = self.headers.get("X-Forwarded-Proto")
        forwarded_host = self.headers.get("X-Forwarded-Host")
        if forwarded_proto and forwarded_host:
            return f"{forwarded_proto}://{forwarded_host}"
        return f"http://{self.headers.get('Host', f'localhost:{PORT}')}"

    def serialize_user(self, user: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": user["id"],
            "username": user["username"],
            "fullName": user["full_name"],
            "role": user["role"],
            "centerId": user.get("center_id") if isinstance(user, dict) else user["center_id"],
            "centerCode": user.get("center_code") if isinstance(user, dict) else user["center_code"],
            "centerName": user.get("center_name") if isinstance(user, dict) else user["center_name"],
        }

    def read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AppError("El cuerpo de la solicitud no es un JSON valido.", 400) from exc

    def serve_static(self, path: str) -> None:
        relative = unquote(path).lstrip("/")
        if relative.startswith("uploads/"):
            file_path = (UPLOADS_DIR / relative[len("uploads/"):]).resolve()
            root_dir = UPLOADS_DIR.resolve()
        else:
            file_path = (BASE_DIR / relative).resolve()
            root_dir = BASE_DIR
        try:
            file_path.relative_to(root_dir)
        except ValueError:
            self.send_error_json("Archivo no encontrado.", 404)
            return
        if not file_path.is_file():
            self.send_error_json("Archivo no encontrado.", 404)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        content = file_path.read_bytes()
        self.send_response(200)
        self.add_common_headers(content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data: Dict[str, Any], status: int = 200, headers: Optional[Dict[str, str]] = None) -> None:
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.add_common_headers("application/json; charset=utf-8")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_binary(self, content: bytes, content_type: str, filename: str, status: int = 200) -> None:
        self.send_response(status)
        self.add_common_headers(content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_error_json(self, message: str, status: int) -> None:
        self.send_json({"error": message}, status)

    def add_common_headers(self, content_type: Optional[str] = None) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-store")
        if content_type:
            self.send_header("Content-Type", content_type)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def parse_vehicle_action(path: str) -> Tuple[str, Optional[str]]:
    parts = path.strip("/").split("/")
    if len(parts) == 4 and parts[0] == "api" and parts[1] == "vehicles":
        return unquote(parts[2]), parts[3]
    return "", None


def parse_entity_delete(path: str, entity_name: str) -> Optional[str]:
    parts = path.strip("/").split("/")
    if len(parts) == 3 and parts[0] == "api" and parts[1] == entity_name:
        return unquote(parts[2])
    return None


def parse_entity_id(path: str, entity_name: str) -> Optional[str]:
    return parse_entity_delete(path, entity_name)


def first_query_value(query: Dict[str, List[str]], key: str) -> Optional[str]:
    values = query.get(key) or []
    return clean_text(values[0]) if values else None

class ResilientServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def _create_pg_pool() -> bool:
    """Crea el pool de conexiones PostgreSQL. Retorna True si tuvo éxito."""
    global _pg_pool
    if not (DATABASE_URL and psycopg2):
        return False
    try:
        pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=DATABASE_URL,
        )
        # Verificar que al menos una conexión funciona
        conn = pool.getconn()
        pool.putconn(conn)
        with _pg_pool_lock:
            _pg_pool = pool
        print("Pool PostgreSQL creado (min=2, max=10).")
        return True
    except Exception as err:
        print(f"No se pudo crear pool PostgreSQL: {err}")
        return False


def initialize_with_retry(max_attempts: int = 10) -> str:
    """Inicializa la base de datos con reintentos y backoff exponencial."""
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            if DATABASE_URL and psycopg2 and not _pg_pool:
                _create_pg_pool()
            init_db()
            with get_connection() as db:
                mode = "PostgreSQL" if is_postgres_connection(db) else "SQLite contingencia"
                print(f"Base de datos lista: {mode}")
                return mode
        except Exception as error:
            last_error = error
            delay = min(2 ** (attempt - 1), 30)  # backoff: 1s, 2s, 4s, 8s, 16s, 30s max
            print(f"Intento de arranque {attempt}/{max_attempts} fallo: {error}. Reintento en {delay}s...")
            if attempt < max_attempts:
                time.sleep(delay)
    raise last_error or RuntimeError("No se pudo inicializar la aplicacion.")


def main() -> None:
    db_mode = initialize_with_retry()
    server = ResilientServer((HOST, PORT), Handler)
    print(f"Aplicacion lista en http://localhost:{PORT}")
    print(f"Base de datos activa: {db_mode}.")
    print("UI: Inter font, pill tabs, lift cards, spring modal — v2.2")
    server.serve_forever()


if __name__ == "__main__":
    main()

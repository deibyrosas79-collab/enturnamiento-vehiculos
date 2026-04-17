from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import mimetypes
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("DB_PATH", str(DATA_DIR / "enturnamiento.db")))
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", str(DB_PATH.parent / "uploads")))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
SESSION_COOKIE = "ev_session"
SESSION_HOURS = 16

ROLE_LOGISTICS = "LOGISTICA"
ROLE_QUALITY = "CALIDAD"
VALID_ROLES = {ROLE_LOGISTICS, ROLE_QUALITY}
QUEUE_STATUS_ACTIVE = "QUEUED"
QUEUE_STATUS_ASSIGNED = "ASSIGNED"
QUEUE_STATUS_REJECTED = "REJECTED"
QUALITY_PENDING = "PENDING"
QUALITY_IN_PROGRESS = "IN_REVIEW"
QUALITY_APPROVED = "APPROVED"
QUALITY_REWORK = "REWORK"
QUALITY_REJECTED = "REJECTED"

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
    ("logistica", "Logistica Principal", ROLE_LOGISTICS, "Logistica2026!"),
    ("calidad", "Inspector Calidad", ROLE_QUALITY, "Calidad2026!"),
]

DEFAULT_SETTINGS = {
    "site_name": "Planta principal",
    "site_lat": "",
    "site_lng": "",
    "site_radius_m": "180",
    "geofence_enabled": "1",
}


class AppError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_id() -> str:
    return uuid.uuid4().hex


def clean_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_plate(value: object) -> str:
    return clean_text(value).upper().replace(" ", "").replace("-", "")


def parse_float(value: object) -> Optional[float]:
    raw = clean_text(value).replace(",", ".")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise AppError("El valor numerico recibido no es valido.", 400) from exc


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


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
                role TEXT NOT NULL CHECK(role IN ('LOGISTICA', 'CALIDAD')),
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
            """
        )
        ensure_vehicle_columns(db)
        seed_settings(db)
        seed_destinations(db)
        seed_carriers(db)
        seed_users(db)
        seed_tracking_tokens(db)


def ensure_vehicle_columns(db: sqlite3.Connection) -> None:
    columns = {row["name"] for row in db.execute("PRAGMA table_info(vehicles)").fetchall()}
    extra_columns = {
        "carrier_id": "TEXT",
        "driver_phone": "TEXT",
        "empty_weight_kg": "REAL",
        "driver_selfie_url": "TEXT",
        "driver_signature_url": "TEXT",
        "registration_channel": "TEXT DEFAULT 'DESK'",
        "gps_lat": "REAL",
        "gps_lng": "REAL",
        "gps_distance_m": "REAL",
        "quality_status": "TEXT DEFAULT 'PENDING'",
        "public_tracking_token": "TEXT",
        "last_quality_at": "TEXT",
    }
    for column_name, column_type in extra_columns.items():
        if column_name not in columns:
            db.execute(f"ALTER TABLE vehicles ADD COLUMN {column_name} {column_type}")
    db.execute(
        "UPDATE vehicles SET quality_status = ? WHERE quality_status IS NULL OR quality_status = ''",
        (QUALITY_PENDING,),
    )
    db.execute(
        "UPDATE vehicles SET registration_channel = 'DESK' WHERE registration_channel IS NULL OR registration_channel = ''"
    )
    db.execute(
        "UPDATE vehicles SET public_tracking_token = ? WHERE public_tracking_token IS NULL OR public_tracking_token = ''",
        (create_id(),),
    )


def seed_settings(db: sqlite3.Connection) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        exists = db.execute("SELECT key FROM settings WHERE key = ?", (key,)).fetchone()
        if not exists:
            db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))


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
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return
    db.executemany(
        """
        INSERT INTO users (id, username, full_name, role, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (create_id(), username, full_name, role, hash_password(password), now_iso())
            for username, full_name, role, password in DEFAULT_USERS
        ],
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


def parse_json_field(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def serialize_inspection(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "vehicleId": row["vehicle_id"],
        "inspectorUserId": row["inspector_user_id"],
        "inspectorName": row["inspector_name"],
        "reviewedAt": row["reviewed_at"],
        "finalDecision": row["final_decision"],
        "suitability": parse_json_field(row["suitability_json"], []),
        "observationsText": row["observations_text"],
        "checklist": parse_json_field(row["checklist_json"], {}),
        "findingsSummary": row["findings_summary"],
    }


def load_latest_inspections(db: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    inspections: Dict[str, Dict[str, Any]] = {}
    rows = db.execute(
        "SELECT * FROM quality_inspections ORDER BY reviewed_at DESC, created_at DESC"
    ).fetchall()
    for row in rows:
        if row["vehicle_id"] in inspections:
            continue
        inspections[row["vehicle_id"]] = serialize_inspection(row)
    return inspections


def calculate_turn_positions(queued_rows: List[sqlite3.Row]) -> Dict[str, int]:
    return {row["id"]: index for index, row in enumerate(queued_rows, start=1)}


def serialize_vehicle(
    row: sqlite3.Row,
    turn_positions: Dict[str, int],
    latest_inspections: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "plate": row["plate"],
        "carrierId": row["carrier_id"],
        "carrierCode": row["carrier_code"],
        "carrier": row["carrier"],
        "driverName": row["driver_name"],
        "driverId": row["driver_id"],
        "driverPhone": row["driver_phone"],
        "emptyWeightKg": row["empty_weight_kg"],
        "driverSelfieUrl": row["driver_selfie_url"],
        "driverSignatureUrl": row["driver_signature_url"],
        "destinationId": row["destination_id"],
        "city": row["city"],
        "zone": row["zone"],
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
        "latestInspection": latest_inspections.get(row["id"]),
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


def get_user_state(user: sqlite3.Row, origin: str) -> Dict[str, Any]:
    with get_connection() as db:
        settings = get_settings_map(db)
        destinations = [
            serialize_destination(row)
            for row in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
        ]
        carriers = [
            serialize_carrier(row)
            for row in db.execute("SELECT * FROM carriers ORDER BY name").fetchall()
        ]
        vehicles = db.execute(
            "SELECT * FROM vehicles ORDER BY CASE status WHEN 'QUEUED' THEN 0 WHEN 'ASSIGNED' THEN 1 ELSE 2 END, queue_position, created_at DESC"
        ).fetchall()
        queued_rows = [row for row in vehicles if row["status"] == QUEUE_STATUS_ACTIVE]
        turn_positions = calculate_turn_positions(queued_rows)
        latest_inspections = load_latest_inspections(db)

        queued = [serialize_vehicle(row, turn_positions, latest_inspections) for row in queued_rows]
        assigned = [
            serialize_vehicle(row, turn_positions, latest_inspections)
            for row in vehicles
            if row["status"] == QUEUE_STATUS_ASSIGNED
        ]
        rejected = [
            serialize_vehicle(row, turn_positions, latest_inspections)
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
            }
            for row in db.execute("SELECT * FROM users ORDER BY role, full_name").fetchall()
        ]
        inspection_rows = db.execute(
            "SELECT * FROM quality_inspections ORDER BY reviewed_at DESC, created_at DESC"
        ).fetchall()
        inspections = [serialize_inspection(row) for row in inspection_rows]

    quality_pending = [vehicle for vehicle in queued if vehicle["qualityStatus"] in {QUALITY_PENDING, QUALITY_IN_PROGRESS}]
    quality_rework = [vehicle for vehicle in queued if vehicle["qualityStatus"] == QUALITY_REWORK]
    quality_approved = [vehicle for vehicle in queued if vehicle["qualityStatus"] == QUALITY_APPROVED]
    quality_rejected = [vehicle for vehicle in rejected if vehicle["qualityStatus"] == QUALITY_REJECTED]
    site_config = {
        "siteName": settings.get("site_name", ""),
        "siteLat": settings.get("site_lat", ""),
        "siteLng": settings.get("site_lng", ""),
        "siteRadiusM": settings.get("site_radius_m", "180"),
        "geofenceEnabled": settings.get("geofence_enabled", "1") == "1",
    }
    registration_url = f"{origin}/driver.html"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&data={registration_url}"

    return {
        "user": {
            "id": user["id"],
            "username": user["username"],
            "fullName": user["full_name"],
            "role": user["role"],
        },
        "destinations": destinations,
        "carriers": carriers,
        "queued": queued,
        "assigned": assigned,
        "rejected": rejected,
        "quality": {
            "pending": quality_pending,
            "rework": quality_rework,
            "approved": quality_approved,
            "rejected": quality_rejected,
            "inspections": inspections,
        },
        "users": users if user["role"] == ROLE_LOGISTICS else [],
        "settings": site_config,
        "analytics": build_analytics(rejected, inspections),
        "publicRegistrationUrl": registration_url,
        "publicQrUrl": qr_url,
    }


def compact_queue(db: sqlite3.Connection) -> None:
    queued = db.execute(
        "SELECT id FROM vehicles WHERE status = 'QUEUED' ORDER BY queue_position, created_at"
    ).fetchall()
    for index, row in enumerate(queued, start=1):
        db.execute("UPDATE vehicles SET queue_position = ? WHERE id = ?", (index, row["id"]))


def create_vehicle(
    payload: Dict[str, Any],
    registration_channel: str,
    gps_lat: Optional[float],
    gps_lng: Optional[float],
    gps_distance_m: Optional[float],
) -> Dict[str, Any]:
    plate = normalize_plate(payload.get("plate"))
    carrier_id = clean_text(payload.get("carrierId"))
    driver_name = clean_text(payload.get("driverName"))
    driver_id = clean_text(payload.get("driverId"))
    driver_phone = clean_text(payload.get("driverPhone"))
    destination_id = clean_text(payload.get("destinationId"))
    empty_weight = parse_float(payload.get("emptyWeightKg"))
    driver_selfie_data_url = payload.get("driverSelfieDataUrl")
    driver_signature_data_url = payload.get("driverSignatureDataUrl")

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
        destination = db.execute("SELECT * FROM destinations WHERE id = ?", (destination_id,)).fetchone()
        if not destination:
            raise AppError("El destino seleccionado no existe.", 404)

        carrier = db.execute("SELECT * FROM carriers WHERE id = ?", (carrier_id,)).fetchone()
        if not carrier:
            raise AppError("La transportadora seleccionada no existe.", 404)

        duplicate = db.execute(
            "SELECT id FROM vehicles WHERE plate = ? AND status = 'QUEUED' LIMIT 1",
            (plate,),
        ).fetchone()
        if duplicate:
            raise AppError(f"La placa {plate} ya esta enturnada.", 409)

        next_position = db.execute(
            "SELECT COALESCE(MAX(queue_position), 0) + 1 FROM vehicles WHERE status = 'QUEUED'"
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
                empty_weight_kg, driver_selfie_url, driver_signature_url, destination_id, city, zone,
                status, quality_status, queue_position, created_at, registration_channel, gps_lat, gps_lng,
                gps_distance_m, public_tracking_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'QUEUED', ?, ?, ?, ?, ?, ?, ?, ?)
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
                destination["id"],
                destination["city"],
                destination["zone"],
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
        in_use = db.execute(
            "SELECT id FROM vehicles WHERE destination_id = ? AND status = 'QUEUED' LIMIT 1",
            (destination_id,),
        ).fetchone()
        if in_use:
            raise AppError("No se puede borrar un destino usado por vehiculos enturnados.", 409)
        db.execute("DELETE FROM destinations WHERE id = ?", (destination_id,))


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


def add_user(payload: Dict[str, Any]) -> None:
    username = clean_text(payload.get("username")).lower()
    full_name = clean_text(payload.get("fullName"))
    role = clean_text(payload.get("role")).upper()
    password = str(payload.get("password") or "").strip()
    if not all([username, full_name, role, password]):
        raise AppError("Usuario, nombre, rol y clave son obligatorios.", 400)
    if role not in VALID_ROLES:
        raise AppError("El rol indicado no es valido.", 400)
    if len(password) < 8:
        raise AppError("La clave debe tener al menos 8 caracteres.", 400)
    with get_connection() as db:
        exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            raise AppError("Ese usuario ya existe.", 409)
        db.execute(
            """
            INSERT INTO users (id, username, full_name, role, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (create_id(), username, full_name, role, hash_password(password), now_iso()),
        )


def assign_vehicle(vehicle_id: str) -> None:
    with get_connection() as db:
        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ? AND status = 'QUEUED'", (vehicle_id,)).fetchone()
        if not vehicle:
            raise AppError("El vehiculo no esta enturnado o no existe.", 404)
        if (vehicle["quality_status"] or QUALITY_PENDING) != QUALITY_APPROVED:
            raise AppError("Solo puedes asignar viaje a vehiculos con calidad aprobada.", 409)
        db.execute(
            "UPDATE vehicles SET status = 'ASSIGNED', assigned_at = ?, queue_position = NULL WHERE id = ?",
            (now_iso(), vehicle_id),
        )
        compact_queue(db)


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


def update_site_settings(payload: Dict[str, Any]) -> None:
    site_name = clean_text(payload.get("siteName")) or "Planta principal"
    site_lat = clean_text(payload.get("siteLat"))
    site_lng = clean_text(payload.get("siteLng"))
    radius_value = parse_float(payload.get("siteRadiusM"))
    geofence_enabled = "1" if payload.get("geofenceEnabled", True) else "0"

    if site_lat:
        parse_float(site_lat)
    if site_lng:
        parse_float(site_lng)
    if radius_value is None or radius_value <= 0:
        raise AppError("El radio GPS debe ser mayor a cero.", 400)

    with get_connection() as db:
        set_settings_values(
            db,
            {
                "site_name": site_name,
                "site_lat": site_lat,
                "site_lng": site_lng,
                "site_radius_m": str(int(radius_value)),
                "geofence_enabled": geofence_enabled,
            },
        )


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def validate_geofence(payload: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    gps_lat = parse_float(payload.get("gpsLat"))
    gps_lng = parse_float(payload.get("gpsLng"))
    with get_connection() as db:
        settings = get_settings_map(db)
    enabled = settings.get("geofence_enabled", "1") == "1"
    if not enabled:
        return gps_lat, gps_lng, None
    if not settings.get("site_lat") or not settings.get("site_lng"):
        raise AppError("La geocerca aun no esta configurada por logistica.", 409)
    if gps_lat is None or gps_lng is None:
        raise AppError("Debes habilitar el GPS para registrarte en planta.", 409)
    site_lat = parse_float(settings.get("site_lat")) or 0.0
    site_lng = parse_float(settings.get("site_lng")) or 0.0
    radius = parse_float(settings.get("site_radius_m")) or 180.0
    distance = haversine_distance_m(gps_lat, gps_lng, site_lat, site_lng)
    if distance > radius:
        raise AppError(f"Estas fuera del radio permitido de planta. Distancia detectada: {int(distance)} m.", 409)
    return gps_lat, gps_lng, distance


def public_register(payload: Dict[str, Any]) -> Dict[str, Any]:
    gps_lat, gps_lng, gps_distance = validate_geofence(payload)
    created = create_vehicle(payload, "QR", gps_lat, gps_lng, gps_distance)
    return build_public_tracking(created["trackingToken"])


def build_public_tracking(token: str) -> Dict[str, Any]:
    with get_connection() as db:
        vehicle = db.execute(
            "SELECT * FROM vehicles WHERE public_tracking_token = ?",
            (token,),
        ).fetchone()
        if not vehicle:
            raise AppError("No se encontro el turno solicitado.", 404)
        queued_rows = db.execute(
            "SELECT * FROM vehicles WHERE status = 'QUEUED' ORDER BY queue_position, created_at"
        ).fetchall()
        turn_positions = calculate_turn_positions(queued_rows)
        latest_inspections = load_latest_inspections(db)
        front_vehicle = queued_rows[0] if queued_rows else None
    return {
        "vehicle": serialize_vehicle(vehicle, turn_positions, latest_inspections),
        "queueSize": len(queued_rows),
        "currentTurnPosition": turn_positions.get(vehicle["id"]),
        "frontOfQueue": serialize_vehicle(front_vehicle, turn_positions, latest_inspections) if front_vehicle else None,
    }


def get_public_config(origin: str) -> Dict[str, Any]:
    with get_connection() as db:
        settings = get_settings_map(db)
        carriers = [
            serialize_carrier(row)
            for row in db.execute("SELECT * FROM carriers ORDER BY name").fetchall()
        ]
        destinations = [
            serialize_destination(row)
            for row in db.execute("SELECT * FROM destinations ORDER BY zone, city").fetchall()
        ]
        queued_rows = db.execute(
            "SELECT * FROM vehicles WHERE status = 'QUEUED' ORDER BY queue_position, created_at"
        ).fetchall()
        turn_positions = calculate_turn_positions(queued_rows)
        latest_inspections = load_latest_inspections(db)
    return {
        "siteName": settings.get("site_name", ""),
        "geofenceEnabled": settings.get("geofence_enabled", "1") == "1",
        "siteConfigured": bool(settings.get("site_lat") and settings.get("site_lng")),
        "siteRadiusM": settings.get("site_radius_m", "180"),
        "registrationUrl": f"{origin}/driver.html",
        "carriers": carriers,
        "destinations": destinations,
        "liveQueue": [
            serialize_vehicle(row, turn_positions, latest_inspections)
            for row in queued_rows[:12]
        ],
    }


def build_findings_summary(checklist: Dict[str, Any]) -> str:
    findings = []
    for key, item in checklist.items():
        if isinstance(item, dict) and clean_text(item.get("status")).upper() == "NO_CUMPLE":
            findings.append(clean_text(item.get("label")) or key)
    return ", ".join(findings[:6]) or "Inspeccion registrada"


def save_data_url_image(vehicle_id: str, inspection_id: str, item_key: str, index: int, data_url: str) -> str:
    try:
        header, encoded = data_url.split(",", 1)
    except ValueError as exc:
        raise AppError("Una evidencia enviada no tiene formato valido.", 400) from exc

    extension = "jpg"
    if "image/png" in header:
        extension = "png"
    elif "image/webp" in header:
        extension = "webp"
    try:
        content = base64.b64decode(encoded)
    except (binascii.Error, ValueError) as exc:
        raise AppError("No se pudo decodificar una evidencia fotografica.", 400) from exc

    vehicle_dir = UPLOADS_DIR / vehicle_id
    vehicle_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{inspection_id}_{item_key}_{index}.{extension}"
    path = vehicle_dir / filename
    path.write_bytes(content)
    return f"/uploads/{vehicle_id}/{filename}"


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
        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ? AND status = 'QUEUED'", (vehicle_id,)).fetchone()
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

        db.execute(
            """
            UPDATE vehicles
            SET quality_status = ?, last_quality_at = ?, status = ?, queue_position = ?, rejected_at = ?, rejection_reason = ?
            WHERE id = ?
            """,
            (decision, reviewed_at, new_status, new_queue_position, rejected_at, rejection_reason, vehicle_id),
        )
        compact_queue(db)


class Handler(BaseHTTPRequestHandler):
    server_version = "EnturnamientoVehiculos/2.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/healthz":
                self.send_json({"status": "ok", "time": now_iso()})
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
            if parsed.path == "/api/public/config":
                self.send_json(get_public_config(self.request_origin()))
                return
            if parsed.path.startswith("/api/public/tracking/"):
                token = parsed.path.rsplit("/", 1)[-1]
                self.send_json(build_public_tracking(unquote(token)))
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
        except sqlite3.Error as error:
            self.send_error_json(f"Error de base de datos: {error}", 500)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()

            if parsed.path == "/api/auth/login":
                self.login(payload)
                return
            if parsed.path == "/api/auth/logout":
                self.logout()
                return
            if parsed.path == "/api/public/register":
                self.send_json(public_register(payload), 201)
                return

            user = self.require_user()
            if not user:
                return

            if parsed.path == "/api/settings/site":
                self.require_role(user, ROLE_LOGISTICS)
                update_site_settings(payload)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            if parsed.path == "/api/destinations":
                self.require_role(user, ROLE_LOGISTICS)
                add_destination(payload)
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return
            if parsed.path == "/api/carriers":
                self.require_role(user, ROLE_LOGISTICS)
                add_carrier(payload)
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return
            if parsed.path == "/api/users":
                self.require_role(user, ROLE_LOGISTICS)
                add_user(payload)
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return
            if parsed.path == "/api/vehicles":
                self.require_role(user, ROLE_LOGISTICS)
                create_vehicle(payload, "DESK", None, None, None)
                self.send_json(get_user_state(user, self.request_origin()), 201)
                return

            vehicle_id, action = parse_vehicle_action(parsed.path)
            if action == "assign":
                self.require_role(user, ROLE_LOGISTICS)
                assign_vehicle(vehicle_id)
                self.send_json(get_user_state(user, self.request_origin()))
                return
            if action == "reject":
                self.require_role(user, ROLE_LOGISTICS)
                reject_vehicle(vehicle_id, clean_text(payload.get("reason")))
                self.send_json(get_user_state(user, self.request_origin()))
                return

            if parsed.path.startswith("/api/quality/") and parsed.path.endswith("/inspect"):
                self.require_role(user, ROLE_QUALITY)
                quality_vehicle_id = parsed.path.split("/")[3]
                save_quality_inspection(quality_vehicle_id, user, payload)
                self.send_json(get_user_state(self.get_fresh_user(user["id"]), self.request_origin()))
                return

            self.send_error_json("Ruta no encontrada.", 404)
        except AppError as error:
            self.send_error_json(error.message, error.status)
        except sqlite3.Error as error:
            self.send_error_json(f"Error de base de datos: {error}", 500)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        try:
            user = self.require_user()
            if not user:
                return
            self.require_role(user, ROLE_LOGISTICS)

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
            self.send_error_json("Ruta no encontrada.", 404)
        except AppError as error:
            self.send_error_json(error.message, error.status)
        except sqlite3.Error as error:
            self.send_error_json(f"Error de base de datos: {error}", 500)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.add_common_headers()
        self.end_headers()

    def login(self, payload: Dict[str, Any]) -> None:
        username = clean_text(payload.get("username")).lower()
        password = str(payload.get("password") or "")
        if not username or not password:
            raise AppError("Usuario y clave son obligatorios.", 400)
        with get_connection() as db:
            user = db.execute("SELECT * FROM users WHERE username = ? AND active = 1", (username,)).fetchone()
            if not user or not verify_password(password, user["password_hash"]):
                raise AppError("Credenciales invalidas.", 401)
            token = create_session(db, user["id"])
            state = build_auth_payload(user, self.request_origin(), token)
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

    def send_error_json(self, message: str, status: int) -> None:
        self.send_json({"error": message}, status)

    def add_common_headers(self, content_type: Optional[str] = None) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
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


def main() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Aplicacion lista en http://localhost:{PORT}")
    print(f"Base de datos SQLite: {DB_PATH}")
    print("UI: Inter font, pill tabs, lift cards, spring modal — v2.1")
    server.serve_forever()


if __name__ == "__main__":
    main()

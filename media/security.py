import socket
import struct

from django.conf import settings


class PermanentMediaValidationError(ValueError):
    pass


def validate_file_signature(path, content_type):
    with open(path, "rb") as media_file:
        header = media_file.read(32)
    checks = {
        "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
        "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": lambda data: data.startswith(b"RIFF") and data[8:12] == b"WEBP",
        "video/mp4": lambda data: data[4:8] == b"ftyp",
        "video/quicktime": lambda data: data[4:8] == b"ftyp",
        "audio/mp4": lambda data: data[4:8] == b"ftyp",
        "video/webm": lambda data: data.startswith(b"\x1aE\xdf\xa3"),
        "audio/webm": lambda data: data.startswith(b"\x1aE\xdf\xa3"),
        "audio/ogg": lambda data: data.startswith(b"OggS"),
        "audio/mpeg": lambda data: data.startswith(b"ID3") or data[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"},
        "audio/wav": lambda data: data.startswith(b"RIFF") and data[8:12] == b"WAVE",
    }
    if content_type not in checks or not checks[content_type](header):
        raise PermanentMediaValidationError("Signature du fichier incompatible avec le type MIME déclaré.")


def scan_file(path):
    if not settings.CLAMAV_ENABLED:
        return
    with socket.create_connection(
        (settings.CLAMAV_HOST, settings.CLAMAV_PORT), timeout=settings.CLAMAV_TIMEOUT_SECONDS
    ) as connection, open(path, "rb") as media_file:
        connection.settimeout(settings.CLAMAV_TIMEOUT_SECONDS)
        connection.sendall(b"zINSTREAM\0")
        while chunk := media_file.read(64 * 1024):
            connection.sendall(struct.pack("!I", len(chunk)) + chunk)
        connection.sendall(struct.pack("!I", 0))
        response = connection.recv(4096).decode("utf-8", errors="replace")
    if "FOUND" in response:
        raise PermanentMediaValidationError("Fichier refusé par l'analyse antivirus.")
    if "OK" not in response:
        raise RuntimeError("Analyse antivirus indisponible ou incomplète.")

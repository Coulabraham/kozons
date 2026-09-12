import pytest

from media.security import PermanentMediaValidationError, validate_file_signature


def test_media_signature_validation(tmp_path):
    image = tmp_path / "image"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 24)
    validate_file_signature(image, "image/png")

    fake = tmp_path / "fake"
    fake.write_bytes(b"not a png")
    with pytest.raises(PermanentMediaValidationError):
        validate_file_signature(fake, "image/png")

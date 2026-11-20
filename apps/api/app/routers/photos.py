import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import Photo
from app.schemas.photo import PhotoDetail, PhotoOut
from app.services.exif import UnsupportedImage, read_image
from app.services.storage import LocalStorage, get_storage
from app.services.variants import all_variant_keys, make_variant, variant_key

router = APIRouter(prefix="/photos", tags=["photos"])

CHUNK = 1024 * 1024
# A photo's files never change after upload (a new upload gets a new id),
# so browsers and later CloudFront can keep them for a year.
IMMUTABLE = {"Cache-Control": "public, max-age=31536000, immutable"}


@router.post("", response_model=PhotoDetail, status_code=status.HTTP_201_CREATED)
def upload_photo(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    storage: LocalStorage = Depends(get_storage),
) -> Photo:
    """Saves the original, reads its EXIF and creates the photo row."""
    data = _read_limited(file, settings.max_upload_mb * 1024 * 1024)

    try:
        info = read_image(data)
    except UnsupportedImage as e:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"{e}. Use JPEG, HEIC or PNG")

    photo_id = uuid.uuid4()
    key = f"originals/{photo_id}{info.extension}"

    storage.save(key, data)
    photo = Photo(
        id=photo_id,
        storage_key=key,
        original_filename=Path(file.filename or "upload").name,
        content_type=info.content_type,
        size_bytes=len(data),
        width=info.width,
        height=info.height,
        taken_at=info.taken_at,
        camera_make=info.camera_make,
        camera_model=info.camera_model,
        lens_model=info.lens_model,
        focal_length_mm=info.focal_length_mm,
        focal_35mm=info.focal_35mm,
        aperture=info.aperture,
        shutter=info.shutter,
        iso=info.iso,
        exif_raw=info.exif_raw,
    )
    try:
        session.add(photo)
        session.commit()
    except Exception:
        # No row means nothing points at the file, so don't leave it behind.
        session.rollback()
        storage.delete(key)
        raise

    session.refresh(photo)
    return photo


@router.get("", response_model=list[PhotoOut])
def list_photos(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
) -> list[Photo]:
    """Newest first by when the photo was taken. Photos without a date come last."""
    stmt = (
        select(Photo)
        .order_by(Photo.taken_at.desc().nulls_last(), Photo.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(stmt))


@router.get("/{photo_id}", response_model=PhotoDetail)
def get_photo(photo_id: uuid.UUID, session: Session = Depends(get_session)) -> Photo:
    return _get_or_404(session, photo_id)


@router.get("/{photo_id}/file")
def get_photo_file(
    photo_id: uuid.UUID,
    size: Literal["original", "display", "thumb"] = "original",
    session: Session = Depends(get_session),
    storage: LocalStorage = Depends(get_storage),
) -> FileResponse:
    """The image itself. `thumb` (640px) for grids, `display` (2048px) for the photo page,
    `original` for the uploaded file. On AWS this becomes CloudFront or a presigned URL."""
    photo = _get_or_404(session, photo_id)
    if not storage.exists(photo.storage_key):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "file missing from storage")

    if size == "original":
        return FileResponse(
            storage.path(photo.storage_key), media_type=photo.content_type, headers=IMMUTABLE
        )

    key = variant_key(photo.id, size)
    if not storage.exists(key):
        storage.save(key, make_variant(storage.read(photo.storage_key), size))
    return FileResponse(storage.path(key), media_type="image/jpeg", headers=IMMUTABLE)


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: uuid.UUID,
    session: Session = Depends(get_session),
    storage: LocalStorage = Depends(get_storage),
) -> Response:
    photo = _get_or_404(session, photo_id)
    key = photo.storage_key
    session.delete(photo)
    session.commit()
    # After the commit, so a failed delete never loses a file that is still listed.
    for k in [key, *all_variant_keys(photo_id)]:
        storage.delete(k)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_or_404(session: Session, photo_id: uuid.UUID) -> Photo:
    photo = session.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "photo not found")
    return photo


def _read_limited(file: UploadFile, max_bytes: int) -> bytes:
    """Reads the upload in chunks and stops as soon as it is too big."""
    chunks, total = [], 0
    while chunk := file.file.read(CHUNK):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                413,
                f"file is larger than {settings.max_upload_mb} MB",
            )
        chunks.append(chunk)
    if total == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty file")
    return b"".join(chunks)

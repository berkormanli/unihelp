import fastapi

from src.api.dependencies.repository import get_repository
from src.models.schemas.post import PhotoInDB
from src.repository.crud.photo import PhotoCRUDRepository
from src.utilities.exceptions.http.exc_404 import http_404_exc_photo_id_not_found_request
from src.utilities.exceptions.database import EntityDoesNotExist

router = fastapi.APIRouter(prefix="/photos", tags=["photos"])

@router.post("", response_model=PhotoInDB)
async def create_photo(
    url: str,
    post_id: int,
    photo_repo: PhotoCRUDRepository = fastapi.Depends(get_repository(PhotoCRUDRepository)),
):
    db_photo = await photo_repo.create_photo(url, post_id)
    return PhotoInDB.from_orm(db_photo)

@router.get("/{photo_id}", response_model=PhotoInDB)
async def read_photo(
    photo_id: int,
    photo_repo: PhotoCRUDRepository = fastapi.Depends(get_repository(PhotoCRUDRepository)),
):
    try:
        db_photo = await photo_repo.read_photo(photo_id)
    except EntityDoesNotExist:
        raise await http_404_exc_photo_id_not_found_request(photo_id=photo_id)
    return PhotoInDB.from_orm(db_photo)

@router.get("/post/{post_id}", response_model=list[PhotoInDB])
async def read_photos_by_post_id(
    post_id: int,
    photo_repo: PhotoCRUDRepository = fastapi.Depends(get_repository(PhotoCRUDRepository)),
):
    db_photos = await photo_repo.read_photos_by_post_id(post_id)
    return [PhotoInDB.from_orm(photo) for photo in db_photos]

@router.patch("/{photo_id}", response_model=PhotoInDB)
async def update_photo(
    photo_id: int,
    url: str,
    photo_repo: PhotoCRUDRepository = fastapi.Depends(get_repository(PhotoCRUDRepository)),
):
    try:
        db_photo = await photo_repo.update_photo(photo_id, url)
    except EntityDoesNotExist:
        raise await http_404_exc_photo_id_not_found_request(photo_id=photo_id)
    return PhotoInDB.from_orm(db_photo)

@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: int,
    photo_repo: PhotoCRUDRepository = fastapi.Depends(get_repository(PhotoCRUDRepository)),
):
    try:
        await photo_repo.delete_photo(photo_id)
    except EntityDoesNotExist:
        raise await http_404_exc_photo_id_not_found_request(photo_id=photo_id)
    return {"message": "Photo deleted successfully"}
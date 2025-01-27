from sqlalchemy import select
from src.models.db.tag import Tag
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists

class TagCRUDRepository(BaseCRUDRepository):
    async def create_tag(self, name: str) -> Tag:
        # Check if tag already exists
        existing = await self.get_tag_by_name(name)
        if existing:
            return existing
            
        tag = Tag(name=name.lower())
        self.async_session.add(tag)
        await self.async_session.commit()
        return tag

    async def get_tag_by_name(self, name: str) -> Tag | None:
        stmt = select(Tag).where(Tag.name == name.lower())
        result = await self.async_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_tags(self) -> list[Tag]:
        stmt = select(Tag)
        result = await self.async_session.execute(stmt)
        return list(result.scalars().all())

    async def add_tags_to_post(self, post_id: int, tag_names: list[str]) -> list[Tag]:
        tags = []
        for name in tag_names:
            tag = await self.create_tag(name)
            tags.append(tag)
        
        # Get the post and add tags
        post = await self.async_session.get(Post, post_id)
        if not post:
            raise EntityDoesNotExist(f"Post with id {post_id} not found")
            
        post.tags.extend(tags)
        await self.async_session.commit()
        return tags
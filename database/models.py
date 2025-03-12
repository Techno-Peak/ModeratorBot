from sqlalchemy import Column, BigInteger, String, Boolean, Integer, select
from database.sessions import AsyncSessionLocal
from .base import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger)  # Telegram User ID
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_permission = Column(Boolean, default=False)
    count = Column(Integer, default=0)

    @classmethod
    async def get_or_create(cls, chat_id: int, username: str = None, first_name: str = None, 
                            last_name: str = None, is_admin: bool = False, is_permission: bool = False):
        async with AsyncSessionLocal() as session:
            stmt = select(cls).where(cls.chat_id == chat_id)
            result = await session.execute(stmt)
            existing_user = result.scalars().first()

            if existing_user:
                return existing_user
            
            new_user = cls(
                chat_id=chat_id,
                username=username,
                first_name=first_name or "Noma'lum",
                last_name=last_name,
                is_admin=is_admin,
                is_permission=is_permission
            )
            session.add(new_user)
            await session.commit()
            return new_user


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Telegram Group ID
    chat_id = Column(BigInteger)
    title = Column(String, nullable=False)
    required_members = Column(Integer, default=0)
    required_channel = Column(BigInteger, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_activate = Column(Boolean, default=False)

    @classmethod
    async def get_or_create(cls, chat_id: int, title: str = None):
        async with AsyncSessionLocal() as session:
            stmt = select(cls).where(cls.chat_id == chat_id)
            result = await session.execute(stmt)
            existing_user = result.scalars().first()

            if existing_user:
                return existing_user

            new_group = cls(
                chat_id=chat_id,
                title=title
            )
            session.add(new_group)
            await session.commit()
            return new_group

    async def activate(self):
        async with AsyncSessionLocal() as session:
            self.is_activate = False if self.is_activate else True
            session.add(self)
            await session.commit()
            return self

    @classmethod
    async def _is_activate(cls, chat_id):
        async with AsyncSessionLocal() as session:
            stmt = select(cls).where(cls.chat_id == chat_id)
            result = await session.execute(stmt)
            _group = result.scalars().first()
            
            if _group is not None:
                return True


class BlockedWord(Base):
    __tablename__ = "blocked_word"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
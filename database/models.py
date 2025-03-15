from sqlalchemy import Column, BigInteger, String, Boolean, Integer, select, ForeignKey, func
from sqlalchemy.orm import relationship

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
    is_private = Column(Boolean, default=False, nullable=True)
    count = Column(Integer, default=0)

    @classmethod
    async def get_or_create(cls, chat_id: int, username: str = None, first_name: str = None, 
                            last_name: str = None, is_admin: bool = False, is_permission: bool = False,
                            is_private: bool = False):
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

    @classmethod
    async def get_user(cls, chat_id: int):
        async with AsyncSessionLocal() as session:
            stmt = select(cls).where(cls.chat_id == chat_id)
            result = await session.execute(stmt)
            existing_user = result.scalars().first()

            if not existing_user:
                return None
            return existing_user

    async def update_is_private(self, is_private: bool = False):
        async with AsyncSessionLocal() as session:
            self.is_private = is_private
            session.add(self)
            await session.commit()
            return self

    async def update_is_admin(self, is_admin: bool):
        async with AsyncSessionLocal() as session:
            self.is_admin = is_admin
            session.add(self)
            await session.commit()
            return self


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
        
    @classmethod
    async def get_group(cls, chat_id: int):
         async with AsyncSessionLocal() as session:
            stmt = select(cls).where(cls.chat_id == chat_id)
            result = await session.execute(stmt)
            existing_user = result.scalars().first()

            if existing_user:
                return existing_user
            return None

    @classmethod
    async def _is_activate(cls, chat_id):
        async with AsyncSessionLocal() as session:
            stmt = select(cls).where(cls.chat_id == chat_id)
            result = await session.execute(stmt)
            _group = result.scalars().first()

            if _group is not None:
                return True

    async def activate(self):
        async with AsyncSessionLocal() as session:
            self.is_activate = False if self.is_activate else True
            session.add(self)
            await session.commit()
            return self

    async def add_channel(self, channel_id):
        async with AsyncSessionLocal() as session:
            self.required_channel = channel_id
            session.add(self)
            await session.commit()
            return self

    async def remove_channel(self, channel_id):
        async with AsyncSessionLocal() as session:
            self.required_channel = None
            session.add(self)
            await session.commit()
            return self

    async def updated_required_members(self, count: int = 0):
        async with AsyncSessionLocal() as session:
            self.required_members = count
            session.add(self)
            await session.commit()
            return self


class BlockedWord(Base):
    __tablename__ = "blocked_word"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)


    @classmethod
    async def get_blocked_words(cls):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(cls.word))
            words = result.scalars().all() 
            return list(words)

    @classmethod
    async def create(cls, word: str):
        async with AsyncSessionLocal() as session:
            new_word = cls(
                word=word
            )
            session.add(new_word)
            await session.commit()
            return new_word


class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_chat_id = Column(BigInteger, nullable=False)  # Taklif qilgan odam
    group_chat_id = Column(BigInteger, nullable=False)  # Qaysi guruhga qo‘shilgan
    count = Column(Integer, default=0)

    histories = relationship("InviteHistory", backref="invite", lazy="joined")

    @classmethod
    async def get_invite(cls, group_chat_id: int, user_chat_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(cls).where(
                    cls.group_chat_id == group_chat_id,
                    cls.user_chat_id == user_chat_id
                )
            )
            invite = result.scalars().first()
            if not invite:
                invite = cls(
                    group_chat_id=group_chat_id,
                    user_chat_id=user_chat_id
                )
                session.add(invite)
                await session.commit()
            return invite

    async def add_invite(self, invited_chat_id: int):
        """Agar invited_chat_id oldin taklif qilingan bo‘lsa, qo‘shilmaydi."""
        async with AsyncSessionLocal() as session:
            try:
                # ✅ Avval taklif qilinganlarni ro‘yxat sifatida olish
                invited_ids = {history.invited_chat_id for history in self.histories}
                for history in self.histories:
                    if history.invited_chat_id == invited_chat_id \
                        and history.group_chat_id == self.group_chat_id:
                        return self

                    if self.user_chat_id == invited_chat_id:
                        return self

                if invited_chat_id in invited_ids:
                    return self  # Agar mavjud bo'lsa, qo‘shmaymiz
            except Exception as e:
                return self

            # ✅ Yangi odamni qo‘shish
            self.count += 1
            session.add(self)

            history = InviteHistory(
                invite_id=self.id,
                user_chat_id=self.user_chat_id,
                invited_chat_id=invited_chat_id,
                group_chat_id=self.group_chat_id
            )
            session.add(history)

            await session.commit()
            return self

    @classmethod
    async def get_top_invites(cls, limit: int = 10):
        """Eng ko‘p odam qo‘shgan foydalanuvchilarni qaytaradi."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(cls.user_chat_id, func.sum(cls.count))
                .group_by(cls.user_chat_id)
                .order_by(func.sum(cls.count).desc())
                .limit(limit)
            )
            return result.all()

    @classmethod
    async def get_user_invite_count(cls, user_chat_id: int):
        """Berilgan foydalanuvchi nechta odam qo‘shganligini qaytaradi."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.sum(cls.count)).where(cls.user_chat_id == user_chat_id)
            )
            return result.scalar() or 0  # Agar natija bo‘lmasa, 0 qaytaradi


class InviteHistory(Base):
    __tablename__ = "invite_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invite_id = Column(Integer, ForeignKey("invites.id"), nullable=False)  # Invite bilan bog‘lanish
    user_chat_id = Column(BigInteger, nullable=False)  # Taklif qilgan odam
    invited_chat_id = Column(BigInteger, nullable=False)  # Taklif qilingan odam
    group_chat_id = Column(BigInteger, nullable=False) # guruh

from sqlalchemy import Column, BigInteger, String, Boolean, Integer, select, ForeignKey, func, update, delete, text, or_
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
    is_super_admin = Column(Boolean, default=False, nullable=True)
    count = Column(Integer, default=0)

    @classmethod
    async def get_private_user_count(cls):
        async with AsyncSessionLocal() as session:
            res = await session.scalar(select(func.count()).select_from(cls).where(cls.is_private == True))
        return res

    @classmethod
    async def get_admins(cls):
        async with AsyncSessionLocal() as session:
            res = await session.scalars(
                select(cls).where(cls.is_admin == True, or_(cls.is_super_admin == False, cls.is_super_admin.is_(None)))
            )
            return res.all()  # Ro'yxat qaytaradi

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
        
    @classmethod
    async def get_private_users(cls):
        async with AsyncSessionLocal() as session:
            stmt = select(cls).where(cls.is_private == True)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update_is_private(self, is_private: bool = False):
        async with AsyncSessionLocal() as session:
            self.is_private = is_private
            session.add(self)
            await session.commit()
            return self

    async def update_is_admin(self, is_admin: bool, is_super_admin: bool = False):
        async with AsyncSessionLocal() as session:
            self.is_admin = is_admin
            self.is_super_admin = is_super_admin
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
    is_activate = Column(Boolean, default=True)

    @classmethod
    async def get_group_count(cls):
        async with AsyncSessionLocal() as session:
            res = await session.scalar(select(func.count()).select_from(cls))
            return res

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
    async def get_all_groups(cls):
        async with AsyncSessionLocal() as session:
            stmt = select(cls)
            result = await session.execute(stmt)
            return result.scalars().all()

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

    @classmethod
    async def delete(cls, word: str):
        async with AsyncSessionLocal() as session:
            # Bazadan so‘zni topamiz
            stmt = select(cls).where(cls.word == word)
            result = await session.execute(stmt)
            word_obj = result.scalar_one_or_none()

            if word_obj:
                await session.delete(word_obj)
                await session.commit()
                return True  # O‘chirildi
            return False  # So‘z topilmadi


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
            # ✅ Yangi odamni qo‘shish
            self.count += 1
            session.add(self)
            await session.commit()
            return self


    @classmethod
    async def get_top_invites(cls, group_chat_id: int, limit: int = 10):
        """Faqat bitta guruh ichida eng ko‘p odam qo‘shganlarni qaytaradi."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(cls.user_chat_id, cls.count)
                .where(cls.group_chat_id == group_chat_id)  # 🔥 Faqat bitta guruhni tekshirish
                .order_by(cls.count.desc())
                .limit(limit)
            )
            return result.all()

    @classmethod
    async def get_user_invite_count(cls, user_chat_id: int, group_chat_id: int):
        """Foydalanuvchining faqat shu guruhga nechta odam qo‘shganini qaytaradi."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(func.sum(cls.count)).where(
                    cls.user_chat_id == user_chat_id,
                    cls.group_chat_id == group_chat_id  # 🔥 Guruhni ham tekshiramiz
                )
            )
            return result.scalar() or 0  # Agar natija bo‘lmasa, 0 qaytaradi

    @classmethod
    async def reset_user_invite_count(cls, user_chat_id: int, group_chat_id: int):
        """Foydalanuvchining shu guruhdagi takliflarini 0 ga tushiradi."""
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(cls).where(
                    cls.user_chat_id == user_chat_id,
                    cls.group_chat_id == group_chat_id
                ).values(count=0)
            )
            await session.commit()

    @classmethod
    async def reset_all_invites(cls, group_chat_id: int):
        """Guruhdagi barcha odamlarning takliflarini 0 ga tushiradi."""
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(cls)
                .where(cls.group_chat_id == group_chat_id)
                .values(count=0)  # invite_count maydonini 0 ga o‘zgartiramiz
            )
            await session.commit()

    @classmethod
    async def create(cls, user_chat_id: int, group_chat_id: int, count: int = 0):
        """Foydalanuvchini yaratish (agar bo'lmasa) yoki ball qo'shish."""
        async with AsyncSessionLocal() as session:
            invite = Invite(user_chat_id=user_chat_id, group_chat_id=group_chat_id, count=count)
            session.add(invite)
            await session.commit()

    @classmethod
    async def update_invite_count(cls, user_id: int, group_chat_id: int, new_invite_count: int):
        """Foydalanuvchining takliflar/balini yangilash."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(cls).where(cls.user_chat_id == user_id, cls.group_chat_id == group_chat_id)
            )
            invite = result.scalar()

            if invite:
                invite.count = new_invite_count
                await session.commit()
            else:
                await cls.create(user_id, group_chat_id, new_invite_count)


class InviteHistory(Base):
    __tablename__ = "invite_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invite_id = Column(Integer, ForeignKey("invites.id"), nullable=False)  # Invite bilan bog‘lanish
    user_chat_id = Column(BigInteger, nullable=False)  # Taklif qilgan odam
    invited_chat_id = Column(BigInteger, nullable=False)  # Taklif qilingan odam
    group_chat_id = Column(BigInteger, nullable=False) # guruh

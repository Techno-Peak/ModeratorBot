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


class BlockedWord(Base):
    __tablename__ = "blocked_word"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
# class Warning(Base):
#     __tablename__ = "warnings"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
#     group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
#     reason = Column(Text, nullable=False)
#     warned_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
#
# class Ban(Base):
#     __tablename__ = "bans"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
#     group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
#     banned_by = Column(BigInteger, ForeignKey("users.id"))
#     reason = Column(Text, nullable=True)
#     banned_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
#
# class MessageLog(Base):
#     __tablename__ = "messages"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
#     group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
#     content = Column(Text, nullable=False)
#     message_type = Column(String, nullable=False)  # spam, swearing, advertisement
#     detected_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
#
# class InvitedUser(Base):
#     __tablename__ = "invited_users"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     inviter_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
#     invited_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
#     group_id = Column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"))
#     invited_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

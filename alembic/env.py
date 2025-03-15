import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from alembic import context
from database.models import Base  # <-- o'z loyihangizdagi model faylini import qiling
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Alembic configuration
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for autogenerate
target_metadata = Base.metadata  # <-- Model metadata ni to‘g‘ri bog‘laymiz

# Asinxron engine yaratish
async_engine = create_async_engine(DATABASE_URL, future=True)

async def run_migrations_online():
    """Asinxron migratsiyalarni bajarish."""
    async with async_engine.connect() as connection:
        await connection.run_sync(lambda conn: context.configure(
            connection=conn, target_metadata=target_metadata
        ))
        await connection.run_sync(lambda conn: context.run_migrations())

async def run_migrations():
    """Migratsiyalarni ishga tushirish."""
    if context.is_offline_mode():
        context.configure(url=DATABASE_URL, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    else:
        await run_migrations_online()

# Asinxron migratsiyalarni bajarish
asyncio.run(run_migrations())

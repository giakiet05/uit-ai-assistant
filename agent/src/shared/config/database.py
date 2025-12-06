from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Import settings from the same config package
from .settings import settings

# Check if database settings are available
if not hasattr(settings, 'database') or not settings.database.SQLALCHEMY_DATABASE_URL:
    raise ValueError("Database settings are not configured in settings.py")

# Database connection URL
ASYNC_SQLALCHEMY_DATABASE_URL = settings.database.SQLALCHEMY_DATABASE_URL

# Create an async engine
# echo=True will log all SQL statements, useful for debugging
engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, echo=True, pool_size=5, max_overflow=10)

# Create a session local factory
# expire_on_commit=False prevents SQLAlchemy from expiring objects after commit,
# which can be useful when objects are still needed after a transaction.
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Base class for declarative class definitions
Base = declarative_base()

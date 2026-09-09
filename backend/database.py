import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import urlparse

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Log only host/db name, never credentials — the old version printed the
# full connection string (including password) straight into Render's logs.
_parsed = urlparse(DATABASE_URL)
print(f"CONNECTED DATABASE: {_parsed.hostname}/{_parsed.path.lstrip('/')}")

# TiDB Serverless requires TLS on its public endpoint. Passing an empty
# ssl dict tells pymysql to use Python's default certificate trust store
# (via ssl.create_default_context()) rather than a manually downloaded CA
# file — Let's Encrypt's root (ISRG Root X1) is already trusted there on
# any modern system, so no cert file needs to be shipped with the repo.
connect_args = {"ssl": {}}

# pool_pre_ping: checks each connection is alive before using it, and
# transparently reconnects if it's gone stale. TiDB Serverless closes idle
# connections after 5 minutes, so without this you'd hit random
# "Lost connection to MySQL server" errors on the first query after a lull.
# pool_recycle: proactively recycles connections before TiDB's 5-minute
# cutoff, so the pool never even offers a connection old enough to be dropped.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

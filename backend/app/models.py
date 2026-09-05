from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="editor", index=True)

class Show(Base):
    __tablename__ = "shows"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    synopsis: Mapped[str] = mapped_column(Text, default="")
    section: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    seasons: Mapped[list["Season"]] = relationship(back_populates="show", cascade="all, delete-orphan")

class Season(Base):
    __tablename__ = "seasons"
    id: Mapped[int] = mapped_column(primary_key=True)
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    season_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255), default="")
    show: Mapped[Show] = relationship(back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship(back_populates="season", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("show_id", "season_number", name="uq_season_show_number"),)

class Episode(Base):
    __tablename__ = "episodes"
    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True)
    episode_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), index=True)
    content_group: Mapped[str] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    synopsis: Mapped[str] = mapped_column(Text, default="")
    season: Mapped[Season] = relationship(back_populates="episodes")
    artwork: Mapped[list["Artwork"]] = relationship(back_populates="episode", cascade="all, delete-orphan")
    # NOTE: deliberately NOT a UNIQUE constraint. The supplied seed data contains an
    # intentional (content_group, language) duplicate that the validation report and
    # publish gate must be able to detect and block on. An unconditional unique index
    # can't coexist with that row (CREATE UNIQUE INDEX fails against pre-existing
    # duplicates, regardless of migration ordering), so uniqueness for new writes is
    # enforced at the application layer (see check_episode + the advisory lock around
    # create/update in main.py) instead. This index exists purely to keep that
    # lookup query fast.
    __table_args__ = (Index("ix_episode_content_group_language", "content_group", "language"),)

class Artwork(Base):
    __tablename__ = "artwork"
    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    storage_key: Mapped[str] = mapped_column(String(500))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(Integer)
    episode: Mapped[Episode] = relationship(back_populates="artwork")
    __table_args__ = (UniqueConstraint("episode_id", "kind", name="uq_artwork_episode_kind"),)

class PublishRun(Base):
    __tablename__ = "publish_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), index=True)
    show_count: Mapped[int] = mapped_column(Integer, default=0)
    episode_count: Mapped[int] = mapped_column(Integer, default=0)
    catalogue_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

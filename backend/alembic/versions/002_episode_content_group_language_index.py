from alembic import op

revision = "002_ep_cg_lang_index"
down_revision = "001_initial"

def upgrade():
    # Non-unique on purpose: the seed data intentionally contains a (content_group,
    # language) duplicate that the validation report / publish gate must detect and
    # block on, so this can't be a UNIQUE index (see app/models.py comment). This
    # index exists only to keep the application-layer uniqueness check's lookup fast.
    op.create_index(
        "ix_episode_content_group_language", "episodes", ["content_group", "language"]
    )

def downgrade():
    op.drop_index("ix_episode_content_group_language", table_name="episodes")

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None

def upgrade():
    op.create_table('users',sa.Column('id',sa.Integer,primary_key=True),sa.Column('username',sa.String(80),nullable=False,unique=True),sa.Column('password_hash',sa.String(255),nullable=False),sa.Column('role',sa.String(20),nullable=False))
    op.create_table('shows',sa.Column('id',sa.Integer,primary_key=True),sa.Column('slug',sa.String(160),nullable=False,unique=True),sa.Column('title',sa.String(255),nullable=False),sa.Column('synopsis',sa.Text,nullable=False),sa.Column('section',sa.String(40)),sa.Column('status',sa.String(20),nullable=False),sa.Column('categories',sa.JSON,nullable=False),sa.Column('created_at',sa.DateTime(timezone=True)),sa.Column('updated_at',sa.DateTime(timezone=True)))
    op.create_table('seasons',sa.Column('id',sa.Integer,primary_key=True),sa.Column('show_id',sa.Integer,sa.ForeignKey('shows.id',ondelete='CASCADE'),nullable=False),sa.Column('season_number',sa.Integer,nullable=False),sa.Column('title',sa.String(255),nullable=False),sa.UniqueConstraint('show_id','season_number',name='uq_season_show_number'))
    op.create_table('episodes',sa.Column('id',sa.Integer,primary_key=True),sa.Column('episode_id',sa.String(80),nullable=False,unique=True),sa.Column('season_id',sa.Integer,sa.ForeignKey('seasons.id',ondelete='CASCADE'),nullable=False),sa.Column('episode_number',sa.Integer,nullable=False),sa.Column('title',sa.String(255),nullable=False),sa.Column('duration_seconds',sa.Integer),sa.Column('language',sa.String(10),nullable=False),sa.Column('content_group',sa.String(180),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('categories',sa.JSON,nullable=False),sa.Column('synopsis',sa.Text,nullable=False))
    op.create_table('artwork',sa.Column('id',sa.Integer,primary_key=True),sa.Column('episode_id',sa.Integer,sa.ForeignKey('episodes.id',ondelete='CASCADE'),nullable=False),sa.Column('kind',sa.String(20),nullable=False),sa.Column('storage_key',sa.String(500),nullable=False),sa.Column('width',sa.Integer,nullable=False),sa.Column('height',sa.Integer,nullable=False),sa.Column('size_bytes',sa.Integer,nullable=False),sa.UniqueConstraint('episode_id','kind',name='uq_artwork_episode_kind'))
    op.create_table('publish_runs',sa.Column('id',sa.Integer,primary_key=True),sa.Column('started_at',sa.DateTime(timezone=True)),sa.Column('completed_at',sa.DateTime(timezone=True)),sa.Column('triggered_by',sa.String(80),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('show_count',sa.Integer,nullable=False),sa.Column('episode_count',sa.Integer,nullable=False),sa.Column('catalogue_hash',sa.String(64)),sa.Column('error',sa.Text))
    for table,cols in [('shows',['slug','section','status']),('seasons',['show_id']),('episodes',['episode_id','season_id','language','content_group','status']),('artwork',['episode_id','kind']),('publish_runs',['status'])]:
        for col in cols: op.create_index(f'ix_{table}_{col}',table,[col])

def downgrade():
    for t in ['publish_runs','artwork','episodes','seasons','shows','users']: op.drop_table(t)

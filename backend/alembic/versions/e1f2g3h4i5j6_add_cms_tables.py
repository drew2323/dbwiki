"""add CMS tables: pages, page_versions, tree_nodes, backlinks, attachments

Revision ID: e1f2g3h4i5j6
Revises: d7e8f9g0h1i2
Create Date: 2025-11-21 00:00:00.000000

This migration adds the core CMS tables for wiki page management:
- pages: Wiki pages with draft content and metadata
- page_versions: Published version history
- tree_nodes: Hierarchical page organization per space
- backlinks: Internal link tracking between pages
- attachments: File attachments for pages
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e1f2g3h4i5j6'
down_revision = 'd7e8f9g0h1i2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pages table
    op.create_table(
        'pages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('space_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('slug', sa.String(length=500), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('draft_etag', sa.String(length=64), nullable=True),
        sa.Column('draft_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('draft_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['space_id'], ['spaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for pages table
    op.create_index('ix_pages_space_id', 'pages', ['space_id'])
    op.create_index('ix_pages_slug', 'pages', ['slug'])
    op.create_index('ix_pages_created_by', 'pages', ['created_by'])
    op.create_index('ix_pages_is_archived', 'pages', ['is_archived'])
    op.create_index('ix_pages_updated_at', 'pages', ['updated_at'])

    # Unique constraint: slug per space
    op.create_index('ix_pages_space_slug_unique', 'pages', ['space_id', 'slug'], unique=True)

    # Full-text search index on draft_text
    op.execute(
        "CREATE INDEX ix_pages_draft_text_fts ON pages USING GIN (to_tsvector('english', COALESCE(draft_text, '')))"
    )

    # Create page_versions table
    op.create_table(
        'page_versions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('page_id', sa.String(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('author_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for page_versions table
    op.create_index('ix_page_versions_page_id', 'page_versions', ['page_id'])
    op.create_index('ix_page_versions_author_id', 'page_versions', ['author_id'])
    op.create_index('ix_page_versions_created_at', 'page_versions', ['created_at'])

    # Unique constraint: version_number per page
    op.create_index('ix_page_versions_page_version_unique', 'page_versions', ['page_id', 'version_number'], unique=True)

    # Full-text search index on content_text
    op.execute(
        "CREATE INDEX ix_page_versions_content_text_fts ON page_versions USING GIN (to_tsvector('english', content_text))"
    )

    # Create tree_nodes table
    op.create_table(
        'tree_nodes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('space_id', sa.String(), nullable=False),
        sa.Column('page_id', sa.String(), nullable=True),  # NULL for root sentinel node
        sa.Column('parent_id', sa.String(), nullable=True),  # NULL for root node
        sa.Column('position', sa.Integer(), nullable=False),  # Gapped positioning (1024, 2048, etc.)
        sa.ForeignKeyConstraint(['space_id'], ['spaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['tree_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for tree_nodes table
    op.create_index('ix_tree_nodes_space_id', 'tree_nodes', ['space_id'])
    op.create_index('ix_tree_nodes_page_id', 'tree_nodes', ['page_id'])
    op.create_index('ix_tree_nodes_parent_id', 'tree_nodes', ['parent_id'])
    op.create_index('ix_tree_nodes_position', 'tree_nodes', ['position'])

    # Unique constraint: page can appear only once per space tree
    op.create_index('ix_tree_nodes_space_page_unique', 'tree_nodes', ['space_id', 'page_id'], unique=True, postgresql_where=sa.text('page_id IS NOT NULL'))

    # Unique constraint: position per parent
    op.create_index('ix_tree_nodes_parent_position_unique', 'tree_nodes', ['parent_id', 'position'], unique=True, postgresql_where=sa.text('parent_id IS NOT NULL'))

    # Create backlinks table
    op.create_table(
        'backlinks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('src_page_id', sa.String(), nullable=False),
        sa.Column('dst_page_id', sa.String(), nullable=False),
        sa.Column('space_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['src_page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dst_page_id'], ['pages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['space_id'], ['spaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for backlinks table
    op.create_index('ix_backlinks_src_page_id', 'backlinks', ['src_page_id'])
    op.create_index('ix_backlinks_dst_page_id', 'backlinks', ['dst_page_id'])
    op.create_index('ix_backlinks_space_id', 'backlinks', ['space_id'])

    # Unique constraint: each link only once
    op.create_index('ix_backlinks_unique', 'backlinks', ['src_page_id', 'dst_page_id'], unique=True)

    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('space_id', sa.String(), nullable=False),
        sa.Column('page_id', sa.String(), nullable=True),  # NULL for orphaned attachments
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=255), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['space_id'], ['spaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for attachments table
    op.create_index('ix_attachments_space_id', 'attachments', ['space_id'])
    op.create_index('ix_attachments_page_id', 'attachments', ['page_id'])
    op.create_index('ix_attachments_created_by', 'attachments', ['created_by'])
    op.create_index('ix_attachments_created_at', 'attachments', ['created_at'])
    op.create_index('ix_attachments_sha256_hash', 'attachments', ['sha256_hash'])

    # Add is_public column to spaces table
    op.add_column('spaces', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_spaces_is_public', 'spaces', ['is_public'])

    # Create root sentinel nodes for existing spaces
    # PostgreSQL needs UUID generation for id column
    op.execute("""
        INSERT INTO tree_nodes (id, space_id, page_id, parent_id, position)
        SELECT gen_random_uuid(), id, NULL, NULL, 0
        FROM spaces
    """)


def downgrade() -> None:
    # Drop is_public from spaces
    op.drop_index('ix_spaces_is_public', table_name='spaces')
    op.drop_column('spaces', 'is_public')

    # Drop attachments table
    op.drop_index('ix_attachments_sha256_hash', table_name='attachments')
    op.drop_index('ix_attachments_created_at', table_name='attachments')
    op.drop_index('ix_attachments_created_by', table_name='attachments')
    op.drop_index('ix_attachments_page_id', table_name='attachments')
    op.drop_index('ix_attachments_space_id', table_name='attachments')
    op.drop_table('attachments')

    # Drop backlinks table
    op.drop_index('ix_backlinks_unique', table_name='backlinks')
    op.drop_index('ix_backlinks_space_id', table_name='backlinks')
    op.drop_index('ix_backlinks_dst_page_id', table_name='backlinks')
    op.drop_index('ix_backlinks_src_page_id', table_name='backlinks')
    op.drop_table('backlinks')

    # Drop tree_nodes table
    op.drop_index('ix_tree_nodes_parent_position_unique', table_name='tree_nodes')
    op.drop_index('ix_tree_nodes_space_page_unique', table_name='tree_nodes')
    op.drop_index('ix_tree_nodes_position', table_name='tree_nodes')
    op.drop_index('ix_tree_nodes_parent_id', table_name='tree_nodes')
    op.drop_index('ix_tree_nodes_page_id', table_name='tree_nodes')
    op.drop_index('ix_tree_nodes_space_id', table_name='tree_nodes')
    op.drop_table('tree_nodes')

    # Drop page_versions table
    op.execute("DROP INDEX IF EXISTS ix_page_versions_content_text_fts")
    op.drop_index('ix_page_versions_page_version_unique', table_name='page_versions')
    op.drop_index('ix_page_versions_created_at', table_name='page_versions')
    op.drop_index('ix_page_versions_author_id', table_name='page_versions')
    op.drop_index('ix_page_versions_page_id', table_name='page_versions')
    op.drop_table('page_versions')

    # Drop pages table
    op.execute("DROP INDEX IF EXISTS ix_pages_draft_text_fts")
    op.drop_index('ix_pages_space_slug_unique', table_name='pages')
    op.drop_index('ix_pages_updated_at', table_name='pages')
    op.drop_index('ix_pages_is_archived', table_name='pages')
    op.drop_index('ix_pages_created_by', table_name='pages')
    op.drop_index('ix_pages_slug', table_name='pages')
    op.drop_index('ix_pages_space_id', table_name='pages')
    op.drop_table('pages')

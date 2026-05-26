"""add professor_ratings

Revision ID: a7f1b29d4e10
Revises: e5a2d1f0c8b7
Create Date: 2026-05-26 00:00:00.000000

Professors live in Sanity (source of truth). We only store ratings in Postgres,
keyed by the Sanity document _id.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = 'a7f1b29d4e10'
down_revision: Union[str, None] = 'e5a2d1f0c8b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'professor_ratings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('professor_sanity_id', sa.String(), nullable=False),
        sa.Column('teacher_id', UUID(as_uuid=True), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('professor_sanity_id', 'teacher_id', name='uq_professor_rating_sanity_teacher'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_professor_rating_range'),
    )
    op.create_index('ix_professor_ratings_sanity_id', 'professor_ratings', ['professor_sanity_id'])
    op.create_index('ix_professor_ratings_teacher_id', 'professor_ratings', ['teacher_id'])


def downgrade() -> None:
    op.drop_index('ix_professor_ratings_teacher_id', table_name='professor_ratings')
    op.drop_index('ix_professor_ratings_sanity_id', table_name='professor_ratings')
    op.drop_table('professor_ratings')

"""add user_types and class_user_types

Revision ID: e5a2d1f0c8b7
Revises: c73348c4bbe7
Create Date: 2026-03-19 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision: str = 'e5a2d1f0c8b7'
down_revision: Union[str, None] = 'c73348c4bbe7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create user_types table
    op.create_table(
        'user_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(), nullable=False, unique=True),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
    )

    # 2. Add user_type_id to teachers
    op.add_column('teachers', sa.Column('user_type_id', UUID(as_uuid=True), sa.ForeignKey('user_types.id'), nullable=True))

    # 3. Create class_user_types join table
    op.create_table(
        'class_user_types',
        sa.Column('class_id', UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_type_id', UUID(as_uuid=True), sa.ForeignKey('user_types.id', ondelete='CASCADE'), primary_key=True),
    )

    # 4. Seed user_types
    admin_id = str(uuid.uuid4())
    profesor_colegio_id = str(uuid.uuid4())
    independiente_id = str(uuid.uuid4())

    op.execute(f"""
        INSERT INTO user_types (id, slug, label, is_admin) VALUES
        ('{admin_id}', 'admin', 'Administrador', true),
        ('{profesor_colegio_id}', 'profesor_colegio', 'Profesor de colegio', false),
        ('{independiente_id}', 'independiente', 'Educador independiente', false)
    """)

    # 5. Set all existing teachers to admin
    op.execute(f"UPDATE teachers SET user_type_id = '{admin_id}'")

    # 6. Make all existing classes visible to all non-admin user types
    op.execute(f"""
        INSERT INTO class_user_types (class_id, user_type_id)
        SELECT c.id, ut.id
        FROM classes c
        CROSS JOIN user_types ut
        WHERE ut.is_admin = false
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('class_user_types')
    op.drop_column('teachers', 'user_type_id')
    op.drop_table('user_types')

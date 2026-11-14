"""create admin demonstration views

Revision ID: c7d91e5a6b22
Revises: a0f2e79e1cf0
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c7d91e5a6b22"
down_revision: Union[str, Sequence[str], None] = "a0f2e79e1cf0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW v_active_found_items AS
        SELECT
            f.id AS item_id,
            f.reference_code,
            f.title,
            c.name AS category_name,
            s.name AS subcategory_name,
            l.name AS location_name,
            u.full_name AS reporter_name,
            f.found_at,
            f.status
        FROM found_items f
        JOIN categories c ON c.id = f.category_id
        LEFT JOIN subcategories s ON s.id = f.subcategory_id
        JOIN campus_locations l ON l.id = f.location_id
        JOIN users u ON u.id = f.reporter_id
        WHERE f.status = 'available'
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW v_category_listing_summary AS
        SELECT
            c.id AS category_id,
            c.name AS category_name,
            COUNT(f.id) AS total_items,
            SUM(CASE WHEN f.status = 'available' THEN 1 ELSE 0 END) AS available_items,
            SUM(CASE WHEN f.status = 'returned' THEN 1 ELSE 0 END) AS returned_items,
            SUM(CASE WHEN f.status = 'removed' THEN 1 ELSE 0 END) AS removed_items
        FROM categories c
        LEFT JOIN found_items f ON f.category_id = c.id
        GROUP BY c.id, c.name
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_category_listing_summary")
    op.execute("DROP VIEW IF EXISTS v_active_found_items")

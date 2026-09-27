"""Add trigram indexes for literal task substring search."""

from alembic import op

revision = "0002_task_search"
down_revision = "cb6d1164e4c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        "ix_tasks_title_trgm",
        "tasks",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_tasks_description_trgm",
        "tasks",
        ["description"],
        postgresql_using="gin",
        postgresql_ops={"description": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_description_trgm", table_name="tasks")
    op.drop_index("ix_tasks_title_trgm", table_name="tasks")
    # The extension may be shared by other schemas, so keep it installed.

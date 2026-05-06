"""add survey_date / survey_year / survey_week columns to polls

Revision ID: a4d1c0fe7b22
Revises: 18c4f48d6d2b
Create Date: 2026-05-06 14:30:00

raw `date` 컬럼은 보존(파싱 실패 케이스 추적용). 정규화된 날짜는 새 컬럼에 저장.
- survey_date: 단일 ISO 날짜로 환산 가능한 경우
- survey_year/week: NESDC 주간 집계 등 (year, week)만 있는 경우
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4d1c0fe7b22"
down_revision: Union[str, Sequence[str], None] = "18c4f48d6d2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("polls", sa.Column("survey_date", sa.Date(), nullable=True))
    op.add_column("polls", sa.Column("survey_year", sa.SmallInteger(), nullable=True))
    op.add_column("polls", sa.Column("survey_week", sa.SmallInteger(), nullable=True))
    op.create_index("ix_polls_survey_date", "polls", ["survey_date"])
    op.create_index("ix_polls_survey_year", "polls", ["survey_year"])


def downgrade() -> None:
    op.drop_index("ix_polls_survey_year", table_name="polls")
    op.drop_index("ix_polls_survey_date", table_name="polls")
    op.drop_column("polls", "survey_week")
    op.drop_column("polls", "survey_year")
    op.drop_column("polls", "survey_date")

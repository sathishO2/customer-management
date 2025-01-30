"""empty message

Revision ID: 168c87a98476
Revises: 55125d76adc3
Create Date: 2024-08-04 09:02:22.471546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '168c87a98476'
down_revision: Union[str, None] = '55125d76adc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payment_details', sa.Column('payment_status', sa.Enum('pending', 'completed', 'cancelled', name='statusenum'), nullable=False))
    op.drop_column('payment_details', 'status')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payment_details', sa.Column('status', postgresql.ENUM('pending', 'completed', 'cancelled', name='statusenum'), autoincrement=False, nullable=False))
    op.drop_column('payment_details', 'payment_status')
    # ### end Alembic commands ###

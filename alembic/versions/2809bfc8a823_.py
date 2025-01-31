"""empty message

Revision ID: 2809bfc8a823
Revises: b7c7f1e1932e
Create Date: 2024-08-04 09:07:23.560361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2809bfc8a823'
down_revision: Union[str, None] = 'b7c7f1e1932e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order_details', sa.Column('order_status', sa.Enum('pending', 'processing', 'delivered', 'cancelled', 'returned', name='orderstatusenum'), nullable=True))
    op.add_column('payment_details', sa.Column('payment_status', sa.Enum('pending', 'completed', 'cancelled', name='statusenum'), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('payment_details', 'payment_status')
    op.drop_column('order_details', 'order_status')
    # ### end Alembic commands ###

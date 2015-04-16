"""empty message

Revision ID: 796de1da12
Revises: 11dde047ce4
Create Date: 2015-04-16 14:40:51.430662

"""

# revision identifiers, used by Alembic.
revision = '796de1da12'
down_revision = '11dde047ce4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('offers', 'availability')
    op.add_column('skus', sa.Column('availability', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('skus', 'availability')
    op.add_column('offers', sa.Column('availability', sa.BOOLEAN(), autoincrement=False, nullable=True))
    ### end Alembic commands ###
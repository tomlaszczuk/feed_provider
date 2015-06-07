"""empty message

Revision ID: 39a481b967c
Revises: 2ec1b458077
Create Date: 2015-06-07 13:36:00.619896

"""

# revision identifiers, used by Alembic.
revision = '39a481b967c'
down_revision = '2ec1b458077'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offers', sa.Column('scrapping_date', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('offers', 'scrapping_date')
    ### end Alembic commands ###

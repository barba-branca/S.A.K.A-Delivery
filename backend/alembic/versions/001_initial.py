"""Initial migration - all models

Revision ID: 001_initial
Revises: 
Create Date: 2026-02-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('saldo_credito', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Orders (KDS)
    op.create_table(
        'orders',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('display_id', sa.Integer(), nullable=True),
        sa.Column('ifood_id', sa.String(), nullable=True),
        sa.Column('ifood_display_id', sa.String(), nullable=True),
        sa.Column('ifood_short_reference', sa.String(), nullable=True),
        sa.Column('customer_name', sa.String(), nullable=False),
        sa.Column('customer_phone', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=True),
        sa.Column('delivery_fee', sa.Float(), nullable=True),
        sa.Column('total', sa.Float(), nullable=True),
        sa.Column('driver_name', sa.String(), nullable=True),
        sa.Column('is_driver_paid', sa.Boolean(), nullable=True),
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('preparing_at', sa.DateTime(), nullable=True),
        sa.Column('ready_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_display_id'), 'orders', ['display_id'], unique=True)
    op.create_index(op.f('ix_orders_ifood_id'), 'orders', ['ifood_id'], unique=True)

    # Order Items
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('options', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Webhook Events
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(), nullable=True),
        sa.Column('event_code', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=True),
        sa.Column('merchant_id', sa.String(), nullable=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_webhook_events_event_id'), 'webhook_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_webhook_events_order_id'), 'webhook_events', ['order_id'], unique=False)

    # Pacotes (SaaS)
    op.create_table(
        'pacotes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('valor_pago', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('qtd_pedidos', sa.Integer(), nullable=False),
        sa.Column('data_compra', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Pedidos SaaS
    op.create_table(
        'pedidos_saas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('valor_consumido', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('via_arnaldo', sa.Boolean(), nullable=True),
        sa.Column('data', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Repasses
    op.create_table(
        'repasses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('valor_para_arnaldo', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('data_repasse', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos_saas.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('repasses')
    op.drop_table('pedidos_saas')
    op.drop_table('pacotes')
    op.drop_index(op.f('ix_webhook_events_order_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_event_id'), table_name='webhook_events')
    op.drop_table('webhook_events')
    op.drop_table('order_items')
    op.drop_index(op.f('ix_orders_ifood_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_display_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')

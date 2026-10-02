"""Add visits table for longitudinal patient-visit management

Revision ID: 002_add_visits
Revises: 001_clinical_tables
Create Date: 2026-10-02

"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_visits'
down_revision = '001_clinical_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('visit_id', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('visit_date', sa.String(length=32), nullable=False),
        sa.Column('eye', sa.String(length=16), nullable=False),
        sa.Column('oct_reference', sa.String(length=512), nullable=True),
        sa.Column('scan_id', sa.String(length=64), nullable=True),
        sa.Column('qc_status', sa.String(length=32), nullable=True),
        sa.Column('qc_message', sa.Text(), nullable=True),
        sa.Column('rnfl_available', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('mean_rnflt_um', sa.Float(), nullable=True),
        sa.Column('median_rnflt_um', sa.Float(), nullable=True),
        sa.Column('min_rnflt_um', sa.Float(), nullable=True),
        sa.Column('max_rnflt_um', sa.Float(), nullable=True),
        sa.Column('phys_mean_rnflt_um', sa.Float(), nullable=True),
        sa.Column('iop_mmhg', sa.Float(), nullable=True),
        sa.Column('iop_method', sa.String(length=64), nullable=True),
        sa.Column('vf_md_db', sa.Float(), nullable=True),
        sa.Column('vf_psd_db', sa.Float(), nullable=True),
        sa.Column('vf_vfi_pct', sa.Float(), nullable=True),
        sa.Column('vf_reliability', sa.String(length=64), nullable=True),
        sa.Column('model_name', sa.String(length=128), nullable=True),
        sa.Column('model_version', sa.String(length=64), nullable=True),
        sa.Column('predicted_class', sa.Integer(), nullable=True),
        sa.Column('predicted_category', sa.String(length=128), nullable=True),
        sa.Column('classification_score', sa.Float(), nullable=True),
        sa.Column('gradcam_available', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('analysis_timestamp', sa.String(length=32), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.scan_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_visits_id'), 'visits', ['id'], unique=False)
    op.create_index(op.f('ix_visits_visit_id'), 'visits', ['visit_id'], unique=True)
    op.create_index(op.f('ix_visits_patient_id'), 'visits', ['patient_id'], unique=False)
    op.create_index(op.f('ix_visits_scan_id'), 'visits', ['scan_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_visits_scan_id'), table_name='visits')
    op.drop_index(op.f('ix_visits_patient_id'), table_name='visits')
    op.drop_index(op.f('ix_visits_visit_id'), table_name='visits')
    op.drop_index(op.f('ix_visits_id'), table_name='visits')
    op.drop_table('visits')

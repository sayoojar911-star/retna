"""Initial migration creating clinical workstation tables

Revision ID: 001_clinical_tables
Revises: 
Create Date: 2026-10-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_clinical_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('dob', sa.String(length=32), nullable=True),
        sa.Column('sex', sa.String(length=32), nullable=False),
        sa.Column('eye_laterality', sa.String(length=16), nullable=False),
        sa.Column('family_history', sa.Text(), nullable=True),
        sa.Column('clinical_notes', sa.Text(), nullable=True),
        sa.Column('photo_avatar', sa.Text(), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=False),
        sa.Column('demo_type', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('last_scan_date', sa.String(length=32), nullable=True),
        sa.Column('latest_rnflt_um', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patients_id'), 'patients', ['id'], unique=False)
    op.create_index(op.f('ix_patients_patient_id'), 'patients', ['patient_id'], unique=True)

    op.create_table(
        'scans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('scan_id', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('date', sa.String(length=32), nullable=False),
        sa.Column('eye', sa.String(length=16), nullable=False),
        sa.Column('scan_type', sa.String(length=64), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('rnflt_available', sa.Boolean(), nullable=False),
        sa.Column('mean_rnflt_um', sa.Float(), nullable=True),
        sa.Column('demo_case_id', sa.String(length=128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scans_id'), 'scans', ['id'], unique=False)
    op.create_index(op.f('ix_scans_scan_id'), 'scans', ['scan_id'], unique=True)
    op.create_index(op.f('ix_scans_patient_id'), 'scans', ['patient_id'], unique=False)

    op.create_table(
        'iop_measurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('record_id', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('date', sa.String(length=32), nullable=False),
        sa.Column('eye', sa.String(length=16), nullable=False),
        sa.Column('iop_mmhg', sa.Float(), nullable=False),
        sa.Column('method', sa.String(length=64), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iop_measurements_id'), 'iop_measurements', ['id'], unique=False)
    op.create_index(op.f('ix_iop_measurements_record_id'), 'iop_measurements', ['record_id'], unique=True)
    op.create_index(op.f('ix_iop_measurements_patient_id'), 'iop_measurements', ['patient_id'], unique=False)

    op.create_table(
        'visual_field_measurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('record_id', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('date', sa.String(length=32), nullable=False),
        sa.Column('eye', sa.String(length=16), nullable=False),
        sa.Column('md_db', sa.Float(), nullable=False),
        sa.Column('psd_db', sa.Float(), nullable=True),
        sa.Column('vfi_pct', sa.Float(), nullable=True),
        sa.Column('reliability', sa.String(length=64), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_visual_field_measurements_id'), 'visual_field_measurements', ['id'], unique=False)
    op.create_index(op.f('ix_visual_field_measurements_record_id'), 'visual_field_measurements', ['record_id'], unique=True)
    op.create_index(op.f('ix_visual_field_measurements_patient_id'), 'visual_field_measurements', ['patient_id'], unique=False)

    op.create_table(
        'clinical_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('report_id', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('report_date', sa.String(length=32), nullable=False),
        sa.Column('upload_date', sa.String(length=32), nullable=False),
        sa.Column('report_type', sa.String(length=128), nullable=False),
        sa.Column('eye', sa.String(length=16), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clinical_reports_id'), 'clinical_reports', ['id'], unique=False)
    op.create_index(op.f('ix_clinical_reports_report_id'), 'clinical_reports', ['report_id'], unique=True)
    op.create_index(op.f('ix_clinical_reports_patient_id'), 'clinical_reports', ['patient_id'], unique=False)

    op.create_table(
        'ai_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('analysis_id', sa.String(length=64), nullable=False),
        sa.Column('scan_id', sa.String(length=64), nullable=True),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('analysis_date', sa.String(length=32), nullable=False),
        sa.Column('model_name', sa.String(length=128), nullable=False),
        sa.Column('predicted_class', sa.Integer(), nullable=True),
        sa.Column('predicted_category', sa.String(length=128), nullable=True),
        sa.Column('classification_score', sa.Float(), nullable=True),
        sa.Column('is_glaucoma_risk', sa.Boolean(), nullable=True),
        sa.Column('mean_rnflt_um', sa.Float(), nullable=True),
        sa.Column('gradcam_available', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.scan_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_analyses_id'), 'ai_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_ai_analyses_analysis_id'), 'ai_analyses', ['analysis_id'], unique=True)
    op.create_index(op.f('ix_ai_analyses_patient_id'), 'ai_analyses', ['patient_id'], unique=False)

    op.create_table(
        'progression_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('assessment_id', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('assessment_date', sa.String(length=32), nullable=False),
        sa.Column('eye', sa.String(length=16), nullable=False),
        sa.Column('observation_count', sa.Integer(), nullable=False),
        sa.Column('rnflt_slope_um_per_year', sa.Float(), nullable=True),
        sa.Column('vf_md_slope_db_per_year', sa.Float(), nullable=True),
        sa.Column('data_sufficient', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_progression_assessments_id'), 'progression_assessments', ['id'], unique=False)
    op.create_index(op.f('ix_progression_assessments_assessment_id'), 'progression_assessments', ['assessment_id'], unique=True)
    op.create_index(op.f('ix_progression_assessments_patient_id'), 'progression_assessments', ['patient_id'], unique=False)

    op.create_table(
        'forecast_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('forecast_id', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.String(length=64), nullable=False),
        sa.Column('request_date', sa.String(length=32), nullable=False),
        sa.Column('horizon_months', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forecast_records_id'), 'forecast_records', ['id'], unique=False)
    op.create_index(op.f('ix_forecast_records_forecast_id'), 'forecast_records', ['forecast_id'], unique=True)


def downgrade() -> None:
    op.drop_table('forecast_records')
    op.drop_table('progression_assessments')
    op.drop_table('ai_analyses')
    op.drop_table('clinical_reports')
    op.drop_table('visual_field_measurements')
    op.drop_table('iop_measurements')
    op.drop_table('scans')
    op.drop_table('patients')

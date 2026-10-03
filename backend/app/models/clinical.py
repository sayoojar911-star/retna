"""SQLAlchemy Data Models for GlaucoMap Clinical Workstation.

Represents clinical domain entities:
- Patient
- Scan
- IOPMeasurement
- VisualFieldMeasurement
- ClinicalReport
- AIAnalysis
- ProgressionAssessment
- ForecastRecord
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from backend.app.models.base import TimestampedModel


class Patient(TimestampedModel):
    __tablename__ = "patients"

    patient_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    dob = Column(String(32), nullable=True)
    sex = Column(String(32), default="Female", nullable=False)
    eye_laterality = Column(String(16), default="OD", nullable=False)
    family_history = Column(Text, default="", nullable=True)
    clinical_notes = Column(Text, default="", nullable=True)
    photo_avatar = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    demo_type = Column(String(255), nullable=True)
    status = Column(String(64), default="Active", nullable=False)
    last_scan_date = Column(String(32), nullable=True)
    latest_rnflt_um = Column(Float, nullable=True)

    # Relationships
    scans = relationship("Scan", back_populates="patient", cascade="all, delete-orphan")
    iop_measurements = relationship("IOPMeasurement", back_populates="patient", cascade="all, delete-orphan")
    visual_field_measurements = relationship("VisualFieldMeasurement", back_populates="patient", cascade="all, delete-orphan")
    reports = relationship("ClinicalReport", back_populates="patient", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="patient", cascade="all, delete-orphan")
    progression_assessments = relationship("ProgressionAssessment", back_populates="patient", cascade="all, delete-orphan")
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")


class Visit(TimestampedModel):
    __tablename__ = "visits"

    visit_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    visit_date = Column(String(32), nullable=False)
    eye = Column(String(16), default="OD", nullable=False)
    oct_reference = Column(String(512), nullable=True)
    scan_id = Column(String(64), ForeignKey("scans.scan_id", ondelete="SET NULL"), nullable=True, index=True)
    qc_status = Column(String(32), nullable=True)
    qc_message = Column(Text, nullable=True)
    rnfl_available = Column(Boolean, default=False, nullable=False)
    mean_rnflt_um = Column(Float, nullable=True)
    median_rnflt_um = Column(Float, nullable=True)
    min_rnflt_um = Column(Float, nullable=True)
    max_rnflt_um = Column(Float, nullable=True)
    phys_mean_rnflt_um = Column(Float, nullable=True)
    iop_mmhg = Column(Float, nullable=True)
    iop_method = Column(String(64), nullable=True)
    vf_md_db = Column(Float, nullable=True)
    vf_psd_db = Column(Float, nullable=True)
    vf_vfi_pct = Column(Float, nullable=True)
    vf_reliability = Column(String(64), nullable=True)
    model_name = Column(String(128), nullable=True)
    model_version = Column(String(64), nullable=True)
    predicted_class = Column(Integer, nullable=True)
    predicted_category = Column(String(128), nullable=True)
    classification_score = Column(Float, nullable=True)
    gradcam_available = Column(Boolean, default=False, nullable=False)
    analysis_timestamp = Column(String(32), nullable=True)
    notes = Column(Text, default="", nullable=True)

    patient = relationship("Patient", back_populates="visits")
    scan = relationship("Scan")


class Scan(TimestampedModel):
    __tablename__ = "scans"

    scan_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(32), nullable=False)
    eye = Column(String(16), default="OD", nullable=False)
    scan_type = Column(String(64), nullable=False)
    file_path = Column(String(512), nullable=True)
    status = Column(String(64), default="Analyzed", nullable=False)
    rnflt_available = Column(Boolean, default=True, nullable=False)
    mean_rnflt_um = Column(Float, nullable=True)
    demo_case_id = Column(String(128), nullable=True)
    notes = Column(Text, default="", nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="scans")
    ai_analyses = relationship("AIAnalysis", back_populates="scan", cascade="all, delete-orphan")


class IOPMeasurement(TimestampedModel):
    __tablename__ = "iop_measurements"

    record_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(32), nullable=False)
    eye = Column(String(16), default="OD", nullable=False)
    iop_mmhg = Column(Float, nullable=False)
    method = Column(String(64), default="Goldmann Applanation", nullable=False)
    notes = Column(Text, default="", nullable=True)

    patient = relationship("Patient", back_populates="iop_measurements")


class VisualFieldMeasurement(TimestampedModel):
    __tablename__ = "visual_field_measurements"

    record_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(32), nullable=False)
    eye = Column(String(16), default="OD", nullable=False)
    md_db = Column(Float, nullable=False)  # Mean Deviation in dB
    psd_db = Column(Float, nullable=True)  # Pattern Standard Deviation in dB
    vfi_pct = Column(Float, nullable=True)  # Visual Field Index percentage
    reliability = Column(String(64), default="Reliable", nullable=False)
    file_name = Column(String(255), nullable=True)
    notes = Column(Text, default="", nullable=True)

    patient = relationship("Patient", back_populates="visual_field_measurements")


class ClinicalReport(TimestampedModel):
    __tablename__ = "clinical_reports"

    report_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    report_date = Column(String(32), nullable=False)
    upload_date = Column(String(32), nullable=False)
    report_type = Column(String(128), nullable=False)
    eye = Column(String(16), default="OD", nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    notes = Column(Text, default="", nullable=True)

    patient = relationship("Patient", back_populates="reports")


class AIAnalysis(TimestampedModel):
    __tablename__ = "ai_analyses"

    analysis_id = Column(String(64), unique=True, index=True, nullable=False)
    scan_id = Column(String(64), ForeignKey("scans.scan_id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_date = Column(String(32), nullable=False)
    model_name = Column(String(128), nullable=False)
    predicted_class = Column(Integer, nullable=True)
    predicted_category = Column(String(128), nullable=True)
    classification_score = Column(Float, nullable=True)
    is_glaucoma_risk = Column(Boolean, nullable=True)
    mean_rnflt_um = Column(Float, nullable=True)
    gradcam_available = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, default="", nullable=True)

    patient = relationship("Patient", back_populates="ai_analyses")
    scan = relationship("Scan", back_populates="ai_analyses")


class ProgressionAssessment(TimestampedModel):
    __tablename__ = "progression_assessments"

    assessment_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_date = Column(String(32), nullable=False)
    eye = Column(String(16), default="OD", nullable=False)
    observation_count = Column(Integer, default=1, nullable=False)
    rnflt_slope_um_per_year = Column(Float, nullable=True)
    vf_md_slope_db_per_year = Column(Float, nullable=True)
    data_sufficient = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, default="", nullable=True)

    patient = relationship("Patient", back_populates="progression_assessments")


class ForecastRecord(TimestampedModel):
    __tablename__ = "forecast_records"

    forecast_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_id = Column(String(64), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    request_date = Column(String(32), nullable=False)
    horizon_months = Column(Integer, default=24, nullable=False)
    status = Column(String(64), default="UNAVAILABLE", nullable=False)
    message = Column(Text, nullable=False)

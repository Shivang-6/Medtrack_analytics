# app/models/prescription.py
from datetime import datetime, date, timedelta
from sqlalchemy.orm import validates

from app import db

class Prescription(db.Model):
    """Prescription model"""
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    prescription_code = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    doctor_name = db.Column(db.String(200), nullable=False)
    doctor_license = db.Column(db.String(100))
    hospital_clinic = db.Column(db.String(200))
    date_prescribed = db.Column(db.Date, nullable=False)
    date_dispensed = db.Column(db.Date)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    refills_allowed = db.Column(db.Integer, default=0)
    refills_used = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Active')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('duration_days')
    def validate_duration_days(self, key, value):
        if value <= 0:
            raise ValueError("Duration must be positive")
        return value

    @validates('refills_allowed')
    def validate_refills_allowed(self, key, value):
        if value < 0:
            raise ValueError("Refills cannot be negative")
        return value

    @validates('refills_used')
    def validate_refills_used(self, key, value):
        if value < 0:
            raise ValueError("Refills used cannot be negative")
        return value

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'prescription_code': self.prescription_code,
            'patient_id': self.patient_id,
            'drug_id': self.drug_id,
            'doctor_name': self.doctor_name,
            'doctor_license': self.doctor_license,
            'hospital_clinic': self.hospital_clinic,
            'date_prescribed': self.date_prescribed.isoformat() if self.date_prescribed else None,
            'date_dispensed': self.date_dispensed.isoformat() if self.date_dispensed else None,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration_days': self.duration_days,
            'refills_allowed': self.refills_allowed,
            'refills_used': self.refills_used,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_expired': self.is_expired(),
            'refills_remaining': self.refills_allowed - self.refills_used
        }

    def is_expired(self):
        """Check if prescription is expired"""
        if self.date_prescribed:
            expiry_date = self.date_prescribed + timedelta(days=self.duration_days)
            return date.today() > expiry_date
        return False

    def can_refill(self):
        """Check if prescription can be refilled"""
        return (self.refills_used < self.refills_allowed) and not self.is_expired() and self.status == 'Active'

    def dispense(self):
        """Mark prescription as dispensed"""
        self.date_dispensed = date.today()
        self.refills_used += 1

        if self.refills_used >= self.refills_allowed:
            self.status = 'Completed'

    @classmethod
    def get_active_prescriptions(cls, patient_id=None):
        """Get active prescriptions, optionally filtered by patient"""
        query = cls.query.filter_by(status='Active')

        if patient_id:
            query = query.filter_by(patient_id=patient_id)

        return query.order_by(cls.date_prescribed.desc()).all()

    def __repr__(self):
        return f'<Prescription {self.prescription_code}>'

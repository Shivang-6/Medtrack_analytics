# app/models/patient.py
from datetime import datetime, date
from sqlalchemy import Computed
from sqlalchemy.orm import validates

from app import db

class Patient(db.Model):
    """Patient demographic model"""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, Computed('EXTRACT(YEAR FROM age(CURRENT_DATE, date_of_birth))'))
    gender = db.Column(db.String(10))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    primary_condition = db.Column(db.String(200))
    insurance_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)

    @validates('email')
    def validate_email(self, key, value):
        if value and '@' not in value:
            raise ValueError("Invalid email format")
        return value

    @validates('date_of_birth')
    def validate_date_of_birth(self, key, value):
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'patient_code': self.patient_code,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
            'gender': self.gender,
            'email': self.email,
            'phone': self.phone,
            'city': self.city,
            'state': self.state,
            'primary_condition': self.primary_condition,
            'insurance_id': self.insurance_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'full_name': self.get_full_name()
        }

    def get_full_name(self):
        """Get patient's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    @classmethod
    def get_by_age_group(cls, min_age=None, max_age=None):
        """Get patients by age group"""
        query = cls.query

        if min_age is not None:
            query = query.filter(cls.age >= min_age)
        if max_age is not None:
            query = query.filter(cls.age <= max_age)

        return query.order_by(cls.age).all()

    @classmethod
    def get_by_condition(cls, condition):
        """Get patients by medical condition"""
        return cls.query.filter(
            cls.primary_condition.ilike(f'%{condition}%')
        ).all()

    def __repr__(self):
        return f'<Patient {self.patient_code}: {self.get_full_name()}>'

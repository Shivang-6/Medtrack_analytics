import logging
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from app import db
from app.models.patient import Patient
from app.models.prescription import Prescription

patient_bp = Blueprint('patients', __name__)
logger = logging.getLogger(__name__)


@patient_bp.route('/patients', methods=['GET'])
def get_patients():
    """Get patients with optional filtering"""
    try:
        min_age = request.args.get('min_age')
        max_age = request.args.get('max_age')
        gender = request.args.get('gender')
        condition = request.args.get('condition')
        city = request.args.get('city')
        state = request.args.get('state')

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        query = Patient.query

        if min_age:
            query = query.filter(Patient.age >= int(min_age))
        if max_age:
            query = query.filter(Patient.age <= int(max_age))
        if gender:
            query = query.filter(Patient.gender == gender)
        if condition:
            query = query.filter(Patient.primary_condition.ilike(f'%{condition}%'))
        if city:
            query = query.filter(Patient.city.ilike(f'%{city}%'))
        if state:
            query = query.filter(Patient.state.ilike(f'%{state}%'))

        paginated_patients = query.order_by(Patient.last_name, Patient.first_name) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'page': paginated_patients.page,
            'per_page': paginated_patients.per_page,
            'total_pages': paginated_patients.pages,
            'total_patients': paginated_patients.total,
            'patients': [patient.to_dict() for patient in paginated_patients.items]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@patient_bp.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get single patient with prescriptions"""
    try:
        patient = Patient.query.get_or_404(patient_id)

        prescriptions = Prescription.query.filter_by(patient_id=patient_id) \
            .order_by(Prescription.date_prescribed.desc()) \
            .limit(20).all()

        response = patient.to_dict()
        response['prescriptions'] = [p.to_dict() for p in prescriptions]
        response['prescription_count'] = len(prescriptions)
        response['active_prescriptions'] = Prescription.query.filter_by(patient_id=patient_id, status='Active').count()

        return jsonify({'success': True, 'patient': response}), 200

    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 404 if '404' in str(e) else 500


@patient_bp.route('/patients', methods=['POST'])
def create_patient():
    """Create a new patient"""
    try:
        data = request.get_json()

        required_fields = ['first_name', 'last_name', 'date_of_birth']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        patient_code = f"PAT-{str(uuid.uuid4())[:8].upper()}"

        patient = Patient(
            patient_code=patient_code,
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date(),
            gender=data.get('gender'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            primary_condition=data.get('primary_condition'),
            insurance_id=data.get('insurance_id')
        )

        db.session.add(patient)
        db.session.commit()
        logger.info(f"Created new patient: {patient_code}")

        return jsonify({'success': True, 'message': 'Patient created successfully', 'patient': patient.to_dict()}), 201

    except ValueError as e:
        return jsonify({'success': False, 'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating patient: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@patient_bp.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Update patient information"""
    try:
        patient = Patient.query.get_or_404(patient_id)
        data = request.get_json()

        updateable_fields = [
            'first_name', 'last_name', 'gender', 'email', 'phone',
            'address', 'city', 'state', 'zip_code', 'primary_condition',
            'insurance_id'
        ]

        for field in updateable_fields:
            if field in data:
                if field == 'date_of_birth' and data[field]:
                    setattr(patient, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                else:
                    setattr(patient, field, data[field])

        db.session.commit()
        logger.info(f"Updated patient {patient_id}")

        return jsonify({'success': True, 'message': 'Patient updated successfully', 'patient': patient.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating patient {patient_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@patient_bp.route('/patients/<int:patient_id>/prescriptions', methods=['GET'])
def get_patient_prescriptions(patient_id):
    """Get all prescriptions for a patient"""
    try:
        Patient.query.get_or_404(patient_id)
        status = request.args.get('status')

        query = Prescription.query.filter_by(patient_id=patient_id)
        if status:
            query = query.filter_by(status=status)

        prescriptions = query.order_by(Prescription.date_prescribed.desc()).all()

        return jsonify({
            'success': True,
            'patient_id': patient_id,
            'prescriptions': [p.to_dict() for p in prescriptions],
            'count': len(prescriptions)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching prescriptions for patient {patient_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@patient_bp.route('/patients/<int:patient_id>/prescriptions', methods=['POST'])
def create_prescription(patient_id):
    """Create a new prescription for a patient"""
    try:
        Patient.query.get_or_404(patient_id)
        data = request.get_json()

        required_fields = ['drug_id', 'doctor_name', 'dosage', 'frequency', 'duration_days']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        prescription_code = f"RX-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

        prescription = Prescription(
            prescription_code=prescription_code,
            patient_id=patient_id,
            drug_id=int(data['drug_id']),
            doctor_name=data['doctor_name'],
            doctor_license=data.get('doctor_license'),
            hospital_clinic=data.get('hospital_clinic'),
            date_prescribed=datetime.strptime(data.get('date_prescribed', datetime.now().date().isoformat()), '%Y-%m-%d').date(),
            dosage=data['dosage'],
            frequency=data['frequency'],
            duration_days=int(data['duration_days']),
            refills_allowed=int(data.get('refills_allowed', 0)),
            status=data.get('status', 'Active'),
            notes=data.get('notes')
        )

        db.session.add(prescription)
        db.session.commit()
        logger.info(f"Created prescription {prescription_code} for patient {patient_id}")

        return jsonify({'success': True, 'message': 'Prescription created successfully', 'prescription': prescription.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating prescription: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@patient_bp.route('/patients/search', methods=['GET'])
def search_patients():
    """Search patients by name, condition, or other criteria"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 20))

        if not query or len(query) < 2:
            return jsonify({'success': True, 'message': 'Search query too short', 'patients': []}), 200

        results = Patient.query.filter(
            or_(
                Patient.first_name.ilike(f'%{query}%'),
                Patient.last_name.ilike(f'%{query}%'),
                Patient.patient_code.ilike(f'%{query}%'),
                Patient.primary_condition.ilike(f'%{query}%'),
                Patient.city.ilike(f'%{query}%')
            )
        ).limit(limit).all()

        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'patients': [patient.to_dict() for patient in results]
        }), 200

    except Exception as e:
        logger.error(f"Error searching patients: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

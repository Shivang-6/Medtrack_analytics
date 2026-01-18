def analytics_root():
import logging
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import case, func

from app import db
from app.models.drug import Drug
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.sale import Sale

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)


@analytics_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        today = date.today()
        last_30_days = today - timedelta(days=30)

        sales_summary = db.session.query(
            func.count(Sale.id).label('total_sales'),
            func.sum(Sale.total_amount).label('total_revenue'),
            func.sum(Sale.quantity).label('total_quantity'),
            func.avg(Sale.total_amount).label('avg_sale_value')
        ).filter(Sale.sale_date >= last_30_days).first()

        inventory_summary = db.session.query(
            func.count(Drug.id).label('total_drugs'),
            func.sum(Drug.stock_quantity).label('total_stock'),
            func.sum(Drug.stock_quantity * Drug.unit_price).label('total_inventory_value'),
            func.count(case([(Drug.stock_quantity <= Drug.min_stock_level * 1.5, 1)])).label('low_stock_count')
        ).first()

        patient_summary = db.session.query(
            func.count(Patient.id).label('total_patients'),
            func.avg(Patient.age).label('avg_age'),
            func.count(case([(Patient.gender == 'Male', 1)])).label('male_count'),
            func.count(case([(Patient.gender == 'Female', 1)])).label('female_count')
        ).first()

        daily_sales = {}
        for single_date in [today - timedelta(days=i) for i in range(6, -1, -1)]:
            day_sales = db.session.query(
                func.sum(Sale.total_amount).label('revenue'),
                func.count(Sale.id).label('transactions')
            ).filter(Sale.sale_date == single_date).first()

            daily_sales[single_date.isoformat()] = {
                'revenue': float(day_sales[0]) if day_sales[0] else 0,
                'transactions': day_sales[1] if day_sales[1] else 0
            }

        top_categories = db.session.query(
            Drug.category,
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.total_amount).label('revenue'),
            func.sum(Sale.quantity).label('quantity')
        ).join(Sale, Sale.drug_id == Drug.id) \
         .filter(Sale.sale_date >= last_30_days) \
         .group_by(Drug.category) \
         .order_by(func.sum(Sale.total_amount).desc()) \
         .limit(5).all()

        top_categories_list = []
        for cat in top_categories:
            top_categories_list.append({
                'category': cat[0] or 'Uncategorized',
                'sales_count': cat[1],
                'revenue': float(cat[2]) if cat[2] else 0,
                'quantity': cat[3] if cat[3] else 0
            })

        return jsonify({
            'success': True,
            'dashboard': {
                'sales_summary': {
                    'total_sales': sales_summary[0] if sales_summary[0] else 0,
                    'total_revenue': float(sales_summary[1]) if sales_summary[1] else 0,
                    'total_quantity': sales_summary[2] if sales_summary[2] else 0,
                    'avg_sale_value': float(sales_summary[3]) if sales_summary[3] else 0,
                    'period': 'last_30_days'
                },
                'inventory_summary': {
                    'total_drugs': inventory_summary[0] if inventory_summary[0] else 0,
                    'total_stock': inventory_summary[1] if inventory_summary[1] else 0,
                    'inventory_value': float(inventory_summary[2]) if inventory_summary[2] else 0,
                    'low_stock_count': inventory_summary[3] if inventory_summary[3] else 0
                },
                'patient_summary': {
                    'total_patients': patient_summary[0] if patient_summary[0] else 0,
                    'avg_age': float(patient_summary[1]) if patient_summary[1] else 0,
                    'male_count': patient_summary[2] if patient_summary[2] else 0,
                    'female_count': patient_summary[3] if patient_summary[3] else 0
                },
                'recent_sales_trend': daily_sales,
                'top_categories': top_categories_list,
                'last_updated': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/analytics/patient-demographics', methods=['GET'])
def get_patient_demographics():
    """Get patient demographic analysis"""
    try:
        age_groups = db.session.query(
            case([
                (Patient.age < 18, 'Under 18'),
                (Patient.age.between(18, 30), '18-30'),
                (Patient.age.between(31, 45), '31-45'),
                (Patient.age.between(46, 60), '46-60'),
                (Patient.age > 60, 'Over 60')
            ]).label('age_group'),
            func.count(Patient.id).label('count'),
            func.avg(Patient.age).label('avg_age')
        ).group_by('age_group').order_by('age_group').all()

        top_conditions = db.session.query(
            Patient.primary_condition,
            func.count(Patient.id).label('patient_count'),
            func.avg(Patient.age).label('avg_age')
        ).filter(Patient.primary_condition.isnot(None)) \
         .group_by(Patient.primary_condition) \
         .order_by(func.count(Patient.id).desc()) \
         .limit(10).all()

        geographic = db.session.query(
            Patient.state,
            func.count(Patient.id).label('patient_count'),
            func.avg(Patient.age).label('avg_age')
        ).filter(Patient.state.isnot(None)) \
         .group_by(Patient.state) \
         .order_by(func.count(Patient.id).desc()) \
         .limit(10).all()

        return jsonify({
            'success': True,
            'demographics': {
                'age_distribution': [
                    {'age_group': ag[0] or 'Unknown', 'count': ag[1], 'avg_age': float(ag[2]) if ag[2] else 0}
                    for ag in age_groups
                ],
                'top_conditions': [
                    {'condition': tc[0], 'patient_count': tc[1], 'avg_age': float(tc[2]) if tc[2] else 0}
                    for tc in top_conditions
                ],
                'geographic_distribution': [
                    {'state': g[0], 'patient_count': g[1], 'avg_age': float(g[2]) if g[2] else 0}
                    for g in geographic
                ]
            }
        }), 200

    except Exception as e:
        logger.error(f"Error analyzing patient demographics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/analytics/prescription-patterns', methods=['GET'])
def get_prescription_patterns():
    """Analyze prescription patterns"""
    try:
        monthly_prescriptions = db.session.query(
            func.to_char(Prescription.date_prescribed, 'YYYY-MM').label('month'),
            func.count(Prescription.id).label('prescription_count'),
            func.count(func.distinct(Prescription.patient_id)).label('unique_patients'),
            func.count(func.distinct(Prescription.doctor_name)).label('unique_doctors')
        ).group_by('month').order_by('month').limit(12).all()

        top_prescribed = db.session.query(
            Drug.drug_name,
            Drug.category,
            func.count(Prescription.id).label('prescription_count'),
            func.count(func.distinct(Prescription.patient_id)).label('unique_patients'),
            func.avg(Prescription.duration_days).label('avg_duration')
        ).join(Drug, Prescription.drug_id == Drug.id) \
         .group_by(Drug.drug_name, Drug.category) \
         .order_by(func.count(Prescription.id).desc()) \
         .limit(10).all()

        top_doctors = db.session.query(
            Prescription.doctor_name,
            func.count(Prescription.id).label('prescription_count'),
            func.count(func.distinct(Prescription.patient_id)).label('unique_patients'),
            func.count(func.distinct(Drug.drug_class)).label('unique_classes')
        ).join(Drug, Prescription.drug_id == Drug.id) \
         .group_by(Prescription.doctor_name) \
         .order_by(func.count(Prescription.id).desc()) \
         .limit(10).all()

        return jsonify({
            'success': True,
            'prescription_patterns': {
                'monthly_trends': [
                    {'month': mp[0], 'prescription_count': mp[1], 'unique_patients': mp[2], 'unique_doctors': mp[3]}
                    for mp in monthly_prescriptions
                ],
                'top_prescribed_drugs': [
                    {
                        'drug_name': tp[0],
                        'category': tp[1],
                        'prescription_count': tp[2],
                        'unique_patients': tp[3],
                        'avg_duration_days': float(tp[4]) if tp[4] else 0
                    }
                    for tp in top_prescribed
                ],
                'top_doctors': [
                    {
                        'doctor_name': td[0],
                        'prescription_count': td[1],
                        'unique_patients': td[2],
                        'unique_drug_classes': td[3]
                    }
                    for td in top_doctors
                ]
            }
        }), 200

    except Exception as e:
        logger.error(f"Error analyzing prescription patterns: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/analytics/inventory-health', methods=['GET'])
def get_inventory_health():
    """Analyze inventory health metrics"""
    try:
        recent_sales = db.session.query(
            Sale.drug_id,
            func.sum(Sale.quantity).label('sold_quantity')
        ).filter(Sale.sale_date >= date.today() - timedelta(days=90)) \
         .group_by(Sale.drug_id).subquery()

        inventory_health = db.session.query(
            Drug.id,
            Drug.drug_name,
            Drug.stock_quantity,
            Drug.min_stock_level,
            Drug.max_stock_level,
            func.coalesce(recent_sales.c.sold_quantity, 0).label('recent_sales'),
            case([
                (Drug.stock_quantity <= Drug.min_stock_level, 'Critical'),
                (Drug.stock_quantity <= Drug.min_stock_level * 1.5, 'Low'),
                (Drug.stock_quantity >= Drug.max_stock_level * 0.9, 'High'),
                (Drug.expiry_date < date.today() + timedelta(days=30), 'Expiring'),
                (True, 'Healthy')
            ]).label('health_status'),
            case([
                (Drug.expiry_date < date.today(), 0),
                (Drug.expiry_date >= date.today(), func.extract('day', Drug.expiry_date - date.today()))
            ]).label('days_to_expiry')
        ).outerjoin(recent_sales, Drug.id == recent_sales.c.drug_id) \
         .filter(Drug.stock_quantity > 0) \
         .order_by(Drug.stock_quantity.asc()) \
         .limit(50).all()

        health_summary = db.session.query(
            func.count(case([(Drug.stock_quantity <= Drug.min_stock_level, 1)])).label('critical'),
            func.count(case([(Drug.stock_quantity <= Drug.min_stock_level * 1.5, 1)])).label('low'),
            func.count(case([(Drug.stock_quantity >= Drug.max_stock_level * 0.9, 1)])).label('high'),
            func.count(case([(Drug.expiry_date < date.today() + timedelta(days=30), 1)])).label('expiring_soon'),
            func.count(Drug.id).label('total')
        ).filter(Drug.stock_quantity > 0).first()

        health_items = []
        for ih in inventory_health:
            stock_percentage = (ih[2] * 100.0 / ih[4]) if ih[4] > 0 else 0
            turnover_rate = (ih[5] * 100.0 / ih[2]) if ih[2] > 0 else 0

            health_items.append({
                'drug_id': ih[0],
                'drug_name': ih[1],
                'stock_quantity': ih[2],
                'min_level': ih[3],
                'max_level': ih[4],
                'recent_sales': ih[5],
                'health_status': ih[6],
                'days_to_expiry': ih[7] if ih[7] else None,
                'stock_percentage': round(stock_percentage, 2),
                'turnover_rate': round(turnover_rate, 2)
            })

        return jsonify({
            'success': True,
            'inventory_health': {
                'summary': {
                    'critical': health_summary[0],
                    'low': health_summary[1],
                    'high': health_summary[2],
                    'expiring_soon': health_summary[3],
                    'total': health_summary[4],
                    'healthy': health_summary[4] - (health_summary[0] + health_summary[1] + health_summary[2] + health_summary[3])
                },
                'items': health_items
            }
        }), 200

    except Exception as e:
        logger.error(f"Error analyzing inventory health: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/analytics/predictive/low-stock-forecast', methods=['GET'])
def predict_low_stock():
    """Predict which drugs will run low based on sales trends"""
    try:
        days_to_forecast = int(request.args.get('days', 30))

        sales_rate_query = db.session.query(
            Sale.drug_id,
            func.sum(Sale.quantity).label('total_sold'),
            func.count(Sale.id).label('sale_count'),
            (func.sum(Sale.quantity) / 90.0).label('daily_sales_rate')
        ).filter(Sale.sale_date >= date.today() - timedelta(days=90)) \
         .group_by(Sale.drug_id).subquery()

        forecast = db.session.query(
            Drug.id,
            Drug.drug_name,
            Drug.stock_quantity,
            Drug.min_stock_level,
            func.coalesce(sales_rate_query.c.daily_sales_rate, 0.1).label('daily_sales_rate'),
            func.coalesce(sales_rate_query.c.total_sold, 0).label('recent_sales'),
            case([
                (Drug.stock_quantity <= 0, 0),
                (sales_rate_query.c.daily_sales_rate <= 0, Drug.stock_quantity / 0.1),
                (True, Drug.stock_quantity / sales_rate_query.c.daily_sales_rate)
            ]).label('days_of_supply')
        ).outerjoin(sales_rate_query, Drug.id == sales_rate_query.c.drug_id) \
         .filter(Drug.stock_quantity > 0) \
         .order_by('days_of_supply').all()

        at_risk_drugs = []
        for f in forecast:
            days_of_supply = float(f[6]) if f[6] else 0
            if days_of_supply <= days_to_forecast:
                at_risk_drugs.append({
                    'drug_id': f[0],
                    'drug_name': f[1],
                    'current_stock': f[2],
                    'min_level': f[3],
                    'daily_sales_rate': float(f[4]),
                    'recent_sales': f[5],
                    'days_of_supply': round(days_of_supply, 1),
                    'risk_level': 'High' if days_of_supply <= 7 else 'Medium' if days_of_supply <= 14 else 'Low'
                })

        return jsonify({
            'success': True,
            'forecast_period_days': days_to_forecast,
            'at_risk_drugs_count': len(at_risk_drugs),
            'at_risk_drugs': at_risk_drugs
        }), 200

    except Exception as e:
        logger.error(f"Error predicting low stock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/analytics/reports/custom', methods=['POST'])
def generate_custom_report():
    """Generate custom analytics report based on parameters"""
    try:
        data = request.get_json()
        report_type = data.get('report_type')
        parameters = data.get('parameters', {})

        if report_type == 'sales_summary':
            start_date = datetime.strptime(parameters.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(parameters.get('end_date'), '%Y-%m-%d').date()
            report_data = generate_sales_summary_report(start_date, end_date)
        elif report_type == 'inventory_valuation':
            report_data = generate_inventory_valuation_report()
        elif report_type == 'patient_demographics':
            report_data = generate_patient_demographics_report()
        else:
            return jsonify({'success': False, 'error': f'Unknown report type: {report_type}'}), 400

        return jsonify({
            'success': True,
            'report_type': report_type,
            'generated_at': datetime.utcnow().isoformat(),
            'parameters': parameters,
            'data': report_data
        }), 200

    except Exception as e:
        logger.error(f"Error generating custom report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_sales_summary_report(start_date, end_date):
    """Helper: sales summary report"""
    sales_data = Sale.get_sales_by_period(start_date, end_date)

    daily_breakdown = db.session.query(
        Sale.sale_date,
        func.count(Sale.id).label('transaction_count'),
        func.sum(Sale.total_amount).label('daily_revenue'),
        func.sum(Sale.quantity).label('daily_quantity')
    ).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).group_by(Sale.sale_date).order_by(Sale.sale_date).all()

    return {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': (end_date - start_date).days + 1
        },
        'summary': sales_data,
        'daily_breakdown': [
            {
                'date': sd[0].isoformat(),
                'transaction_count': sd[1],
                'revenue': float(sd[2]) if sd[2] else 0,
                'quantity': sd[3] if sd[3] else 0
            }
            for sd in daily_breakdown
        ]
    }


def generate_inventory_valuation_report():
    """Helper: inventory valuation report"""
    drugs = Drug.query.filter(Drug.stock_quantity > 0).all()

    total_value = 0
    by_category = {}

    for drug in drugs:
        drug_value = drug.get_stock_value()
        total_value += drug_value

        category = drug.category or 'Uncategorized'
        if category not in by_category:
            by_category[category] = {
                'count': 0,
                'total_quantity': 0,
                'total_value': 0,
                'drugs': []
            }

        by_category[category]['count'] += 1
        by_category[category]['total_quantity'] += drug.stock_quantity
        by_category[category]['total_value'] += drug_value
        by_category[category]['drugs'].append({
            'drug_name': drug.drug_name,
            'stock_quantity': drug.stock_quantity,
            'unit_price': float(drug.unit_price) if drug.unit_price else 0,
            'total_value': drug_value
        })

    return {
        'total_inventory_value': total_value,
        'total_unique_drugs': len(drugs),
        'total_units': sum(d.stock_quantity for d in drugs),
        'by_category': by_category
    }


def generate_patient_demographics_report():
    """Helper: patient demographics report"""
    patients = Patient.query.all()

    age_groups = {
        'Under 18': 0,
        '18-30': 0,
        '31-45': 0,
        '46-60': 0,
        'Over 60': 0
    }

    conditions = {}
    cities = {}

    for patient in patients:
        if patient.age < 18:
            age_groups['Under 18'] += 1
        elif patient.age <= 30:
            age_groups['18-30'] += 1
        elif patient.age <= 45:
            age_groups['31-45'] += 1
        elif patient.age <= 60:
            age_groups['46-60'] += 1
        else:
            age_groups['Over 60'] += 1

        if patient.primary_condition:
            conditions[patient.primary_condition] = conditions.get(patient.primary_condition, 0) + 1

        if patient.city:
            cities[patient.city] = cities.get(patient.city, 0) + 1

    return {
        'total_patients': len(patients),
        'age_distribution': age_groups,
        'top_conditions': dict(sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:10]),
        'top_cities': dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]),
        'gender_distribution': {
            'Male': len([p for p in patients if p.gender == 'Male']),
            'Female': len([p for p in patients if p.gender == 'Female']),
            'Other': len([p for p in patients if p.gender == 'Other']),
            'Unknown': len([p for p in patients if not p.gender])
        }
    }

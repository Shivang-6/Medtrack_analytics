import logging
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from app import db
from app.models.drug import Drug
from app.models.inventory_transaction import InventoryTransaction

drug_bp = Blueprint('drugs', __name__)
logger = logging.getLogger(__name__)


@drug_bp.route('/drugs', methods=['GET'])
def get_drugs():
    """Get all drugs with optional filtering"""
    try:
        category = request.args.get('category')
        manufacturer = request.args.get('manufacturer')
        low_stock = request.args.get('low_stock', 'false').lower() == 'true'
        expiring_soon = request.args.get('expiring_soon', 'false').lower() == 'true'
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')

        query = Drug.query

        if category:
            query = query.filter(Drug.category == category)
        if manufacturer:
            query = query.filter(Drug.manufacturer.ilike(f'%{manufacturer}%'))
        if min_price:
            query = query.filter(Drug.unit_price >= float(min_price))
        if max_price:
            query = query.filter(Drug.unit_price <= float(max_price))
        if low_stock:
            query = query.filter(Drug.stock_quantity <= Drug.min_stock_level * 1.5)
        if expiring_soon:
            expiry_threshold = date.today() + timedelta(days=30)
            query = query.filter(
                Drug.expiry_date <= expiry_threshold,
                Drug.expiry_date >= date.today()
            )

        drugs = query.order_by(Drug.drug_name).all()

        return jsonify({
            'success': True,
            'count': len(drugs),
            'drugs': [drug.to_dict() for drug in drugs]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching drugs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/<int:drug_id>', methods=['GET'])
def get_drug(drug_id):
    """Get single drug by ID"""
    try:
        drug = Drug.query.get_or_404(drug_id)
        transactions = InventoryTransaction.get_transactions_by_drug(drug_id, limit=10)

        response = drug.to_dict()
        response['recent_transactions'] = [t.to_dict() for t in transactions]

        return jsonify({'success': True, 'drug': response}), 200

    except Exception as e:
        logger.error(f"Error fetching drug {drug_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 404 if '404' in str(e) else 500


@drug_bp.route('/drugs', methods=['POST'])
def create_drug():
    """Create a new drug"""
    try:
        data = request.get_json()

        required_fields = ['drug_code', 'drug_name', 'manufacturer', 'unit_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        existing_drug = Drug.query.filter_by(drug_code=data['drug_code']).first()
        if existing_drug:
            return jsonify({'success': False, 'error': f'Drug with code {data["drug_code"]} already exists'}), 409

        drug = Drug(
            drug_code=data['drug_code'],
            drug_name=data['drug_name'],
            generic_name=data.get('generic_name'),
            manufacturer=data['manufacturer'],
            drug_class=data.get('drug_class'),
            category=data.get('category', 'Prescription'),
            unit_price=float(data['unit_price']),
            cost_price=float(data.get('cost_price', float(data['unit_price']) * 0.7)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            min_stock_level=int(data.get('min_stock_level', 10)),
            max_stock_level=int(data.get('max_stock_level', 1000)),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            storage_conditions=data.get('storage_conditions')
        )

        db.session.add(drug)
        db.session.commit()
        logger.info(f"Created new drug: {drug.drug_code}")

        return jsonify({'success': True, 'message': 'Drug created successfully', 'drug': drug.to_dict()}), 201

    except ValueError as e:
        return jsonify({'success': False, 'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating drug: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/<int:drug_id>', methods=['PUT'])
def update_drug(drug_id):
    """Update an existing drug"""
    try:
        drug = Drug.query.get_or_404(drug_id)
        data = request.get_json()

        updateable_fields = [
            'drug_name', 'generic_name', 'manufacturer', 'drug_class',
            'category', 'unit_price', 'cost_price', 'stock_quantity',
            'min_stock_level', 'max_stock_level', 'expiry_date',
            'storage_conditions'
        ]

        for field in updateable_fields:
            if field in data:
                if field == 'expiry_date' and data[field]:
                    setattr(drug, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                else:
                    setattr(drug, field, data[field])

        db.session.commit()
        logger.info(f"Updated drug {drug_id}")

        return jsonify({'success': True, 'message': 'Drug updated successfully', 'drug': drug.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating drug {drug_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/<int:drug_id>', methods=['DELETE'])
def delete_drug(drug_id):
    """Soft delete: mark drug as discontinued"""
    try:
        drug = Drug.query.get_or_404(drug_id)
        drug.category = 'Discontinued'
        db.session.commit()
        logger.info(f"Marked drug {drug_id} as discontinued")
        return jsonify({'success': True, 'message': 'Drug marked as discontinued'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting drug {drug_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/<int:drug_id>/stock', methods=['POST'])
def update_stock(drug_id):
    """Update drug stock quantity"""
    try:
        drug = Drug.query.get_or_404(drug_id)
        data = request.get_json()

        quantity_change = int(data['quantity_change'])
        transaction_type = data['transaction_type']
        notes = data.get('notes', '')

        transaction = drug.update_stock(
            quantity_change=quantity_change,
            transaction_type=transaction_type,
            reference_id=data.get('reference_id'),
            notes=notes
        )

        db.session.commit()
        logger.info(f"Updated stock for drug {drug_id}: {quantity_change} ({transaction_type})")

        return jsonify({
            'success': True,
            'message': 'Stock updated successfully',
            'drug': drug.to_dict(),
            'transaction': transaction.to_dict()
        }), 200

    except ValueError as e:
        return jsonify({'success': False, 'error': f'Stock error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating stock for drug {drug_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/low-stock', methods=['GET'])
def get_low_stock():
    """Get all drugs that are low in stock"""
    try:
        threshold_multiplier = float(request.args.get('threshold', 1.5))
        low_stock_drugs = Drug.get_low_stock_items(threshold_multiplier)

        critical_count = len([d for d in low_stock_drugs if d.needs_restock(1.0)])
        low_count = len([d for d in low_stock_drugs if not d.needs_restock(1.0)])

        return jsonify({
            'success': True,
            'summary': {
                'total_low_stock': len(low_stock_drugs),
                'critical_count': critical_count,
                'low_count': low_count,
                'threshold_multiplier': threshold_multiplier
            },
            'drugs': [drug.to_dict() for drug in low_stock_drugs]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching low stock items: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/expiring-soon', methods=['GET'])
def get_expiring_soon():
    """Get drugs expiring soon"""
    try:
        days_threshold = int(request.args.get('days', 30))
        expiring_drugs = Drug.get_expiring_soon(days_threshold)

        from collections import defaultdict
        by_month = defaultdict(list)
        for drug in expiring_drugs:
            if drug.expiry_date:
                month_key = drug.expiry_date.strftime('%Y-%m')
                by_month[month_key].append(drug.to_dict())

        return jsonify({
            'success': True,
            'summary': {
                'total_expiring': len(expiring_drugs),
                'days_threshold': days_threshold,
                'by_month': dict(by_month)
            },
            'drugs': [drug.to_dict() for drug in expiring_drugs]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching expiring drugs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/inventory/value', methods=['GET'])
def get_inventory_value():
    """Calculate total inventory value"""
    try:
        drugs = Drug.query.filter(Drug.stock_quantity > 0).all()

        total_value = sum(drug.get_stock_value() for drug in drugs)
        total_items = sum(drug.stock_quantity for drug in drugs)
        unique_drugs = len(drugs)

        value_by_category = {}
        for drug in drugs:
            category = drug.category or 'Uncategorized'
            value_by_category[category] = value_by_category.get(category, 0) + drug.get_stock_value()

        return jsonify({
            'success': True,
            'inventory_summary': {
                'total_value': round(total_value, 2),
                'total_items': total_items,
                'unique_drugs': unique_drugs,
                'value_by_category': value_by_category,
                'average_drug_value': round(total_value / unique_drugs, 2) if unique_drugs > 0 else 0
            }
        }), 200

    except Exception as e:
        logger.error(f"Error calculating inventory value: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/batch-update', methods=['POST'])
def batch_update_drugs():
    """Update multiple drugs at once"""
    try:
        data = request.get_json()
        updates = data.get('updates', [])

        updated_drugs = []
        for update in updates:
            drug_id = update.get('drug_id')
            field = update.get('field')
            value = update.get('value')

            if not all([drug_id, field, value]):
                continue

            drug = Drug.query.get(drug_id)
            if drug and hasattr(drug, field):
                setattr(drug, field, value)
                updated_drugs.append(drug.id)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully updated {len(updated_drugs)} drugs',
            'updated_ids': updated_drugs
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in batch update: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@drug_bp.route('/drugs/search', methods=['GET'])
def search_drugs():
    """Search drugs by name, code, or manufacturer"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 20))

        if not query or len(query) < 2:
            return jsonify({'success': True, 'message': 'Search query too short', 'drugs': []}), 200

        results = Drug.query.filter(
            or_(
                Drug.drug_name.ilike(f'%{query}%'),
                Drug.generic_name.ilike(f'%{query}%'),
                Drug.drug_code.ilike(f'%{query}%'),
                Drug.manufacturer.ilike(f'%{query}%')
            )
        ).limit(limit).all()

        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'drugs': [drug.to_dict() for drug in results]
        }), 200

    except Exception as e:
        logger.error(f"Error searching drugs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

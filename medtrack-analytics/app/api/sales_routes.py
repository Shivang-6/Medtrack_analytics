import logging
import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app import db
from app.models.drug import Drug
from app.models.sale import Sale

sales_bp = Blueprint('sales', __name__)
logger = logging.getLogger(__name__)


@sales_bp.route('/sales', methods=['GET'])
def get_sales():
    """Get sales with filtering and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        drug_id = request.args.get('drug_id')
        pharmacy_id = request.args.get('pharmacy_id')
        payment_method = request.args.get('payment_method')

        query = Sale.query

        if start_date:
            query = query.filter(Sale.sale_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Sale.sale_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        if drug_id:
            query = query.filter(Sale.drug_id == int(drug_id))
        if pharmacy_id:
            query = query.filter(Sale.pharmacy_id == int(pharmacy_id))
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)

        paginated_sales = query.order_by(Sale.sale_date.desc(), Sale.sale_datetime.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'page': paginated_sales.page,
            'per_page': paginated_sales.per_page,
            'total_pages': paginated_sales.pages,
            'total_items': paginated_sales.total,
            'sales': [sale.to_dict() for sale in paginated_sales.items]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching sales: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    """Get single sale by ID"""
    try:
        sale = Sale.query.get_or_404(sale_id)
        drug = Drug.query.get(sale.drug_id)

        response = sale.to_dict()
        if drug:
            response['drug_details'] = {
                'drug_name': drug.drug_name,
                'manufacturer': drug.manufacturer,
                'category': drug.category
            }

        return jsonify({'success': True, 'sale': response}), 200

    except Exception as e:
        logger.error(f"Error fetching sale {sale_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 404 if '404' in str(e) else 500


@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    """Create a new sales transaction"""
    try:
        data = request.get_json()

        required_fields = ['drug_id', 'quantity', 'unit_price', 'pharmacy_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        drug = Drug.query.get(int(data['drug_id']))
        if not drug:
            return jsonify({'success': False, 'error': f'Drug with ID {data["drug_id"]} not found'}), 404

        if drug.stock_quantity < int(data['quantity']):
            return jsonify({
                'success': False,
                'error': f'Insufficient stock. Available: {drug.stock_quantity}, Requested: {data["quantity"]}'
            }), 400

        transaction_id = f"SALE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        quantity = int(data['quantity'])
        unit_price = float(data['unit_price'])
        discount = float(data.get('discount', 0))
        tax_rate = float(data.get('tax_rate', 0.08))

        subtotal = unit_price * quantity
        tax_amount = (subtotal - discount) * tax_rate
        total_amount = (subtotal - discount) + tax_amount

        sale = Sale(
            transaction_id=transaction_id,
            drug_id=int(data['drug_id']),
            sale_date=datetime.strptime(data.get('sale_date', datetime.now().date().isoformat()), '%Y-%m-%d').date(),
            quantity=quantity,
            unit_price=unit_price,
            discount=discount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            pharmacy_id=int(data['pharmacy_id']),
            pharmacy_name=data.get('pharmacy_name', 'Unknown Pharmacy'),
            salesperson_id=data.get('salesperson_id'),
            payment_method=data.get('payment_method', 'Cash'),
            insurance_provider=data.get('insurance_provider'),
            prescription_id=data.get('prescription_id')
        )

        db.session.add(sale)

        drug.update_stock(
            quantity_change=-quantity,
            transaction_type='Sale',
            reference_id=transaction_id,
            notes=f'Sale transaction {transaction_id}'
        )

        db.session.commit()
        logger.info(f"Created sale {transaction_id} for ${total_amount}")

        return jsonify({
            'success': True,
            'message': 'Sale recorded successfully',
            'sale': sale.to_dict(),
            'receipt': {
                'transaction_id': transaction_id,
                'date': sale.sale_date.isoformat(),
                'drug_name': drug.drug_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'subtotal': subtotal,
                'discount': discount,
                'tax_amount': tax_amount,
                'total_amount': total_amount
            }
        }), 201

    except ValueError as e:
        return jsonify({'success': False, 'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating sale: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    """Update a sale (limited fields)"""
    try:
        sale = Sale.query.get_or_404(sale_id)
        data = request.get_json()

        updateable_fields = ['payment_method', 'insurance_provider', 'prescription_id']
        for field in updateable_fields:
            if field in data:
                setattr(sale, field, data[field])

        db.session.commit()

        return jsonify({'success': True, 'message': 'Sale updated successfully', 'sale': sale.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating sale {sale_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/analytics/daily', methods=['GET'])
def get_daily_sales():
    """Get daily sales summary"""
    try:
        target_date = request.args.get('date', date.today().isoformat())
        daily_sales = Sale.get_daily_sales(datetime.strptime(target_date, '%Y-%m-%d').date())
        return jsonify({'success': True, 'analytics': daily_sales}), 200

    except Exception as e:
        logger.error(f"Error fetching daily sales: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/analytics/period', methods=['GET'])
def get_sales_by_period():
    """Get sales analytics for a date period"""
    try:
        start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
        end_date = request.args.get('end_date', date.today().isoformat())

        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        period_sales = Sale.get_sales_by_period(start, end)
        return jsonify({'success': True, 'analytics': period_sales}), 200

    except Exception as e:
        logger.error(f"Error fetching period sales: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/analytics/top-drugs', methods=['GET'])
def get_top_drugs():
    """Get top-selling drugs by revenue or quantity"""
    try:
        limit = int(request.args.get('limit', 10))
        by = request.args.get('by', 'revenue')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = db.session.query(
            Sale.drug_id,
            Drug.drug_name,
            Drug.manufacturer,
            func.sum(Sale.quantity).label('total_quantity'),
            func.sum(Sale.total_amount).label('total_revenue'),
            func.count(Sale.id).label('transaction_count')
        ).join(Drug, Sale.drug_id == Drug.id)

        if start_date:
            query = query.filter(Sale.sale_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Sale.sale_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

        query = query.group_by(Sale.drug_id, Drug.drug_name, Drug.manufacturer)

        if by == 'revenue':
            query = query.order_by(func.sum(Sale.total_amount).desc())
        else:
            query = query.order_by(func.sum(Sale.quantity).desc())

        results = query.limit(limit).all()

        top_drugs = []
        for r in results:
            top_drugs.append({
                'drug_id': r[0],
                'drug_name': r[1],
                'manufacturer': r[2],
                'total_quantity': int(r[3]),
                'total_revenue': float(r[4]),
                'transaction_count': r[5],
                'average_sale_value': float(r[4]) / r[5] if r[5] > 0 else 0
            })

        return jsonify({'success': True, 'metric': by, 'limit': limit, 'top_drugs': top_drugs}), 200

    except Exception as e:
        logger.error(f"Error fetching top drugs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/analytics/revenue-trend', methods=['GET'])
def get_revenue_trend():
    """Get revenue trend over time"""
    try:
        period = request.args.get('period', 'monthly')
        months = int(request.args.get('months', 6))

        end_date = date.today()
        start_date = end_date - timedelta(days=30 * months)

        if period == 'daily':
            date_format = func.to_char(Sale.sale_date, 'YYYY-MM-DD')
        elif period == 'weekly':
            date_format = func.to_char(Sale.sale_date, 'IYYY-IW')
        else:
            date_format = func.to_char(Sale.sale_date, 'YYYY-MM')

        results = db.session.query(
            date_format.label('period'),
            func.sum(Sale.total_amount).label('revenue'),
            func.sum(Sale.quantity).label('quantity'),
            func.count(Sale.id).label('transactions')
        ).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        ).group_by(date_format).order_by(date_format).all()

        trend_data = []
        for r in results:
            trend_data.append({
                'period': r[0],
                'revenue': float(r[1]),
                'quantity': int(r[2]),
                'transactions': r[3],
                'avg_transaction_value': float(r[1]) / r[3] if r[3] > 0 else 0
            })

        return jsonify({
            'success': True,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'trend_data': trend_data
        }), 200

    except Exception as e:
        logger.error(f"Error fetching revenue trend: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/analytics/pharmacy-performance', methods=['GET'])
def get_pharmacy_performance():
    """Get sales performance by pharmacy"""
    try:
        limit = int(request.args.get('limit', 10))

        results = db.session.query(
            Sale.pharmacy_id,
            Sale.pharmacy_name,
            func.count(Sale.id).label('transaction_count'),
            func.sum(Sale.total_amount).label('total_revenue'),
            func.sum(Sale.quantity).label('total_quantity'),
            func.avg(Sale.total_amount).label('avg_transaction_value'),
            func.max(Sale.total_amount).label('max_transaction'),
            func.min(Sale.sale_date).label('first_sale'),
            func.max(Sale.sale_date).label('last_sale')
        ).group_by(Sale.pharmacy_id, Sale.pharmacy_name) \
         .order_by(func.sum(Sale.total_amount).desc()) \
         .limit(limit).all()

        pharmacy_performance = []
        for r in results:
            pharmacy_performance.append({
                'pharmacy_id': r[0],
                'pharmacy_name': r[1],
                'transaction_count': r[2],
                'total_revenue': float(r[3]),
                'total_quantity': int(r[4]),
                'avg_transaction_value': float(r[5]) if r[5] else 0,
                'max_transaction': float(r[6]) if r[6] else 0,
                'first_sale': r[7].isoformat() if r[7] else None,
                'last_sale': r[8].isoformat() if r[8] else None,
                'active_days': (r[8] - r[7]).days if r[7] and r[8] else 0
            })

        return jsonify({'success': True, 'limit': limit, 'pharmacies': pharmacy_performance}), 200

    except Exception as e:
        logger.error(f"Error fetching pharmacy performance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sales_bp.route('/sales/analytics/payment-methods', methods=['GET'])
def get_payment_method_analysis():
    """Analyze sales by payment method"""
    try:
        results = db.session.query(
            Sale.payment_method,
            func.count(Sale.id).label('transaction_count'),
            func.sum(Sale.total_amount).label('total_revenue'),
            func.avg(Sale.total_amount).label('avg_transaction_value'),
            func.sum(Sale.discount).label('total_discount')
        ).filter(Sale.payment_method.isnot(None)) \
         .group_by(Sale.payment_method) \
         .order_by(func.sum(Sale.total_amount).desc()).all()

        payment_analysis = []
        total_revenue = sum(float(r[2]) for r in results)

        for r in results:
            revenue_share = (float(r[2]) / total_revenue * 100) if total_revenue > 0 else 0
            payment_analysis.append({
                'payment_method': r[0],
                'transaction_count': r[1],
                'total_revenue': float(r[2]),
                'avg_transaction_value': float(r[3]) if r[3] else 0,
                'total_discount': float(r[4]) if r[4] else 0,
                'revenue_share_percent': round(revenue_share, 2)
            })

        return jsonify({'success': True, 'total_revenue': total_revenue, 'payment_methods': payment_analysis}), 200

    except Exception as e:
        logger.error(f"Error analyzing payment methods: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# app/models/sale.py
from datetime import datetime
from sqlalchemy.orm import validates

from app import db

class Sale(db.Model):
    """Sales transaction model"""
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
    sale_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    pharmacy_id = db.Column(db.Integer, nullable=False)
    pharmacy_name = db.Column(db.String(150))
    salesperson_id = db.Column(db.Integer)
    payment_method = db.Column(db.String(30))
    insurance_provider = db.Column(db.String(100))
    prescription_id = db.Column(db.String(50))

    @validates('quantity')
    def validate_quantity(self, key, value):
        if value <= 0:
            raise ValueError("Quantity must be positive")
        return value

    @validates('unit_price')
    def validate_unit_price(self, key, value):
        if value <= 0:
            raise ValueError("Unit price must be positive")
        return value

    @validates('total_amount')
    def validate_total_amount(self, key, value):
        if value <= 0:
            raise ValueError("Total amount must be positive")
        return value

    def calculate_total(self):
        """Calculate total amount"""
        subtotal = self.unit_price * self.quantity
        discounted = subtotal - self.discount
        total = discounted + self.tax_amount
        return max(total, 0)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'drug_id': self.drug_id,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'sale_datetime': self.sale_datetime.isoformat() if self.sale_datetime else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'discount': float(self.discount) if self.discount else None,
            'tax_amount': float(self.tax_amount) if self.tax_amount else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'pharmacy_id': self.pharmacy_id,
            'pharmacy_name': self.pharmacy_name,
            'payment_method': self.payment_method,
            'insurance_provider': self.insurance_provider,
            'prescription_id': self.prescription_id
        }

    @classmethod
    def get_daily_sales(cls, date=None):
        """Get sales for a specific date or today"""
        from datetime import date as date_class
        query_date = date or date_class.today()

        sales = cls.query.filter_by(sale_date=query_date).all()
        return {
            'date': query_date.isoformat(),
            'total_sales': len(sales),
            'total_revenue': sum(float(s.total_amount) for s in sales),
            'total_quantity': sum(s.quantity for s in sales),
            'transactions': [s.to_dict() for s in sales]
        }

    @classmethod
    def get_sales_by_period(cls, start_date, end_date):
        """Get sales within a date range"""
        sales = cls.query.filter(
            cls.sale_date >= start_date,
            cls.sale_date <= end_date
        ).all()

        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_sales': len(sales),
            'total_revenue': sum(float(s.total_amount) for s in sales),
            'total_quantity': sum(s.quantity for s in sales),
            'transactions': [s.to_dict() for s in sales]
        }

    def __repr__(self):
        return f'<Sale {self.transaction_id}: ${self.total_amount}>'

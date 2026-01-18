# app/models/drug.py
from datetime import datetime
from sqlalchemy.orm import validates

from app import db

class Drug(db.Model):
    """Drug model representing pharmaceutical products"""
    __tablename__ = 'drugs'

    id = db.Column(db.Integer, primary_key=True)
    drug_code = db.Column(db.String(20), unique=True, nullable=False)
    drug_name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200))
    manufacturer = db.Column(db.String(150), nullable=False)
    drug_class = db.Column(db.String(100))
    category = db.Column(db.String(50))
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2))
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    max_stock_level = db.Column(db.Integer, default=1000)
    expiry_date = db.Column(db.Date)
    storage_conditions = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sales = db.relationship('Sale', backref='drug', lazy=True)
    prescriptions = db.relationship('Prescription', backref='drug', lazy=True)
    inventory_transactions = db.relationship('InventoryTransaction', backref='drug', lazy=True)

    @validates('unit_price')
    def validate_unit_price(self, key, value):
        if value <= 0:
            raise ValueError("Unit price must be positive")
        return value

    @validates('stock_quantity')
    def validate_stock_quantity(self, key, value):
        if value < 0:
            raise ValueError("Stock quantity cannot be negative")
        return value

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'drug_code': self.drug_code,
            'drug_name': self.drug_name,
            'generic_name': self.generic_name,
            'manufacturer': self.manufacturer,
            'drug_class': self.drug_class,
            'category': self.category,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'stock_quantity': self.stock_quantity,
            'min_stock_level': self.min_stock_level,
            'max_stock_level': self.max_stock_level,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'storage_conditions': self.storage_conditions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'needs_restock': self.needs_restock(),
            'stock_value': self.get_stock_value(),
            'days_to_expiry': self.get_days_to_expiry()
        }

    def needs_restock(self, threshold_multiplier=1.0):
        """Check if drug needs restocking"""
        return self.stock_quantity <= (self.min_stock_level * threshold_multiplier)

    def get_stock_value(self):
        """Calculate total value of stock"""
        if self.unit_price and self.stock_quantity:
            return float(self.unit_price * self.stock_quantity)
        return 0.0

    def get_days_to_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            delta = self.expiry_date - datetime.utcnow().date()
            return delta.days if delta.days > 0 else 0
        return None

    def update_stock(self, quantity_change, transaction_type, reference_id=None, notes=None):
        """Update stock quantity and create inventory transaction"""
        from app.models.inventory_transaction import InventoryTransaction

        previous_quantity = self.stock_quantity
        self.stock_quantity += quantity_change

        if self.stock_quantity < 0:
            raise ValueError("Stock cannot go below zero")

        # Create inventory transaction
        transaction = InventoryTransaction(
            drug_id=self.id,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            previous_quantity=previous_quantity,
            new_quantity=self.stock_quantity,
            reference_id=reference_id,
            notes=notes
        )

        db.session.add(transaction)
        return transaction

    @classmethod
    def get_low_stock_items(cls, threshold_multiplier=1.5):
        """Get all drugs that are low in stock"""
        return cls.query.filter(
            cls.stock_quantity <= (cls.min_stock_level * threshold_multiplier)
        ).order_by(cls.stock_quantity.asc()).all()

    @classmethod
    def get_expiring_soon(cls, days_threshold=30):
        """Get drugs expiring within specified days"""
        from datetime import date, timedelta
        expiry_threshold = date.today() + timedelta(days=days_threshold)

        return cls.query.filter(
            cls.expiry_date <= expiry_threshold,
            cls.expiry_date >= date.today()
        ).order_by(cls.expiry_date.asc()).all()

    def __repr__(self):
        return f'<Drug {self.drug_code}: {self.drug_name}>'

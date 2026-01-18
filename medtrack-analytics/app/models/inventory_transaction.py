# app/models/inventory_transaction.py
from datetime import datetime

from app import db

class InventoryTransaction(db.Model):
    """Inventory transaction tracking model"""
    __tablename__ = 'inventory_transactions'

    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey('drugs.id'), nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_type = db.Column(db.String(20))
    quantity_change = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer)
    new_quantity = db.Column(db.Integer)
    reference_id = db.Column(db.String(100))
    reference_type = db.Column(db.String(50))
    performed_by = db.Column(db.Integer)
    notes = db.Column(db.Text)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'drug_id': self.drug_id,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'transaction_type': self.transaction_type,
            'quantity_change': self.quantity_change,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'reference_id': self.reference_id,
            'reference_type': self.reference_type,
            'performed_by': self.performed_by,
            'notes': self.notes
        }

    @classmethod
    def get_transactions_by_drug(cls, drug_id, limit=100):
        """Get recent transactions for a specific drug"""
        return cls.query.filter_by(drug_id=drug_id)\
            .order_by(cls.transaction_date.desc())\
            .limit(limit).all()

    @classmethod
    def get_stock_movement_summary(cls, start_date, end_date):
        """Get summary of stock movements within date range"""
        from sqlalchemy import func

        result = db.session.query(
            cls.transaction_type,
            func.sum(cls.quantity_change).label('total_quantity'),
            func.count(cls.id).label('transaction_count')
        ).filter(
            cls.transaction_date >= start_date,
            cls.transaction_date <= end_date
        ).group_by(cls.transaction_type).all()

        return [
            {
                'transaction_type': r[0],
                'total_quantity': r[1],
                'transaction_count': r[2]
            }
            for r in result
        ]

    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type}: {self.quantity_change}>'

import json
import logging
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import func

from app import db
from app.models.drug import Drug
from app.models.patient import Patient
from app.models.sale import Sale


class DataQualityMonitor:
    """Monitor and maintain data quality across the system"""

    def __init__(self):
        self.logger = logging.getLogger('data_quality')

    def check_completeness(self, table_name):
        """Check data completeness for a table"""
        self.logger.info(f"Checking completeness for {table_name}")

        if table_name == 'drugs':
            total = Drug.query.count()
            complete = (
                Drug.query.filter(
                    Drug.drug_code.isnot(None),
                    Drug.drug_name.isnot(None),
                    Drug.manufacturer.isnot(None),
                    Drug.unit_price.isnot(None),
                ).count()
            )
        elif table_name == 'sales':
            total = Sale.query.count()
            complete = (
                Sale.query.filter(
                    Sale.transaction_id.isnot(None),
                    Sale.drug_id.isnot(None),
                    Sale.sale_date.isnot(None),
                    Sale.total_amount.isnot(None),
                ).count()
            )
        elif table_name == 'patients':
            total = Patient.query.count()
            complete = (
                Patient.query.filter(
                    Patient.first_name.isnot(None),
                    Patient.last_name.isnot(None),
                    Patient.date_of_birth.isnot(None),
                ).count()
            )
        else:
            return {'error': f'Unknown table: {table_name}'}

        completeness_rate = (complete / total * 100) if total > 0 else 0

        return {
            'table': table_name,
            'total_records': total,
            'complete_records': complete,
            'completeness_rate': round(completeness_rate, 2),
            'timestamp': datetime.now().isoformat(),
        }

    def check_consistency(self):
        """Check data consistency across tables"""
        self.logger.info('Checking data consistency')

        orphaned_sales = (
            db.session.query(Sale)
            .filter(~Sale.drug_id.in_(db.session.query(Drug.id)))
            .count()
        )

        negative_stock = Drug.query.filter(Drug.stock_quantity < 0).count()

        future_sales = Sale.query.filter(Sale.sale_date > date.today()).count()

        expired_drugs = (
            Drug.query.filter(
                Drug.expiry_date < date.today(), Drug.stock_quantity > 0
            ).count()
        )

        return {
            'orphaned_sales': orphaned_sales,
            'negative_stock': negative_stock,
            'future_sales': future_sales,
            'expired_drugs_in_stock': expired_drugs,
            'timestamp': datetime.now().isoformat(),
        }

    def check_accuracy(self):
        """Check data accuracy through business rules"""
        self.logger.info('Checking data accuracy')

        issues = []

        invalid_prices = Drug.query.filter(Drug.unit_price <= 0).all()
        if invalid_prices:
            issues.append(
                {
                    'rule': 'Unit price must be positive',
                    'violations': len(invalid_prices),
                    'example': f"Drug ID: {invalid_prices[0].id}" if invalid_prices else None,
                }
            )

        invalid_quantities = Sale.query.filter(Sale.quantity <= 0).all()
        if invalid_quantities:
            issues.append(
                {
                    'rule': 'Sale quantity must be positive',
                    'violations': len(invalid_quantities),
                    'example': f"Sale ID: {invalid_quantities[0].id}" if invalid_quantities else None,
                }
            )

        invalid_ages = Patient.query.filter(
            (Patient.age < 0) | (Patient.age > 120)
        ).all()
        if invalid_ages:
            issues.append(
                {
                    'rule': 'Patient age must be between 0 and 120',
                    'violations': len(invalid_ages),
                    'example': f"Patient ID: {invalid_ages[0].id}" if invalid_ages else None,
                }
            )

        invalid_discounts = Sale.query.filter(
            Sale.discount > (Sale.unit_price * Sale.quantity)
        ).all()
        if invalid_discounts:
            issues.append(
                {
                    'rule': 'Discount cannot exceed sale amount',
                    'violations': len(invalid_discounts),
                    'example': f"Sale ID: {invalid_discounts[0].id}" if invalid_discounts else None,
                }
            )

        return {
            'total_issues': len(issues),
            'issues': issues,
            'timestamp': datetime.now().isoformat(),
        }

    def check_timeliness(self):
        """Check data timeliness (how up-to-date is the data)"""
        self.logger.info('Checking data timeliness')

        last_sale = Sale.query.order_by(Sale.sale_date.desc()).first()
        last_sale_date = last_sale.sale_date if last_sale else None

        if last_sale_date:
            days_since_last_sale = (date.today() - last_sale_date).days
        else:
            days_since_last_sale = None

        week_ago = date.today() - pd.Timedelta(days=7)
        recent_sales = Sale.query.filter(Sale.sale_date >= week_ago).count()
        recent_patients = Patient.query.filter(
            Patient.created_at >= week_ago
        ).count()

        return {
            'last_sale_date': last_sale_date.isoformat() if last_sale_date else None,
            'days_since_last_sale': days_since_last_sale,
            'recent_sales_7_days': recent_sales,
            'recent_patients_7_days': recent_patients,
            'timestamp': datetime.now().isoformat(),
        }

    def run_comprehensive_quality_check(self):
        """Run all quality checks and generate report"""
        self.logger.info('Running comprehensive data quality check')

        report = {'execution_time': datetime.now().isoformat(), 'checks': {}}

        tables = ['drugs', 'sales', 'patients']
        for table in tables:
            report['checks'][f'completeness_{table}'] = self.check_completeness(table)

        report['checks']['consistency'] = self.check_consistency()
        report['checks']['accuracy'] = self.check_accuracy()
        report['checks']['timeliness'] = self.check_timeliness()

        completeness_scores = []
        for table in tables:
            score = report['checks'][f'completeness_{table}'].get(
                'completeness_rate', 0
            )
            completeness_scores.append(score)

        avg_completeness = np.mean(completeness_scores) if completeness_scores else 0

        consistency_score = 100
        consistency_issues = report['checks']['consistency']
        total_consistency_issues = sum(consistency_issues.values())
        if total_consistency_issues > 0:
            consistency_score = max(0, 100 - (total_consistency_issues * 10))

        accuracy_score = 100
        accuracy_issues = report['checks']['accuracy']['total_issues']
        if accuracy_issues > 0:
            accuracy_score = max(0, 100 - (accuracy_issues * 5))

        timeliness_score = 100
        days_since_sale = report['checks']['timeliness']['days_since_last_sale']
        if days_since_sale is not None and days_since_sale > 7:
            timeliness_score = max(0, 100 - ((days_since_sale - 7) * 5))

        overall_score = (
            avg_completeness * 0.4
            + consistency_score * 0.3
            + accuracy_score * 0.2
            + timeliness_score * 0.1
        )

        report['quality_score'] = {
            'completeness': round(avg_completeness, 2),
            'consistency': consistency_score,
            'accuracy': accuracy_score,
            'timeliness': timeliness_score,
            'overall': round(overall_score, 2),
            'grade': self._get_quality_grade(overall_score),
        }

        self._save_quality_report(report)

        return report

    def _get_quality_grade(self, score):
        """Convert score to letter grade"""
        if score >= 90:
            return 'A'
        if score >= 80:
            return 'B'
        if score >= 70:
            return 'C'
        if score >= 60:
            return 'D'
        return 'F'

    def _save_quality_report(self, report):
        """Save quality report to file"""
        reports_dir = Path('reports/quality')
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f'quality_report_{timestamp}.json'

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Quality report saved: {report_file}")

    def fix_data_issues(self):
        """Attempt to automatically fix common data issues"""
        self.logger.info('Attempting to fix data issues')

        fixes_applied = []

        negative_stock_drugs = Drug.query.filter(Drug.stock_quantity < 0).all()
        for drug in negative_stock_drugs:
            old_value = drug.stock_quantity
            drug.stock_quantity = 0
            fixes_applied.append(
                {
                    'table': 'drugs',
                    'id': drug.id,
                    'field': 'stock_quantity',
                    'old_value': old_value,
                    'new_value': 0,
                    'fix_type': 'Negative to zero',
                }
            )

        orphaned_sales = db.session.query(Sale).filter(
            ~Sale.drug_id.in_(db.session.query(Drug.id))
        ).all()
        for sale in orphaned_sales:
            db.session.delete(sale)
            fixes_applied.append(
                {
                    'table': 'sales',
                    'id': sale.id,
                    'field': 'all',
                    'old_value': 'Exists',
                    'new_value': 'Deleted',
                    'fix_type': 'Remove orphaned record',
                }
            )

        future_sales = Sale.query.filter(Sale.sale_date > date.today()).all()
        for sale in future_sales:
            old_date = sale.sale_date
            sale.sale_date = date.today()
            fixes_applied.append(
                {
                    'table': 'sales',
                    'id': sale.id,
                    'field': 'sale_date',
                    'old_value': old_date.isoformat(),
                    'new_value': date.today().isoformat(),
                    'fix_type': 'Future date correction',
                }
            )

        if fixes_applied:
            db.session.commit()
            self.logger.info(f"Applied {len(fixes_applied)} fixes")

        return {
            'fixes_applied': len(fixes_applied),
            'details': fixes_applied,
            'timestamp': datetime.now().isoformat(),
        }

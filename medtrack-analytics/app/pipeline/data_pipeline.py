import json
import logging
import os
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker
from sqlalchemy import create_engine

from app import db
from app.models.drug import Drug
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.sale import Sale


class PharmaDataPipeline:
    """Main data pipeline class for pharmaceutical data processing"""

    def __init__(self, config_path='config/pipeline_config.json'):
        self.logger = self._setup_logging()
        self.faker = Faker()
        self.config = self._load_config(config_path)

        # Database connection
        self.db_engine = create_engine(os.getenv('DATABASE_URL'))

        # Pipeline statistics
        self.stats = {
            'files_processed': 0,
            'records_processed': 0,
            'errors': 0,
            'warnings': 0,
            'start_time': None,
            'end_time': None,
        }

        self.logger.info('PharmaDataPipeline initialized')

    def _setup_logging(self):
        """Setup logging configuration"""
        logger = logging.getLogger('data_pipeline')
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers if re-instantiated
        if not logger.handlers:
            file_handler = logging.FileHandler('logs/data_pipeline.log')
            console_handler = logging.StreamHandler()

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def _load_config(self, config_path):
        """Load pipeline configuration"""
        default_config = {
            'data_sources': {
                'drugs': 'data/raw/drugs.csv',
                'sales': 'data/raw/sales.csv',
                'patients': 'data/raw/patients.csv',
                'prescriptions': 'data/raw/prescriptions.csv',
            },
            'processing': {
                'chunk_size': 1000,
                'max_errors': 10,
                'validate_data': True,
                'backup_raw_data': True,
            },
            'output': {
                'clean_data_path': 'data/processed/',
                'archive_path': 'data/archive/',
                'reports_path': 'reports/',
            },
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.logger.info(f"Loaded config from {config_path}")
                    return {**default_config, **config}
            else:
                self.logger.warning(
                    f"Config file {config_path} not found, using defaults"
                )
                return default_config
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Error loading config: {str(e)}")
            return default_config

    def extract_data(self, source_type, file_path=None):
        """
        Extract data from various sources
        Supported source_types: 'csv', 'excel', 'api', 'database'
        """
        self.logger.info(f"Extracting data from {source_type}")

        try:
            if source_type == 'csv':
                if not file_path:
                    file_path = self.config['data_sources'].get(
                        'drugs', 'data/raw/drugs.csv'
                    )

                # Read CSV with error handling
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin-1')

                self.logger.info(
                    f"Extracted {len(df)} rows from CSV: {file_path}"
                )
                return df

            if source_type == 'excel':
                if not file_path:
                    file_path = self.config['data_sources'].get(
                        'sales', 'data/raw/sales.xlsx'
                    )

                df = pd.read_excel(file_path)
                self.logger.info(
                    f"Extracted {len(df)} rows from Excel: {file_path}"
                )
                return df

            if source_type == 'database':
                table_name = file_path or 'drugs'
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql(query, self.db_engine)
                self.logger.info(
                    f"Extracted {len(df)} rows from database table: {table_name}"
                )
                return df

            if source_type == 'api':
                self.logger.info('API data extraction not implemented in demo')
                return pd.DataFrame()

            raise ValueError(f"Unsupported source type: {source_type}")

        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Error extracting data: {str(e)}")
            raise

    def transform_drugs(self, df):
        """Transform drugs data"""
        self.logger.info('Transforming drugs data')
        df_clean = df.copy()

        column_mapping = {
            'DrugCode': 'drug_code',
            'DrugName': 'drug_name',
            'GenericName': 'generic_name',
            'Manufacturer': 'manufacturer',
            'Category': 'category',
            'UnitPrice': 'unit_price',
            'Stock': 'stock_quantity',
            'ExpiryDate': 'expiry_date',
            'Drug_ID': 'drug_code',
            'Product_Name': 'drug_name',
            'MFR': 'manufacturer',
        }
        df_clean.columns = [column_mapping.get(col, col) for col in df_clean.columns]

        if 'unit_price' in df_clean.columns:
            df_clean['unit_price'] = pd.to_numeric(
                df_clean['unit_price'], errors='coerce'
            )

        if 'stock_quantity' in df_clean.columns:
            df_clean['stock_quantity'] = (
                pd.to_numeric(df_clean['stock_quantity'], errors='coerce')
                .fillna(0)
                .astype(int)
            )

        if 'expiry_date' in df_clean.columns:
            df_clean['expiry_date'] = pd.to_datetime(
                df_clean['expiry_date'], errors='coerce'
            )

        df_clean = df_clean.dropna(subset=['drug_code', 'drug_name'])

        if 'category' not in df_clean.columns:
            df_clean['category'] = 'Prescription'

        if 'min_stock_level' not in df_clean.columns:
            df_clean['min_stock_level'] = 10

        if 'max_stock_level' not in df_clean.columns:
            df_clean['max_stock_level'] = 1000

        df_clean['stock_value'] = df_clean['unit_price'] * df_clean['stock_quantity']

        if 'expiry_date' in df_clean.columns:
            df_clean['days_to_expiry'] = (
                df_clean['expiry_date'] - pd.Timestamp.today()
            ).dt.days

        self.logger.info(f"Transformed {len(df_clean)} drug records")
        return df_clean

    def transform_sales(self, df):
        """Transform sales data"""
        self.logger.info('Transforming sales data')
        df_clean = df.copy()

        column_mapping = {
            'TransactionID': 'transaction_id',
            'SaleDate': 'sale_date',
            'DrugID': 'drug_id',
            'Quantity': 'quantity',
            'Price': 'unit_price',
            'Total': 'total_amount',
            'Pharmacy': 'pharmacy_name',
            'PaymentMethod': 'payment_method',
        }
        df_clean.columns = [column_mapping.get(col, col) for col in df_clean.columns]

        if 'sale_date' in df_clean.columns:
            df_clean['sale_date'] = pd.to_datetime(
                df_clean['sale_date'], errors='coerce'
            )

        for col in ['quantity', 'unit_price', 'total_amount', 'discount', 'tax_amount']:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        if 'total_amount' not in df_clean.columns and all(
            col in df_clean.columns for col in ['unit_price', 'quantity']
        ):
            df_clean['total_amount'] = df_clean['unit_price'] * df_clean['quantity']

        df_clean['year'] = df_clean['sale_date'].dt.year
        df_clean['month'] = df_clean['sale_date'].dt.month
        df_clean['day'] = df_clean['sale_date'].dt.day
        df_clean['day_of_week'] = df_clean['sale_date'].dt.day_name()

        df_clean = df_clean.dropna(subset=['transaction_id', 'drug_id', 'sale_date'])
        df_clean = df_clean[df_clean['quantity'] > 0]

        self.logger.info(f"Transformed {len(df_clean)} sales records")
        return df_clean

    def transform_patients(self, df):
        """Transform patient data"""
        self.logger.info('Transforming patient data')
        df_clean = df.copy()

        column_mapping = {
            'PatientID': 'patient_code',
            'FirstName': 'first_name',
            'LastName': 'last_name',
            'DOB': 'date_of_birth',
            'Gender': 'gender',
            'Email': 'email',
            'Phone': 'phone',
            'Condition': 'primary_condition',
            'Insurance': 'insurance_id',
        }
        df_clean.columns = [column_mapping.get(col, col) for col in df_clean.columns]

        if 'date_of_birth' in df_clean.columns:
            df_clean['date_of_birth'] = pd.to_datetime(
                df_clean['date_of_birth'], errors='coerce'
            )
            today = pd.Timestamp.today()
            df_clean['age'] = (
                (today - df_clean['date_of_birth']).dt.days / 365.25
            ).astype(int)

        if 'email' in df_clean.columns:
            email_mask = df_clean['email'].str.contains('@', na=False)
            df_clean.loc[~email_mask, 'email'] = None

        if 'gender' in df_clean.columns:
            df_clean['gender'] = df_clean['gender'].str.upper().map(
                {
                    'M': 'Male',
                    'MALE': 'Male',
                    'F': 'Female',
                    'FEMALE': 'Female',
                    'O': 'Other',
                    'OTHER': 'Other',
                }
            )

        df_clean = df_clean.dropna(subset=['first_name', 'last_name', 'date_of_birth'])

        if 'patient_code' not in df_clean.columns:
            import uuid

            df_clean['patient_code'] = [
                f"PAT-{str(uuid.uuid4())[:8].upper()}" for _ in range(len(df_clean))
            ]

        self.logger.info(f"Transformed {len(df_clean)} patient records")
        return df_clean

    def validate_data_quality(self, df, data_type):
        """Validate data quality and create quality report"""
        self.logger.info(f"Validating {data_type} data quality")

        validation_report = {
            'data_type': data_type,
            'timestamp': datetime.now().isoformat(),
            'total_records': len(df),
            'valid_records': 0,
            'invalid_records': 0,
            'quality_score': 0,
            'issues': [],
        }

        if data_type == 'drugs':
            required_fields = ['drug_code', 'drug_name', 'manufacturer', 'unit_price']
            numeric_fields = ['unit_price', 'stock_quantity']
            date_fields = ['expiry_date']
        elif data_type == 'sales':
            required_fields = ['transaction_id', 'drug_id', 'sale_date', 'quantity']
            numeric_fields = ['quantity', 'unit_price', 'total_amount']
            date_fields = ['sale_date']
        elif data_type == 'patients':
            required_fields = ['first_name', 'last_name', 'date_of_birth']
            numeric_fields = ['age']
            date_fields = ['date_of_birth']
        else:
            required_fields = []
            numeric_fields = []
            date_fields = []

        for field in required_fields:
            if field in df.columns:
                null_count = df[field].isna().sum()
                if null_count > 0:
                    validation_report['issues'].append(
                        {
                            'field': field,
                            'issue': f'Missing values: {null_count}',
                            'severity': 'High',
                        }
                    )

        for field in numeric_fields:
            if field in df.columns:
                non_numeric = (~pd.to_numeric(df[field], errors='coerce').notna()).sum()
                if non_numeric > 0:
                    validation_report['issues'].append(
                        {
                            'field': field,
                            'issue': f'Non-numeric values: {non_numeric}',
                            'severity': 'Medium',
                        }
                    )

        for field in date_fields:
            if field in df.columns:
                invalid_dates = df[field].isna().sum()
                if invalid_dates > 0:
                    validation_report['issues'].append(
                        {
                            'field': field,
                            'issue': f'Invalid dates: {invalid_dates}',
                            'severity': 'Medium',
                        }
                    )

        total_issues = len(validation_report['issues'])
        validation_report['invalid_records'] = total_issues
        validation_report['valid_records'] = (
            validation_report['total_records'] - total_issues
        )

        if validation_report['total_records'] > 0:
            validation_report['quality_score'] = round(
                (
                    validation_report['valid_records']
                    / validation_report['total_records']
                )
                * 100,
                2,
            )

        report_file = (
            f"{self.config['output']['reports_path']}quality_report_{data_type}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(validation_report, f, indent=2)

        self.logger.info(f"Data quality report saved: {report_file}")
        return validation_report

    def load_to_database(self, df, table_name, mode='append'):
        """Load transformed data to database"""
        self.logger.info(f"Loading {len(df)} records to {table_name} (mode: {mode})")

        try:
            df.head(0).to_sql(table_name, self.db_engine, if_exists='replace', index=False)

            chunksize = self.config['processing']['chunk_size']
            for i in range(0, len(df), chunksize):
                chunk = df.iloc[i : i + chunksize]
                chunk.to_sql(table_name, self.db_engine, if_exists=mode, index=False)
                self.logger.info(f"Loaded chunk {i // chunksize + 1}")

            self.logger.info(f"Successfully loaded {len(df)} records to {table_name}")
            return True

        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Error loading data to database: {str(e)}")
            return False

    def run_etl_pipeline(self, data_type, source_file=None):
        """Run complete ETL pipeline for specific data type"""
        self.stats['start_time'] = datetime.now()
        self.logger.info(f"Starting {data_type} ETL pipeline")

        try:
            df_raw = self.extract_data('csv', source_file)
            self.stats['records_processed'] = len(df_raw)

            if data_type == 'drugs':
                df_transformed = self.transform_drugs(df_raw)
            elif data_type == 'sales':
                df_transformed = self.transform_sales(df_raw)
            elif data_type == 'patients':
                df_transformed = self.transform_patients(df_raw)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            if self.config['processing']['validate_data']:
                quality_report = self.validate_data_quality(
                    df_transformed, data_type
                )
                if quality_report['quality_score'] < 80:
                    self.logger.warning(
                        f"Low data quality score: {quality_report['quality_score']}%"
                    )
                    self.stats['warnings'] += 1

            success = self.load_to_database(df_transformed, data_type)

            if success:
                if self.config['processing']['backup_raw_data']:
                    self._archive_raw_data(df_raw, data_type)

                self.stats['files_processed'] += 1
                self.logger.info(
                    f"ETL pipeline completed successfully for {data_type}"
                )

            return success

        except Exception as e:  # noqa: BLE001
            self.logger.error(f"ETL pipeline failed for {data_type}: {str(e)}")
            self.stats['errors'] += 1
            return False

        finally:
            self.stats['end_time'] = datetime.now()
            self._save_pipeline_stats()

    def _archive_raw_data(self, df, data_type):
        """Archive raw data for audit purposes"""
        archive_path = self.config['output']['archive_path']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{data_type}_raw_{timestamp}.csv"

        os.makedirs(archive_path, exist_ok=True)
        df.to_csv(os.path.join(archive_path, filename), index=False)
        self.logger.info(f"Raw data archived: {filename}")

    def _save_pipeline_stats(self):
        """Save pipeline statistics"""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            self.stats['duration_seconds'] = duration.total_seconds()

        stats_file = (
            f"{self.config['output']['reports_path']}pipeline_stats_"
            f"{datetime.now().strftime('%Y%m%d')}.json"
        )
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)

        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)

        self.logger.info(f"Pipeline statistics saved: {stats_file}")

    def generate_sample_data(self, data_type, num_records=100):
        """Generate sample data for testing"""
        self.logger.info(f"Generating {num_records} sample {data_type} records")

        if data_type == 'drugs':
            return self._generate_sample_drugs(num_records)
        if data_type == 'sales':
            return self._generate_sample_sales(num_records)
        if data_type == 'patients':
            return self._generate_sample_patients(num_records)
        raise ValueError(f"Unsupported data type for sample generation: {data_type}")

    def _generate_sample_drugs(self, num_records):
        """Generate sample drug data"""
        manufacturers = ['Pfizer', 'GSK', 'Merck', 'AstraZeneca', 'Johnson & Johnson', 'Novartis', 'Roche']
        categories = ['Prescription', 'OTC', 'Controlled', 'Herbal']
        drug_classes = ['Antibiotic', 'Analgesic', 'Antihypertensive', 'Antidiabetic', 'NSAID', 'Antidepressant']

        drugs = []
        for i in range(num_records):
            drug = {
                'drug_code': f"DRG{1000 + i:04d}",
                'drug_name': f"{self.faker.word().capitalize()} {self.faker.word().capitalize()}",
                'generic_name': f"Generic {i + 1}",
                'manufacturer': np.random.choice(manufacturers),
                'drug_class': np.random.choice(drug_classes),
                'category': np.random.choice(categories),
                'unit_price': round(np.random.uniform(5, 150), 2),
                'cost_price': round(np.random.uniform(3, 100), 2),
                'stock_quantity': np.random.randint(0, 1000),
                'min_stock_level': np.random.randint(10, 50),
                'max_stock_level': np.random.randint(500, 2000),
                'expiry_date': (
                    date.today() + timedelta(days=np.random.randint(30, 1095))
                ).isoformat(),
                'storage_conditions': np.random.choice(
                    ['Room Temperature', 'Refrigerated', 'Frozen', 'Protected from Light']
                ),
            }
            drugs.append(drug)

        return pd.DataFrame(drugs)

    def _generate_sample_sales(self, num_records):
        """Generate sample sales data"""
        try:
            drugs_df = pd.read_sql(
                'SELECT id, drug_code, unit_price FROM drugs LIMIT 20', self.db_engine
            )
            drug_ids = drugs_df['id'].tolist()
            drug_prices = dict(zip(drug_ids, drugs_df['unit_price']))
        except Exception:  # noqa: BLE001
            drug_ids = list(range(1, 21))
            drug_prices = {i: np.random.uniform(10, 100) for i in drug_ids}

        pharmacies = ['City Pharmacy', 'Health Plus', 'MediCare', 'Wellness Center', 'QuickCare']
        payment_methods = ['Cash', 'Credit Card', 'Insurance', 'Digital']

        sales = []
        start_date = date.today() - timedelta(days=90)

        for i in range(num_records):
            drug_id = np.random.choice(drug_ids)
            quantity = np.random.randint(1, 20)
            unit_price = drug_prices.get(drug_id, np.random.uniform(10, 100))
            discount = (
                round(np.random.uniform(0, unit_price * 0.2), 2)
                if np.random.random() > 0.7
                else 0
            )
            tax_rate = 0.08

            subtotal = unit_price * quantity
            tax_amount = (subtotal - discount) * tax_rate
            total_amount = subtotal - discount + tax_amount

            sale = {
                'transaction_id': f"SALE-{(10000 + i):05d}",
                'drug_id': drug_id,
                'sale_date': (
                    start_date + timedelta(days=np.random.randint(0, 90))
                ).isoformat(),
                'quantity': quantity,
                'unit_price': round(unit_price, 2),
                'discount': discount,
                'tax_amount': round(tax_amount, 2),
                'total_amount': round(total_amount, 2),
                'pharmacy_id': np.random.randint(100, 110),
                'pharmacy_name': np.random.choice(pharmacies),
                'payment_method': np.random.choice(payment_methods),
            }
            sales.append(sale)

        return pd.DataFrame(sales)

    def _generate_sample_patients(self, num_records):
        """Generate sample patient data"""
        conditions = [
            'Hypertension',
            'Type 2 Diabetes',
            'Asthma',
            'Arthritis',
            'Migraine',
            'Depression',
            'High Cholesterol',
            'COPD',
            'Osteoporosis',
            'GERD',
        ]
        cities = [
            'New York',
            'Los Angeles',
            'Chicago',
            'Houston',
            'Phoenix',
            'Philadelphia',
            'San Antonio',
            'San Diego',
            'Dallas',
            'San Jose',
        ]

        patients = []
        for i in range(num_records):
            dob = self.faker.date_of_birth(minimum_age=18, maximum_age=90)
            age = (date.today() - dob).days // 365

            patient = {
                'patient_code': f"PAT{(1000 + i):04d}",
                'first_name': self.faker.first_name(),
                'last_name': self.faker.last_name(),
                'date_of_birth': dob.isoformat(),
                'age': age,
                'gender': np.random.choice(['Male', 'Female', 'Other']),
                'email': self.faker.email(),
                'phone': self.faker.phone_number(),
                'address': self.faker.address().replace('\n', ', '),
                'city': np.random.choice(cities),
                'state': self.faker.state_abbr(),
                'zip_code': self.faker.zipcode(),
                'primary_condition': np.random.choice(conditions),
                'insurance_id': f"INS{np.random.randint(10000, 99999)}",
            }
            patients.append(patient)

        return pd.DataFrame(patients)

    def run_daily_pipeline(self):
        """Run complete daily data pipeline"""
        self.logger.info('Starting daily data pipeline')

        for path in ['data/raw', 'data/processed', 'data/archive', 'reports', 'logs']:
            os.makedirs(path, exist_ok=True)

        data_types = ['drugs', 'sales', 'patients']
        results = {}

        for data_type in data_types:
            source_file = self.config['data_sources'].get(data_type)
            if source_file and os.path.exists(source_file):
                self.logger.info(f"Processing {data_type} from {source_file}")
                success = self.run_etl_pipeline(data_type, source_file)
                results[data_type] = 'Success' if success else 'Failed'
            else:
                self.logger.warning(
                    f"Source file not found for {data_type}: {source_file}"
                )
                results[data_type] = 'Skipped'

        summary = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'statistics': self.stats,
        }

        summary_file = (
            f"{self.config['output']['reports_path']}daily_pipeline_summary_"
            f"{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        self.logger.info(
            f"Daily pipeline completed. Summary: {summary_file}"
        )
        return results

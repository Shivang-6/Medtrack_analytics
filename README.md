# MedTrack Analytics Platform


A comprehensive pharmaceutical data analytics platform built with modern technologies. This project demonstrates end-to-end software development skills including REST API development, data pipeline engineering, database design, and interactive dashboard creation.


## 🎯 Features

### **Core Functionality**
- **RESTful API** with 25+ endpoints for data management
- **Data Pipeline** with ETL processes and quality monitoring
- **Interactive Dashboard** with real-time analytics
- **Inventory Management** with low stock alerts
- **Sales Analytics** with trend analysis
- **Patient Management** with demographic insights

### **Technical Highlights**
- **Database Design**: Normalized PostgreSQL schema with 7 tables
- **API Development**: Comprehensive CRUD operations with filtering/pagination
- **Data Processing**: Pandas-based ETL pipeline with data validation
- **Frontend**: Responsive dashboard with Chart.js visualizations
- **DevOps**: Docker containerization and deployment ready
- **Testing**: Unit tests with pytest

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Data Pipeline │
│   Dashboard     │◄──►│   Flask REST    │◄──►│   ETL & Quality │
│   HTML/CSS/JS   │    │   SQLAlchemy    │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────┬───────┘
                                                        │
                                                ┌───────▼───────┐
                                                │  PostgreSQL   │
                                                │   Database    │
                                                └───────────────┘
```

## 🛠️ Technology Stack

### **Backend**
- **Python 3.9+** with Flask framework
- **PostgreSQL** with SQLAlchemy ORM
- **RESTful API** design with proper HTTP methods
- **Pandas** for data processing and analysis
- **SQLAlchemy** for database operations

### **Frontend**
- **HTML5/CSS3** with Bootstrap 5
- **JavaScript** with Chart.js for visualizations
- **Responsive Design** for all device sizes

### **DevOps & Tools**
- **Docker** for containerization
- **Docker Compose** for multi-container orchestration
- **Git** for version control
- **pytest** for unit testing
- **Postman** for API testing

## 📋 Prerequisites

- **Python 3.9+**
- **Docker & Docker Compose**
- **Git**
- **PostgreSQL** (or use Docker)
- **Modern web browser**

## 🚀 Quick Start

### **Option 1: Using Docker (Recommended)**
```bash
# Clone the repository
git clone https://github.com/yourusername/medtrack-analytics.git
cd medtrack-analytics

# Start the application
docker-compose up -d

# Access the application
# API: http://localhost:5000
# Dashboard: Open frontend/index.html in browser
```

### **Option 2: Local Development Setup**
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/medtrack-analytics.git
cd medtrack-analytics

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start database
docker-compose up -d postgres

# 5. Set up environment variables
cp .env.example .env

# 6. Run the application
python run.py
```

## 📊 API Documentation

### **Base URL**
```
http://localhost:5000/api
```

### **Key Endpoints**

#### **Health & Information**
```
GET  /health                    # Health check
GET  /                          # API information
```

#### **Drug Management**
```
GET  /drugs                    # List all drugs
GET  /drugs/{id}               # Get specific drug
POST /drugs                    # Create new drug
PUT  /drugs/{id}               # Update drug
GET  /drugs/low-stock          # Get low stock items
GET  /drugs/inventory/value    # Get inventory valuation
GET  /drugs/expiring-soon      # Get expiring drugs
```

#### **Sales Analytics**
```
GET  /sales                    # List sales with pagination
POST /sales                    # Create sale record
GET  /sales/analytics/daily    # Daily sales summary
GET  /sales/analytics/period   # Sales by date range
GET  /sales/analytics/top-drugs # Top selling drugs
GET  /sales/analytics/revenue-trend # Revenue trends
```

#### **Analytics Dashboard**
```
GET  /analytics/dashboard      # Dashboard metrics
GET  /analytics/inventory-health # Inventory analysis
GET  /analytics/patient-demographics # Patient analysis
GET  /analytics/prescription-patterns # Prescription analysis
GET  /analytics/predictive/low-stock-forecast # Predictive analytics
```

#### **Data Pipeline**
```
POST /pipeline/run             # Run data pipeline
GET  /pipeline/status          # Pipeline status
GET  /pipeline/quality         # Data quality check
GET  /pipeline/logs            # Pipeline logs
```

### **Sample API Requests**

```bash
# Get dashboard analytics
curl http://localhost:5000/api/analytics/dashboard

# Get low stock items
curl http://localhost:5000/api/drugs/low-stock

# Create a new drug
curl -X POST http://localhost:5000/api/drugs \
  -H "Content-Type: application/json" \
  -d '{
    "drug_code": "PAN500",
    "drug_name": "Panadol Extra",
    "manufacturer": "GSK",
    "category": "OTC",
    "unit_price": 5.99,
    "stock_quantity": 150
  }'
```

## 🗄️ Database Schema

The system uses a normalized database schema with the following tables:

### **Core Tables**
1. **drugs** - Pharmaceutical products with inventory details
2. **sales** - Sales transactions and revenue data
3. **patients** - Patient demographics and medical information
4. **prescriptions** - Doctor prescriptions and medication details
5. **inventory_transactions** - Stock movement tracking
6. **suppliers** - Drug manufacturers and suppliers
7. **data_quality_logs** - Pipeline monitoring and quality checks

### **Key Views**
- **low_stock_alert** - Real-time low stock monitoring
- **monthly_sales_summary** - Aggregated sales analytics

## 🔧 Data Pipeline

The platform includes a robust data pipeline:

### **ETL Process**
1. **Extract**: From CSV, Excel, or database sources
2. **Transform**: Data cleaning, validation, and enrichment
3. **Load**: To PostgreSQL database with error handling

### **Quality Monitoring**
- Data completeness validation
- Consistency checks across tables
- Accuracy validation with business rules
- Timeliness monitoring

### **Pipeline Features**
- **Scheduled execution** with automated runs
- **Error handling** with detailed logging
- **Data quality reports** with scoring
- **Sample data generation** for testing

## 📁 Project Structure

```
medtrack-analytics/
├── app/                          # Flask Application
│   ├── __init__.py              # Application factory
│   ├── models/                  # Database models (OOP)
│   │   ├── drug.py             # Drug model with business logic
│   │   ├── sale.py             # Sales transaction model
│   │   ├── patient.py          # Patient model with demographics
│   │   ├── prescription.py     # Prescription model
│   │   └── inventory_transaction.py # Stock tracking
│   ├── api/                     # REST API endpoints
│   │   ├── drug_routes.py      # Drug management API
│   │   ├── sales_routes.py     # Sales analytics API
│   │   ├── analytics_routes.py # Business intelligence API
│   │   ├── patient_routes.py   # Patient management API
│   │   └── pipeline_routes.py  # Data pipeline API
│   ├── pipeline/               # Data engineering components
│   │   ├── data_pipeline.py    # ETL pipeline implementation
│   │   ├── data_quality.py     # Data quality monitoring
│   │   └── pipeline_runner.py  # Pipeline scheduler
│   └── tests/                  # Unit tests
│       ├── test_models.py      # Model tests
│       └── test_api.py         # API endpoint tests
├── frontend/                   # Dashboard interface
│   ├── index.html             # Main dashboard
│   ├── js/                    # JavaScript files
│   │   ├── api.js            # API client library
│   │   ├── charts.js         # Chart.js wrapper
│   │   └── dashboard.js      # Dashboard logic
│   └── css/                   # Stylesheets
├── data/                       # Data files
│   ├── raw/                   # Raw input data
│   ├── processed/             # Processed data
│   └── archive/               # Archived data
├── logs/                      # Application logs
├── reports/                   # Generated reports
├── docs/                      # Documentation
├── docker-compose.yml         # Multi-container setup
├── Dockerfile                 # Container configuration
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── README.md                 # This file
└── run.py                    # Application entry point
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/

# Run specific test file
pytest app/tests/test_models.py -v

# Run API tests
pytest app/tests/test_api.py -v
```

## 🐳 Docker Deployment

### **Development**
```bash
# Build and run with Docker Compose
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Production**
```bash
# Build production images
docker build -t medtrack-api:latest .

# Run with production settings
docker run -d -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e FLASK_ENV=production \
  medtrack-api:latest
```

## 📈 Features Demonstration

### **For Axtria Interview Assessment**

This project demonstrates proficiency in **all required skills**:

| **Skill** | **Demonstrated In** |
|-----------|-------------------|
| **Python OOP** | Database models with inheritance and polymorphism |
| **Data Structures** | Efficient data handling with Pandas DataFrames |
| **Algorithms** | Sorting, searching, and data transformation logic |
| **SQL/RDBMS** | Complex queries, joins, and query optimization |
| **RESTful APIs** | 25+ endpoints with proper HTTP methods |
| **Git Version Control** | Proper commit history and branching strategy |
| **Backend Development** | Complete Flask application with middleware |
| **Data Pipelines** | ETL processes with quality monitoring |
| **Frontend (Good to have)** | Interactive dashboard with charts |
| **Cloud (Good to have)** | Docker containerization ready for cloud deploy |
| **Testing** | Comprehensive unit tests with pytest |

## 🎨 Dashboard Features

### **Real-time Analytics**
- **Inventory Health**: Visual stock status with alerts
- **Sales Trends**: Revenue and transaction trends
- **Top Products**: Best-selling drugs by revenue
- **Patient Demographics**: Age and condition distribution
- **Pipeline Monitoring**: ETL process status

### **Interactive Elements**
- **Filtering**: Date range, category, and status filters
- **Search**: Real-time search across data
- **Charts**: Interactive charts with hover details
- **Tables**: Sortable and paginated data tables
- **Alerts**: Real-time notifications for critical issues

## 🔍 Code Quality

### **Best Practices Implemented**
- **Modular Design**: Separated concerns with clear boundaries
- **Error Handling**: Comprehensive error handling and logging
- **Input Validation**: Data validation at API boundaries
- **Security**: Environment variables for sensitive data
- **Documentation**: Code comments and API documentation
- **Testing**: Unit tests for critical functionality

### **Performance Optimizations**
- **Database Indexing**: Proper indexes for frequently queried columns
- **Query Optimization**: Efficient SQL queries with joins
- **Pagination**: API responses paginated for large datasets
- **Caching**: Frontend caching for API responses
- **Lazy Loading**: Database relationships loaded on demand

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


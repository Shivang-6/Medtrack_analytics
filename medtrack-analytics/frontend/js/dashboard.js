class Dashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.lastUpdate = new Date();
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadSection(this.currentSection);
        this.startAutoRefresh();
    }

    setupEventListeners() {
        document.querySelectorAll('.nav-link').forEach((link) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.navigateTo(section);
            });
        });

        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshCurrentSection();
        });

        document.getElementById('runPipelineBtn').addEventListener('click', () => {
            this.runPipeline();
        });

        const pipelineModal = document.getElementById('pipelineModal');
        pipelineModal.addEventListener('hidden.bs.modal', () => {
            this.refreshCurrentSection();
        });
    }

    navigateTo(section) {
        document.querySelectorAll('.nav-link').forEach((link) => {
            link.classList.remove('active');
            if (link.getAttribute('data-section') === section) {
                link.classList.add('active');
            }
        });

        this.currentSection = section;
        this.updatePageTitle(section);
        this.loadSection(section);
    }

    updatePageTitle(section) {
        const titles = {
            dashboard: 'Dashboard Overview',
            inventory: 'Inventory Management',
            sales: 'Sales Analytics',
            patients: 'Patient Management',
            prescriptions: 'Prescription Tracking',
            pipeline: 'Data Pipeline',
            reports: 'Reports',
            settings: 'Settings',
        };

        const subtitles = {
            dashboard: 'Real-time pharmaceutical analytics and insights',
            inventory: 'Monitor stock levels and inventory health',
            sales: 'Analyze sales performance and trends',
            patients: 'Manage patient information and demographics',
            prescriptions: 'Track prescription patterns and compliance',
            pipeline: 'Monitor data pipeline status and quality',
            reports: 'Generate and view analytical reports',
            settings: 'Configure system settings',
        };

        document.getElementById('pageTitle').textContent =
            titles[section] || 'Dashboard';
        document.getElementById('pageSubtitle').textContent =
            subtitles[section] || '';
    }

    async loadSection(section) {
        const container = document.getElementById('contentContainer');

        container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Loading ${section}...</p>
            </div>
        `;

        try {
            let html = '';

            switch (section) {
                case 'dashboard':
                    html = await this.loadDashboard();
                    break;
                case 'inventory':
                    html = await this.loadInventory();
                    break;
                case 'sales':
                    html = await this.loadSales();
                    break;
                case 'patients':
                    html = await this.loadPatients();
                    break;
                case 'prescriptions':
                    html = await this.loadPrescriptions();
                    break;
                case 'pipeline':
                    html = await this.loadPipeline();
                    break;
                case 'reports':
                    html = await this.loadReports();
                    break;
                case 'settings':
                    html = await this.loadSettings();
                    break;
                default:
                    html = await this.loadDashboard();
            }

            container.innerHTML = html;
            this.initializeSection(section);
            this.updateLastUpdated();
        } catch (error) {
            console.error(`Error loading section ${section}:`, error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <h4>Error Loading Content</h4>
                    <p>Failed to load ${section} data. Please try again.</p>
                    <pre class="mt-2">${error.message}</pre>
                </div>
            `;
        }
    }

    async loadDashboard() {
        try {
            const dashboardData = await api.getDashboardData();
            const lowStock = await api.getLowStockDrugs();
            const topDrugs = await api.getTopDrugs(5);
            const revenueTrend = await api.getRevenueTrend('monthly', 6);

            const dashboard = dashboardData.dashboard;
            const salesSummary = dashboard.sales_summary;
            const inventorySummary = dashboard.inventory_summary;
            const patientSummary = dashboard.patient_summary;

            return `
                <div class="row">
                    <div class="col-xl-3 col-md-6">
                        <div class="metric-card success">
                            <div class="metric-value">${api.formatCurrency(salesSummary.total_revenue)}</div>
                            <div class="metric-label">30-Day Revenue</div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-chart-line"></i> ${salesSummary.total_sales} transactions
                                </small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-xl-3 col-md-6">
                        <div class="metric-card">
                            <div class="metric-value">${inventorySummary.total_drugs}</div>
                            <div class="metric-label">Total Drugs</div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-box"></i> ${inventorySummary.total_stock} units in stock
                                </small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-xl-3 col-md-6">
                        <div class="metric-card ${lowStock.summary.critical_count > 0 ? 'danger' : 'warning'}">
                            <div class="metric-value">${lowStock.summary.critical_count}</div>
                            <div class="metric-label">Critical Stock</div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-exclamation-triangle"></i> ${lowStock.summary.total_low_stock} total low stock
                                </small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-xl-3 col-md-6">
                        <div class="metric-card">
                            <div class="metric-value">${patientSummary.total_patients}</div>
                            <div class="metric-label">Total Patients</div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-user-friends"></i> Avg age: ${Math.round(patientSummary.avg_age)}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-lg-8">
                        <div class="chart-container">
                            <canvas id="salesTrendChart" height="250"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="chart-container">
                            <canvas id="topDrugsChart" height="250"></canvas>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-lg-6">
                        <div class="data-table">
                            <h5><i class="fas fa-exclamation-triangle text-warning"></i> Low Stock Alerts</h5>
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Drug</th>
                                            <th>Manufacturer</th>
                                            <th>Stock</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody id="lowStockTable">
                                        ${lowStock.drugs.slice(0, 5).map((drug) => `
                                            <tr>
                                                <td>${drug.drug_name}</td>
                                                <td>${drug.manufacturer}</td>
                                                <td>${drug.stock_quantity}</td>
                                                <td>
                                                    <span class="status-badge ${drug.stock_status === 'CRITICAL' ? 'status-critical' : 'status-warning'}">
                                                        ${drug.stock_status}
                                                    </span>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                            <div class="text-end">
                                <a href="#inventory" class="btn btn-sm btn-outline-primary">View All</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-lg-6">
                        <div class="data-table">
                            <h5><i class="fas fa-chart-line text-success"></i> Top Performing Drugs</h5>
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Drug</th>
                                            <th>Revenue</th>
                                            <th>Quantity</th>
                                            <th>Avg Price</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${topDrugs.top_drugs.map((drug) => `
                                            <tr>
                                                <td>${drug.drug_name}</td>
                                                <td>${api.formatCurrency(drug.total_revenue)}</td>
                                                <td>${api.formatNumber(drug.total_quantity)}</td>
                                                <td>${api.formatCurrency(drug.total_revenue / drug.total_quantity)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-12">
                        <div class="data-table">
                            <h5><i class="fas fa-info-circle text-primary"></i> System Status</h5>
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="text-center p-3">
                                        <div class="h2 mb-0">${Math.round(dashboard.recent_sales_trend[Object.keys(dashboard.recent_sales_trend)[0]]?.revenue || 0)}</div>
                                        <small class="text-muted">Today's Revenue</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center p-3">
                                        <div class="h2 mb-0">${dashboard.recent_sales_trend[Object.keys(dashboard.recent_sales_trend)[0]]?.transactions || 0}</div>
                                        <small class="text-muted">Today's Transactions</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center p-3">
                                        <div class="h2 mb-0">${inventorySummary.low_stock_count}</div>
                                        <small class="text-muted">Low Stock Items</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center p-3">
                                        <div class="h2 mb-0">${dashboard.top_categories.length}</div>
                                        <small class="text-muted">Active Categories</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading dashboard:', error);
            throw error;
        }
    }

    async loadInventory() {
        try {
            const inventory = await api.getInventoryHealth();
            const lowStock = await api.getLowStockDrugs();
            const expiring = await api.getDrugs({ expiring_soon: 'true' });

            return `
                <div class="row">
                    <div class="col-lg-8">
                        <div class="chart-container">
                            <canvas id="inventoryHealthChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="metric-card danger">
                            <div class="metric-value">${inventory.summary.critical}</div>
                            <div class="metric-label">Critical Stock</div>
                        </div>
                        <div class="metric-card warning">
                            <div class="metric-value">${inventory.summary.low}</div>
                            <div class="metric-label">Low Stock</div>
                        </div>
                        <div class="metric-card success">
                            <div class="metric-value">${inventory.summary.healthy}</div>
                            <div class="metric-label">Healthy Stock</div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-12">
                        <div class="data-table">
                            <h5><i class="fas fa-exclamation-triangle text-danger"></i> Critical Stock Items</h5>
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Drug Code</th>
                                            <th>Drug Name</th>
                                            <th>Manufacturer</th>
                                            <th>Current Stock</th>
                                            <th>Min Level</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${lowStock.drugs.filter((d) => d.stock_status === 'CRITICAL').map((drug) => `
                                            <tr>
                                                <td>${drug.drug_code}</td>
                                                <td><strong>${drug.drug_name}</strong></td>
                                                <td>${drug.manufacturer}</td>
                                                <td>
                                                    <span class="badge bg-danger">${drug.stock_quantity}</span>
                                                </td>
                                                <td>${drug.min_stock_level}</td>
                                                <td>
                                                    <span class="status-badge status-critical">CRITICAL</span>
                                                </td>
                                                <td>
                                                    <button class="btn btn-sm btn-outline-primary" onclick="dashboard.reorderDrug(${drug.id})">
                                                        <i class="fas fa-shopping-cart"></i> Reorder
                                                    </button>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading inventory:', error);
            throw error;
        }
    }

    async loadSales() {
        try {
            const revenueTrend = await api.getRevenueTrend('monthly', 6);
            const topDrugs = await api.getTopDrugs(10);
            const paymentMethods = await api.getSalesAnalytics(
                new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
                    .toISOString()
                    .split('T')[0],
                new Date().toISOString().split('T')[0]
            );

            return `
                <div class="row">
                    <div class="col-lg-8">
                        <div class="chart-container">
                            <canvas id="salesTrendChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="chart-container">
                            <canvas id="paymentMethodsChart" height="300"></canvas>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-12">
                        <div class="data-table">
                            <h5><i class="fas fa-chart-bar text-primary"></i> Top Performing Drugs</h5>
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Rank</th>
                                            <th>Drug Name</th>
                                            <th>Manufacturer</th>
                                            <th>Revenue</th>
                                            <th>Quantity</th>
                                            <th>Avg. Price</th>
                                            <th>Transactions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${topDrugs.top_drugs.map((drug, index) => `
                                            <tr>
                                                <td><span class="badge bg-primary">#${index + 1}</span></td>
                                                <td><strong>${drug.drug_name}</strong></td>
                                                <td>${drug.manufacturer}</td>
                                                <td>${api.formatCurrency(drug.total_revenue)}</td>
                                                <td>${api.formatNumber(drug.total_quantity)}</td>
                                                <td>${api.formatCurrency(drug.average_sale_value)}</td>
                                                <td>${api.formatNumber(drug.transaction_count)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading sales:', error);
            throw error;
        }
    }

    async loadPatients() {
        try {
            const demographics = await api.getPatientDemographics();
            const patients = await api.getPatients({ per_page: 10 });

            return `
                <div class="row">
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <canvas id="patientDemographicsChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="data-table">
                            <h5><i class="fas fa-users text-primary"></i> Recent Patients</h5>
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Patient ID</th>
                                            <th>Name</th>
                                            <th>Age</th>
                                            <th>Condition</th>
                                            <th>Location</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${patients.patients.map((patient) => `
                                            <tr>
                                                <td>${patient.patient_code}</td>
                                                <td>${patient.full_name}</td>
                                                <td>${patient.age}</td>
                                                <td>${patient.primary_condition || 'N/A'}</td>
                                                <td>${patient.city}, ${patient.state}</td>
                                                <td>
                                                    <span class="status-badge status-active">Active</span>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-12">
                        <div class="data-table">
                            <h5><i class="fas fa-chart-pie text-success"></i> Top Medical Conditions</h5>
                            <div class="row">
                                ${demographics.demographics.top_conditions.map((condition) => `
                                    <div class="col-md-3 mb-3">
                                        <div class="card">
                                            <div class="card-body text-center">
                                                <h3 class="text-primary">${condition.patient_count}</h3>
                                                <p class="mb-0">${condition.condition}</p>
                                                <small class="text-muted">Avg age: ${Math.round(condition.avg_age)}</small>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading patients:', error);
            throw error;
        }
    }

    async loadPipeline() {
        return `
            <div class="row">
                <div class="col-12">
                    <div class="data-table">
                        <h5><i class="fas fa-cogs text-primary"></i> Data Pipeline Status</h5>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="card text-center mb-3">
                                    <div class="card-body">
                                        <h1 class="display-4 text-success"><i class="fas fa-check-circle"></i></h1>
                                        <h5>ETL Pipeline</h5>
                                        <p class="text-muted">Last run: 2 hours ago</p>
                                        <button class="btn btn-primary" onclick="dashboard.runPipeline()">
                                            Run Now
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center mb-3">
                                    <div class="card-body">
                                        <h1 class="display-4 text-warning"><i class="fas fa-chart-line"></i></h1>
                                        <h5>Data Quality</h5>
                                        <p class="text-muted">Score: 95%</p>
                                        <button class="btn btn-warning" onclick="dashboard.checkQuality()">
                                            Check Quality
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-center mb-3">
                                    <div class="card-body">
                                        <h1 class="display-4 text-info"><i class="fas fa-database"></i></h1>
                                        <h5>Backup Status</h5>
                                        <p class="text-muted">Last backup: 1 day ago</p>
                                        <button class="btn btn-info" onclick="dashboard.runBackup()">
                                            Backup Now
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="mt-4">
                            <h6>Recent Pipeline Runs</h6>
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Run ID</th>
                                            <th>Type</th>
                                            <th>Start Time</th>
                                            <th>Duration</th>
                                            <th>Status</th>
                                            <th>Records Processed</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>RUN-20240115-001</td>
                                            <td>Daily ETL</td>
                                            <td>2024-01-15 02:00</td>
                                            <td>45s</td>
                                            <td><span class="badge bg-success">Success</span></td>
                                            <td>1,245</td>
                                        </tr>
                                        <tr>
                                            <td>RUN-20240114-001</td>
                                            <td>Daily ETL</td>
                                            <td>2024-01-14 02:00</td>
                                            <td>52s</td>
                                            <td><span class="badge bg-success">Success</span></td>
                                            <td>1,198</td>
                                        </tr>
                                        <tr>
                                            <td>RUN-20240113-001</td>
                                            <td>Daily ETL</td>
                                            <td>2024-01-13 02:00</td>
                                            <td>1m 15s</td>
                                            <td><span class="badge bg-warning">Warning</span></td>
                                            <td>1,150</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async loadReports() {
        return `
            <div class="row">
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-file-pdf text-danger"></i> Sales Report</h5>
                            <p class="card-text">Monthly sales performance and revenue analysis.</p>
                            <button class="btn btn-outline-danger" onclick="dashboard.generateReport('sales')">
                                Generate Report
                            </button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-file-excel text-success"></i> Inventory Report</h5>
                            <p class="card-text">Stock levels, turnover rates, and reorder suggestions.</p>
                            <button class="btn btn-outline-success" onclick="dashboard.generateReport('inventory')">
                                Generate Report
                            </button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-file-alt text-primary"></i> Patient Report</h5>
                            <p class="card-text">Patient demographics and prescription patterns.</p>
                            <button class="btn btn-outline-primary" onclick="dashboard.generateReport('patient')">
                                Generate Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-12">
                    <div class="data-table">
                        <h5><i class="fas fa-history"></i> Recent Reports</h5>
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Report Name</th>
                                        <th>Generated On</th>
                                        <th>Type</th>
                                        <th>Size</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Sales_Report_Jan_2024.pdf</td>
                                        <td>2024-01-15 10:30</td>
                                        <td><span class="badge bg-danger">PDF</span></td>
                                        <td>2.4 MB</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary">
                                                <i class="fas fa-download"></i> Download
                                            </button>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Inventory_Status_Jan_2024.xlsx</td>
                                        <td>2024-01-14 09:15</td>
                                        <td><span class="badge bg-success">Excel</span></td>
                                        <td>1.8 MB</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-success">
                                                <i class="fas fa-download"></i> Download
                                            </button>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Patient_Analytics_Jan_2024.pdf</td>
                                        <td>2024-01-13 14:20</td>
                                        <td><span class="badge bg-danger">PDF</span></td>
                                        <td>3.1 MB</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary">
                                                <i class="fas fa-download"></i> Download
                                            </button>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async loadSettings() {
        return `
            <div class="row">
                <div class="col-lg-6">
                    <div class="data-table">
                        <h5><i class="fas fa-cog"></i> System Settings</h5>
                        <form id="settingsForm">
                            <div class="mb-3">
                                <label class="form-label">Auto-refresh Interval</label>
                                <select class="form-select" id="refreshInterval">
                                    <option value="30000">30 seconds</option>
                                    <option value="60000" selected>1 minute</option>
                                    <option value="300000">5 minutes</option>
                                    <option value="600000">10 minutes</option>
                                    <option value="0">Disabled</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Low Stock Threshold</label>
                                <input type="range" class="form-range" id="stockThreshold" min="1" max="3" step="0.1" value="1.5">
                                <div class="text-end">
                                    <span id="thresholdValue">1.5x</span> of minimum stock level
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Data Retention (days)</label>
                                <input type="number" class="form-control" id="dataRetention" value="365" min="30" max="1095">
                            </div>
                            <button type="submit" class="btn btn-primary">Save Settings</button>
                        </form>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="data-table">
                        <h5><i class="fas fa-database"></i> Database Information</h5>
                        <div class="list-group">
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between">
                                    <span>Total Tables</span>
                                    <span class="badge bg-primary">7</span>
                                </div>
                            </div>
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between">
                                    <span>Total Records</span>
                                    <span class="badge bg-success">12,458</span>
                                </div>
                            </div>
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between">
                                    <span>Database Size</span>
                                    <span class="badge bg-info">245 MB</span>
                                </div>
                            </div>
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between">
                                    <span>Last Backup</span>
                                    <span>2024-01-14 00:00</span>
                                </div>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button class="btn btn-outline-danger w-100" onclick="dashboard.clearDatabase()">
                                <i class="fas fa-trash"></i> Clear Test Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    initializeSection(section) {
        setTimeout(() => {
            switch (section) {
                case 'dashboard':
                    this.initializeDashboard();
                    break;
                case 'inventory':
                    this.initializeInventory();
                    break;
                case 'sales':
                    this.initializeSales();
                    break;
                case 'patients':
                    this.initializePatients();
                    break;
                case 'pipeline':
                    this.initializePipeline();
                    break;
                case 'settings':
                    this.initializeSettings();
                    break;
            }
        }, 100);
    }

    async initializeDashboard() {
        try {
            const revenueTrend = await api.getRevenueTrend('monthly', 6);
            const topDrugs = await api.getTopDrugs(5);

            chartManager.createSalesTrendChart(revenueTrend);
            chartManager.createTopDrugsChart(topDrugs);
        } catch (error) {
            console.error('Error initializing dashboard charts:', error);
        }
    }

    async initializeInventory() {
        try {
            const inventory = await api.getInventoryHealth();
            chartManager.createInventoryHealthChart(inventory);
        } catch (error) {
            console.error('Error initializing inventory charts:', error);
        }
    }

    async initializeSales() {
        try {
            const revenueTrend = await api.getRevenueTrend('monthly', 6);
            const paymentMethods = await api.getSalesAnalytics(
                new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
                    .toISOString()
                    .split('T')[0],
                new Date().toISOString().split('T')[0]
            );

            chartManager.createSalesTrendChart(revenueTrend);
            chartManager.createPaymentMethodsChart(paymentMethods);
        } catch (error) {
            console.error('Error initializing sales charts:', error);
        }
    }

    async initializePatients() {
        try {
            const demographics = await api.getPatientDemographics();
            chartManager.createPatientDemographicsChart(demographics);
        } catch (error) {
            console.error('Error initializing patient charts:', error);
        }
    }

    initializePipeline() {
        const form = document.getElementById('settingsForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }
    }

    initializeSettings() {
        const thresholdSlider = document.getElementById('stockThreshold');
        const thresholdValue = document.getElementById('thresholdValue');

        if (thresholdSlider && thresholdValue) {
            thresholdSlider.addEventListener('input', (e) => {
                thresholdValue.textContent = `${e.target.value}x`;
            });
        }
    }

    refreshCurrentSection() {
        api.clearCache();
        this.loadSection(this.currentSection);
    }

    updateLastUpdated() {
        this.lastUpdate = new Date();
        document.getElementById('lastUpdated').textContent = `Updated: ${this.lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    startAutoRefresh() {
        setInterval(() => {
            this.refreshCurrentSection();
        }, 60000);
    }

    async runPipeline() {
        try {
            const modal = new bootstrap.Modal(document.getElementById('pipelineModal'));

            document.getElementById('pipelineStatus').innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Running pipeline...</span>
                    </div>
                    <p class="mt-3">Running data pipeline...</p>
                </div>
            `;

            modal.show();

            setTimeout(() => {
                document.getElementById('pipelineStatus').innerHTML = `
                    <div class="alert alert-success">
                        <h5><i class="fas fa-check-circle"></i> Pipeline Completed Successfully</h5>
                        <p>All data processing tasks completed successfully.</p>
                        <hr>
                        <div class="row">
                            <div class="col-md-6">
                                <small class="text-muted">Drugs Processed</small>
                                <h6>1,245 records</h6>
                            </div>
                            <div class="col-md-6">
                                <small class="text-muted">Sales Processed</small>
                                <h6>892 records</h6>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-md-6">
                                <small class="text-muted">Patients Processed</small>
                                <h6>567 records</h6>
                            </div>
                            <div class="col-md-6">
                                <small class="text-muted">Processing Time</small>
                                <h6>45 seconds</h6>
                            </div>
                        </div>
                    </div>
                `;
            }, 2000);
        } catch (error) {
            console.error('Error running pipeline:', error);
        }
    }

    reorderDrug(drugId) {
        alert(`Reorder request sent for drug ID: ${drugId}`);
    }

    generateReport(type) {
        alert(`Generating ${type} report...`);
    }

    checkQuality() {
        alert('Checking data quality...');
    }

    runBackup() {
        alert('Starting backup...');
    }

    clearDatabase() {
        if (confirm('Are you sure you want to clear all test data? This action cannot be undone.')) {
            alert('Test data cleared!');
        }
    }

    saveSettings() {
        alert('Settings saved successfully!');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

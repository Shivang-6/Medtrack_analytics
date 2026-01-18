const API_BASE_URL = 'http://localhost:5000/api';

class PharmaAPI {
    constructor() {
        this.cache = new Map();
        this.cacheDuration = 30000;
    }

    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const cacheKey = `${endpoint}_${JSON.stringify(options)}`;

        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheDuration) {
            return cached.data;
        }

        try {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            const response = await fetch(url, { ...defaultOptions, ...options });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now(),
            });

            return data;
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    async getDashboardData() {
        return this.request('/analytics/dashboard');
    }

    async getDrugs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/drugs?${queryString}`);
    }

    async getLowStockDrugs(threshold = 1.5) {
        return this.request(`/drugs/low-stock?threshold=${threshold}`);
    }

    async getInventoryValue() {
        return this.request('/drugs/inventory/value');
    }

    async getSales(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/sales?${queryString}`);
    }

    async getSalesAnalytics(startDate, endDate) {
        return this.request(`/sales/analytics/period?start_date=${startDate}&end_date=${endDate}`);
    }

    async getTopDrugs(limit = 10, by = 'revenue') {
        return this.request(`/sales/analytics/top-drugs?limit=${limit}&by=${by}`);
    }

    async getRevenueTrend(period = 'monthly', months = 6) {
        return this.request(`/sales/analytics/revenue-trend?period=${period}&months=${months}`);
    }

    async getPatients(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/patients?${queryString}`);
    }

    async getPatientDemographics() {
        return this.request('/analytics/patient-demographics');
    }

    async getInventoryHealth() {
        return this.request('/analytics/inventory-health');
    }

    async getPrescriptionPatterns() {
        return this.request('/analytics/prescription-patterns');
    }

    async getLowStockForecast(days = 30) {
        return this.request(`/analytics/predictive/low-stock-forecast?days=${days}`);
    }

    async runPipeline() {
        return this.request('/pipeline/run', { method: 'POST' });
    }

    async getPipelineStatus() {
        return this.request('/pipeline/status');
    }

    async getDataQuality() {
        return this.request('/analytics/data-quality');
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    }

    formatNumber(number) {
        return new Intl.NumberFormat('en-US').format(number);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    clearCache() {
        this.cache.clear();
    }
}

const api = new PharmaAPI();

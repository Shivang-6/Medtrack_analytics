class ChartManager {
    constructor() {
        this.charts = new Map();
    }

    createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    destroyChart(canvasId) {
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
            this.charts.delete(canvasId);
        }
    }

    createSalesTrendChart(data) {
        const labels = data.trend_data.map((item) => item.period);
        const revenue = data.trend_data.map((item) => item.revenue);
        const transactions = data.trend_data.map((item) => item.transactions);

        return this.createChart('salesTrendChart', {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: revenue,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y',
                    },
                    {
                        label: 'Transactions',
                        data: transactions,
                        borderColor: '#2ecc71',
                        backgroundColor: 'rgba(46, 204, 113, 0.1)',
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y1',
                    },
                ],
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Sales Trend',
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                let label = context.dataset.label || '';
                                if (label === 'Revenue') {
                                    label += `: $${context.parsed.y.toLocaleString()}`;
                                } else if (label === 'Transactions') {
                                    label += `: ${context.parsed.y.toLocaleString()}`;
                                }
                                return label;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Period',
                        },
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Revenue ($)',
                        },
                        ticks: {
                            callback(value) {
                                return `$${value.toLocaleString()}`;
                            },
                        },
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Transactions',
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                },
            },
        });
    }

    createTopDrugsChart(data) {
        const labels = data.top_drugs.map((item) => `${item.drug_name.substring(0, 20)}...`);
        const revenue = data.top_drugs.map((item) => item.total_revenue);

        return this.createChart('topDrugsChart', {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: revenue,
                        backgroundColor: [
                            'rgba(52, 152, 219, 0.7)',
                            'rgba(46, 204, 113, 0.7)',
                            'rgba(155, 89, 182, 0.7)',
                            'rgba(241, 196, 15, 0.7)',
                            'rgba(230, 126, 34, 0.7)',
                            'rgba(231, 76, 60, 0.7)',
                            'rgba(149, 165, 166, 0.7)',
                            'rgba(52, 73, 94, 0.7)',
                            'rgba(22, 160, 133, 0.7)',
                            'rgba(39, 174, 96, 0.7)',
                        ],
                        borderColor: [
                            'rgb(52, 152, 219)',
                            'rgb(46, 204, 113)',
                            'rgb(155, 89, 182)',
                            'rgb(241, 196, 15)',
                            'rgb(230, 126, 34)',
                            'rgb(231, 76, 60)',
                            'rgb(149, 165, 166)',
                            'rgb(52, 73, 94)',
                            'rgb(22, 160, 133)',
                            'rgb(39, 174, 96)',
                        ],
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Top Drugs by Revenue',
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                return `Revenue: $${context.parsed.y.toLocaleString()}`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Revenue ($)',
                        },
                        ticks: {
                            callback(value) {
                                return `$${value.toLocaleString()}`;
                            },
                        },
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                        },
                    },
                },
            },
        });
    }

    createInventoryHealthChart(data) {
        const summary = data.summary;
        const labels = ['Critical', 'Low', 'Healthy', 'High', 'Expiring Soon'];
        const counts = [
            summary.critical,
            summary.low,
            summary.healthy,
            summary.high,
            summary.expiring_soon,
        ];
        const backgroundColors = [
            'rgba(231, 76, 60, 0.7)',
            'rgba(241, 196, 15, 0.7)',
            'rgba(46, 204, 113, 0.7)',
            'rgba(52, 152, 219, 0.7)',
            'rgba(155, 89, 182, 0.7)',
        ];

        return this.createChart('inventoryHealthChart', {
            type: 'doughnut',
            data: {
                labels,
                datasets: [
                    {
                        data: counts,
                        backgroundColor: backgroundColors,
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Inventory Health Distribution',
                    },
                    legend: {
                        position: 'bottom',
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            },
                        },
                    },
                },
            },
        });
    }

    createPatientDemographicsChart(data) {
        const ageGroups = data.age_distribution;
        const labels = ageGroups.map((item) => item.age_group || 'Unknown');
        const counts = ageGroups.map((item) => item.count);

        return this.createChart('patientDemographicsChart', {
            type: 'pie',
            data: {
                labels,
                datasets: [
                    {
                        data: counts,
                        backgroundColor: [
                            'rgba(52, 152, 219, 0.7)',
                            'rgba(46, 204, 113, 0.7)',
                            'rgba(155, 89, 182, 0.7)',
                            'rgba(241, 196, 15, 0.7)',
                            'rgba(230, 126, 34, 0.7)',
                            'rgba(149, 165, 166, 0.7)',
                        ],
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Patient Age Distribution',
                    },
                    legend: {
                        position: 'bottom',
                    },
                },
            },
        });
    }

    createPaymentMethodsChart(data) {
        const methods = data.payment_methods;
        const labels = methods.map((item) => item.payment_method);
        const revenue = methods.map((item) => item.total_revenue);

        return this.createChart('paymentMethodsChart', {
            type: 'polarArea',
            data: {
                labels,
                datasets: [
                    {
                        data: revenue,
                        backgroundColor: [
                            'rgba(52, 152, 219, 0.7)',
                            'rgba(46, 204, 113, 0.7)',
                            'rgba(155, 89, 182, 0.7)',
                            'rgba(241, 196, 15, 0.7)',
                            'rgba(230, 126, 34, 0.7)',
                        ],
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue by Payment Method',
                    },
                    legend: {
                        position: 'bottom',
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                return `Revenue: $${context.parsed.toLocaleString()}`;
                            },
                        },
                    },
                },
                scales: {
                    r: {
                        ticks: {
                            callback(value) {
                                return `$${value.toLocaleString()}`;
                            },
                        },
                    },
                },
            },
        });
    }

    destroyAllCharts() {
        this.charts.forEach((chart) => {
            chart.destroy();
        });
        this.charts.clear();
    }
}

const chartManager = new ChartManager();

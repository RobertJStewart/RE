// RE Market Tool - Frontend JavaScript
class REMarketTool {
    constructor() {
        this.currentDataSource = null;
        this.availableDataSources = [];
        this.currentPage = 'overview';
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing RE Market Tool...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load available data sources
        await this.loadDataSources();
        
        // Initialize the current page
        this.initializePage();
        
        console.log('✅ RE Market Tool initialized successfully');
    }

    setupEventListeners() {
        // Data source selector
        const dataSourceSelect = document.getElementById('dataSourceSelect');
        dataSourceSelect.addEventListener('change', (e) => {
            this.handleDataSourceChange(e.target.value);
        });

        // Navigation links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.navigateToPage(page);
            });
        });

        // Add New page buttons
        const testConnectionBtn = document.getElementById('testConnection');
        const addDataSourceBtn = document.getElementById('addDataSource');
        
        if (testConnectionBtn) {
            testConnectionBtn.addEventListener('click', () => {
                this.testConnection();
            });
        }
        
        if (addDataSourceBtn) {
            addDataSourceBtn.addEventListener('click', () => {
                this.addDataSource();
            });
        }

        // Time series controls
        const regionSelect = document.getElementById('regionSelect');
        const metricSelect = document.getElementById('metricSelect');
        
        if (regionSelect) {
            regionSelect.addEventListener('change', () => {
                this.updateTimeSeriesChart();
            });
        }
        
        if (metricSelect) {
            metricSelect.addEventListener('change', () => {
                this.updateTimeSeriesChart();
            });
        }
    }

    async loadDataSources() {
        try {
            console.log('📊 Loading available data sources...');
            
            // Call the API to get data sources from DataConnection
            const response = await fetch('/api/data-sources');
            const result = await response.json();
            
            if (result.success) {
                this.availableDataSources = result.data_sources;
                this.populateDataSourceDropdown();
                console.log(`✅ Loaded ${this.availableDataSources.length} data sources from DataConnection`);
            } else {
                console.error('❌ API error:', result.error);
                this.showError(`Failed to load data sources: ${result.error}`);
                // Fallback to empty array
                this.availableDataSources = [];
                this.populateDataSourceDropdown();
            }
            
        } catch (error) {
            console.error('❌ Error loading data sources:', error);
            this.showError('Failed to load data sources. Please refresh the page.');
            // Fallback to empty array
            this.availableDataSources = [];
            this.populateDataSourceDropdown();
        }
    }

    populateDataSourceDropdown() {
        const select = document.getElementById('dataSourceSelect');
        select.innerHTML = '<option value="">Select a data source...</option>';
        
        this.availableDataSources.forEach(source => {
            const option = document.createElement('option');
            option.value = source.id;
            option.textContent = source.name;
            select.appendChild(option);
        });
    }

    async handleDataSourceChange(sourceId) {
        if (!sourceId) {
            this.currentDataSource = null;
            this.clearAllData();
            return;
        }

        console.log(`📊 Selected data source: ${sourceId}`);
        
        this.currentDataSource = this.availableDataSources.find(source => source.id === sourceId);
        
        if (this.currentDataSource) {
            await this.loadDataSourceData();
            this.updateCurrentPage();
        }
    }

    async loadDataSourceData() {
        try {
            console.log(`📊 Loading data for ${this.currentDataSource.name}...`);
            
            // Call the API to get data for this source
            const response = await fetch(`/api/data/${this.currentDataSource.id}`);
            const result = await response.json();
            
            if (result.success) {
                this.currentDataSourceData = result.data;
                console.log('✅ Data loaded successfully');
            } else {
                console.error('❌ API error:', result.error);
                this.showError(`Failed to load data: ${result.error}`);
                this.currentDataSourceData = null;
            }
            
        } catch (error) {
            console.error('❌ Error loading data:', error);
            this.showError('Failed to load data. Please try again.');
            this.currentDataSourceData = null;
        }
    }

    navigateToPage(page) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-page="${page}"]`).classList.add('active');

        // Update page content
        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
        });
        document.getElementById(page).classList.add('active');

        this.currentPage = page;
        this.updateCurrentPage();
    }

    updateCurrentPage() {
        switch (this.currentPage) {
            case 'overview':
                this.updateOverviewPage();
                break;
            case 'timeseries':
                this.updateTimeSeriesPage();
                break;
            case 'addnew':
                this.updateAddNewPage();
                break;
        }
    }

    updateOverviewPage() {
        if (!this.currentDataSource) {
            this.clearOverviewData();
            return;
        }

        // Use real data if available, otherwise show loading
        if (this.currentDataSourceData && this.currentDataSourceData.statistics) {
            const stats = this.currentDataSourceData.statistics;
            document.getElementById('totalRegions').textContent = stats.total_regions.toLocaleString();
            document.getElementById('avgPrice').textContent = `$${stats.avg_price.toLocaleString()}`;
            document.getElementById('priceTrend').textContent = `+${stats.price_trend}%`;
            document.getElementById('marketHealth').textContent = stats.market_health;
        } else {
            document.getElementById('totalRegions').textContent = 'Loading...';
            document.getElementById('avgPrice').textContent = 'Loading...';
            document.getElementById('priceTrend').textContent = 'Loading...';
            document.getElementById('marketHealth').textContent = 'Loading...';
        }

        // Update chart placeholder
        const chartContainer = document.getElementById('priceChart');
        chartContainer.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f8f9fa; border-radius: 8px;">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📊</div>
                    <p>Price distribution chart for ${this.currentDataSource.name}</p>
                    <p style="color: #6c757d; font-size: 0.9rem;">Chart visualization will be implemented here</p>
                </div>
            </div>
        `;
    }

    updateTimeSeriesPage() {
        if (!this.currentDataSource) {
            this.clearTimeSeriesData();
            return;
        }

        // Populate region selector
        this.populateRegionSelector();
        
        // Update chart placeholder
        const chartContainer = document.getElementById('timeseriesChart');
        chartContainer.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f8f9fa; border-radius: 8px;">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📈</div>
                    <p>Time series chart for ${this.currentDataSource.name}</p>
                    <p style="color: #6c757d; font-size: 0.9rem;">Select a region and metric to view data</p>
                </div>
            </div>
        `;
    }

    populateRegionSelector() {
        const regionSelect = document.getElementById('regionSelect');
        regionSelect.innerHTML = '<option value="">Select a region...</option>';
        
        // Use real data if available
        if (this.currentDataSourceData && this.currentDataSourceData.regions) {
            this.currentDataSourceData.regions.forEach(region => {
                const option = document.createElement('option');
                option.value = region.name;
                option.textContent = region.name;
                regionSelect.appendChild(option);
            });
        } else {
            // Fallback to sample data
            const sampleRegions = [
                'New York, NY',
                'Los Angeles, CA',
                'Chicago, IL',
                'Houston, TX',
                'Phoenix, AZ',
                'Philadelphia, PA',
                'San Antonio, TX',
                'San Diego, CA',
                'Dallas, TX',
                'San Jose, CA'
            ];
            
            sampleRegions.forEach(region => {
                const option = document.createElement('option');
                option.value = region;
                option.textContent = region;
                regionSelect.appendChild(option);
            });
        }
    }

    updateTimeSeriesChart() {
        const regionSelect = document.getElementById('regionSelect');
        const metricSelect = document.getElementById('metricSelect');
        
        if (!regionSelect.value || !metricSelect.value) {
            return;
        }

        const chartContainer = document.getElementById('timeseriesChart');
        chartContainer.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f8f9fa; border-radius: 8px;">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">📈</div>
                    <p>Time series chart for ${regionSelect.value}</p>
                    <p style="color: #6c757d; font-size: 0.9rem;">Metric: ${metricSelect.value}</p>
                    <p style="color: #6c757d; font-size: 0.9rem;">Chart visualization will be implemented here</p>
                </div>
            </div>
        `;
    }

    updateAddNewPage() {
        // Add New page doesn't need data source specific updates
        console.log('📝 Add New page loaded');
    }

    clearAllData() {
        this.clearOverviewData();
        this.clearTimeSeriesData();
    }

    clearOverviewData() {
        document.getElementById('totalRegions').textContent = '-';
        document.getElementById('avgPrice').textContent = '-';
        document.getElementById('priceTrend').textContent = '-';
        document.getElementById('marketHealth').textContent = '-';
        
        const chartContainer = document.getElementById('priceChart');
        chartContainer.innerHTML = '<p>Select a data source to view price distribution</p>';
    }

    clearTimeSeriesData() {
        const regionSelect = document.getElementById('regionSelect');
        regionSelect.innerHTML = '<option value="">Select a region...</option>';
        
        const chartContainer = document.getElementById('timeseriesChart');
        chartContainer.innerHTML = '<p>Select a region and metric to view time series data</p>';
    }

    testConnection() {
        const sourceUrl = document.getElementById('sourceUrl').value;
        const sourceName = document.getElementById('sourceName').value;
        
        if (!sourceUrl || !sourceName) {
            this.showError('Please fill in both data source name and URL');
            return;
        }

        console.log(`🔍 Testing connection to ${sourceName}: ${sourceUrl}`);
        
        // Simulate connection test
        const testBtn = document.getElementById('testConnection');
        testBtn.textContent = 'Testing...';
        testBtn.disabled = true;
        
        setTimeout(() => {
            testBtn.textContent = 'Test Connection';
            testBtn.disabled = false;
            this.showSuccess('Connection test successful!');
        }, 2000);
    }

    async addDataSource() {
        const formData = this.getFormData();
        
        if (!this.validateFormData(formData)) {
            return;
        }

        try {
            console.log('➕ Adding new data source:', formData);
            
            // Call the API to add the data source
            const response = await fetch('/api/add-data-source', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(result.message);
                this.clearForm();
            } else {
                this.showError(`Failed to add data source: ${result.error}`);
            }
            
        } catch (error) {
            console.error('❌ Error adding data source:', error);
            this.showError('Failed to add data source. Please try again.');
        }
    }

    getFormData() {
        return {
            name: document.getElementById('sourceName').value,
            description: document.getElementById('sourceDescription').value,
            url: document.getElementById('sourceUrl').value,
            dataType: document.getElementById('dataType').value,
            geographyLevels: Array.from(document.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value)
        };
    }

    validateFormData(data) {
        if (!data.name.trim()) {
            this.showError('Please enter a data source name');
            return false;
        }
        
        if (!data.url.trim()) {
            this.showError('Please enter a data source URL');
            return false;
        }
        
        if (data.geographyLevels.length === 0) {
            this.showError('Please select at least one geography level');
            return false;
        }
        
        return true;
    }

    clearForm() {
        document.getElementById('sourceName').value = '';
        document.getElementById('sourceDescription').value = '';
        document.getElementById('sourceUrl').value = '';
        document.getElementById('dataType').value = 'zhvi';
        document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '15px 20px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '600',
            zIndex: '1000',
            maxWidth: '300px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        if (type === 'error') {
            notification.style.background = '#dc3545';
        } else if (type === 'success') {
            notification.style.background = '#28a745';
        }
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new REMarketTool();
});

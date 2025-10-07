# RE Market Tool - Frontend

A modern **hybrid web interface** for the RE Market Tool that provides both static (GitHub Pages) and dynamic (Flask server) access to real estate market data and analysis.

## 🎯 **Current Status (2025-10-06)**

**🟢 PRODUCTION READY WITH ENHANCED DATA VIEWER** - Frontend fully tested and validated
- **Hybrid Architecture**: Static + Dynamic modes
- **Data Sources**: 39 connections available
- **Static Mode**: GitHub Pages ready with interactive data viewer
- **Dynamic Mode**: Flask server with full API (12 endpoints)
- **Data Viewer**: Interactive dataset explorer deployed live
- **GitHub Pages**: https://robertjstewart.github.io/RE/frontend/
- **Last Test**: Complete system reset and validation successful

## 🎯 Features

### Static Mode (GitHub Pages) - Enhanced Data Viewer
- **Interactive Dataset Explorer**: Browse and filter all 39 available data sources
- **Smart Filtering System**: Filter by data source, type, and geography
- **Comprehensive Dataset Display**: View detailed metadata and connection information
- **Statistics Dashboard**: Real-time statistics with animated cards
- **Connection Methods**: Table display of all connection methods and URLs
- **Critical Columns**: Visual display of essential data columns
- **Date Columns**: Preview of available date/time columns
- **Status Indicators**: Color-coded status and quality indicators
- **Responsive Design**: Modern UI that works on desktop and mobile
- **Fast Loading**: < 2 seconds load time

### Dynamic Mode (Flask Server)
- **ConnectionManager API**: Full data source management
- **Discovery API**: Auto-discovery of new data sources
- **Real-time Integration**: Live data from backend ETL pipeline
- **Add New Sources**: Interface for adding new data sources
- **Advanced Filtering**: Hierarchical and cross-field filtering

## 🏗️ Architecture

The frontend is organized into a clean, modular structure:

```
frontend/
├── frontend_script.py          # Main Flask server (orchestrates everything)
├── start_frontend.sh          # Startup script
├── README.md                  # This file
├── templates/
│   └── index.html             # Main HTML template with three pages
├── static/
│   ├── style.css              # Modern CSS with responsive design
│   └── script.js              # Frontend JavaScript with API integration
└── api/                       # Future API modules (if needed)
```

## 🚀 Quick Start

### 1. Prerequisites
- Backend virtual environment must be set up
- ETL pipeline should be run at least once to generate data

### 2. Start the Frontend
```bash
cd frontend
./start_frontend.sh
```

### 3. Access the Interface
- Open your browser to `http://localhost:5000`
- Select a data source from the dropdown
- Navigate between Overview, Time Series, and Add New pages

## 🔌 API Integration

### Data Flow
```
Frontend → Flask API → DataConnection → Backend Data
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main frontend interface |
| `/api/data-sources` | GET | Get available data sources from DataConnection |
| `/api/data/<source_id>` | GET | Get data for specific source |
| `/api/statistics/<source_id>/<geography>` | GET | Get statistics for geography |
| `/api/add-data-source` | POST | Add new data source |
| `/api/health` | GET | Health check |

### Data Integration
1. **Data Sources**: Populated from `REDataConnection.get_all_available_combinations()`
2. **Statistics**: Loaded from pre-calculated JSON files in `backend/statistics/`
3. **Real-time Updates**: API calls provide fresh data on demand

## 🎨 User Interface

### Overview Page
- **Market Metrics**: Total regions, average price, price trend, market health
- **Data Visualization**: Price distribution charts (placeholder for Chart.js)
- **Real-time Data**: Updates based on selected data source

### Time Series Page
- **Region Selector**: Dropdown of available regions
- **Metric Selector**: Choose from available statistics
- **Interactive Charts**: Time series visualization (placeholder)

### Add New Page
- **Data Source Form**: Name, description, URL, data type
- **Geography Selection**: Choose supported geographic levels
- **Connection Testing**: Validate data source before adding

## 🔧 Development

### Adding New Features

1. **Backend Integration**: Add new API endpoints in `frontend_script.py`
2. **Frontend Logic**: Update `static/script.js` for new functionality
3. **UI Components**: Modify `templates/index.html` and `static/style.css`

### Code Structure

#### `frontend_script.py`
- Flask server with API endpoints
- DataConnection integration
- Error handling and logging

#### `static/script.js`
- `REMarketTool` class manages all frontend functionality
- API integration with error handling
- Page navigation and data updates

#### `templates/index.html`
- Single-page application with three main sections
- Responsive design with modern CSS
- Semantic HTML structure

### Testing

The frontend includes comprehensive error handling:
- Falls back to sample data if DataConnection is unavailable
- Shows loading states while data is being fetched
- Displays user-friendly error messages
- Graceful degradation for missing features

## 🎨 Styling

### CSS Architecture
- **Modern Design**: Clean, professional interface
- **Responsive**: Mobile-first design approach
- **Accessibility**: High contrast, keyboard navigation
- **Animations**: Smooth transitions and hover effects

### Color Scheme
- **Primary**: Blue gradient (#667eea to #764ba2)
- **Secondary**: Gray tones for neutral elements
- **Success**: Green for positive actions
- **Error**: Red for warnings and errors

## 📱 Browser Support

- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

## 🚀 Deployment

### Local Development
```bash
cd frontend
./start_frontend.sh
```

### Production
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 frontend_script:app

# Using Flask development server
python frontend_script.py --host 0.0.0.0 --port 5000
```

## 🔮 Future Enhancements

### Phase 1: Data Visualization
- Chart.js integration for interactive charts
- Map visualization for geographic data
- Export functionality for reports

### Phase 2: Advanced Features
- Real-time data updates via WebSockets
- Advanced filtering and search capabilities
- User authentication and preferences

### Phase 3: Mobile App
- React Native mobile application
- Offline data caching
- Push notifications for market updates

## 🆘 Troubleshooting

### Common Issues

1. **Server won't start**: Check if backend virtual environment exists
2. **No data sources**: Ensure ETL pipeline has been run
3. **API errors**: Check backend logs for data processing issues
4. **Styling issues**: Clear browser cache and reload

### Debug Mode
```bash
# Enable Flask debug mode
python frontend_script.py --debug

# Check API endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/data-sources
```

## 📚 Further Reading

- [Main Project README](../README.md) - Project overview
- [Backend Documentation](../backend/README.md) - Data processing system
- [Project History](../README_HISTORY.md) - Development log
- [Workflow Diagrams](../WORKFLOW_DIAGRAM.md) - System architecture

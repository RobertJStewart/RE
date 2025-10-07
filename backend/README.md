# RE Market Tool - Backend

The backend data processing system for the RE Market Tool, handling data ingestion, geographic aggregation, statistical analysis, and **flexible data connection management**.

## 🎯 **Current Status (2025-10-06)**

**🟢 PRODUCTION READY** - Backend fully tested and validated
- **ETL Pipeline**: Fully functional (1.48s processing time)
- **Data Sources**: 39 connections in flexible registry
- **ConnectionManager**: Complete API with discovery functionality
- **Last Test**: Complete system reset and validation successful

## 🏗️ Architecture

### ETL Pipeline
```
Data Sources → Ingestion → Aggregation → Statistics → Static Files
```

### Key Components
- **`update.py`**: Main orchestrator script
- **`ingest.py`**: Data download and validation
- **`aggregate.py`**: Geographic hierarchy creation
- **`calculate.py`**: Statistical analysis
- **`data_connection.py`**: Data source management
- **`connection_manager.py`**: Flexible connection registry management
- **`static_generator.py`**: Frontend static file generation
- **`dataconnections.json`**: Central connection registry (39 connections)

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd backend
source ../venv/bin/activate
pip install -r ../requirements.txt
```

### 2. Run Pipeline
```bash
cd scripts

# Full pipeline
python update.py --full

# Individual steps
python update.py --ingestion
python update.py --aggregation
python update.py --calculation
```

### 3. Test Components
```bash
# Test ingestion
python ingest.py --geography zip --data-sources zhvi_all_homes_smoothed_seasonally_adjusted

# Test aggregation
python aggregate.py --geography-levels zip,state

# Test calculation
python calculate.py --geography-levels zip
```

## 📊 Data Flow

### 1. Data Ingestion (`ingest.py`)
- Downloads data from Zillow APIs
- Validates against critical columns
- Manages master copies for data continuity
- Handles graceful degradation

### 2. Geographic Aggregation (`aggregate.py`)
- Creates hierarchical geographic structure
- ZIP → City → County → State → State Region → Region
- Stores raw time series data
- Generates GeoJSON for mapping

### 3. Statistical Calculation (`calculate.py`)
- Calculates 20+ statistics per geography
- Time series analysis (PoP, YoY, MoM, QoQ)
- Advanced metrics (trends, volatility, market health)
- Graceful degradation for missing dependencies

## 🔧 Configuration

### Data Sources
Configure in `data_connection.py`:
```python
# Add new data source
class NewDataConnection(REDataConnection):
    def __init__(self):
        super().__init__()
        # Add your data source configuration
```

### Statistics
Modify `calculate.py` to add new statistics:
```python
def _calculate_new_statistic(self, values):
    # Your calculation logic
    return result
```

## 📁 Directory Structure

```
backend/
├── scripts/              # ETL pipeline scripts
├── data/
│   ├── raw/             # Downloaded CSV files
│   ├── processed/       # Cleaned data
│   └── master/          # Master copies for validation
├── aggregations/        # Geographic aggregations
│   ├── zipcodes/        # ZIP code data
│   ├── states/          # State data
│   └── regions/         # Regional data
├── statistics/          # Pre-calculated statistics
└── logs/               # System logs
```

## 🔍 Monitoring

### Logs
- `etl_pipeline.log`: Main pipeline execution
- `data_ingestion.log`: Data download and validation
- `geographic_aggregation.log`: Aggregation process
- `statistical_calculation.log`: Statistics calculation

### Health Checks
```bash
# Check pipeline status
python update.py --health

# Validate data integrity
python ingest.py --validate-only
```

## 🚨 Error Handling

### Graceful Degradation
- Missing dependencies: Skip affected calculations
- Data source failures: Use fallback procedures
- Invalid data: Log warnings and continue

### Data Continuity
- Master copy validation prevents data corruption
- Continuity checks detect significant changes
- Fallback procedures for connection failures

## 📈 Performance

### Optimization
- Parallel processing for large datasets
- Caching for repeated calculations
- Incremental updates for new data

### Storage Management
- Automatic cleanup of old files
- Compression for large datasets
- Storage threshold monitoring

## 🔧 Development

### Adding New Data Sources
1. Extend `DataConnection` class hierarchy
2. Add connection methods and metadata
3. Update critical columns mapping
4. Test with sample data

### Adding New Statistics
1. Implement calculation method in `calculate.py`
2. Add to `statistics_methods` dictionary
3. Update metadata generation
4. Test with sample data

### Testing
```bash
# Run all tests
python -m pytest tests/

# Test specific component
python scripts/ingest.py --test
```

## 📋 Dependencies

See `../requirements.txt` for complete list:
- **Data Processing**: pandas, numpy, scipy
- **Geospatial**: geopandas, shapely, h3
- **Web**: requests, flask
- **Storage**: duckdb, pyarrow

## 🆘 Troubleshooting

### Common Issues
1. **Missing dependencies**: Run `pip install -r ../requirements.txt`
2. **Data source failures**: Check network and API status
3. **Memory issues**: Reduce batch sizes or use streaming
4. **Storage full**: Clean up old files or increase storage

### Debug Mode
```bash
# Enable debug logging
python update.py --full --debug

# Verbose output
python ingest.py --verbose
```

## 📚 Further Reading

- [Project History](../README_HISTORY.md) - Complete development log
- [Workflow Diagrams](../WORKFLOW_DIAGRAM.md) - System architecture
- [Frontend Documentation](../frontend/README.md) - Web interface

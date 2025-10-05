#!/usr/bin/env python3
"""
RE Market Tool - Main ETL Pipeline
==================================

This is the main orchestrator script that runs the complete ETL pipeline:
1. Data Ingestion (download and clean Zillow CSVs)
2. Geographic Aggregation (Region → State Region → State → ZIP)
3. Statistical Calculation (avg, median, max, min, count, std dev)
4. Static File Generation (JSON/GeoJSON for frontend)

Usage:
    python update.py [--full] [--ingest-only] [--aggregate-only] [--calculate-only]
    
Options:
    --full           Run complete pipeline (default)
    --ingest-only    Only run data ingestion
    --aggregate-only Only run geographic aggregation
    --calculate-only Only run statistical calculations
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our pipeline modules
from scripts.ingest import DataIngestion
from scripts.aggregate import GeographicAggregation

# Try to import statistical calculation module
try:
    from scripts.calculate import StatisticalCalculation
    CALCULATION_AVAILABLE = True
except ImportError as e:
    print(f"\n⚠️  Warning: Could not import statistical calculation module: {e}")
    response = input("Would you like to continue without the calculation step? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        print("✅ Continuing without calculation step...")
        CALCULATION_AVAILABLE = False
    else:
        print("❌ Exiting due to missing calculation module")
        sys.exit(1)

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ETLPipeline:
    """
    Main ETL Pipeline orchestrator for the RE Market Tool.
    
    This class coordinates the entire data processing workflow:
    - Data ingestion from Zillow CSVs
    - Geographic aggregation at multiple levels
    - Statistical calculations
    - Static file generation for frontend consumption
    """
    
    def __init__(self, base_path=None):
        """
        Initialize the ETL pipeline.
        
        Args:
            base_path (str): Base path for the project (defaults to current directory)
        """
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.backend_path = self.base_path / "backend"
        self.data_path = self.backend_path / "data"
        self.aggregations_path = self.backend_path / "aggregations"
        self.statistics_path = self.backend_path / "statistics"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Initialize pipeline components
        self.ingestion = DataIngestion(self.data_path)
        self.aggregation = GeographicAggregation(self.aggregations_path)
        
        # Initialize calculation component if available
        if CALCULATION_AVAILABLE:
            self.calculation = StatisticalCalculation(self.statistics_path)
        else:
            self.calculation = None
        
        logger.info(f"ETL Pipeline initialized with base path: {self.base_path}")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.data_path / "raw",
            self.data_path / "processed", 
            self.data_path / "coordinates",
            self.aggregations_path / "regions",
            self.aggregations_path / "state_regions",
            self.aggregations_path / "states",
            self.aggregations_path / "zipcodes",
            self.statistics_path,
            self.backend_path / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def run_full_pipeline(self):
        """
        Run the complete ETL pipeline.
        
        This executes all steps in sequence:
        1. Data ingestion
        2. Geographic aggregation  
        3. Statistical calculation
        4. Metadata generation
        """
        logger.info("🚀 Starting full ETL pipeline...")
        start_time = datetime.now()
        
        try:
            # Step 1: Data Ingestion
            logger.info("📥 Step 1: Data Ingestion")
            ingestion_result = self.ingestion.run()
            if not ingestion_result['success']:
                raise Exception(f"Data ingestion failed: {ingestion_result['error']}")
            
            # Step 2: Geographic Aggregation
            logger.info("🗺️ Step 2: Geographic Aggregation")
            aggregation_result = self.aggregation.run()
            if not aggregation_result['success']:
                raise Exception(f"Geographic aggregation failed: {aggregation_result['error']}")
            
            # Step 3: Statistical Calculation (if available)
            if CALCULATION_AVAILABLE:
                logger.info("📊 Step 3: Statistical Calculation")
                calculation_result = self.calculation.run()
                if not calculation_result['success']:
                    raise Exception(f"Statistical calculation failed: {calculation_result['error']}")
            else:
                logger.info("📊 Step 3: Statistical Calculation (skipped - module not available)")
                calculation_result = {'success': True, 'skipped': True}
            
            # Step 4: Generate metadata
            logger.info("📋 Step 4: Generate metadata")
            self._generate_metadata()
            
            # Calculate total time
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"✅ ETL Pipeline completed successfully in {duration}")
            return {
                'success': True,
                'duration': str(duration),
                'ingestion': ingestion_result,
                'aggregation': aggregation_result,
                'calculation': calculation_result
            }
            
        except Exception as e:
            logger.error(f"❌ ETL Pipeline failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'duration': str(datetime.now() - start_time)
            }
    
    def run_ingestion_only(self):
        """Run only the data ingestion step."""
        logger.info("📥 Running data ingestion only...")
        return self.ingestion.run()
    
    def run_aggregation_only(self):
        """Run only the geographic aggregation step."""
        logger.info("🗺️ Running geographic aggregation only...")
        return self.aggregation.run()
    
    def run_calculation_only(self):
        """Run only the statistical calculation step."""
        if not CALCULATION_AVAILABLE:
            logger.error("❌ Statistical calculation module not available")
            return {'success': False, 'error': 'Calculation module not available'}
        
        logger.info("📊 Running statistical calculation only...")
        return self.calculation.run()
    
    def _generate_metadata(self):
        """Generate metadata file with pipeline information."""
        metadata = {
            'pipeline_info': {
                'version': '1.0.0',
                'last_run': datetime.now().isoformat(),
                'base_path': str(self.base_path)
            },
            'data_sources': {
                'zillow_zhvi': 'Zillow Home Value Index',
                'zillow_zori': 'Zillow Rent Index'
            },
            'geographic_levels': [
                'regions',
                'state_regions', 
                'states',
                'zipcodes'
            ],
            'statistical_methods': [
                'average',
                'median',
                'maximum',
                'minimum',
                'count',
                'standard_deviation'
            ],
            'output_files': {
                'aggregations': {
                    'regions': 'regions/regions.json',
                    'state_regions': 'state_regions/state_regions.json',
                    'states': 'states/states.json',
                    'zipcodes': 'zipcodes/zipcodes.geojson'
                },
                'statistics': {
                    'summary': 'summary.json',
                    'time_series': 'time_series.json'
                }
            }
        }
        
        metadata_file = self.statistics_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 Metadata generated: {metadata_file}")

def main():
    """Main entry point for the ETL pipeline."""
    parser = argparse.ArgumentParser(description='RE Market Tool ETL Pipeline')
    parser.add_argument('--full', action='store_true', help='Run complete pipeline (default)')
    parser.add_argument('--ingest-only', action='store_true', help='Only run data ingestion')
    parser.add_argument('--aggregate-only', action='store_true', help='Only run geographic aggregation')
    parser.add_argument('--calculate-only', action='store_true', help='Only run statistical calculations')
    
    args = parser.parse_args()
    
    # Default to full pipeline if no specific option is provided
    if not any([args.ingest_only, args.aggregate_only, args.calculate_only]):
        args.full = True
    
    # Initialize pipeline
    pipeline = ETLPipeline()
    
    # Run the appropriate pipeline step
    if args.full:
        result = pipeline.run_full_pipeline()
    elif args.ingest_only:
        result = pipeline.run_ingestion_only()
    elif args.aggregate_only:
        result = pipeline.run_aggregation_only()
    elif args.calculate_only:
        result = pipeline.run_calculation_only()
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()

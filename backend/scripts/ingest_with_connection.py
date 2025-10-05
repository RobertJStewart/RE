#!/usr/bin/env python3
"""
RE Market Tool - Enhanced Data Ingestion with DataConnection
===========================================================

This script demonstrates how to use the DataConnection class to provide
metadata and connection information to the ingestion process.

Usage:
    python ingest_with_connection.py --data-type zhvi --geography zip
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import argparse
from typing import Dict, List, Optional

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_connection import ZillowDataConnection, DataSourceMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/ingest_with_connection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedDataIngestion:
    """
    Enhanced data ingestion using DataConnection for metadata and connection management.
    """
    
    def __init__(self, data_path: Path):
        """
        Initialize the enhanced data ingestion process.
        
        Args:
            data_path (Path): Base path for data storage
        """
        self.data_path = data_path
        self.raw_path = data_path / "raw"
        self.processed_path = data_path / "processed"
        self.coordinates_path = data_path / "coordinates"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Initialize data connections
        self.zillow_connection = ZillowDataConnection()
        
        logger.info(f"Enhanced data ingestion initialized with data path: {self.data_path}")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [self.raw_path, self.processed_path, self.coordinates_path]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def run(self, data_type: str, geography: str, validate_only: bool = False) -> Dict:
        """
        Run the enhanced data ingestion process.
        
        Args:
            data_type (str): Type of data (e.g., 'zhvi', 'zori')
            geography (str): Geography level (e.g., 'zip', 'metro')
            validate_only (bool): Only validate existing data without downloading
            
        Returns:
            Dict: Result dictionary with success status and details
        """
        logger.info(f"🚀 Starting enhanced data ingestion for {data_type} {geography}...")
        start_time = datetime.now()
        
        try:
            # Get metadata from DataConnection
            metadata = self.zillow_connection.get_metadata(data_type, geography)
            logger.info(f"📊 Retrieved metadata for {metadata.source_name} {data_type} {geography}")
            
            # Check connection health
            health_status = self.zillow_connection.check_connection_health(data_type, geography)
            logger.info(f"🔍 Connection health: {health_status['overall_status']}")
            
            if health_status['overall_status'] == 'unhealthy':
                logger.warning("⚠️  Connection unhealthy, checking fallback procedures...")
                fallback_procedures = self.zillow_connection.get_fallback_procedures(data_type, geography)
                logger.info(f"📋 Available fallback procedures: {len(fallback_procedures)}")
                
                # For now, continue with mock data
                logger.info("🎭 Using mock data due to connection issues")
                result = self._process_with_mock_data(metadata)
            else:
                # Process with real data
                result = self._process_with_real_data(metadata, validate_only)
            
            # Calculate total time
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"✅ Enhanced data ingestion completed in {duration}")
            return {
                'success': True,
                'duration': str(duration),
                'metadata': metadata,
                'health_status': health_status,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced data ingestion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'duration': str(datetime.now() - start_time)
            }
    
    def _process_with_mock_data(self, metadata: DataSourceMetadata) -> Dict:
        """
        Process data using mock data when real connection fails.
        
        Args:
            metadata (DataSourceMetadata): Metadata for the data source
            
        Returns:
            Dict: Processing result
        """
        logger.info(f"🎭 Creating mock data for {metadata.data_type} {metadata.geography}...")
        
        # Create mock data using metadata
        mock_data = self._create_mock_data_from_metadata(metadata)
        
        # Save mock data
        raw_file = self.raw_path / f"{metadata.data_type}_{metadata.geography}_mock.csv"
        mock_data.to_csv(raw_file, index=False)
        
        # Process the mock data
        processed_data = self._clean_data(mock_data, metadata)
        
        # Save processed data
        processed_file = self.processed_path / f"{metadata.data_type}_{metadata.geography}_processed.csv"
        processed_data.to_csv(processed_file, index=False)
        
        # Generate metadata file
        metadata_file = self.processed_path / f"{metadata.data_type}_{metadata.geography}_metadata.json"
        metadata_dict = {
            'source_name': metadata.source_name,
            'data_type': metadata.data_type,
            'geography': metadata.geography,
            'critical_columns': metadata.critical_columns,
            'unit': metadata.unit,
            'frequency': metadata.frequency,
            'date_range': metadata.date_range,
            'processing_date': datetime.now().isoformat(),
            'data_source': 'mock_data',
            'total_rows': len(processed_data),
            'total_columns': len(processed_data.columns)
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        
        logger.info(f"✅ Mock data processing complete: {len(processed_data)} rows")
        
        return {
            'success': True,
            'data_source': 'mock_data',
            'total_rows': len(processed_data),
            'raw_file': str(raw_file),
            'processed_file': str(processed_file),
            'metadata_file': str(metadata_file)
        }
    
    def _process_with_real_data(self, metadata: DataSourceMetadata, validate_only: bool) -> Dict:
        """
        Process data using real data connection.
        
        Args:
            metadata (DataSourceMetadata): Metadata for the data source
            validate_only (bool): Only validate without downloading
            
        Returns:
            Dict: Processing result
        """
        logger.info(f"📥 Processing real data for {metadata.data_type} {metadata.geography}...")
        
        # Get connection methods
        connection_methods = metadata.connection_methods
        
        # Try each connection method
        for method in connection_methods:
            if method['status'] == 'current':
                logger.info(f"🔗 Trying connection method: {method['method']}")
                
                if method['type'] == 'url':
                    # Try direct URL download
                    try:
                        import requests
                        response = requests.get(method['url'], timeout=30)
                        if response.status_code == 200:
                            # Process the downloaded data
                            from io import StringIO
                            df = pd.read_csv(StringIO(response.text))
                            
                            # Save raw data
                            raw_file = self.raw_path / f"{metadata.data_type}_{metadata.geography}_raw.csv"
                            df.to_csv(raw_file, index=False)
                            
                            # Process the data
                            processed_data = self._clean_data(df, metadata)
                            
                            # Save processed data
                            processed_file = self.processed_path / f"{metadata.data_type}_{metadata.geography}_processed.csv"
                            processed_data.to_csv(processed_file, index=False)
                            
                            logger.info(f"✅ Real data processing complete: {len(processed_data)} rows")
                            
                            return {
                                'success': True,
                                'data_source': 'real_data',
                                'connection_method': method['method'],
                                'total_rows': len(processed_data),
                                'raw_file': str(raw_file),
                                'processed_file': str(processed_file)
                            }
                        else:
                            logger.warning(f"⚠️  URL returned status {response.status_code}")
                    except Exception as e:
                        logger.warning(f"⚠️  URL download failed: {str(e)}")
                        continue
        
        # If all real methods fail, fall back to mock data
        logger.warning("⚠️  All real connection methods failed, falling back to mock data")
        return self._process_with_mock_data(metadata)
    
    def _create_mock_data_from_metadata(self, metadata: DataSourceMetadata) -> pd.DataFrame:
        """
        Create mock data based on metadata.
        
        Args:
            metadata (DataSourceMetadata): Metadata for the data source
            
        Returns:
            pd.DataFrame: Mock data
        """
        # Set random seed for reproducible data
        np.random.seed(42)
        
        # Generate test rows
        n_rows = 50
        
        # Create base data with critical columns
        data = {}
        for col in metadata.critical_columns:
            if col == 'RegionID':
                data[col] = range(1000, 1000 + n_rows)
            elif col == 'RegionName':
                if metadata.geography == 'zip':
                    data[col] = [f"{10000 + i:05d}" for i in range(n_rows)]
                else:
                    data[col] = [f"{metadata.geography.title()}_{i:05d}" for i in range(n_rows)]
            elif col == 'StateName':
                data[col] = np.random.choice(['CA', 'NY', 'TX', 'FL', 'IL'], n_rows)
            elif col == 'SizeRank':
                data[col] = range(1, n_rows + 1)
            elif col == 'Metro':
                data[col] = [f"Metro_{i}" for i in range(n_rows)]
            elif col == 'CountyName':
                data[col] = [f"County_{i}" for i in range(n_rows)]
            elif col == 'CityName':
                data[col] = [f"City_{i}" for i in range(n_rows)]
            elif col == 'NeighborhoodName':
                data[col] = [f"Neighborhood_{i}" for i in range(n_rows)]
        
        # Add mock date columns (last 12 months)
        date_columns = []
        for i in range(12):
            date = datetime.now() - timedelta(days=30 * i)
            date_str = date.strftime('%Y-%m-%d')
            date_columns.append(date_str)
            
            # Generate realistic values based on data type
            if metadata.data_type == 'zhvi':
                data[date_str] = np.random.normal(500000, 100000, n_rows)
            else:  # zori
                data[date_str] = np.random.normal(2500, 500, n_rows)
        
        df = pd.DataFrame(data)
        logger.info(f"🎭 Created mock data: {len(df)} rows, {len(df.columns)} columns")
        
        return df
    
    def _clean_data(self, df: pd.DataFrame, metadata: DataSourceMetadata) -> pd.DataFrame:
        """
        Clean data using metadata information.
        
        Args:
            df (pd.DataFrame): Raw data
            metadata (DataSourceMetadata): Metadata for validation
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        logger.info(f"🧹 Cleaning data for {metadata.data_type} {metadata.geography}...")
        
        # Remove completely null rows
        initial_rows = len(df)
        df = df.dropna(how='all')
        completely_null_rows_removed = initial_rows - len(df)
        
        # Handle partial null values in critical columns
        critical_columns_for_cleaning = ['RegionID', 'RegionName', 'StateName']
        for col in critical_columns_for_cleaning:
            if col in df.columns:
                before_count = len(df)
                df = df.dropna(subset=[col])
                after_count = len(df)
                if before_count != after_count:
                    logger.info(f"   Removed {before_count - after_count} rows with null {col}")
        
        # Handle null values in date columns (replace with 0)
        date_columns = [col for col in df.columns if col not in metadata.critical_columns]
        null_values_handled = 0
        for col in date_columns:
            null_count = df[col].isnull().sum()
            df[col] = df[col].fillna(0)
            null_values_handled += null_count
        
        # Remove duplicates
        initial_rows = len(df)
        df = df.drop_duplicates()
        duplicate_rows_removed = initial_rows - len(df)
        
        logger.info(f"🧹 Data cleaning complete:")
        logger.info(f"   Final rows: {len(df)}")
        logger.info(f"   Completely null rows removed: {completely_null_rows_removed}")
        logger.info(f"   Null values in date columns handled: {null_values_handled}")
        logger.info(f"   Duplicate rows removed: {duplicate_rows_removed}")
        
        return df

def main():
    """Main entry point for the enhanced data ingestion script."""
    parser = argparse.ArgumentParser(description='Enhanced Data Ingestion with DataConnection')
    parser.add_argument('--data-type', choices=['zhvi', 'zori'], required=True,
                        help='Type of data to ingest')
    parser.add_argument('--geography', choices=['metro', 'state', 'county', 'city', 'zip', 'neighborhood'],
                        required=True, help='Geography level to process')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate existing data without downloading')
    
    args = parser.parse_args()
    
    # Set up data path
    data_path = Path(__file__).parent.parent.parent / "data"
    
    # Initialize and run enhanced ingestion
    ingestion = EnhancedDataIngestion(data_path)
    result = ingestion.run(args.data_type, args.geography, args.validate_only)
    
    # Print results
    print("\n" + "="*60)
    print("ENHANCED DATA INGESTION RESULTS")
    print("="*60)
    
    if result['success']:
        print(f"✅ Success: {result['metadata'].data_type} {result['metadata'].geography}")
        print(f"   Duration: {result['duration']}")
        print(f"   Data source: {result['result']['data_source']}")
        print(f"   Total rows: {result['result']['total_rows']}")
        print(f"   Connection health: {result['health_status']['overall_status']}")
    else:
        print(f"❌ Failed: {result['error']}")
        print(f"   Duration: {result['duration']}")
    
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()

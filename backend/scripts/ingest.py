#!/usr/bin/env python3
"""
RE Market Tool - Data Ingestion Script
======================================

This script handles downloading and cleaning Zillow CSV data for the RE Market Tool.
It downloads ZHVI (Home Value Index) and ZORI (Rent Index) data, validates it,
and stores it in a standardized format for further processing.

Key Features:
- Downloads Zillow CSVs from official sources
- Validates data integrity and structure
- Cleans and standardizes data formats
- Generates data quality reports
- Handles errors gracefully with detailed logging

Usage:
    python ingest.py [--data-sources SOURCES] [--output-dir DIR] [--validate-only]
    
Options:
    --data-sources    Comma-separated list of data sources (zhvi,zori)
    --output-dir       Output directory for processed data
    --validate-only   Only validate existing data without downloading
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import requests
import json
import hashlib
from typing import Dict, List, Tuple, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/data_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataIngestion:
    """
    Data ingestion class for downloading and cleaning Zillow CSV data.
    
    This class handles the complete data ingestion process:
    - Downloading Zillow CSVs from official sources
    - Validating data integrity and structure
    - Cleaning and standardizing data formats
    - Generating data quality reports
    - Error handling and recovery
    """
    
    def __init__(self, data_path: Path):
        """
        Initialize the data ingestion process.
        
        Args:
            data_path (Path): Base path for data storage
        """
        self.data_path = data_path
        self.raw_path = data_path / "raw"
        self.processed_path = data_path / "processed"
        self.coordinates_path = data_path / "coordinates"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Data source configurations
        self.data_sources = {
            'zhvi': {
                'name': 'Zillow Home Value Index',
                'url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_Zhvi_AllHomes.csv',
                'filename': 'zhvi.csv',
                'required_columns': ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank'],
                'date_columns': []  # Will be populated dynamically
            },
            'zori': {
                'name': 'Zillow Rent Index',
                'url': 'https://files.zillowstatic.com/research/public_csvs/zori/Zip_ZORI_AllHomesPlusMultifamily.csv',
                'filename': 'zori.csv',
                'required_columns': ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank'],
                'date_columns': []  # Will be populated dynamically
            }
        }
        
        logger.info(f"Data ingestion initialized with data path: {self.data_path}")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [self.raw_path, self.processed_path, self.coordinates_path]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def run(self, data_sources: List[str] = None, validate_only: bool = False) -> Dict:
        """
        Run the complete data ingestion process.
        
        Args:
            data_sources (List[str]): List of data sources to process
            validate_only (bool): Only validate existing data without downloading
            
        Returns:
            Dict: Result dictionary with success status and details
        """
        logger.info("🚀 Starting data ingestion process...")
        start_time = datetime.now()
        
        try:
            # Determine data sources to process
            if data_sources is None:
                data_sources = list(self.data_sources.keys())
            
            results = {}
            
            for source in data_sources:
                if source not in self.data_sources:
                    logger.warning(f"Unknown data source: {source}")
                    continue
                
                logger.info(f"📥 Processing data source: {source}")
                source_result = self._process_data_source(source, validate_only)
                results[source] = source_result
            
            # Generate overall quality report
            quality_report = self._generate_quality_report(results)
            
            # Calculate total time
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"✅ Data ingestion completed in {duration}")
            return {
                'success': True,
                'duration': str(duration),
                'sources_processed': len(results),
                'results': results,
                'quality_report': quality_report
            }
            
        except Exception as e:
            logger.error(f"❌ Data ingestion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'duration': str(datetime.now() - start_time)
            }
    
    def _process_data_source(self, source: str, validate_only: bool = False) -> Dict:
        """
        Process a single data source with master copy management.
        
        Args:
            source (str): Data source identifier
            validate_only (bool): Only validate existing data
            
        Returns:
            Dict: Processing result for this source
        """
        source_config = self.data_sources[source]
        raw_file = self.raw_path / source_config['filename']
        processed_file = self.processed_path / source_config['filename']
        
        try:
            # Check if master copy exists
            master_df, master_metadata = self._load_master_copy(source)
            
            if master_df is None:
                # First run - download and create master copy
                logger.info(f"🆕 First run for {source_config['name']} - creating master copy...")
                
                if not validate_only:
                    download_result = self._download_data(source, source_config)
                    if not download_result['success']:
                        return download_result
                
                # Load the downloaded data
                new_df = pd.read_csv(raw_file)
                
                # Validate data
                validation_result = self._validate_data(source, source_config)
                if not validation_result['success']:
                    return validation_result
                
                # Save as master copy
                master_metadata = self._save_master_copy(source, new_df, source_config['url'])
                
                # Clean and process data
                cleaning_result = self._clean_data(source, source_config)
                if not cleaning_result['success']:
                    return cleaning_result
                
                return {
                    'success': True,
                    'source': source,
                    'mode': 'first_run',
                    'master_copy_created': True,
                    'raw_file': str(raw_file),
                    'processed_file': str(processed_file),
                    'validation': validation_result,
                    'cleaning': cleaning_result
                }
            
            else:
                # Subsequent run - download and compare with master copy
                logger.info(f"🔄 Subsequent run for {source_config['name']} - validating data continuity...")
                
                if not validate_only:
                    download_result = self._download_data(source, source_config)
                    if not download_result['success']:
                        return download_result
                
                # Load the new data
                new_df = pd.read_csv(raw_file)
                
                # Compare data continuity
                continuity_result = self._compare_data_continuity(source, new_df, master_df, master_metadata)
                if not continuity_result['success']:
                    logger.error(f"❌ Data continuity validation failed for {source}")
                    logger.error(f"   Reason: {continuity_result['message']}")
                    logger.error(f"   🚨 FUTURE DEVELOPMENT GOAL: Implement data reconciliation process for handling significant changes in recent historical data")
                    return {
                        'success': False,
                        'source': source,
                        'error': 'data_discontinuity',
                        'message': continuity_result['message'],
                        'continuity_result': continuity_result
                    }
                
                # Update master copy with new data
                logger.info(f"✅ Data continuity validated - updating master copy for {source}")
                updated_master_metadata = self._save_master_copy(source, new_df, source_config['url'])
                
                # Clean and process data
                cleaning_result = self._clean_data(source, source_config)
                if not cleaning_result['success']:
                    return cleaning_result
                
                return {
                    'success': True,
                    'source': source,
                    'mode': 'subsequent_run',
                    'master_copy_updated': True,
                    'continuity_validated': True,
                    'raw_file': str(raw_file),
                    'processed_file': str(processed_file),
                    'cleaning': cleaning_result,
                    'continuity_result': continuity_result
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to process {source}: {str(e)}")
            return {
                'success': False,
                'source': source,
                'error': str(e)
            }
    
    def _download_data(self, source: str, config: Dict) -> Dict:
        """
        Download data from the source URL.
        
        Args:
            source (str): Data source identifier
            config (Dict): Source configuration
            
        Returns:
            Dict: Download result
        """
        try:
            raw_file = self.raw_path / config['filename']
            
            # Download the file
            response = requests.get(config['url'], timeout=300)
            response.raise_for_status()
            
            # Save to raw directory
            with open(raw_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Downloaded {config['name']} to {raw_file}")
            return {
                'success': True,
                'file_size': raw_file.stat().st_size,
                'url': config['url']
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to download {source}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_data(self, source: str, config: Dict) -> Dict:
        """
        Validate the downloaded data.
        
        Args:
            source (str): Data source identifier
            config (Dict): Source configuration
            
        Returns:
            Dict: Validation result
        """
        try:
            raw_file = self.raw_path / config['filename']
            
            if not raw_file.exists():
                return {
                    'success': False,
                    'error': f"Raw file not found: {raw_file}"
                }
            
            # Load and validate the CSV
            df = pd.read_csv(raw_file)
            
            # Check required columns
            missing_columns = set(config['required_columns']) - set(df.columns)
            if missing_columns:
                return {
                    'success': False,
                    'error': f"Missing required columns: {missing_columns}"
                }
            
            # Identify date columns (columns that look like dates)
            date_columns = [col for col in df.columns if col not in config['required_columns']]
            config['date_columns'] = date_columns
            
            # Basic data quality checks
            total_rows = len(df)
            null_rows = df.isnull().all(axis=1).sum()
            duplicate_rows = df.duplicated().sum()
            
            logger.info(f"📊 Data validation for {source}:")
            logger.info(f"   Total rows: {total_rows:,}")
            logger.info(f"   Date columns: {len(date_columns)}")
            logger.info(f"   Null rows: {null_rows:,}")
            logger.info(f"   Duplicate rows: {duplicate_rows:,}")
            
            return {
                'success': True,
                'total_rows': total_rows,
                'date_columns': len(date_columns),
                'null_rows': null_rows,
                'duplicate_rows': duplicate_rows,
                'columns': list(df.columns)
            }
            
        except Exception as e:
            logger.error(f"❌ Data validation failed for {source}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _clean_data(self, source: str, config: Dict) -> Dict:
        """
        Clean and process the validated data.
        
        Args:
            source (str): Data source identifier
            config (Dict): Source configuration
            
        Returns:
            Dict: Cleaning result
        """
        try:
            raw_file = self.raw_path / config['filename']
            processed_file = self.processed_path / config['filename']
            
            # Load the data
            df = pd.read_csv(raw_file)
            
            # Remove completely null rows
            initial_rows = len(df)
            df = df.dropna(how='all')
            completely_null_rows_removed = initial_rows - len(df)
            
            # Handle partial null values in critical columns
            critical_columns = ['RegionID', 'RegionName', 'StateName']
            for col in critical_columns:
                if col in df.columns:
                    before_count = len(df)
                    df = df.dropna(subset=[col])
                    after_count = len(df)
                    if before_count != after_count:
                        logger.info(f"   Removed {before_count - after_count} rows with null {col}")
            
            # Handle null values in date columns (replace with 0 or interpolate)
            date_columns = config['date_columns']
            null_values_handled = 0
            for col in date_columns:
                if col in df.columns:
                    null_count = df[col].isnull().sum()
                    if null_count > 0:
                        # For time series data, we'll replace nulls with 0 (no data)
                        df[col] = df[col].fillna(0)
                        null_values_handled += null_count
                        logger.info(f"   Replaced {null_count} null values in {col} with 0")
            
            # Remove duplicate rows
            initial_rows = len(df)
            df = df.drop_duplicates()
            duplicate_rows_removed = initial_rows - len(df)
            
            # Clean RegionID (ensure it's numeric)
            if 'RegionID' in df.columns:
                df['RegionID'] = pd.to_numeric(df['RegionID'], errors='coerce')
                df = df.dropna(subset=['RegionID'])
            
            # Clean RegionName (remove extra whitespace)
            if 'RegionName' in df.columns:
                df['RegionName'] = df['RegionName'].str.strip()
            
            # Clean StateName (standardize state names)
            if 'StateName' in df.columns:
                df['StateName'] = df['StateName'].str.strip().str.title()
            
            # Convert date columns to datetime
            date_columns = config['date_columns']
            for col in date_columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    logger.warning(f"Could not convert {col} to datetime")
            
            # Save processed data
            df.to_csv(processed_file, index=False)
            
            logger.info(f"🧹 Data cleaning for {source}:")
            logger.info(f"   Final rows: {len(df):,}")
            logger.info(f"   Completely null rows removed: {completely_null_rows_removed:,}")
            logger.info(f"   Null values in date columns handled: {null_values_handled:,}")
            logger.info(f"   Duplicate rows removed: {duplicate_rows_removed:,}")
            logger.info(f"   Saved to: {processed_file}")
            
            return {
                'success': True,
                'final_rows': len(df),
                'completely_null_rows_removed': completely_null_rows_removed,
                'null_values_handled': null_values_handled,
                'duplicate_rows_removed': duplicate_rows_removed,
                'processed_file': str(processed_file)
            }
            
        except Exception as e:
            logger.error(f"❌ Data cleaning failed for {source}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_quality_report(self, results: Dict) -> Dict:
        """
        Generate a data quality report.
        
        Args:
            results (Dict): Processing results for all sources
            
        Returns:
            Dict: Quality report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_sources': len(results),
            'successful_sources': sum(1 for r in results.values() if r.get('success', False)),
            'sources': {}
        }
        
        for source, result in results.items():
            report['sources'][source] = {
                'success': result.get('success', False),
                'validation': result.get('validation', {}),
                'cleaning': result.get('cleaning', {})
            }
        
        # Save quality report
        report_file = self.processed_path / "quality_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Quality report generated: {report_file}")
        return report
    
    def _get_master_file_path(self, source: str) -> Path:
        """Get the path for the master copy of a data source."""
        return self.raw_path / f"{source}_master.csv"
    
    def _get_master_metadata_path(self, source: str) -> Path:
        """Get the path for the master copy metadata."""
        return self.raw_path / f"{source}_master_metadata.json"
    
    def _save_master_copy(self, source: str, df: pd.DataFrame, download_url: str) -> Dict:
        """
        Save a master copy of the data with metadata.
        
        Args:
            source (str): Data source identifier
            df (pd.DataFrame): Data to save as master copy
            download_url (str): URL where data was downloaded from
            
        Returns:
            Dict: Master copy metadata
        """
        master_file = self._get_master_file_path(source)
        metadata_file = self._get_master_metadata_path(source)
        
        # Save the data
        df.to_csv(master_file, index=False)
        
        # Calculate file hash for integrity checking
        file_hash = hashlib.md5(master_file.read_bytes()).hexdigest()
        
        # Create metadata
        metadata = {
            'source': source,
            'download_date': datetime.now().isoformat(),
            'download_url': download_url,
            'file_hash': file_hash,
            'total_rows': len(df),
            'columns': list(df.columns),
            'date_columns': [col for col in df.columns if col not in ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank']]
        }
        
        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"💾 Master copy saved for {source}: {master_file}")
        return metadata
    
    def _load_master_copy(self, source: str) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
        """
        Load the master copy and its metadata.
        
        Args:
            source (str): Data source identifier
            
        Returns:
            Tuple[Optional[pd.DataFrame], Optional[Dict]]: Master data and metadata
        """
        master_file = self._get_master_file_path(source)
        metadata_file = self._get_master_metadata_path(source)
        
        if not master_file.exists() or not metadata_file.exists():
            return None, None
        
        try:
            # Load data
            df = pd.read_csv(master_file)
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            logger.info(f"📂 Master copy loaded for {source}: {len(df):,} rows")
            return df, metadata
            
        except Exception as e:
            logger.warning(f"⚠️ Could not load master copy for {source}: {str(e)}")
            return None, None
    
    def _compare_data_continuity(self, source: str, new_df: pd.DataFrame, master_df: pd.DataFrame, master_metadata: Dict) -> Dict:
        """
        Compare new data with master copy for data continuity.
        
        Args:
            source (str): Data source identifier
            new_df (pd.DataFrame): Newly downloaded data
            master_df (pd.DataFrame): Master copy data
            master_metadata (Dict): Master copy metadata
            
        Returns:
            Dict: Comparison results
        """
        logger.info(f"🔍 Comparing data continuity for {source}...")
        
        # Get date columns (time series data)
        date_columns = master_metadata.get('date_columns', [])
        if not date_columns:
            logger.warning(f"No date columns found for {source}, skipping continuity check")
            return {'success': True, 'reason': 'no_date_columns'}
        
        # Find recent date columns (last 12 months)
        recent_cutoff = datetime.now() - timedelta(days=365)
        recent_columns = []
        
        for col in date_columns:
            try:
                # Try to parse the column name as a date
                col_date = pd.to_datetime(col, errors='coerce')
                if pd.notna(col_date) and col_date >= recent_cutoff:
                    recent_columns.append(col)
            except:
                continue
        
        if not recent_columns:
            logger.warning(f"No recent date columns found for {source}, skipping continuity check")
            return {'success': True, 'reason': 'no_recent_columns'}
        
        logger.info(f"📅 Checking {len(recent_columns)} recent columns for {source}")
        
        # Compare recent data
        differences_found = []
        tolerance = 0.01  # 1% tolerance for differences
        
        for col in recent_columns:
            if col not in new_df.columns:
                differences_found.append(f"Missing column: {col}")
                continue
            
            # Get common RegionIDs
            common_regions = set(new_df['RegionID']) & set(master_df['RegionID'])
            
            for region_id in common_regions:
                new_value = new_df[new_df['RegionID'] == region_id][col].iloc[0] if len(new_df[new_df['RegionID'] == region_id]) > 0 else None
                master_value = master_df[master_df['RegionID'] == region_id][col].iloc[0] if len(master_df[master_df['RegionID'] == region_id]) > 0 else None
                
                # Skip if either value is null or zero
                if pd.isna(new_value) or pd.isna(master_value) or new_value == 0 or master_value == 0:
                    continue
                
                # Calculate percentage difference
                if master_value != 0:
                    pct_diff = abs(new_value - master_value) / master_value
                    if pct_diff > tolerance:
                        differences_found.append(f"RegionID {region_id}, {col}: {master_value:.2f} → {new_value:.2f} ({pct_diff:.1%} change)")
        
        if differences_found:
            logger.error(f"❌ Data continuity issues found for {source}:")
            for diff in differences_found[:10]:  # Show first 10 differences
                logger.error(f"   {diff}")
            if len(differences_found) > 10:
                logger.error(f"   ... and {len(differences_found) - 10} more differences")
            
            return {
                'success': False,
                'reason': 'data_discontinuity',
                'differences': differences_found,
                'message': f"Recent data values have changed significantly for {source}. This may indicate data source issues or corrections."
            }
        
        logger.info(f"✅ Data continuity validated for {source}")
        return {
            'success': True,
            'reason': 'continuity_validated',
            'recent_columns_checked': len(recent_columns)
        }

def main():
    """Main entry point for the data ingestion script."""
    parser = argparse.ArgumentParser(description='RE Market Tool Data Ingestion')
    parser.add_argument('--data-sources', default='zhvi,zori', 
                       help='Comma-separated list of data sources')
    parser.add_argument('--output-dir', type=Path, 
                       help='Output directory for processed data')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing data without downloading')
    
    args = parser.parse_args()
    
    # Set up data path
    if args.output_dir:
        data_path = args.output_dir
    else:
        data_path = Path(__file__).parent.parent / "data"
    
    # Parse data sources
    data_sources = [s.strip() for s in args.data_sources.split(',')]
    
    # Initialize and run ingestion
    ingestion = DataIngestion(data_path)
    result = ingestion.run(data_sources, args.validate_only)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()

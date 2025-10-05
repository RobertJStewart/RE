#!/usr/bin/env python3
"""
RE Market Tool - Zillow Column Analysis
======================================

This script downloads Zillow CSV files and analyzes their column structure
to validate our critical column assumptions and identify any missing columns.

Usage:
    python test_zillow_columns.py
"""

import os
import sys
import logging
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZillowColumnAnalyzer:
    """
    Analyzes Zillow CSV files to validate column structure and identify issues.
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        self.data_sources = {
            'zhvi': {
                'name': 'Zillow Home Value Index',
                'url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_Zhvi_AllHomes.csv',
                'filename': 'zhvi_test.csv'
            },
            'zori': {
                'name': 'Zillow Rent Index',
                'url': 'https://files.zillowstatic.com/research/public_csvs/zori/Zip_ZORI_AllHomesPlusMultifamily.csv',
                'filename': 'zori_test.csv'
            }
        }
        
        # Critical columns we expect
        self.expected_critical_columns = [
            'RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank'
        ]
        
        # Create test directory
        self.test_dir = Path(__file__).parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)
        
        logger.info("Zillow Column Analyzer initialized")
    
    def download_and_analyze(self):
        """
        Download Zillow files and analyze their column structure.
        
        Returns:
            Dict: Analysis results for all sources
        """
        logger.info("🚀 Starting Zillow column analysis...")
        results = {}
        
        for source, config in self.data_sources.items():
            logger.info(f"📥 Analyzing {config['name']}...")
            result = self._analyze_source(source, config)
            results[source] = result
        
        # Generate summary report
        self._generate_summary_report(results)
        return results
    
    def _analyze_source(self, source: str, config: Dict) -> Dict:
        """
        Analyze a single data source.
        
        Args:
            source (str): Data source identifier
            config (Dict): Source configuration
            
        Returns:
            Dict: Analysis result
        """
        try:
            # Download the file
            logger.info(f"📥 Downloading {config['name']}...")
            response = requests.get(config['url'], timeout=300)
            response.raise_for_status()
            
            # Save to test directory
            test_file = self.test_dir / config['filename']
            with open(test_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Downloaded {config['name']} to {test_file}")
            
            # Load and analyze the CSV
            df = pd.read_csv(test_file)
            
            # Analyze columns
            analysis = self._analyze_columns(df, source)
            
            # Clean up test file
            test_file.unlink()
            
            return {
                'success': True,
                'source': source,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze {source}: {str(e)}")
            return {
                'success': False,
                'source': source,
                'error': str(e)
            }
    
    def _analyze_columns(self, df: pd.DataFrame, source: str) -> Dict:
        """
        Analyze the column structure of a DataFrame.
        
        Args:
            df (pd.DataFrame): Data to analyze
            source (str): Source identifier
            
        Returns:
            Dict: Column analysis results
        """
        all_columns = list(df.columns)
        
        # Check for expected critical columns
        missing_critical = []
        present_critical = []
        
        for col in self.expected_critical_columns:
            if col in all_columns:
                present_critical.append(col)
            else:
                missing_critical.append(col)
        
        # Identify date columns (columns that look like dates)
        date_columns = []
        non_date_columns = []
        
        for col in all_columns:
            if col in self.expected_critical_columns:
                non_date_columns.append(col)
            else:
                # Try to parse as date
                try:
                    pd.to_datetime(col, errors='coerce')
                    if pd.notna(pd.to_datetime(col, errors='coerce')):
                        date_columns.append(col)
                    else:
                        non_date_columns.append(col)
                except:
                    non_date_columns.append(col)
        
        # Check for data types
        column_types = {}
        for col in all_columns:
            column_types[col] = str(df[col].dtype)
        
        # Check for null values
        null_counts = {}
        for col in all_columns:
            null_counts[col] = int(df[col].isnull().sum())
        
        logger.info(f"📊 Column analysis for {source}:")
        logger.info(f"   Total columns: {len(all_columns)}")
        logger.info(f"   Critical columns present: {len(present_critical)}/{len(self.expected_critical_columns)}")
        logger.info(f"   Date columns: {len(date_columns)}")
        logger.info(f"   Missing critical columns: {missing_critical}")
        
        return {
            'all_columns': all_columns,
            'critical_columns': {
                'expected': self.expected_critical_columns,
                'present': present_critical,
                'missing': missing_critical
            },
            'date_columns': date_columns,
            'non_date_columns': non_date_columns,
            'column_types': column_types,
            'null_counts': null_counts
        }
    
    def _generate_summary_report(self, results: Dict):
        """
        Generate a summary report of the analysis.
        
        Args:
            results (Dict): Analysis results for all sources
        """
        report = {
            'analysis_date': datetime.now().isoformat(),
            'sources_analyzed': len(results),
            'successful_sources': sum(1 for r in results.values() if r.get('success', False)),
            'sources': {}
        }
        
        for source, result in results.items():
            if result.get('success', False):
                analysis = result['analysis']
                report['sources'][source] = {
                    'total_rows': result['total_rows'],
                    'total_columns': result['total_columns'],
                    'critical_columns_present': len(analysis['critical_columns']['present']),
                    'critical_columns_missing': analysis['critical_columns']['missing'],
                    'date_columns_count': len(analysis['date_columns']),
                    'all_columns': analysis['all_columns']
                }
            else:
                report['sources'][source] = {
                    'error': result.get('error', 'Unknown error')
                }
        
        # Save report
        report_file = self.test_dir / "column_analysis_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Column analysis report saved: {report_file}")
        
        # Print summary
        logger.info("📊 COLUMN ANALYSIS SUMMARY:")
        logger.info("=" * 50)
        
        for source, result in results.items():
            if result.get('success', False):
                analysis = result['analysis']
                logger.info(f"\n🔍 {source.upper()}:")
                logger.info(f"   Total rows: {result['total_rows']:,}")
                logger.info(f"   Total columns: {result['total_columns']}")
                logger.info(f"   Critical columns present: {len(analysis['critical_columns']['present'])}/{len(self.expected_critical_columns)}")
                logger.info(f"   Date columns: {len(analysis['date_columns'])}")
                
                if analysis['critical_columns']['missing']:
                    logger.warning(f"   ⚠️  Missing critical columns: {analysis['critical_columns']['missing']}")
                else:
                    logger.info(f"   ✅ All critical columns present")
                
                logger.info(f"   📅 Date columns (first 5): {analysis['date_columns'][:5]}")
                logger.info(f"   📋 All columns: {analysis['all_columns']}")
            else:
                logger.error(f"\n❌ {source.upper()}: {result.get('error', 'Unknown error')}")

def main():
    """Main entry point for the column analyzer."""
    analyzer = ZillowColumnAnalyzer()
    results = analyzer.download_and_analyze()
    
    # Exit with appropriate code
    successful_sources = sum(1 for r in results.values() if r.get('success', False))
    total_sources = len(results)
    
    if successful_sources == total_sources:
        logger.info("✅ All sources analyzed successfully")
        sys.exit(0)
    else:
        logger.error(f"❌ {total_sources - successful_sources} sources failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

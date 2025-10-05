#!/usr/bin/env python3
"""
RE Market Tool - New Data Connection Discovery
=============================================

This module provides an intelligent data connection discovery system that can:
1. Accept URLs or connection descriptions from users
2. Query AI models for connection strategies
3. Test and validate connections
4. Analyze data structure to populate DataConnection metadata
5. Generate fallback procedures
6. Save connection configurations for future use

Usage:
    from new_data_connection import NewDataConnection
    connection = NewDataConnection()
    result = connection.discover_connection(url="https://example.com/data.csv")
"""

import os
import sys
import logging
import requests
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import re
from dataclasses import dataclass, asdict

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.data_connection import BaseDataConnection, DataSourceMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionDiscoveryResult:
    """Result of a data connection discovery attempt."""
    success: bool
    source_name: str
    data_type: str
    geography: str
    connection_methods: List[Dict[str, Any]]
    fallback_procedures: List[Dict[str, Any]]
    critical_columns: List[str]
    expected_columns: List[str]
    sample_data: Optional[pd.DataFrame]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class NewDataConnection:
    """
    Intelligent data connection discovery and configuration system.
    
    This class can automatically discover, analyze, and configure new data sources
    by leveraging AI assistance and data analysis.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the new data connection discovery system.
        
        Args:
            config_path (Path): Path to save discovered connections
        """
        self.config_path = config_path or Path(__file__).parent.parent / "data_connections"
        self.config_path.mkdir(exist_ok=True)
        
        # AI model configuration (placeholder for now)
        self.ai_model = "claude"  # Could be "gpt", "claude", "local", etc.
        
        logger.info(f"New Data Connection discovery initialized with config path: {self.config_path}")
    
    def discover_connection(self, 
                          url: Optional[str] = None,
                          description: Optional[str] = None,
                          source_name: Optional[str] = None) -> ConnectionDiscoveryResult:
        """
        Discover and configure a new data connection.
        
        Args:
            url (str): Direct URL to data source
            description (str): Description of data source and how to access it
            source_name (str): Name for the data source
            
        Returns:
            ConnectionDiscoveryResult: Discovery result with connection details
        """
        logger.info(f"🔍 Starting connection discovery for: {source_name or url or description}")
        
        try:
            # Step 1: Get AI assistance for connection strategy
            connection_strategy = self._get_ai_connection_strategy(url, description, source_name)
            
            # Step 2: Test connection methods
            working_methods = self._test_connection_methods(connection_strategy)
            
            if not working_methods:
                return ConnectionDiscoveryResult(
                    success=False,
                    source_name=source_name or "Unknown",
                    data_type="unknown",
                    geography="unknown",
                    connection_methods=[],
                    fallback_procedures=[],
                    critical_columns=[],
                    expected_columns=[],
                    sample_data=None,
                    metadata={},
                    error="No working connection methods found"
                )
            
            # Step 3: Download and analyze sample data
            sample_data = self._download_sample_data(working_methods[0])
            
            if sample_data is None or sample_data.empty:
                return ConnectionDiscoveryResult(
                    success=False,
                    source_name=source_name or "Unknown",
                    data_type="unknown",
                    geography="unknown",
                    connection_methods=working_methods,
                    fallback_procedures=[],
                    critical_columns=[],
                    expected_columns=[],
                    sample_data=None,
                    metadata={},
                    error="Failed to download sample data"
                )
            
            # Step 4: Analyze data structure
            analysis_result = self._analyze_data_structure(sample_data, source_name)
            
            # Step 5: Generate fallback procedures
            fallback_procedures = self._generate_fallback_procedures(connection_strategy, working_methods)
            
            # Step 6: Create connection result
            result = ConnectionDiscoveryResult(
                success=True,
                source_name=analysis_result['source_name'],
                data_type=analysis_result['data_type'],
                geography=analysis_result['geography'],
                connection_methods=working_methods,
                fallback_procedures=fallback_procedures,
                critical_columns=analysis_result['critical_columns'],
                expected_columns=analysis_result['expected_columns'],
                sample_data=sample_data,
                metadata=analysis_result['metadata']
            )
            
            # Step 7: Save connection configuration
            self._save_connection_config(result)
            
            logger.info(f"✅ Connection discovery completed successfully for {result.source_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Connection discovery failed: {str(e)}")
            return ConnectionDiscoveryResult(
                success=False,
                source_name=source_name or "Unknown",
                data_type="unknown",
                geography="unknown",
                connection_methods=[],
                fallback_procedures=[],
                critical_columns=[],
                expected_columns=[],
                sample_data=None,
                metadata={},
                error=str(e)
            )
    
    def _get_ai_connection_strategy(self, url: Optional[str], description: Optional[str], source_name: Optional[str]) -> Dict[str, Any]:
        """
        Get AI assistance for connection strategy.
        
        Args:
            url (str): Direct URL to data source
            description (str): Description of data source
            source_name (str): Name for the data source
            
        Returns:
            Dict: Connection strategy with methods to try
        """
        logger.info("🤖 Getting AI assistance for connection strategy...")
        
        # For now, implement basic heuristics
        # In the future, this would call an AI model
        
        strategy = {
            'source_name': source_name or self._infer_source_name(url, description),
            'connection_methods': [],
            'data_type_hints': [],
            'geography_hints': []
        }
        
        if url:
            # Analyze URL for connection hints
            if url.endswith('.csv'):
                strategy['connection_methods'].append({
                    'type': 'url',
                    'url': url,
                    'method': 'direct_csv_download',
                    'status': 'unknown',
                    'notes': 'Direct CSV download from URL'
                })
            elif 'api' in url.lower():
                strategy['connection_methods'].append({
                    'type': 'api',
                    'url': url,
                    'method': 'api_endpoint',
                    'status': 'unknown',
                    'notes': 'API endpoint connection'
                })
            else:
                strategy['connection_methods'].append({
                    'type': 'url',
                    'url': url,
                    'method': 'web_scraping',
                    'status': 'unknown',
                    'notes': 'Web scraping approach'
                })
        else:
            # No URL provided, create mock connection method for testing
            strategy['connection_methods'].append({
                'type': 'mock',
                'url': 'mock://data',
                'method': 'mock_data_generation',
                'status': 'healthy',
                'notes': 'Mock data generation for testing'
            })
        
        if description:
            # Extract hints from description
            description_lower = description.lower()
            
            if 'zillow' in description_lower:
                strategy['data_type_hints'].extend(['zhvi', 'zori'])
                strategy['geography_hints'].extend(['zip', 'metro', 'state', 'county', 'city'])
            elif 'real estate' in description_lower or 'housing' in description_lower:
                strategy['data_type_hints'].extend(['home_values', 'rental_prices'])
                strategy['geography_hints'].extend(['zip', 'metro', 'state'])
            elif 'rental' in description_lower:
                strategy['data_type_hints'].extend(['rental_prices', 'zori'])
                strategy['geography_hints'].extend(['zip', 'metro', 'city'])
        
        return strategy
    
    def _test_connection_methods(self, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Test connection methods and return working ones.
        
        Args:
            strategy (Dict): Connection strategy with methods to test
            
        Returns:
            List[Dict]: List of working connection methods
        """
        logger.info("🔗 Testing connection methods...")
        
        working_methods = []
        
        for method in strategy['connection_methods']:
            try:
                if method['type'] == 'url':
                    # Test URL accessibility
                    response = requests.head(method['url'], timeout=10)
                    if response.status_code == 200:
                        method['status'] = 'healthy'
                        method['response_time'] = response.elapsed.total_seconds()
                        working_methods.append(method)
                        logger.info(f"✅ Method {method['method']} is working")
                    else:
                        method['status'] = 'unhealthy'
                        logger.warning(f"⚠️  Method {method['method']} returned status {response.status_code}")
                elif method['type'] == 'mock':
                    # Mock method is always working
                    method['status'] = 'healthy'
                    working_methods.append(method)
                    logger.info(f"✅ Method {method['method']} is working (mock)")
                else:
                    # For now, mark as unknown
                    method['status'] = 'unknown'
                    working_methods.append(method)
                    logger.info(f"❓ Method {method['method']} status unknown")
                    
            except Exception as e:
                method['status'] = 'unhealthy'
                method['error'] = str(e)
                logger.warning(f"⚠️  Method {method['method']} failed: {str(e)}")
        
        return working_methods
    
    def _download_sample_data(self, method: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Download sample data using a working connection method.
        
        Args:
            method (Dict): Working connection method
            
        Returns:
            Optional[pd.DataFrame]: Sample data or None if failed
        """
        logger.info(f"📥 Downloading sample data using {method['method']}...")
        
        try:
            if method['type'] == 'url':
                response = requests.get(method['url'], timeout=30)
                if response.status_code == 200:
                    # Try to parse as CSV
                    from io import StringIO
                    df = pd.read_csv(StringIO(response.text))
                    logger.info(f"✅ Downloaded {len(df)} rows, {len(df.columns)} columns")
                    return df
                else:
                    logger.error(f"❌ Failed to download data: HTTP {response.status_code}")
                    return None
            else:
                logger.warning(f"⚠️  Unsupported method type: {method['type']}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to download sample data: {str(e)}")
            return None
    
    def _analyze_data_structure(self, df: pd.DataFrame, source_name: Optional[str]) -> Dict[str, Any]:
        """
        Analyze data structure to determine metadata.
        
        Args:
            df (pd.DataFrame): Sample data
            source_name (Optional[str]): Source name hint
            
        Returns:
            Dict: Analysis result with metadata
        """
        logger.info("🔍 Analyzing data structure...")
        
        # Basic analysis
        total_rows = len(df)
        total_columns = len(df.columns)
        
        # Identify column types
        column_types = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                column_types[col] = 'string'
            elif df[col].dtype in ['int64', 'float64']:
                column_types[col] = 'numeric'
            else:
                column_types[col] = 'other'
        
        # Identify potential critical columns
        critical_columns = []
        expected_columns = list(df.columns)
        
        # Look for common patterns
        for col in df.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in ['region', 'id', 'name', 'state', 'county', 'city', 'zip']):
                critical_columns.append(col)
        
        # Identify date columns
        date_columns = []
        for col in df.columns:
            if re.match(r'\d{4}-\d{2}-\d{2}', str(col)) or 'date' in col.lower():
                date_columns.append(col)
        
        # Infer data type and geography
        data_type = self._infer_data_type(df, source_name)
        geography = self._infer_geography(df, source_name)
        
        # Create metadata
        metadata = {
            'total_rows': total_rows,
            'total_columns': total_columns,
            'column_types': column_types,
            'date_columns': date_columns,
            'sample_values': {}
        }
        
        # Add sample values for each column
        for col in df.columns:
            sample_values = df[col].dropna().head(3).tolist()
            metadata['sample_values'][col] = sample_values
        
        result = {
            'source_name': source_name or self._infer_source_name_from_data(df),
            'data_type': data_type,
            'geography': geography,
            'critical_columns': critical_columns,
            'expected_columns': expected_columns,
            'metadata': metadata
        }
        
        logger.info(f"📊 Analysis complete: {data_type} {geography} data with {len(critical_columns)} critical columns")
        return result
    
    def _generate_fallback_procedures(self, strategy: Dict[str, Any], working_methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate fallback procedures for the connection.
        
        Args:
            strategy (Dict): Connection strategy
            working_methods (List[Dict]): Working connection methods
            
        Returns:
            List[Dict]: Fallback procedures
        """
        logger.info("🔄 Generating fallback procedures...")
        
        fallback_procedures = [
            {
                'type': 'cached_data',
                'description': 'Use last known good data from master copy',
                'priority': 1,
                'notes': 'Continue with existing data until connection restored'
            },
            {
                'type': 'alternative_source',
                'description': 'Switch to alternative data provider',
                'priority': 2,
                'notes': 'Find alternative source for same data type'
            },
            {
                'type': 'manual_download',
                'description': 'Manual data download and upload',
                'priority': 3,
                'notes': 'Human intervention required'
            }
        ]
        
        # Add method-specific fallbacks
        for method in working_methods:
            if method['type'] == 'url':
                fallback_procedures.append({
                    'type': 'url_variation',
                    'description': f'Try URL variations for {method["method"]}',
                    'priority': 2,
                    'notes': 'Attempt different URL patterns or endpoints'
                })
        
        return fallback_procedures
    
    def _save_connection_config(self, result: ConnectionDiscoveryResult):
        """
        Save connection configuration for future use.
        
        Args:
            result (ConnectionDiscoveryResult): Discovery result to save
        """
        logger.info(f"💾 Saving connection configuration for {result.source_name}...")
        
        # Create configuration file
        config = {
            'discovery_date': datetime.now().isoformat(),
            'source_name': result.source_name,
            'data_type': result.data_type,
            'geography': result.geography,
            'connection_methods': result.connection_methods,
            'fallback_procedures': result.fallback_procedures,
            'critical_columns': result.critical_columns,
            'expected_columns': result.expected_columns,
            'metadata': result.metadata
        }
        
        # Save to file
        config_file = self.config_path / f"{result.source_name}_{result.data_type}_{result.geography}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"✅ Configuration saved to {config_file}")
    
    def _infer_source_name(self, url: Optional[str], description: Optional[str]) -> str:
        """Infer source name from URL or description."""
        if url:
            # Extract domain name
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain.split('.')[0].title()
        elif description:
            # Look for company names in description
            description_lower = description.lower()
            if 'zillow' in description_lower:
                return 'Zillow'
            elif 'redfin' in description_lower:
                return 'Redfin'
            elif 'realtor' in description_lower:
                return 'Realtor'
            else:
                return 'Unknown'
        else:
            return 'Unknown'
    
    def _infer_data_type(self, df: pd.DataFrame, source_name: Optional[str]) -> str:
        """Infer data type from DataFrame structure."""
        columns_lower = [col.lower() for col in df.columns]
        
        if any('zhvi' in col for col in columns_lower) or any('home' in col for col in columns_lower):
            return 'zhvi'
        elif any('zori' in col for col in columns_lower) or any('rent' in col for col in columns_lower):
            return 'zori'
        elif source_name and 'zillow' in source_name.lower():
            return 'zhvi'  # Default for Zillow
        else:
            return 'unknown'
    
    def _infer_geography(self, df: pd.DataFrame, source_name: Optional[str]) -> str:
        """Infer geography level from DataFrame structure."""
        columns_lower = [col.lower() for col in df.columns]
        
        if any('zip' in col for col in columns_lower):
            return 'zip'
        elif any('metro' in col for col in columns_lower):
            return 'metro'
        elif any('state' in col for col in columns_lower):
            return 'state'
        elif any('county' in col for col in columns_lower):
            return 'county'
        elif any('city' in col for col in columns_lower):
            return 'city'
        elif any('neighborhood' in col for col in columns_lower):
            return 'neighborhood'
        else:
            return 'unknown'
    
    def _infer_source_name_from_data(self, df: pd.DataFrame) -> str:
        """Infer source name from data structure."""
        # Look for patterns in column names or data
        columns_lower = [col.lower() for col in df.columns]
        
        if any('zillow' in col for col in columns_lower):
            return 'Zillow'
        elif any('redfin' in col for col in columns_lower):
            return 'Redfin'
        else:
            return 'Unknown'

# Example usage and testing
if __name__ == "__main__":
    # Initialize new data connection discovery
    discovery = NewDataConnection()
    
    # Example: Discover connection from URL
    print("=== New Data Connection Discovery Test ===")
    
    # Test with a mock URL (replace with real URL for testing)
    result = discovery.discover_connection(
        url="https://example.com/sample_data.csv",
        description="Zillow home value data for ZIP codes",
        source_name="Zillow"
    )
    
    print(f"\nDiscovery Result:")
    print(f"  Success: {result.success}")
    print(f"  Source: {result.source_name}")
    print(f"  Data Type: {result.data_type}")
    print(f"  Geography: {result.geography}")
    print(f"  Critical Columns: {result.critical_columns}")
    print(f"  Connection Methods: {len(result.connection_methods)}")
    print(f"  Fallback Procedures: {len(result.fallback_procedures)}")
    
    if result.error:
        print(f"  Error: {result.error}")
    
    print(f"\n=== Test Complete ===")

#!/usr/bin/env python3
"""
RE Market Tool - Data Connection Management
==========================================

This module provides a centralized data connection management system for
different real estate data sources. It encapsulates all metadata, connection
methods, and fallback procedures for each data source.

Usage:
    from data_connection import ZillowDataConnection
    connection = ZillowDataConnection()
    metadata = connection.get_metadata('zhvi', 'zip')
"""

import os
import sys
import logging
import requests
import pandas as pd
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
import json
import hashlib
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataSourceMetadata:
    """Metadata for a specific data source and geography combination."""
    source_name: str
    data_type: str
    geography: str
    critical_columns: List[str]
    expected_columns: List[str]
    date_columns: List[str]
    typical_row_count: str
    data_availability: str
    unit: str
    frequency: str
    date_range: str
    connection_methods: List[Dict[str, Any]]
    fallback_procedures: List[Dict[str, Any]]

@dataclass
class DiscoveryResult:
    """Result of data source discovery process."""
    success: bool
    discovered_columns: List[str]
    critical_columns: List[str]
    date_columns: List[str]
    sample_data: Optional[pd.DataFrame] = None
    error_message: Optional[str] = None
    confidence_score: float = 0.0

class BaseDataConnection(ABC):
    """
    Abstract base class for all data connections.
    
    This class defines the interface that all data source connections must implement.
    """
    
    def __init__(self, source_name: str):
        """
        Initialize the base data connection.
        
        Args:
            source_name (str): Name of the data source (e.g., 'RE', 'Zillow', 'Redfin')
        """
        self.source_name = source_name
        self.connection_health = {}
        self.last_health_check = None
        
        logger.info(f"Initialized {source_name} data connection")
    
    @abstractmethod
    def get_metadata(self, data_type: str, geography: str) -> DataSourceMetadata:
        """
        Get metadata for a specific data type and geography.
        
        Args:
            data_type (str): Type of data (e.g., 'zhvi', 'zori')
            geography (str): Geography level (e.g., 'zip', 'metro')
            
        Returns:
            DataSourceMetadata: Metadata for the requested combination
        """
        pass
    
    @abstractmethod
    def get_connection_methods(self, data_type: str, geography: str) -> List[Dict[str, Any]]:
        """
        Get available connection methods for a data type and geography.
        
        Args:
            data_type (str): Type of data
            geography (str): Geography level
            
        Returns:
            List[Dict]: List of connection methods with their details
        """
        pass
    
    @abstractmethod
    def get_fallback_procedures(self, data_type: str, geography: str) -> List[Dict[str, Any]]:
        """
        Get fallback procedures when primary connection fails.
        
        Args:
            data_type (str): Type of data
            geography (str): Geography level
            
        Returns:
            List[Dict]: List of fallback procedures
        """
        pass
    
    # Phase 1: Data Source Introspection Methods
    @abstractmethod
    def discover_columns(self, data_type: str, sub_type: str, geography: str, sample_size: int = 100) -> DiscoveryResult:
        """
        Discover required columns by analyzing sample data.
        
        Args:
            data_type: Type of data (e.g., 'zhvi', 'zori')
            sub_type: Sub-type of data (e.g., 'all_homes_smoothed_seasonally_adjusted')
            geography: Geographic level (e.g., 'zip', 'metro')
            sample_size: Number of rows to sample for analysis
            
        Returns:
            DiscoveryResult with discovered column information
        """
        pass
    
    @abstractmethod
    def discover_geographic_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available geographic levels and their relationships.
        
        Returns:
            Dictionary mapping geography levels to their metadata
        """
        pass
    
    def _analyze_required_columns(self, sample_data: pd.DataFrame, data_type: str, geography: str) -> Tuple[List[str], List[str], float]:
        """
        Analyze sample data to determine required columns and date columns.
        
        Args:
            sample_data: Sample DataFrame to analyze
            data_type: Type of data being analyzed
            geography: Geographic level being analyzed
            
        Returns:
            Tuple of (critical_columns, date_columns, confidence_score)
        """
        if sample_data.empty:
            return [], [], 0.0
        
        # Identify critical columns based on data type and geography
        critical_columns = []
        date_columns = []
        confidence_score = 0.0
        
        # Always required columns
        base_columns = ['RegionID', 'RegionName']
        
        # Geography-specific columns
        geography_columns = {
            'metro': ['StateName', 'Metro', 'CountyName', 'SizeRank'],
            'state': ['StateName', 'SizeRank'],
            'county': ['StateName', 'CountyName', 'SizeRank'],
            'city': ['StateName', 'CityName', 'SizeRank'],
            'zip': ['StateName', 'SizeRank'],
            'neighborhood': ['StateName', 'NeighborhoodName', 'CityName', 'SizeRank']
        }
        
        # Check for base columns
        for col in base_columns:
            if col in sample_data.columns:
                critical_columns.append(col)
                confidence_score += 0.2
        
        # Check for geography-specific columns
        geo_cols = geography_columns.get(geography, [])
        for col in geo_cols:
            if col in sample_data.columns:
                critical_columns.append(col)
                confidence_score += 0.1
        
        # Identify date columns (typically YYYY-MM-DD format or similar)
        for col in sample_data.columns:
            if col not in critical_columns:
                # Check if column looks like a date
                if self._is_date_column(sample_data[col]):
                    date_columns.append(col)
                    confidence_score += 0.05
        
        # Normalize confidence score
        confidence_score = min(confidence_score, 1.0)
        
        return critical_columns, date_columns, confidence_score
    
    def _is_date_column(self, series: pd.Series) -> bool:
        """
        Check if a pandas Series contains date-like data.
        
        Args:
            series: Pandas Series to check
            
        Returns:
            True if series appears to contain dates
        """
        try:
            # Try to convert to datetime
            pd.to_datetime(series.dropna().head(10))
            return True
        except:
            # Check if column name suggests it's a date
            col_name = series.name.lower()
            date_indicators = ['date', 'time', 'year', 'month', 'day', 'period']
            return any(indicator in col_name for indicator in date_indicators)
    
    def check_connection_health(self, data_type: str, sub_type: str, geography: str) -> Dict[str, Any]:
        """
        Check the health of a specific data connection.
        
        Args:
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            Dict: Health status and details
        """
        connection_key = f"{data_type}_{sub_type}_{geography}"
        
        try:
            # Get connection methods
            methods = self.get_connection_methods(data_type, sub_type, geography)
            
            health_status = {
                'source': self.source_name,
                'data_type': data_type,
                'sub_type': sub_type,
                'geography': geography,
                'timestamp': datetime.now().isoformat(),
                'methods': [],
                'overall_status': 'unknown'
            }
            
            # Test each connection method
            for method in methods:
                method_status = self._test_connection_method(method)
                health_status['methods'].append(method_status)
            
            # Determine overall status
            if any(m['status'] == 'healthy' for m in health_status['methods']):
                health_status['overall_status'] = 'healthy'
            elif any(m['status'] == 'degraded' for m in health_status['methods']):
                health_status['overall_status'] = 'degraded'
            else:
                health_status['overall_status'] = 'unhealthy'
            
            # Cache the result
            self.connection_health[connection_key] = health_status
            self.last_health_check = datetime.now()
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking connection health for {data_type} {geography}: {str(e)}")
            return {
                'source': self.source_name,
                'data_type': data_type,
                'geography': geography,
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _test_connection_method(self, method: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a specific connection method.
        
        Args:
            method (Dict): Connection method details
            
        Returns:
            Dict: Test results
        """
        try:
            if method['type'] == 'url':
                # Test URL accessibility
                response = requests.head(method['url'], timeout=10)
                if response.status_code == 200:
                    return {
                        'method': method,
                        'status': 'healthy',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code
                    }
                elif response.status_code in [301, 302, 307, 308]:
                    return {
                        'method': method,
                        'status': 'degraded',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code,
                        'note': 'Redirect detected'
                    }
                else:
                    return {
                        'method': method,
                        'status': 'unhealthy',
                        'response_time': response.elapsed.total_seconds(),
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}"
                    }
            else:
                return {
                    'method': method,
                    'status': 'unknown',
                    'note': f"Unknown method type: {method['type']}"
                }
                
        except requests.exceptions.Timeout:
            return {
                'method': method,
                'status': 'unhealthy',
                'error': 'Connection timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'method': method,
                'status': 'unhealthy',
                'error': 'Connection error'
            }
        except Exception as e:
            return {
                'method': method,
                'status': 'unhealthy',
                'error': str(e)
            }

class REDataConnection(BaseDataConnection):
    """
    Real Estate data connection management.
    
    This class encapsulates all real estate data source information, including
    metadata, connection methods, and fallback procedures.
    """
    
    def __init__(self):
        """Initialize RE data connection."""
        super().__init__("RE")
        
        # Initialize data source subclasses
        self.zillow = ZillowDataConnection()
        # Future: self.redfin = RedfinDataConnection()
        # Future: self.corelogic = CoreLogicDataConnection()
    
    def get_metadata(self, data_source: str, data_type: str, sub_type: str, geography: str) -> DataSourceMetadata:
        """
        Get metadata for a specific data source, data type, sub-type, and geography.
        
        Args:
            data_source (str): Data source (e.g., 'zillow', 'redfin')
            data_type (str): Type of data (e.g., 'zhvi', 'zori')
            sub_type (str): Sub-type of data (e.g., 'all_homes_smoothed_seasonally_adjusted')
            geography (str): Geography level (e.g., 'zip', 'metro')
            
        Returns:
            DataSourceMetadata: Metadata for the requested combination
        """
        if data_source == 'zillow':
            return self.zillow.get_metadata(data_type, sub_type, geography)
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def get_connection_methods(self, data_source: str, data_type: str, sub_type: str, geography: str) -> List[Dict[str, Any]]:
        """
        Get available connection methods for a data source, data type, sub-type, and geography.
        
        Args:
            data_source (str): Data source
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            List[Dict]: List of connection methods with their details
        """
        if data_source == 'zillow':
            return self.zillow.get_connection_methods(data_type, sub_type, geography)
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def get_fallback_procedures(self, data_source: str, data_type: str, sub_type: str, geography: str) -> List[Dict[str, Any]]:
        """
        Get fallback procedures when primary connection fails.
        
        Args:
            data_source (str): Data source
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            List[Dict]: List of fallback procedures
        """
        if data_source == 'zillow':
            return self.zillow.get_fallback_procedures(data_type, sub_type, geography)
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def get_download_url(self, data_source: str, data_type: str, sub_type: str, geography: str) -> str:
        """
        Get the download URL for a specific data source, data type, sub-type, and geography combination.
        
        Args:
            data_source (str): Data source
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            str: Download URL for the requested combination
        """
        if data_source == 'zillow':
            return self.zillow.get_download_url(data_type, sub_type, geography)
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    # Phase 2: Geographic Hierarchy Discovery
    def discover_geographic_hierarchy(self, data_source: str = 'zillow') -> Dict[str, Dict[str, Any]]:
        """
        Discover available geographic levels and their relationships.
        
        Args:
            data_source: Data source to discover hierarchy for
            
        Returns:
            Dictionary mapping geography levels to their metadata
        """
        if data_source == 'zillow':
            return self.zillow.discover_geographic_hierarchy()
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def discover_columns(self, data_source: str, data_type: str, sub_type: str, geography: str, sample_size: int = 100) -> DiscoveryResult:
        """
        Discover required columns by analyzing sample data.
        
        Args:
            data_source: Data source
            data_type: Type of data
            sub_type: Sub-type of data
            geography: Geographic level
            sample_size: Number of rows to sample for analysis
            
        Returns:
            DiscoveryResult with discovered column information
        """
        if data_source == 'zillow':
            return self.zillow.discover_columns(data_type, sub_type, geography, sample_size)
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def get_dynamic_critical_columns(self, data_source: str, data_type: str, sub_type: str, geography: str, use_discovery: bool = True) -> List[str]:
        """
        Get critical columns using either discovery or hardcoded fallback.
        
        Args:
            data_source: Data source
            data_type: Type of data
            sub_type: Sub-type of data
            geography: Geographic level
            use_discovery: Whether to use discovery or fallback to hardcoded
            
        Returns:
            List of critical columns
        """
        if use_discovery:
            try:
                # Try discovery first
                result = self.discover_columns(data_source, data_type, sub_type, geography, sample_size=50)
                if result.success and result.critical_columns:
                    logger.info(f"✅ Using discovered critical columns for {data_source}-{data_type}-{geography}")
                    return result.critical_columns
            except Exception as e:
                logger.warning(f"⚠️ Discovery failed, falling back to hardcoded: {e}")
        
        # Fallback to hardcoded
        if data_source == 'zillow':
            return self.zillow.get_critical_columns(geography)
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    def get_dynamic_geographic_hierarchy(self, data_source: str = 'zillow', use_discovery: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Get geographic hierarchy using either discovery or hardcoded fallback.
        
        Args:
            data_source: Data source
            use_discovery: Whether to use discovery or fallback to hardcoded
            
        Returns:
            Dictionary mapping geography levels to their metadata
        """
        if use_discovery:
            try:
                # Try discovery first
                hierarchy = self.discover_geographic_hierarchy(data_source)
                if hierarchy:
                    logger.info(f"✅ Using discovered geographic hierarchy for {data_source}")
                    return hierarchy
            except Exception as e:
                logger.warning(f"⚠️ Discovery failed, falling back to hardcoded: {e}")
        
        # Fallback to hardcoded
        if data_source == 'zillow':
            return {
                'metro': {'name': 'Metro', 'description': 'Metropolitan areas'},
                'state': {'name': 'State', 'description': 'US states'},
                'county': {'name': 'County', 'description': 'Counties'},
                'city': {'name': 'City', 'description': 'Cities'},
                'zip': {'name': 'ZIP Code', 'description': 'ZIP codes'},
                'neighborhood': {'name': 'Neighborhood', 'description': 'Neighborhoods'}
            }
        else:
            raise ValueError(f"Unknown data source: {data_source}")
    
    # Phase 3: Cross-Source Standardization and Schema Registry
    def standardize_columns(self, source_columns: List[str], data_source: str) -> Dict[str, str]:
        """
        Standardize column names across different data sources.
        
        Args:
            source_columns: List of column names from the data source
            data_source: Name of the data source
            
        Returns:
            Dictionary mapping source columns to standardized names
        """
        # Standard column mappings for different sources
        column_mappings = {
            'zillow': {
                'RegionID': 'region_id',
                'RegionName': 'region_name', 
                'StateName': 'state_name',
                'Metro': 'metro_name',
                'CountyName': 'county_name',
                'CityName': 'city_name',
                'NeighborhoodName': 'neighborhood_name',
                'SizeRank': 'size_rank'
            }
        }
        
        mapping = column_mappings.get(data_source, {})
        standardized = {}
        
        for col in source_columns:
            # Use mapping if available, otherwise keep original
            standardized[col] = mapping.get(col, col.lower().replace(' ', '_'))
        
        logger.info(f"📋 Standardized {len(standardized)} columns for {data_source}")
        return standardized
    
    def get_schema_registry(self, data_source: str) -> Dict[str, Any]:
        """
        Get schema registry information for a data source.
        
        Args:
            data_source: Name of the data source
            
        Returns:
            Dictionary containing schema information
        """
        schemas = {
            'zillow': {
                'name': 'Zillow Real Estate Data',
                'version': '1.0',
                'description': 'Zillow home value and rental data',
                'supported_data_types': ['zhvi', 'zori'],
                'supported_geographies': ['metro', 'state', 'county', 'city', 'zip', 'neighborhood'],
                'column_standards': {
                    'region_id': {'type': 'integer', 'required': True, 'description': 'Unique region identifier'},
                    'region_name': {'type': 'string', 'required': True, 'description': 'Human-readable region name'},
                    'state_name': {'type': 'string', 'required': True, 'description': 'State name'},
                    'size_rank': {'type': 'integer', 'required': True, 'description': 'Size ranking within geography'},
                    'metro_name': {'type': 'string', 'required': False, 'description': 'Metropolitan area name'},
                    'county_name': {'type': 'string', 'required': False, 'description': 'County name'},
                    'city_name': {'type': 'string', 'required': False, 'description': 'City name'},
                    'neighborhood_name': {'type': 'string', 'required': False, 'description': 'Neighborhood name'}
                },
                'date_column_pattern': r'^\d{4}-\d{2}-\d{2}$',
                'data_frequency': 'monthly',
                'last_updated': '2025-10-05'
            }
        }
        
        return schemas.get(data_source, {})
    
    def validate_schema_compliance(self, data_source: str, data_type: str, sub_type: str, geography: str, sample_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that sample data complies with the expected schema.
        
        Args:
            data_source: Data source name
            data_type: Type of data
            sub_type: Sub-type of data
            geography: Geographic level
            sample_data: Sample DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        schema = self.get_schema_registry(data_source)
        if not schema:
            return {'valid': False, 'error': f'No schema found for {data_source}'}
        
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'compliance_score': 0.0,
            'missing_required': [],
            'extra_columns': [],
            'type_mismatches': []
        }
        
        # Check required columns
        required_columns = [col for col, info in schema['column_standards'].items() if info.get('required', False)]
        standardized_mapping = self.standardize_columns(list(sample_data.columns), data_source)
        
        # Check for missing required columns
        for req_col in required_columns:
            if req_col not in standardized_mapping.values():
                validation_results['missing_required'].append(req_col)
                validation_results['errors'].append(f'Missing required column: {req_col}')
        
        # Check for extra columns
        expected_columns = set(schema['column_standards'].keys())
        actual_columns = set(standardized_mapping.values())
        validation_results['extra_columns'] = list(actual_columns - expected_columns)
        
        # Calculate compliance score
        total_checks = len(required_columns) + len(validation_results['extra_columns'])
        passed_checks = len(required_columns) - len(validation_results['missing_required'])
        validation_results['compliance_score'] = passed_checks / total_checks if total_checks > 0 else 1.0
        
        # Overall validation
        validation_results['valid'] = len(validation_results['errors']) == 0
        
        logger.info(f"🔍 Schema validation for {data_source}-{data_type}-{geography}: {validation_results['compliance_score']:.2f} compliance")
        return validation_results
    
    def get_all_available_combinations(self) -> List[Tuple[str, str, str, str]]:
        """
        Get all available data source, data type, sub-type, and geography combinations.
        
        Returns:
            List[Tuple[str, str, str, str]]: List of (data_source, data_type, sub_type, geography) tuples
        """
        combinations = []
        # Add Zillow combinations
        zillow_combinations = self.zillow.get_all_available_combinations()
        for data_type, sub_type, geography in zillow_combinations:
            combinations.append(('zillow', data_type, sub_type, geography))
        
        # Future: Add other data source combinations
        return combinations
    
    def validate_geography_data_type(self, data_source: str, data_type: str, sub_type: str, geography: str) -> bool:
        """
        Validate if a data source, data type, sub-type, and geography combination is supported.
        
        Args:
            data_source (str): Data source
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            bool: True if combination is valid
        """
        if data_source == 'zillow':
            return self.zillow.validate_geography_data_type(data_type, sub_type, geography)
        else:
            return False
    
    def check_connection_health(self, data_source: str, data_type: str, sub_type: str, geography: str) -> Dict[str, Any]:
        """
        Check the health of connection methods for a specific data source, data type, sub-type, and geography.
        
        Args:
            data_source (str): Data source
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            Dict[str, Any]: Health status information
        """
        if data_source == 'zillow':
            return self.zillow.check_connection_health(data_type, sub_type, geography)
        else:
            return {
                'overall_status': 'unknown',
                'methods': [],
                'last_checked': None,
                'notes': f'Unknown data source: {data_source}'
            }

class ZillowDataConnection(BaseDataConnection):
    """
    Zillow-specific data connection management.
    
    This class encapsulates all Zillow data source information, including
    metadata, connection methods, and fallback procedures.
    """
    
    def __init__(self):
        """Initialize Zillow data connection."""
        super().__init__("Zillow")
        
        # Geography-specific critical columns (from our analysis)
        self.geography_critical_columns = {
            'metro': ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank'],
            'state': ['RegionID', 'RegionName', 'StateName', 'SizeRank'],
            'county': ['RegionID', 'RegionName', 'StateName', 'CountyName', 'SizeRank'],
            'city': ['RegionID', 'RegionName', 'StateName', 'CityName', 'SizeRank'],
            'zip': ['RegionID', 'RegionName', 'StateName', 'SizeRank'],
            'neighborhood': ['RegionID', 'RegionName', 'StateName', 'NeighborhoodName', 'CityName', 'SizeRank']
        }
        
        # Data type information (from our analysis)
        self.data_types = {
            'zhvi': {
                'full_name': 'Zillow Home Value Index',
                'description': 'Median home value estimates',
                'unit': 'USD',
                'frequency': 'Monthly',
                'date_range': '2000-01-01 to present',
                'typical_date_columns': 300,
                'sub_types': {
                    'all_homes_smoothed_seasonally_adjusted': {
                        'full_name': 'ZHVI All Homes (SFR, Condo/Co-op) Time Series, Smoothed, Seasonally Adjusted',
                        'description': 'Typical home value for homes in the 35th to 65th percentile range, smoothed and seasonally adjusted',
                        'unit': 'USD',
                        'frequency': 'Monthly',
                        'date_range': '2000-01-01 to present',
                        'typical_date_columns': 300
                    },
                    'all_homes_raw_mid_tier': {
                        'full_name': 'ZHVI All Homes (SFR, Condo/Co-op) Time Series, Raw, Mid-Tier',
                        'description': 'Typical home value for homes in the 35th to 65th percentile range, raw data',
                        'unit': 'USD',
                        'frequency': 'Monthly',
                        'date_range': '2000-01-01 to present',
                        'typical_date_columns': 300
                    },
                    'all_homes_top_tier': {
                        'full_name': 'ZHVI All Homes - Top Tier Time Series',
                        'description': 'Typical home value for homes in the 65th to 95th percentile range',
                        'unit': 'USD',
                        'frequency': 'Monthly',
                        'date_range': '2000-01-01 to present',
                        'typical_date_columns': 300
                    },
                    'all_homes_bottom_tier': {
                        'full_name': 'ZHVI All Homes - Bottom Tier Time Series',
                        'description': 'Typical home value for homes in the 5th to 35th percentile range',
                        'unit': 'USD',
                        'frequency': 'Monthly',
                        'date_range': '2000-01-01 to present',
                        'typical_date_columns': 300
                    },
                    'single_family_homes': {
                        'full_name': 'ZHVI Single-Family Homes Time Series',
                        'description': 'Typical home value for single-family homes',
                        'unit': 'USD',
                        'frequency': 'Monthly',
                        'date_range': '2000-01-01 to present',
                        'typical_date_columns': 300
                    },
                    'condo_coop': {
                        'full_name': 'ZHVI Condo/Co-op Time Series',
                        'description': 'Typical home value for condominiums and co-operatives',
                        'unit': 'USD',
                        'frequency': 'Monthly',
                        'date_range': '2000-01-01 to present',
                        'typical_date_columns': 300
                    }
                }
            },
            'zori': {
                'full_name': 'Zillow Rent Index',
                'description': 'Median rental price estimates',
                'unit': 'USD per month',
                'frequency': 'Monthly',
                'date_range': '2014-01-01 to present',
                'typical_date_columns': 120,
                'sub_types': {
                    'all_homes': {
                        'full_name': 'ZORI All Homes',
                        'description': 'Rental price index for all homes',
                        'unit': 'USD per month',
                        'frequency': 'Monthly',
                        'date_range': '2014-01-01 to present',
                        'typical_date_columns': 120
                    }
                }
            }
        }
        
        # Geography level information (from our analysis)
        self.geography_levels = {
            'metro': {
                'description': 'Metropolitan Statistical Areas',
                'typical_rows': '300-400',
                'data_availability': 'ZHVI, ZORI, ZHVI_AllHomes, ZHVI_SingleFamilyResidential'
            },
            'state': {
                'description': 'State level data',
                'typical_rows': '50-60',
                'data_availability': 'ZHVI, ZORI, ZHVI_AllHomes, ZHVI_SingleFamilyResidential'
            },
            'county': {
                'description': 'County level data',
                'typical_rows': '3000-4000',
                'data_availability': 'ZHVI, ZORI, ZHVI_AllHomes, ZHVI_SingleFamilyResidential'
            },
            'city': {
                'description': 'City level data',
                'typical_rows': '10000-15000',
                'data_availability': 'ZHVI, ZORI, ZHVI_AllHomes, ZHVI_SingleFamilyResidential'
            },
            'zip': {
                'description': 'ZIP code level data',
                'typical_rows': '30000-40000',
                'data_availability': 'ZHVI, ZORI, ZHVI_AllHomes, ZHVI_SingleFamilyResidential'
            },
            'neighborhood': {
                'description': 'Neighborhood level data',
                'typical_rows': '50000-100000',
                'data_availability': 'ZHVI, ZORI, ZHVI_AllHomes, ZHVI_SingleFamilyResidential'
            }
        }
        
        # Connection methods (current and historical)
        self.connection_methods = {
            'zhvi': {
                'all_homes_smoothed_seasonally_adjusted': {
                    'metro': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'state': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'county': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'city': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'zip': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'neighborhood': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}]
                },
                'all_homes_raw_mid_tier': {
                    'metro': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'state': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'county': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'city': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'zip': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'neighborhood': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}]
                },
                'all_homes_top_tier': {
                    'metro': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'state': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'county': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'city': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'zip': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'neighborhood': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}]
                },
                'all_homes_bottom_tier': {
                    'metro': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'state': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'county': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'city': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'zip': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'neighborhood': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}]
                },
                'single_family_homes': {
                    'metro': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'state': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'county': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'city': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'zip': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'neighborhood': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}]
                },
                'condo_coop': {
                    'metro': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'state': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'county': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'city': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'zip': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}],
                    'neighborhood': [{'type': 'csv_download', 'method': 'zillow_csv_direct', 'description': 'Direct CSV download from Zillow research data portal', 'priority': 1, 'notes': 'Most reliable method - data updated monthly on 16th', 'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/', 'status': 'healthy'}]
                }
            },
            'zori': {
                'all_homes': {
                    'zip': [
                        {
                            'type': 'csv_download',
                            'method': 'zillow_csv_direct',
                            'description': 'Direct CSV download from Zillow research data portal',
                            'priority': 1,
                            'notes': 'Most reliable method - data updated monthly on 16th',
                            'base_url': 'https://files.zillowstatic.com/research/public_csvs/zori/',
                            'status': 'healthy'
                        }
                    ]
                }
            }
        }
        
        # Fallback procedures
        self.fallback_procedures = {
            'zhvi': {
                'all_homes_smoothed_seasonally_adjusted': {
                    'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
                },
                'all_homes_raw_mid_tier': {
                    'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
                },
                'all_homes_top_tier': {
                    'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
                },
                'all_homes_bottom_tier': {
                    'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
                },
                'single_family_homes': {
                    'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
                },
                'condo_coop': {
                    'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                    'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_sub_type', 'description': 'Switch to alternative ZHVI sub-type', 'priority': 2, 'notes': 'Use different ZHVI sub-type (raw vs smoothed, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
                }
            },
            'zhvi_all_homes_smoothed_seasonally_adjusted': {
                'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
            },
            'zhvi_all_homes_raw_mid_tier': {
                'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
            },
            'zhvi_all_homes_top_tier': {
                'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
            },
            'zhvi_all_homes_bottom_tier': {
                'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
            },
            'zhvi_single_family_homes': {
                'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
            },
            'zhvi_condo_coop': {
                'metro': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'state': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'county': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'city': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'zip': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}],
                'neighborhood': [{'type': 'cached_data', 'description': 'Use last known good data from master copy', 'priority': 1, 'notes': 'Continue with existing data until connection restored'}, {'type': 'alternative_variant', 'description': 'Switch to alternative ZHVI variant', 'priority': 2, 'notes': 'Use different ZHVI variant (smoothed vs raw, different tiers)'}, {'type': 'alternative_source', 'description': 'Switch to alternative Zillow data provider', 'priority': 3, 'notes': 'Redfin, CoreLogic, or other Zillow data sources'}, {'type': 'manual_download', 'description': 'Manual data download and upload', 'priority': 4, 'notes': 'Human intervention required'}]
            },
            'zori': {
                'all_homes': {
                    'zip': [
                        {
                            'type': 'cached_data',
                            'description': 'Use last known good data from master copy',
                            'priority': 1,
                            'notes': 'Continue with existing data until connection restored'
                        },
                        {
                            'type': 'alternative_source',
                            'description': 'Switch to alternative rental data provider',
                            'priority': 2,
                            'notes': 'Apartment List, RentSpree, or other rental data sources'
                        }
                    ]
                }
            }
        }
    
    def get_metadata(self, data_type: str, sub_type: str, geography: str) -> DataSourceMetadata:
        """
        Get metadata for a specific Zillow data type, sub-type, and geography.
        
        Args:
            data_type (str): Type of data (e.g., 'zhvi', 'zori')
            sub_type (str): Sub-type of data (e.g., 'all_homes_smoothed_seasonally_adjusted')
            geography (str): Geography level (e.g., 'zip', 'metro')
            
        Returns:
            DataSourceMetadata: Metadata for the requested combination
        """
        if data_type not in self.data_types:
            raise ValueError(f"Unknown data type: {data_type}")
        
        if sub_type not in self.data_types[data_type].get('sub_types', {}):
            raise ValueError(f"Unknown sub-type: {sub_type} for data type: {data_type}")
        
        if geography not in self.geography_levels:
            raise ValueError(f"Unknown geography: {geography}")
        
        # Get critical columns for this geography
        critical_columns = self.geography_critical_columns.get(geography, [])
        
        # Generate expected columns (critical + date columns)
        expected_columns = critical_columns.copy()
        # Date columns would be added dynamically based on actual data
        
        # Get connection methods
        connection_methods = self.get_connection_methods(data_type, sub_type, geography)
        
        # Get fallback procedures
        fallback_procedures = self.get_fallback_procedures(data_type, sub_type, geography)
        
        # Get sub-type specific info
        sub_type_info = self.data_types[data_type]['sub_types'][sub_type]
        
        return DataSourceMetadata(
            source_name=self.source_name,
            data_type=f"{data_type}_{sub_type}",
            geography=geography,
            critical_columns=critical_columns,
            expected_columns=expected_columns,
            date_columns=[],  # Will be populated dynamically
            typical_row_count=self.geography_levels[geography]['typical_rows'],
            data_availability=self.geography_levels[geography]['data_availability'],
            unit=sub_type_info.get('unit', self.data_types[data_type]['unit']),
            frequency=sub_type_info.get('frequency', self.data_types[data_type]['frequency']),
            date_range=sub_type_info.get('date_range', self.data_types[data_type]['date_range']),
            connection_methods=connection_methods,
            fallback_procedures=fallback_procedures
        )
    
    def get_connection_methods(self, data_type: str, sub_type: str, geography: str) -> List[Dict[str, Any]]:
        """
        Get available connection methods for a Zillow data type, sub-type, and geography.
        
        Args:
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            List[Dict]: List of connection methods with their details
        """
        return self.connection_methods.get(data_type, {}).get(sub_type, {}).get(geography, [])
    
    def get_fallback_procedures(self, data_type: str, sub_type: str, geography: str) -> List[Dict[str, Any]]:
        """
        Get fallback procedures when primary Zillow connection fails.
        
        Args:
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            List[Dict]: List of fallback procedures
        """
        return self.fallback_procedures.get(data_type, {}).get(sub_type, {}).get(geography, [])
    
    def get_critical_columns(self, geography: str) -> List[str]:
        """
        Get critical columns for a specific geography level.
        
        Args:
            geography (str): Geography level
            
        Returns:
            List[str]: List of critical columns
        """
        return self.geography_critical_columns.get(geography, [])
    
    def validate_geography_data_type(self, data_type: str, sub_type: str, geography: str) -> bool:
        """
        Validate if a data type, sub-type, and geography combination is supported.
        
        Args:
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            bool: True if combination is valid
        """
        return (data_type in self.data_types and 
                sub_type in self.data_types[data_type].get('sub_types', {}) and
                geography in self.geography_levels and
                data_type in self.connection_methods and
                sub_type in self.connection_methods[data_type] and
                geography in self.connection_methods[data_type][sub_type])
    
    def get_all_available_combinations(self) -> List[Tuple[str, str, str]]:
        """
        Get all available data type, sub-type, and geography combinations.
        
        Returns:
            List[Tuple[str, str, str]]: List of (data_type, sub_type, geography) tuples
        """
        combinations = []
        for data_type in self.connection_methods:
            for sub_type in self.connection_methods[data_type]:
                for geography in self.connection_methods[data_type][sub_type]:
                    combinations.append((data_type, sub_type, geography))
        return combinations
    
    def get_download_url(self, data_type: str, sub_type: str, geography: str) -> str:
        """
        Get the download URL for a specific data type, sub-type, and geography combination.
        
        Args:
            data_type (str): Type of data
            sub_type (str): Sub-type of data
            geography (str): Geography level
            
        Returns:
            str: Download URL for the requested combination
        """
        # ZHVI URL patterns for different sub-types and geographies
        zhvi_url_patterns = {
            'all_homes_smoothed_seasonally_adjusted': {
                'metro': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                'state': 'https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                'county': 'https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                'city': 'https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                'zip': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                'neighborhood': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Neighborhood_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'
            },
            'all_homes_raw_mid_tier': {
                'metro': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv',
                'state': 'https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv',
                'county': 'https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv',
                'city': 'https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv',
                'zip': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv',
                'neighborhood': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Neighborhood_zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv'
            },
            'all_homes_top_tier': {
                'metro': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv',
                'state': 'https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv',
                'county': 'https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv',
                'city': 'https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv',
                'zip': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv',
                'neighborhood': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Neighborhood_zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv'
            },
            'all_homes_bottom_tier': {
                'metro': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv',
                'state': 'https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv',
                'county': 'https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv',
                'city': 'https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv',
                'zip': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv',
                'neighborhood': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Neighborhood_zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv'
            },
            'single_family_homes': {
                'metro': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv',
                'state': 'https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv',
                'county': 'https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv',
                'city': 'https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv',
                'zip': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv',
                'neighborhood': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Neighborhood_zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv'
            },
            'condo_coop': {
                'metro': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv',
                'state': 'https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv',
                'county': 'https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv',
                'city': 'https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv',
                'zip': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv',
                'neighborhood': 'https://files.zillowstatic.com/research/public_csvs/zhvi/Neighborhood_zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv'
            }
        }
        
        if data_type == 'zhvi' and sub_type in zhvi_url_patterns and geography in zhvi_url_patterns[sub_type]:
            return zhvi_url_patterns[sub_type][geography]
        elif data_type == 'zori' and sub_type == 'all_homes' and geography == 'zip':
            return 'https://files.zillowstatic.com/research/public_csvs/zori/Zip_ZORI_AllHomesPlusMultifamily.csv'
        else:
            raise ValueError(f"No download URL available for {data_type}-{sub_type}-{geography}")
    
    # Phase 1: Data Source Introspection Implementation
    def discover_columns(self, data_type: str, sub_type: str, geography: str, sample_size: int = 100) -> DiscoveryResult:
        """
        Discover required columns by analyzing sample data from Zillow.
        
        Args:
            data_type: Type of data (e.g., 'zhvi', 'zori')
            sub_type: Sub-type of data (e.g., 'all_homes_smoothed_seasonally_adjusted')
            geography: Geographic level (e.g., 'zip', 'metro')
            sample_size: Number of rows to sample for analysis
            
        Returns:
            DiscoveryResult with discovered column information
        """
        try:
            logger.info(f"🔍 Discovering columns for {data_type}-{sub_type}-{geography}")
            
            # Get download URL
            download_url = self.get_download_url(data_type, sub_type, geography)
            
            # Download sample data
            sample_data = self._download_sample_data(download_url, sample_size)
            
            if sample_data.empty:
                return DiscoveryResult(
                    success=False,
                    discovered_columns=[],
                    critical_columns=[],
                    date_columns=[],
                    error_message="No data available for analysis"
                )
            
            # Analyze the sample data
            critical_columns, date_columns, confidence_score = self._analyze_required_columns(
                sample_data, data_type, geography
            )
            
            # All columns in the sample
            discovered_columns = list(sample_data.columns)
            
            logger.info(f"✅ Discovered {len(discovered_columns)} columns with {confidence_score:.2f} confidence")
            
            return DiscoveryResult(
                success=True,
                discovered_columns=discovered_columns,
                critical_columns=critical_columns,
                date_columns=date_columns,
                sample_data=sample_data,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"❌ Column discovery failed: {str(e)}")
            return DiscoveryResult(
                success=False,
                discovered_columns=[],
                critical_columns=[],
                date_columns=[],
                error_message=str(e)
            )
    
    def discover_geographic_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available geographic levels and their relationships for Zillow data.
        
        Returns:
            Dictionary mapping geography levels to their metadata
        """
        hierarchy = {
            'region': {
                'name': 'Region',
                'description': 'Major US regions (Northeast, Southeast, etc.)',
                'parent_level': None,
                'child_levels': ['state_region'],
                'typical_count': 5,
                'data_available': True
            },
            'state_region': {
                'name': 'State Region',
                'description': 'Logical state groupings (New England, Mid-Atlantic, etc.)',
                'parent_level': 'region',
                'child_levels': ['state'],
                'typical_count': 9,
                'data_available': True
            },
            'state': {
                'name': 'State',
                'description': 'Individual US states',
                'parent_level': 'state_region',
                'child_levels': ['county', 'city'],
                'typical_count': 50,
                'data_available': True
            },
            'county': {
                'name': 'County',
                'description': 'Counties within states',
                'parent_level': 'state',
                'child_levels': ['city', 'zip'],
                'typical_count': 3000,
                'data_available': True
            },
            'city': {
                'name': 'City',
                'description': 'Cities within counties',
                'parent_level': 'county',
                'child_levels': ['zip', 'neighborhood'],
                'typical_count': 10000,
                'data_available': True
            },
            'zip': {
                'name': 'ZIP Code',
                'description': 'Individual ZIP codes',
                'parent_level': 'city',
                'child_levels': ['neighborhood'],
                'typical_count': 40000,
                'data_available': True
            },
            'neighborhood': {
                'name': 'Neighborhood',
                'description': 'Neighborhoods within cities',
                'parent_level': 'city',
                'child_levels': [],
                'typical_count': 100000,
                'data_available': True
            }
        }
        
        logger.info(f"🗺️ Discovered geographic hierarchy with {len(hierarchy)} levels")
        return hierarchy
    
    def _download_sample_data(self, url: str, sample_size: int) -> pd.DataFrame:
        """
        Download sample data from Zillow URL.
        
        Args:
            url: Download URL
            sample_size: Number of rows to sample
            
        Returns:
            Sample DataFrame
        """
        try:
            logger.info(f"📥 Downloading sample data from {url}")
            
            # Download the CSV
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            
            # Read CSV into DataFrame
            df = pd.read_csv(io.StringIO(response.text))
            
            # Sample the data
            if len(df) > sample_size:
                df = df.sample(n=sample_size, random_state=42)
            
            logger.info(f"✅ Downloaded {len(df)} rows with {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to download sample data: {str(e)}")
            return pd.DataFrame()

# Example usage and testing
if __name__ == "__main__":
    # Initialize RE connection (top level)
    re_connection = REDataConnection()
    
    print("=== RE Data Connection Test ===")
    
    # Test metadata retrieval for ZHVI All Homes Smoothed Seasonally Adjusted ZIP
    try:
        metadata = re_connection.get_metadata('zillow', 'zhvi', 'all_homes_smoothed_seasonally_adjusted', 'zip')
        print(f"\nZHVI All Homes Smoothed Seasonally Adjusted ZIP Metadata:")
        print(f"  Data type: {metadata.data_type}")
        print(f"  Geography: {metadata.geography}")
        print(f"  Critical columns: {metadata.critical_columns}")
        print(f"  Unit: {metadata.unit}")
        print(f"  Frequency: {metadata.frequency}")
        print(f"  Connection methods: {len(metadata.connection_methods)}")
        print(f"  Fallback procedures: {len(metadata.fallback_procedures)}")
    except Exception as e:
        print(f"Error getting metadata: {e}")
    
    # Test available combinations
    combinations = re_connection.get_all_available_combinations()
    print(f"\n=== Available Combinations ===")
    print(f"Total combinations: {len(combinations)}")
    for data_source, data_type, sub_type, geography in combinations[:5]:
        print(f"  {data_source} - {data_type} - {sub_type} - {geography}")
    
    # Test download URL
    try:
        url = re_connection.get_download_url('zillow', 'zhvi', 'all_homes_smoothed_seasonally_adjusted', 'zip')
        print(f"\n=== Download URL ===")
        print(f"URL: {url}")
    except Exception as e:
        print(f"Error getting download URL: {e}")
    
    print(f"\n=== Test Complete ===")

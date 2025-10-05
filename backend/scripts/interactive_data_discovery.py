#!/usr/bin/env python3
"""
Interactive Data Source Discovery Script

This script prompts the user for a description of their data source and automatically
discovers connection methods, analyzes the data structure, and generates a complete
DataConnection configuration.
"""

import os
import sys
import logging
import pandas as pd
import requests
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_connection import DataSourceMetadata, ZillowDataConnection

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'interactive_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InteractiveDataDiscovery:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Interactive Data Discovery initialized with config path: {self.config_path}")

    def _analyze_description(self, description: str) -> Dict[str, Any]:
        """
        Analyzes the user's description to extract key information about the data source.
        This simulates AI analysis of the description.
        """
        logger.info(f"🤖 Analyzing description: {description}")
        
        description_lower = description.lower()
        
        # Initialize analysis result
        analysis = {
            'source_name': 'Unknown',
            'data_types': [],
            'geographies': [],
            'connection_methods': [],
            'confidence': 0.0,
            'suggestions': []
        }
        
        # Extract source name
        if 'zillow' in description_lower:
            analysis['source_name'] = 'Zillow'
            analysis['confidence'] += 0.3
        elif 'redfin' in description_lower:
            analysis['source_name'] = 'Redfin'
            analysis['confidence'] += 0.3
        elif 'corelogic' in description_lower:
            analysis['source_name'] = 'CoreLogic'
            analysis['confidence'] += 0.3
        elif 'census' in description_lower:
            analysis['source_name'] = 'US Census'
            analysis['confidence'] += 0.3
        elif 'fred' in description_lower or 'federal reserve' in description_lower:
            analysis['source_name'] = 'Federal Reserve'
            analysis['confidence'] += 0.3
        
        # Extract data types
        if 'home value' in description_lower or 'zhvi' in description_lower:
            # For ZHVI, we'll discover all available variants
            analysis['data_types'].append('zhvi_discover_variants')
            analysis['confidence'] += 0.2
        if 'rent' in description_lower or 'zori' in description_lower:
            analysis['data_types'].append('zori')
            analysis['confidence'] += 0.2
        if 'sales' in description_lower:
            analysis['data_types'].append('sales')
            analysis['confidence'] += 0.1
        if 'inventory' in description_lower:
            analysis['data_types'].append('inventory')
            analysis['confidence'] += 0.1
        
        # Extract geographies
        if 'zip' in description_lower or 'zipcode' in description_lower:
            analysis['geographies'].append('zip')
            analysis['confidence'] += 0.1
        if 'metro' in description_lower or 'metropolitan' in description_lower:
            analysis['geographies'].append('metro')
            analysis['confidence'] += 0.1
        if 'state' in description_lower:
            analysis['geographies'].append('state')
            analysis['confidence'] += 0.1
        if 'county' in description_lower:
            analysis['geographies'].append('county')
            analysis['confidence'] += 0.1
        if 'city' in description_lower:
            analysis['geographies'].append('city')
            analysis['confidence'] += 0.1
        if 'neighborhood' in description_lower:
            analysis['geographies'].append('neighborhood')
            analysis['confidence'] += 0.1
        
        # If no geographies specified but it's Zillow ZHVI, include all available geographies
        if analysis['source_name'] == 'Zillow' and 'zhvi' in description_lower and not analysis['geographies']:
            analysis['geographies'] = ['metro', 'state', 'county', 'city', 'zip', 'neighborhood']
            analysis['confidence'] += 0.2
        
        # Generate connection method suggestions
        if analysis['source_name'] == 'Zillow':
            analysis['connection_methods'] = [
                {
                    'type': 'csv_download',
                    'method': 'zillow_csv_direct',
                    'description': 'Direct CSV download from Zillow research data portal',
                    'priority': 1,
                    'notes': 'Most reliable method - data updated monthly on 16th',
                    'base_url': 'https://files.zillowstatic.com/research/public_csvs/zhvi/'
                },
                {
                    'type': 'web_scraping',
                    'method': 'zillow_web_scraping',
                    'description': 'Web scraping from Zillow research data page',
                    'priority': 2,
                    'notes': 'May violate terms of service - use with caution'
                },
                {
                    'type': 'api',
                    'method': 'zillow_api',
                    'description': 'Zillow API for real estate data',
                    'priority': 3,
                    'notes': 'Requires API key - may not have all research data'
                }
            ]
        elif analysis['source_name'] == 'Redfin':
            analysis['connection_methods'] = [
                {
                    'type': 'api',
                    'method': 'redfin_api',
                    'description': 'Redfin API for real estate data',
                    'priority': 1,
                    'notes': 'Requires API key'
                },
                {
                    'type': 'web_scraping',
                    'method': 'redfin_web_scraping',
                    'description': 'Web scraping from Redfin website',
                    'priority': 2,
                    'notes': 'May violate terms of service'
                }
            ]
        else:
            # Generic connection methods
            analysis['connection_methods'] = [
                {
                    'type': 'url',
                    'method': 'direct_download',
                    'description': 'Direct download from URL',
                    'priority': 1,
                    'notes': 'Most common method'
                },
                {
                    'type': 'api',
                    'method': 'api_endpoint',
                    'description': 'API endpoint connection',
                    'priority': 2,
                    'notes': 'Requires API key'
                },
                {
                    'type': 'web_scraping',
                    'method': 'web_scraping',
                    'description': 'Web scraping approach',
                    'priority': 3,
                    'notes': 'May violate terms of service'
                }
            ]
        
        # Generate suggestions
        if analysis['confidence'] < 0.5:
            analysis['suggestions'].append("Consider providing more specific details about the data source")
        if not analysis['data_types']:
            analysis['suggestions'].append("Specify what type of data you're looking for (home values, rents, sales, etc.)")
        if not analysis['geographies']:
            analysis['suggestions'].append("Specify the geographic level (ZIP, metro, state, county, city, neighborhood)")
        
        return analysis

    def _discover_zhvi_variants(self) -> Dict[str, Dict[str, str]]:
        """
        Discover all available ZHVI variants by testing different URL patterns.
        """
        logger.info("🔍 Discovering ZHVI variants...")
        
        # Base URL patterns for different ZHVI variants
        variants = {
            'zhvi_all_homes_smoothed_seasonally_adjusted': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                'description': 'ZHVI All Homes (SFR, Condo/Co-op) Time Series, Smoothed, Seasonally Adjusted ($)'
            },
            'zhvi_all_homes_raw_mid_tier': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv',
                'description': 'ZHVI All Homes (SFR, Condo/Co-op) Time Series, Raw, Mid-Tier ($)'
            },
            'zhvi_all_homes_top_tier': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.67_1.0_sm_sa_month.csv',
                'description': 'ZHVI All Homes - Top Tier Time Series ($)'
            },
            'zhvi_all_homes_bottom_tier': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.0_0.33_sm_sa_month.csv',
                'description': 'ZHVI All Homes - Bottom Tier Time Series ($)'
            },
            'zhvi_single_family_homes': {
                'pattern': 'zhvi_uc_sfr_tier_0.33_0.67_sm_sa_month.csv',
                'description': 'ZHVI Single-Family Homes Time Series ($)'
            },
            'zhvi_condo_coop': {
                'pattern': 'zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv',
                'description': 'ZHVI Condo/Co-op Time Series ($)'
            },
            'zhvi_1_bedroom': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month_1bedroom.csv',
                'description': 'ZHVI 1-Bedroom Time Series ($)'
            },
            'zhvi_2_bedroom': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month_2bedroom.csv',
                'description': 'ZHVI 2-Bedroom Time Series ($)'
            },
            'zhvi_3_bedroom': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month_3bedroom.csv',
                'description': 'ZHVI 3-Bedroom Time Series ($)'
            },
            'zhvi_4_bedroom': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month_4bedroom.csv',
                'description': 'ZHVI 4-Bedroom Time Series ($)'
            },
            'zhvi_5_plus_bedroom': {
                'pattern': 'zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month_5bedroom.csv',
                'description': 'ZHVI 5+ Bedroom Time Series ($)'
            }
        }
        
        # Geography prefixes
        geography_prefixes = {
            'metro': 'Metro_',
            'state': 'State_',
            'county': 'County_',
            'city': 'City_',
            'zip': 'Zip_',
            'neighborhood': 'Neighborhood_'
        }
        
        discovered_variants = {}
        
        for variant_name, variant_info in variants.items():
            discovered_variants[variant_name] = {
                'description': variant_info['description'],
                'geographies': {}
            }
            
            for geography, prefix in geography_prefixes.items():
                url = f"https://files.zillowstatic.com/research/public_csvs/zhvi/{prefix}{variant_info['pattern']}"
                
                try:
                    response = requests.head(url, timeout=10)
                    if response.status_code == 200:
                        discovered_variants[variant_name]['geographies'][geography] = url
                        logger.info(f"✅ Found {variant_name} for {geography}: {url}")
                    else:
                        logger.debug(f"❌ {variant_name} for {geography} not available: {response.status_code}")
                except Exception as e:
                    logger.debug(f"❌ {variant_name} for {geography} failed: {str(e)}")
        
        # Filter out variants with no available geographies
        available_variants = {k: v for k, v in discovered_variants.items() if v['geographies']}
        
        logger.info(f"📊 Discovered {len(available_variants)} ZHVI variants with available data")
        return available_variants

    def _test_connection_methods(self, methods: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
        """
        Tests the identified connection methods to determine their health.
        """
        logger.info("🔗 Testing connection methods...")
        
        working_methods = []
        
        for method in methods:
            try:
                if method['type'] == 'api':
                    # For now, mark API methods as unknown (would need API keys to test)
                    method['status'] = 'unknown'
                    method['notes'] += ' (API key required for testing)'
                    working_methods.append(method)
                    logger.info(f"❓ Method {method['method']} status unknown (API key required)")
                    
                elif method['type'] == 'web_scraping':
                    # For now, mark web scraping as unknown (would need to test specific URLs)
                    method['status'] = 'unknown'
                    method['notes'] += ' (URL required for testing)'
                    working_methods.append(method)
                    logger.info(f"❓ Method {method['method']} status unknown (URL required)")
                    
                elif method['type'] == 'csv_download':
                    # Test Zillow CSV URLs based on the research data page
                    if source_name == 'Zillow':
                        # ZHVI All Homes Time Series, Smoothed, Seasonally Adjusted URLs
                        test_urls = [
                            'https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                            'https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                            'https://files.zillowstatic.com/research/public_csvs/zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                            'https://files.zillowstatic.com/research/public_csvs/zhvi/City_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                            'https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv',
                            'https://files.zillowstatic.com/research/public_csvs/zhvi/Neighborhood_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'
                        ]
                        
                        working_urls = []
                        for url in test_urls:
                            try:
                                response = requests.head(url, timeout=10)
                                if response.status_code == 200:
                                    working_urls.append(url)
                                    logger.info(f"✅ URL accessible: {url}")
                                else:
                                    logger.warning(f"⚠️  URL returned {response.status_code}: {url}")
                            except Exception as e:
                                logger.warning(f"⚠️  URL failed: {url} - {str(e)}")
                        
                        if working_urls:
                            method['status'] = 'healthy'
                            method['working_urls'] = working_urls
                            method['total_tested'] = len(test_urls)
                            method['working_count'] = len(working_urls)
                            working_methods.append(method)
                            logger.info(f"✅ Method {method['method']} is working ({len(working_urls)}/{len(test_urls)} URLs accessible)")
                        else:
                            method['status'] = 'unhealthy'
                            method['error'] = 'All test URLs failed'
                            method['total_tested'] = len(test_urls)
                            method['working_count'] = 0
                            logger.warning(f"⚠️  Method {method['method']} failed: All {len(test_urls)} test URLs failed")
                    else:
                        method['status'] = 'unknown'
                        method['notes'] += ' (URL required for testing)'
                        working_methods.append(method)
                        logger.info(f"❓ Method {method['method']} status unknown (URL required)")
                        
                else:
                    method['status'] = 'unknown'
                    working_methods.append(method)
                    logger.info(f"❓ Method {method['method']} status unknown")
                    
            except Exception as e:
                method['status'] = 'unhealthy'
                method['error'] = str(e)
                logger.warning(f"⚠️  Method {method['method']} failed: {str(e)}")
        
        return working_methods

    def _generate_critical_columns(self, data_types: List[str], geographies: List[str], discovered_variants: Dict = None) -> Dict[str, List[str]]:
        """
        Generates critical columns based on data types and geographies.
        """
        logger.info("📊 Generating critical columns...")
        
        # Base critical columns
        base_columns = ['RegionID', 'RegionName', 'StateName']
        
        # Geography-specific columns
        geography_columns = {
            'metro': ['Metro'],
            'state': ['StateName'],
            'county': ['CountyName'],
            'city': ['CityName'],
            'zip': ['RegionName'],  # ZIP codes are in RegionName
            'neighborhood': ['NeighborhoodName']
        }
        
        # Data type specific columns
        data_type_columns = {
            'zori': ['SizeRank'],
            'sales': ['SizeRank'],
            'inventory': ['SizeRank']
        }
        
        # Add ZHVI variants if discovered
        if discovered_variants:
            for variant_name in discovered_variants.keys():
                data_type_columns[variant_name] = ['SizeRank']
        
        critical_columns = {}
        
        # Handle discovered variants
        if discovered_variants:
            for variant_name, variant_info in discovered_variants.items():
                for geography in variant_info['geographies'].keys():
                    key = f"{variant_name}-{geography}"
                    columns = base_columns.copy()
                    
                    # Add geography-specific columns
                    if geography in geography_columns:
                        columns.extend(geography_columns[geography])
                    
                    # Add data type specific columns
                    if variant_name in data_type_columns:
                        columns.extend(data_type_columns[variant_name])
                    
                    # Remove duplicates while preserving order
                    critical_columns[key] = list(dict.fromkeys(columns))
        else:
            # Handle regular data types
            for data_type in data_types:
                if data_type == 'zhvi_discover_variants':
                    continue  # Skip placeholder
                    
                for geography in geographies:
                    key = f"{data_type}-{geography}"
                    columns = base_columns.copy()
                    
                    # Add geography-specific columns
                    if geography in geography_columns:
                        columns.extend(geography_columns[geography])
                    
                    # Add data type specific columns
                    if data_type in data_type_columns:
                        columns.extend(data_type_columns[data_type])
                    
                    # Remove duplicates while preserving order
                    critical_columns[key] = list(dict.fromkeys(columns))
        
        return critical_columns

    def _generate_fallback_procedures(self, source_name: str, data_types: List[str], geographies: List[str], discovered_variants: Dict = None) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Generates fallback procedures for each data type and geography combination.
        """
        logger.info("🔄 Generating fallback procedures...")
        
        fallback_procedures = {}
        
        # Handle discovered variants
        if discovered_variants:
            for variant_name, variant_info in discovered_variants.items():
                fallback_procedures[variant_name] = {}
                
                for geography in variant_info['geographies'].keys():
                    fallback_procedures[variant_name][geography] = [
                        {
                            'type': 'cached_data',
                            'description': 'Use last known good data from master copy',
                            'priority': 1,
                            'notes': 'Continue with existing data until connection restored'
                        },
                        {
                            'type': 'alternative_variant',
                            'description': f'Switch to alternative ZHVI variant',
                            'priority': 2,
                            'notes': f'Use different ZHVI variant (smoothed vs raw, different tiers)'
                        },
                        {
                            'type': 'alternative_source',
                            'description': f'Switch to alternative {source_name} data provider',
                            'priority': 3,
                            'notes': f'Redfin, CoreLogic, or other {source_name} data sources'
                        },
                        {
                            'type': 'manual_download',
                            'description': 'Manual data download and upload',
                            'priority': 4,
                            'notes': 'Human intervention required'
                        }
                    ]
        else:
            # Handle regular data types
            for data_type in data_types:
                if data_type == 'zhvi_discover_variants':
                    continue  # Skip placeholder
                    
                fallback_procedures[data_type] = {}
                
                for geography in geographies:
                    fallback_procedures[data_type][geography] = [
                        {
                            'type': 'cached_data',
                            'description': 'Use last known good data from master copy',
                            'priority': 1,
                            'notes': 'Continue with existing data until connection restored'
                        },
                        {
                            'type': 'alternative_source',
                            'description': f'Switch to alternative {source_name} data provider',
                            'priority': 2,
                            'notes': f'Redfin, CoreLogic, or other {source_name} data sources'
                        },
                        {
                            'type': 'manual_download',
                            'description': 'Manual data download and upload',
                            'priority': 3,
                            'notes': 'Human intervention required'
                        }
                    ]
        
        return fallback_procedures

    def _create_data_connection_class(self, analysis: Dict[str, Any], critical_columns: Dict[str, List[str]], 
                                    fallback_procedures: Dict[str, Dict[str, List[Dict]]], discovered_variants: Dict = None) -> str:
        """
        Generates a complete DataConnection class based on the analysis.
        """
        logger.info("🏗️  Generating DataConnection class...")
        
        source_name = analysis['source_name']
        data_types = analysis['data_types']
        geographies = analysis['geographies']
        connection_methods = analysis['connection_methods']
        
        # Use discovered variants if available
        if discovered_variants:
            actual_data_types = list(discovered_variants.keys())
            actual_geographies = set()
            for variant_info in discovered_variants.values():
                actual_geographies.update(variant_info['geographies'].keys())
            actual_geographies = list(actual_geographies)
        else:
            actual_data_types = [dt for dt in data_types if dt != 'zhvi_discover_variants']
            actual_geographies = geographies
        
        # Generate class name
        class_name = f"{source_name.replace(' ', '')}DataConnection"
        
        # Generate the class code
        class_code = f'''"""
Auto-generated DataConnection class for {source_name}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Based on: https://www.zillow.com/research/data/
"""

from data_connection import BaseDataConnection, DataSourceMetadata
from typing import Dict, List, Any

class {class_name}(BaseDataConnection):
    def __init__(self):
        super().__init__("{source_name}")
        
        # Data types available
        self.data_types = {actual_data_types}
        
        # Geographies available
        self.geographies = {actual_geographies}
        
        # Critical columns for each data type and geography combination
        self.geography_critical_columns = {critical_columns}
        
        # Connection methods
        self.connection_methods = {connection_methods}
        
        # Fallback procedures
        self.fallback_procedures = {fallback_procedures}
        
        # ZHVI URL patterns for different variants and geographies
        self.zhvi_url_patterns = {discovered_variants if discovered_variants else {}}
    
    def get_metadata(self, data_type: str, geography: str) -> DataSourceMetadata:
        """Get metadata for a specific data type and geography combination."""
        key = f"{{data_type}}-{{geography}}"
        
        if key not in self.geography_critical_columns:
            raise ValueError(f"Unsupported combination: {{data_type}}-{{geography}}")
        
        return DataSourceMetadata(
            source_name=self.source_name,
            data_type=data_type,
            geography=geography,
            critical_columns=self.geography_critical_columns[key],
            connection_methods=self.connection_methods,
            fallback_procedures=self.fallback_procedures.get(data_type, {{}}).get(geography, [])
        )
    
    def check_connection_health(self, data_type: str, geography: str) -> Dict[str, Any]:
        """Check the health of connection methods for a specific data type and geography."""
        # This would implement actual health checks
        return {{
            'status': 'unknown',
            'methods': self.connection_methods,
            'last_checked': '{datetime.now().isoformat()}',
            'notes': 'Health check not implemented yet'
        }}
    
    def get_critical_columns(self, data_type: str, geography: str) -> List[str]:
        """Get critical columns for a specific data type and geography combination."""
        key = f"{{data_type}}-{{geography}}"
        return self.geography_critical_columns.get(key, [])
    
    def get_connection_methods(self, data_type: str, geography: str) -> List[Dict[str, Any]]:
        """Get connection methods for a specific data type and geography combination."""
        return self.connection_methods
    
    def get_download_url(self, data_type: str, geography: str) -> str:
        """Get the download URL for a specific data type and geography combination."""
        if data_type in self.zhvi_url_patterns and geography in self.zhvi_url_patterns[data_type]['geographies']:
            return self.zhvi_url_patterns[data_type]['geographies'][geography]
        else:
            raise ValueError(f"No download URL available for {{data_type}}-{{geography}}")
    
    def get_fallback_procedures(self, data_type: str, geography: str) -> List[Dict[str, Any]]:
        """Get fallback procedures for a specific data type and geography combination."""
        return self.fallback_procedures.get(data_type, {{}}).get(geography, [])
    
    def get_all_available_combinations(self) -> List[Tuple[str, str]]:
        """Get all available data type and geography combinations."""
        combinations = []
        for data_type in self.data_types:
            for geography in self.geographies:
                combinations.append((data_type, geography))
        return combinations
    
    def validate_geography_data_type(self, data_type: str, geography: str) -> bool:
        """Validate if a data type and geography combination is supported."""
        key = f"{{data_type}}-{{geography}}"
        return key in self.geography_critical_columns
'''
        
        return class_code

    def discover_and_configure(self, source_name: str, description: str) -> Dict[str, Any]:
        """
        Main method to discover and configure a new data source.
        """
        logger.info(f"🔍 Starting discovery for: {source_name}")
        logger.info(f"📝 Description: {description}")
        
        try:
            # Step 1: Analyze the description
            analysis = self._analyze_description(description)
            logger.info(f"📊 Analysis complete. Confidence: {analysis['confidence']:.2f}")
            
            # Step 2: Discover ZHVI variants if needed
            discovered_variants = None
            if 'zhvi_discover_variants' in analysis['data_types']:
                discovered_variants = self._discover_zhvi_variants()
                logger.info(f"🔍 Discovered {len(discovered_variants)} ZHVI variants")
            
            # Step 3: Test connection methods
            working_methods = self._test_connection_methods(analysis['connection_methods'], analysis['source_name'])
            analysis['connection_methods'] = working_methods
            
            # Step 4: Generate critical columns
            critical_columns = self._generate_critical_columns(analysis['data_types'], analysis['geographies'], discovered_variants)
            
            # Step 5: Generate fallback procedures
            fallback_procedures = self._generate_fallback_procedures(
                analysis['source_name'], analysis['data_types'], analysis['geographies'], discovered_variants
            )
            
            # Step 6: Create DataConnection class
            class_code = self._create_data_connection_class(analysis, critical_columns, fallback_procedures, discovered_variants)
            
            # Step 6: Save configuration
            config_file = self.config_path / f"{source_name.lower().replace(' ', '_')}_connection.py"
            with open(config_file, 'w') as f:
                f.write(class_code)
            
            # Step 7: Generate summary report
            if discovered_variants:
                actual_data_types = list(discovered_variants.keys())
                actual_geographies = set()
                for variant_info in discovered_variants.values():
                    actual_geographies.update(variant_info['geographies'].keys())
                actual_geographies = list(actual_geographies)
            else:
                actual_data_types = [dt for dt in analysis['data_types'] if dt != 'zhvi_discover_variants']
                actual_geographies = analysis['geographies']
            
            summary = {
                'source_name': analysis['source_name'],
                'data_types': actual_data_types,
                'geographies': actual_geographies,
                'connection_methods': len(working_methods),
                'critical_columns': len(critical_columns),
                'fallback_procedures': len(fallback_procedures),
                'confidence': analysis['confidence'],
                'suggestions': analysis['suggestions'],
                'discovered_variants': len(discovered_variants) if discovered_variants else 0
            }
            
            return {
                'success': True,
                'message': f"Successfully discovered and configured {source_name}",
                'config_file': str(config_file),
                'summary': summary,
                'class_code': class_code
            }
            
        except Exception as e:
            logger.error(f"❌ Discovery failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to discover and configure {source_name}"
            }

def main():
    """Interactive main function."""
    print("🔍 Interactive Data Source Discovery")
    print("=" * 50)
    
    # Get user input
    print("\n📝 Please describe your data source:")
    print("   Example: 'Zillow home value data for ZIP codes'")
    print("   Example: 'Redfin sales data for metro areas'")
    print("   Example: 'US Census population data by county'")
    
    description = input("\nDescription: ").strip()
    
    if not description:
        print("❌ No description provided. Exiting.")
        sys.exit(1)
    
    # Get source name
    print("\n🏷️  What would you like to call this data source?")
    source_name = input("Source name: ").strip()
    
    if not source_name:
        print("❌ No source name provided. Exiting.")
        sys.exit(1)
    
    # Initialize discovery
    config_path = Path(__file__).parent.parent / "data_connections"
    discovery = InteractiveDataDiscovery(config_path)
    
    print(f"\n🚀 Starting discovery for: {source_name}")
    print(f"📝 Description: {description}")
    print("=" * 50)
    
    # Run discovery
    result = discovery.discover_and_configure(source_name, description)
    
    print("\n" + "=" * 60)
    print("DISCOVERY RESULT")
    print("=" * 60)
    
    if result['success']:
        print(f"✅ Success: {result['message']}")
        print(f"📁 Configuration saved to: {result['config_file']}")
        
        summary = result['summary']
        print(f"\n📊 Summary:")
        print(f"   Source: {summary['source_name']}")
        print(f"   Data Types: {', '.join(summary['data_types'])}")
        print(f"   Geographies: {', '.join(summary['geographies'])}")
        print(f"   Connection Methods: {summary['connection_methods']}")
        print(f"   Critical Columns: {summary['critical_columns']}")
        print(f"   Fallback Procedures: {summary['fallback_procedures']}")
        print(f"   Confidence: {summary['confidence']:.2f}")
        
        if summary['suggestions']:
            print(f"\n💡 Suggestions:")
            for suggestion in summary['suggestions']:
                print(f"   - {suggestion}")
        
        print(f"\n📋 Next Steps:")
        print(f"   1. Review the generated configuration file")
        print(f"   2. Test the connection methods")
        print(f"   3. Integrate with your ingestion script")
        print(f"   4. Update your DataConnection imports")
        
    else:
        print(f"❌ Failed: {result['error']}")
        print(f"💡 Try providing more specific details about your data source")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

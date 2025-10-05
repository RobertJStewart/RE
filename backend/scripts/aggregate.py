#!/usr/bin/env python3
"""
RE Market Tool - Geographic Aggregation Script
==============================================

This script creates geographic aggregations with support for both:
1. **Calculated Aggregations** - Our custom geographic hierarchy
2. **Provider Data** - Direct use of Zillow's pre-calculated data

Geographic Hierarchy (Calculated):
- ZIP Code → State → State Region → Region
- Each level aggregates data from the level below

Provider Data Options:
- Use Zillow's pre-calculated data directly
- No additional processing required
- Faster performance for large datasets

Usage:
    python aggregate.py [--data-source SOURCE] [--aggregation-mode MODE] [--geography-levels LEVELS]
    
Options:
    --data-source        Data source (calculated, provider, both)
    --aggregation-mode   Aggregation method (hierarchical, direct)
    --geography-levels   Comma-separated list (metro,state,county,city,zip,neighborhood)
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/geographic_aggregation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeographicAggregation:
    """
    Geographic aggregation class with support for calculated and provider data.
    
    This class handles creating geographic aggregations using either:
    - Calculated aggregations (our custom hierarchy)
    - Provider data (Zillow's pre-calculated data)
    - Both options for comparison
    """
    
    def __init__(self, aggregations_path: Path, data_source: str = 'both'):
        """
        Initialize the geographic aggregation process.
        
        Args:
            aggregations_path (Path): Base path for aggregation storage
            data_source (str): Data source option (calculated, provider, both)
        """
        self.aggregations_path = aggregations_path
        self.data_source = data_source
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Geographic hierarchy configuration
        self.geography_hierarchy = {
            'zip': {
                'name': 'ZIP Code',
                'parent': 'state',
                'key_columns': ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank']
            },
            'city': {
                'name': 'City',
                'parent': 'state',
                'key_columns': ['RegionID', 'RegionName', 'StateName', 'Metro', 'SizeRank']
            },
            'county': {
                'name': 'County',
                'parent': 'state',
                'key_columns': ['RegionID', 'RegionName', 'StateName', 'SizeRank']
            },
            'state': {
                'name': 'State',
                'parent': 'state_region',
                'key_columns': ['RegionID', 'RegionName', 'SizeRank']
            },
            'state_region': {
                'name': 'State Region',
                'parent': 'region',
                'key_columns': ['RegionID', 'RegionName', 'SizeRank']
            },
            'region': {
                'name': 'Region',
                'parent': None,
                'key_columns': ['RegionID', 'RegionName', 'SizeRank']
            }
        }
        
        # State to region mapping
        self.state_region_mapping = {
            'Northeast': ['CT', 'ME', 'MA', 'NH', 'NJ', 'NY', 'PA', 'RI', 'VT'],
            'Southeast': ['AL', 'AR', 'DE', 'FL', 'GA', 'KY', 'LA', 'MD', 'MS', 'NC', 'SC', 'TN', 'VA', 'WV'],
            'Midwest': ['IL', 'IN', 'IA', 'KS', 'MI', 'MN', 'MO', 'NE', 'ND', 'OH', 'SD', 'WI'],
            'Southwest': ['AZ', 'NM', 'OK', 'TX'],
            'West': ['AK', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'OR', 'UT', 'WA', 'WY']
        }
        
        # State region groupings
        self.state_region_mapping = {
            'New England': ['CT', 'ME', 'MA', 'NH', 'RI', 'VT'],
            'Mid-Atlantic': ['DE', 'MD', 'NJ', 'NY', 'PA'],
            'South Atlantic': ['FL', 'GA', 'NC', 'SC', 'VA', 'WV'],
            'East South Central': ['AL', 'KY', 'MS', 'TN'],
            'West South Central': ['AR', 'LA', 'OK', 'TX'],
            'East North Central': ['IL', 'IN', 'MI', 'OH', 'WI'],
            'West North Central': ['IA', 'KS', 'MN', 'MO', 'NE', 'ND', 'SD'],
            'Mountain': ['AZ', 'CO', 'ID', 'MT', 'NV', 'NM', 'UT', 'WY'],
            'Pacific': ['AK', 'CA', 'HI', 'OR', 'WA']
        }
        
        logger.info(f"🗺️ Geographic Aggregation initialized")
        logger.info(f"📁 Aggregations path: {self.aggregations_path}")
        logger.info(f"📊 Data source: {data_source}")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.aggregations_path / "regions",
            self.aggregations_path / "state_regions",
            self.aggregations_path / "states",
            self.aggregations_path / "counties",
            self.aggregations_path / "cities",
            self.aggregations_path / "zipcodes",
            self.aggregations_path / "neighborhoods"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Ensured directory exists: {directory}")
    
    def run(self, geography_levels: List[str] = None, aggregation_mode: str = 'hierarchical') -> Dict:
        """
        Run the geographic aggregation process.
        
        Args:
            geography_levels (List[str]): List of geography levels to process
            aggregation_mode (str): Aggregation mode (hierarchical, direct)
            
        Returns:
            Dict: Result dictionary with success status and details
        """
        logger.info("🚀 Starting geographic aggregation...")
        start_time = datetime.now()
        
        try:
            # Determine geography levels to process
            if geography_levels is None:
                geography_levels = list(self.geography_hierarchy.keys())
            
            results = {}
            
            if self.data_source in ['calculated', 'both']:
                logger.info("🧮 Processing calculated aggregations...")
                calculated_results = self._process_calculated_aggregations(geography_levels, aggregation_mode)
                results['calculated'] = calculated_results
            
            if self.data_source in ['provider', 'both']:
                logger.info("📊 Processing provider data...")
                provider_results = self._process_provider_data(geography_levels)
                results['provider'] = provider_results
            
            # Generate aggregation metadata
            metadata = self._generate_aggregation_metadata(results)
            
            # Calculate total time
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"✅ Geographic aggregation completed in {duration}")
            return {
                'success': True,
                'duration': str(duration),
                'data_source': self.data_source,
                'geography_levels': geography_levels,
                'results': results,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Geographic aggregation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'duration': str(datetime.now() - start_time)
            }
    
    def _process_calculated_aggregations(self, geography_levels: List[str], aggregation_mode: str) -> Dict:
        """
        Process calculated geographic aggregations.
        
        Args:
            geography_levels (List[str]): Geography levels to process
            aggregation_mode (str): Aggregation mode
            
        Returns:
            Dict: Calculated aggregation results
        """
        try:
            results = {}
            
            # Start with ZIP code data (most granular)
            if 'zip' in geography_levels:
                logger.info("📮 Processing ZIP code aggregations...")
                zip_results = self._aggregate_zip_data()
                results['zip'] = zip_results
            
            # Aggregate to state level
            if 'state' in geography_levels:
                logger.info("🏛️ Processing state aggregations...")
                state_results = self._aggregate_state_data()
                results['state'] = state_results
            
            # Aggregate to state region level
            if 'state_region' in geography_levels:
                logger.info("🗺️ Processing state region aggregations...")
                state_region_results = self._aggregate_state_region_data()
                results['state_region'] = state_region_results
            
            # Aggregate to region level
            if 'region' in geography_levels:
                logger.info("🌎 Processing region aggregations...")
                region_results = self._aggregate_region_data()
                results['region'] = region_results
            
            return {
                'success': True,
                'aggregation_mode': aggregation_mode,
                'geography_results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Calculated aggregations failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _process_provider_data(self, geography_levels: List[str]) -> Dict:
        """
        Process provider data (Zillow's pre-calculated data).
        
        Args:
            geography_levels (List[str]): Geography levels to process
            
        Returns:
            Dict: Provider data results
        """
        try:
            results = {}
            
            for geography in geography_levels:
                if geography in ['metro', 'state', 'county', 'city', 'zip', 'neighborhood']:
                    logger.info(f"📊 Processing provider data for {geography}...")
                    provider_result = self._process_provider_geography(geography)
                    results[geography] = provider_result
            
            return {
                'success': True,
                'provider_results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Provider data processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _aggregate_zip_data(self) -> Dict:
        """
        Aggregate ZIP code data (base level).
        
        Returns:
            Dict: ZIP aggregation results
        """
        try:
            # Load ZIP code data
            zip_file = self.aggregations_path.parent / "data" / "processed" / "zhvi_zip_processed.csv"
            if not zip_file.exists():
                return {'success': False, 'error': 'ZIP code data not found'}
            
            df = pd.read_csv(zip_file)
            
            # Create ZIP code aggregations
            zip_aggregations = self._create_geographic_aggregations(df, 'zip')
            
            # Save ZIP aggregations
            zip_output = self.aggregations_path / "zipcodes" / "zipcodes.json"
            with open(zip_output, 'w') as f:
                json.dump(zip_aggregations, f, indent=2)
            
            logger.info(f"📮 ZIP code aggregations created: {len(zip_aggregations)} records")
            return {
                'success': True,
                'output_file': str(zip_output),
                'record_count': len(zip_aggregations)
            }
            
        except Exception as e:
            logger.error(f"❌ ZIP aggregation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _aggregate_state_data(self) -> Dict:
        """
        Aggregate state-level data from ZIP codes.
        
        Returns:
            Dict: State aggregation results
        """
        try:
            # Load ZIP code data
            zip_file = self.aggregations_path.parent / "data" / "processed" / "zhvi_zip_processed.csv"
            if not zip_file.exists():
                return {'success': False, 'error': 'ZIP code data not found'}
            
            df = pd.read_csv(zip_file)
            
            # Group by state and aggregate
            state_aggregations = self._create_state_aggregations(df)
            
            # Save state aggregations
            state_output = self.aggregations_path / "states" / "states.json"
            with open(state_output, 'w') as f:
                json.dump(state_aggregations, f, indent=2)
            
            logger.info(f"🏛️ State aggregations created: {len(state_aggregations)} records")
            return {
                'success': True,
                'output_file': str(state_output),
                'record_count': len(state_aggregations)
            }
            
        except Exception as e:
            logger.error(f"❌ State aggregation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _aggregate_state_region_data(self) -> Dict:
        """
        Aggregate state region data from states.
        
        Returns:
            Dict: State region aggregation results
        """
        try:
            # Load state data
            state_file = self.aggregations_path / "states" / "states.json"
            if not state_file.exists():
                return {'success': False, 'error': 'State data not found'}
            
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            # Group by state region and aggregate
            state_region_aggregations = self._create_state_region_aggregations(state_data)
            
            # Save state region aggregations
            state_region_output = self.aggregations_path / "state_regions" / "state_regions.json"
            with open(state_region_output, 'w') as f:
                json.dump(state_region_aggregations, f, indent=2)
            
            logger.info(f"🗺️ State region aggregations created: {len(state_region_aggregations)} records")
            return {
                'success': True,
                'output_file': str(state_region_output),
                'record_count': len(state_region_aggregations)
            }
            
        except Exception as e:
            logger.error(f"❌ State region aggregation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _aggregate_region_data(self) -> Dict:
        """
        Aggregate region data from state regions.
        
        Returns:
            Dict: Region aggregation results
        """
        try:
            # Load state region data
            state_region_file = self.aggregations_path / "state_regions" / "state_regions.json"
            if not state_region_file.exists():
                return {'success': False, 'error': 'State region data not found'}
            
            with open(state_region_file, 'r') as f:
                state_region_data = json.load(f)
            
            # Group by region and aggregate
            region_aggregations = self._create_region_aggregations(state_region_data)
            
            # Save region aggregations
            region_output = self.aggregations_path / "regions" / "regions.json"
            with open(region_output, 'w') as f:
                json.dump(region_aggregations, f, indent=2)
            
            logger.info(f"🌎 Region aggregations created: {len(region_aggregations)} records")
            return {
                'success': True,
                'output_file': str(region_output),
                'record_count': len(region_aggregations)
            }
            
        except Exception as e:
            logger.error(f"❌ Region aggregation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_geographic_aggregations(self, df: pd.DataFrame, geography: str) -> List[Dict]:
        """
        Create geographic aggregations from DataFrame.
        
        Args:
            df (pd.DataFrame): Source data
            geography (str): Geography level
            
        Returns:
            List[Dict]: Aggregated data
        """
        aggregations = []
        
        # Get date columns (time series data)
        date_columns = [col for col in df.columns if col not in ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank']]
        
        for _, row in df.iterrows():
            aggregation = {
                'RegionID': int(row['RegionID']),
                'RegionName': row['RegionName'],
                'SizeRank': int(row['SizeRank']),
                'time_series': {}
            }
            
            # Add geography-specific fields
            if 'StateName' in row:
                aggregation['StateName'] = row['StateName']
            if 'Metro' in row:
                aggregation['Metro'] = row['Metro']
            if 'CountyName' in row:
                aggregation['CountyName'] = row['CountyName']
            
            # Add time series data
            for date_col in date_columns:
                if pd.notna(row[date_col]):
                    aggregation['time_series'][date_col] = float(row[date_col])
            
            aggregations.append(aggregation)
        
        return aggregations
    
    def _create_state_aggregations(self, df: pd.DataFrame) -> List[Dict]:
        """
        Create state-level aggregations from ZIP code data.
        
        Args:
            df (pd.DataFrame): ZIP code data
            
        Returns:
            List[Dict]: State aggregations
        """
        if 'StateName' not in df.columns:
            return []
        
        # Group by state
        state_groups = df.groupby('StateName')
        aggregations = []
        
        for state_name, state_df in state_groups:
            # Get date columns
            date_columns = [col for col in state_df.columns if col not in ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank']]
            
            aggregation = {
                'RegionID': hash(state_name) % 1000000,  # Generate unique ID
                'RegionName': state_name,
                'SizeRank': len(aggregations) + 1,
                'time_series': {}
            }
            
            # Aggregate time series data (average)
            for date_col in date_columns:
                values = state_df[date_col].dropna()
                if len(values) > 0:
                    aggregation['time_series'][date_col] = float(values.mean())
            
            aggregations.append(aggregation)
        
        return aggregations
    
    def _create_state_region_aggregations(self, state_data: List[Dict]) -> List[Dict]:
        """
        Create state region aggregations from state data.
        
        Args:
            state_data (List[Dict]): State data
            
        Returns:
            List[Dict]: State region aggregations
        """
        # Group states by state region
        state_region_groups = {}
        
        for state in state_data:
            state_name = state.get('StateName', '')
            for region, states in self.state_region_mapping.items():
                if state_name in states:
                    if region not in state_region_groups:
                        state_region_groups[region] = []
                    state_region_groups[region].append(state)
                    break
        
        aggregations = []
        
        for region_name, states in state_region_groups.items():
            aggregation = {
                'RegionID': hash(region_name) % 1000000,
                'RegionName': region_name,
                'SizeRank': len(aggregations) + 1,
                'time_series': {}
            }
            
            # Aggregate time series data from states
            if states:
                # Get all date columns from first state
                first_state = states[0]
                date_columns = list(first_state.get('time_series', {}).keys())
                
                for date_col in date_columns:
                    values = []
                    for state in states:
                        if date_col in state.get('time_series', {}):
                            values.append(state['time_series'][date_col])
                    
                    if values:
                        aggregation['time_series'][date_col] = float(np.mean(values))
            
            aggregations.append(aggregation)
        
        return aggregations
    
    def _create_region_aggregations(self, state_region_data: List[Dict]) -> List[Dict]:
        """
        Create region aggregations from state region data.
        
        Args:
            state_region_data (List[Dict]): State region data
            
        Returns:
            List[Dict]: Region aggregations
        """
        # Group state regions by major region
        region_groups = {
            'Northeast': ['New England', 'Mid-Atlantic'],
            'Southeast': ['South Atlantic', 'East South Central'],
            'Midwest': ['East North Central', 'West North Central'],
            'Southwest': ['West South Central'],
            'West': ['Mountain', 'Pacific']
        }
        
        aggregations = []
        
        for region_name, state_regions in region_groups.items():
            # Find matching state regions
            matching_regions = [sr for sr in state_region_data if sr['RegionName'] in state_regions]
            
            if matching_regions:
                aggregation = {
                    'RegionID': hash(region_name) % 1000000,
                    'RegionName': region_name,
                    'SizeRank': len(aggregations) + 1,
                    'time_series': {}
                }
                
                # Aggregate time series data from state regions
                if matching_regions:
                    # Get all date columns from first state region
                    first_region = matching_regions[0]
                    date_columns = list(first_region.get('time_series', {}).keys())
                    
                    for date_col in date_columns:
                        values = []
                        for sr in matching_regions:
                            if date_col in sr.get('time_series', {}):
                                values.append(sr['time_series'][date_col])
                        
                        if values:
                            aggregation['time_series'][date_col] = float(np.mean(values))
                
                aggregations.append(aggregation)
        
        return aggregations
    
    def _process_provider_geography(self, geography: str) -> Dict:
        """
        Process provider data for a specific geography level.
        
        Args:
            geography (str): Geography level
            
        Returns:
            Dict: Provider data results
        """
        try:
            # Load provider data
            provider_file = self.aggregations_path.parent / "data" / "processed" / f"zhvi_{geography}_processed.csv"
            if not provider_file.exists():
                return {'success': False, 'error': f'Provider data not found for {geography}'}
            
            df = pd.read_csv(provider_file)
            
            # Convert to JSON format
            provider_data = self._create_geographic_aggregations(df, geography)
            
            # Save provider data
            output_file = self.aggregations_path / f"{geography}s" / f"{geography}s_provider.json"
            with open(output_file, 'w') as f:
                json.dump(provider_data, f, indent=2)
            
            logger.info(f"📊 Provider data processed for {geography}: {len(provider_data)} records")
            return {
                'success': True,
                'output_file': str(output_file),
                'record_count': len(provider_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Provider data processing failed for {geography}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_aggregation_metadata(self, results: Dict) -> Dict:
        """
        Generate metadata for the aggregation process.
        
        Args:
            results (Dict): Aggregation results
            
        Returns:
            Dict: Aggregation metadata
        """
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'data_source': self.data_source,
            'geography_hierarchy': self.geography_hierarchy,
            'state_region_mapping': self.state_region_mapping,
            'results': results
        }
        
        # Save metadata
        metadata_file = self.aggregations_path / "aggregation_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 Aggregation metadata generated: {metadata_file}")
        return metadata

def main():
    """Main entry point for the geographic aggregation script."""
    parser = argparse.ArgumentParser(description='RE Market Tool Geographic Aggregation')
    parser.add_argument('--data-source', default='both', 
                       choices=['calculated', 'provider', 'both'],
                       help='Data source option')
    parser.add_argument('--aggregation-mode', default='hierarchical',
                       choices=['hierarchical', 'direct'],
                       help='Aggregation mode')
    parser.add_argument('--geography-levels', default='metro,state,county,city,zip,neighborhood',
                       help='Comma-separated list of geography levels')
    
    args = parser.parse_args()
    
    # Set up aggregations path
    aggregations_path = Path(__file__).parent.parent / "aggregations"
    
    # Parse geography levels
    geography_levels = [s.strip() for s in args.geography_levels.split(',')]
    
    # Initialize and run aggregation
    aggregation = GeographicAggregation(aggregations_path, args.data_source)
    result = aggregation.run(geography_levels, args.aggregation_mode)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
RE Market Tool - Statistical Calculation Script
==============================================

This script performs statistical calculations on geographic aggregations.
It takes the raw time series data from aggregate.py and calculates various
statistics including average, median, quartiles, standard deviation, etc.

Statistical Methods Supported:
- Average (mean)
- Median
- Quartiles (Q1, Q3)
- Min/Max
- Standard Deviation
- Count
- Percentiles (custom)

Usage:
    python calculate.py [--statistics STATS] [--geography-levels LEVELS] [--output-format FORMAT]
    
Options:
    --statistics        Comma-separated list of statistics (avg,median,q1,q3,min,max,std,count)
    --geography-levels  Comma-separated list (zip,state,state_region,region)
    --output-format     Output format (json,csv)
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional, Any
import argparse

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'statistical_calculation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StatisticalCalculation:
    """
    Statistical calculation class for geographic aggregations.
    
    This class takes raw time series data from geographic aggregations
    and calculates various statistics including averages, medians,
    quartiles, standard deviations, and more.
    """
    
    def __init__(self, statistics_path: Path):
        """
        Initialize the statistical calculation process.
        
        Args:
            statistics_path (Path): Base path for statistics storage
        """
        self.statistics_path = statistics_path
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Available statistics methods
        self.statistics_methods = {
            # Basic statistics
            'avg': {
                'name': 'Average',
                'description': 'Arithmetic mean of values',
                'function': self._calculate_average
            },
            'median': {
                'name': 'Median',
                'description': 'Middle value when sorted',
                'function': self._calculate_median
            },
            'q1': {
                'name': 'First Quartile',
                'description': '25th percentile',
                'function': self._calculate_q1
            },
            'q3': {
                'name': 'Third Quartile',
                'description': '75th percentile',
                'function': self._calculate_q3
            },
            'min': {
                'name': 'Minimum',
                'description': 'Smallest value',
                'function': self._calculate_min
            },
            'max': {
                'name': 'Maximum',
                'description': 'Largest value',
                'function': self._calculate_max
            },
            'std': {
                'name': 'Standard Deviation',
                'description': 'Measure of data spread',
                'function': self._calculate_std
            },
            'count': {
                'name': 'Count',
                'description': 'Number of data points',
                'function': self._calculate_count
            },
            
            # Percentiles
            'p10': {
                'name': '10th Percentile',
                'description': 'Bottom 10% of values',
                'function': self._calculate_p10
            },
            'p25': {
                'name': '25th Percentile',
                'description': 'Bottom quartile',
                'function': self._calculate_p25
            },
            'p75': {
                'name': '75th Percentile',
                'description': 'Top quartile',
                'function': self._calculate_p75
            },
            'p90': {
                'name': '90th Percentile',
                'description': 'Top 10% of values',
                'function': self._calculate_p90
            },
            'p95': {
                'name': '95th Percentile',
                'description': 'Top 5% of values',
                'function': self._calculate_p95
            },
            'p99': {
                'name': '99th Percentile',
                'description': 'Top 1% of values',
                'function': self._calculate_p99
            },
            
            # Distribution shape
            'skewness': {
                'name': 'Skewness',
                'description': 'Measure of distribution asymmetry',
                'function': self._calculate_skewness
            },
            'kurtosis': {
                'name': 'Kurtosis',
                'description': 'Measure of distribution tail heaviness',
                'function': self._calculate_kurtosis
            },
            
            # Volatility & risk metrics
            'coefficient_of_variation': {
                'name': 'Coefficient of Variation',
                'description': 'Relative volatility (std/mean)',
                'function': self._calculate_coefficient_of_variation
            },
            'range': {
                'name': 'Range',
                'description': 'Max - Min',
                'function': self._calculate_range
            },
            'interquartile_range': {
                'name': 'IQR',
                'description': 'Q3 - Q1',
                'function': self._calculate_interquartile_range
            },
            'mad': {
                'name': 'Mean Absolute Deviation',
                'description': 'Average absolute deviation from mean',
                'function': self._calculate_mad
            },
            'var_95': {
                'name': 'Value at Risk (95%)',
                'description': '95th percentile value',
                'function': self._calculate_var_95
            },
            'var_99': {
                'name': 'Value at Risk (99%)',
                'description': '99th percentile value',
                'function': self._calculate_var_99
            },
            
            # Time series trend analysis
            'linear_trend': {
                'name': 'Linear Trend',
                'description': 'Slope of linear regression over time',
                'function': self._calculate_linear_trend
            },
            'trend_strength': {
                'name': 'Trend Strength',
                'description': 'R-squared of linear trend',
                'function': self._calculate_trend_strength
            },
            'volatility_trend': {
                'name': 'Volatility Trend',
                'description': 'Change in volatility over time',
                'function': self._calculate_volatility_trend
            },
            'momentum_3m': {
                'name': '3-Month Momentum',
                'description': 'Change over last 3 months',
                'function': self._calculate_momentum_3m
            },
            'momentum_6m': {
                'name': '6-Month Momentum',
                'description': 'Change over last 6 months',
                'function': self._calculate_momentum_6m
            },
            'momentum_12m': {
                'name': '12-Month Momentum',
                'description': 'Change over last 12 months',
                'function': self._calculate_momentum_12m
            },
            
            # Market health indicators
            'positive_change_pct': {
                'name': '% Positive Changes',
                'description': 'Percentage of positive period-over-period changes',
                'function': self._calculate_positive_change_pct
            },
            'above_median_pct': {
                'name': '% Above Median',
                'description': 'Percentage of values above overall median',
                'function': self._calculate_above_median_pct
            },
            'price_efficiency': {
                'name': 'Price Efficiency',
                'description': 'How close values are to trend line',
                'function': self._calculate_price_efficiency
            },
            
            # Comparative analysis
            'percentile_rank': {
                'name': 'Percentile Rank',
                'description': 'Current value percentile within historical range',
                'function': self._calculate_percentile_rank
            },
            'z_score': {
                'name': 'Z-Score',
                'description': 'Standard deviations from mean',
                'function': self._calculate_z_score
            },
            'relative_strength': {
                'name': 'Relative Strength',
                'description': 'Performance vs benchmark',
                'function': self._calculate_relative_strength
            }
        }
        
        # Time series calculation methods
        self.timeseries_methods = {
            'pop': {
                'name': 'Period over Period',
                'description': 'Current period vs previous period',
                'function': self._calculate_period_over_period
            },
            'yoy': {
                'name': 'Year over Year',
                'description': 'Current period vs same period last year',
                'function': self._calculate_year_over_year
            },
            'mom': {
                'name': 'Month over Month',
                'description': 'Current month vs previous month',
                'function': self._calculate_month_over_month
            },
            'qoq': {
                'name': 'Quarter over Quarter',
                'description': 'Current quarter vs previous quarter',
                'function': self._calculate_quarter_over_quarter
            }
        }
        
        logger.info(f"📊 Statistical Calculation initialized")
        logger.info(f"📁 Statistics path: {self.statistics_path}")
        logger.info(f"📈 Available statistics: {list(self.statistics_methods.keys())}")
        
        # Initialize storage monitoring
        self.storage_threshold_gb = 50.0  # 50GB threshold
        self.storage_warning_gb = 40.0    # 40GB warning threshold
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.statistics_path / "zipcodes",
            self.statistics_path / "states",
            self.statistics_path / "state_regions",
            self.statistics_path / "regions"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Ensured directory exists: {directory}")
    
    def run(self, statistics: List[str] = None, geography_levels: List[str] = None, output_format: str = 'json', timeseries: List[str] = None) -> Dict:
        """
        Run the statistical calculation process.
        
        Args:
            statistics (List[str]): List of statistics to calculate
            geography_levels (List[str]): List of geography levels to process
            output_format (str): Output format (json, csv)
            timeseries (List[str]): List of time series calculations to perform
            
        Returns:
            Dict: Result dictionary with success status and details
        """
        logger.info("🚀 Starting statistical calculations...")
        start_time = datetime.now()
        
        try:
            # Determine statistics to calculate
            if statistics is None:
                statistics = list(self.statistics_methods.keys())
            
            # Determine time series calculations to perform
            if timeseries is None:
                timeseries = []
            
            # Determine geography levels to process
            if geography_levels is None:
                geography_levels = ['zip', 'state', 'state_region', 'region']
            
            results = {}
            
            for geography in geography_levels:
                logger.info(f"📊 Processing statistics for {geography} level...")
                geography_result = self._process_geography_statistics(geography, statistics, output_format, timeseries)
                results[geography] = geography_result
            
            # Generate statistics metadata
            metadata = self._generate_statistics_metadata(results, statistics, geography_levels, timeseries)
            
            # Calculate total time
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"✅ Statistical calculations completed in {duration}")
            return {
                'success': True,
                'duration': str(duration),
                'statistics': statistics,
                'timeseries': timeseries,
                'geography_levels': geography_levels,
                'output_format': output_format,
                'results': results,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Statistical calculations failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'duration': str(datetime.now() - start_time)
            }
    
    def _process_geography_statistics(self, geography: str, statistics: List[str], output_format: str, timeseries: List[str]) -> Dict:
        """
        Process statistics for a specific geography level.
        
        Args:
            geography (str): Geography level
            statistics (List[str]): Statistics to calculate
            output_format (str): Output format
            timeseries (List[str]): Time series calculations to perform
            
        Returns:
            Dict: Geography statistics results
        """
        try:
            # Load geographic aggregation data
            # Handle special case for zip -> zipcodes
            geography_dir = "zipcodes" if geography == "zip" else f"{geography}s"
            aggregation_file = Path(__file__).parent.parent / "aggregations" / geography_dir / f"{geography_dir}.json"
            if not aggregation_file.exists():
                return {'success': False, 'error': f'Aggregation file not found: {aggregation_file}'}
            
            with open(aggregation_file, 'r') as f:
                aggregation_data = json.load(f)
            
            # Calculate statistics for each region
            calculated_statistics = []
            
            for region in aggregation_data:
                region_stats = self._calculate_region_statistics(region, statistics, timeseries, geography)
                calculated_statistics.append(region_stats)
            
                # Save statistics
                if output_format == 'json':
                    # Handle special case for zip -> zipcodes
                    output_dir = "zipcodes" if geography == "zip" else f"{geography}s"
                    output_file = self.statistics_path / output_dir / f"{output_dir}_statistics.json"
                    with open(output_file, 'w') as f:
                        json.dump(calculated_statistics, f, indent=2)
                elif output_format == 'csv':
                    # Handle special case for zip -> zipcodes
                    output_dir = "zipcodes" if geography == "zip" else f"{geography}s"
                    output_file = self.statistics_path / output_dir / f"{output_dir}_statistics.csv"
                    self._save_statistics_csv(calculated_statistics, output_file)
            
            logger.info(f"📊 {geography.title()} statistics calculated: {len(calculated_statistics)} regions")
            return {
                'success': True,
                'output_file': str(output_file),
                'region_count': len(calculated_statistics),
                'statistics_calculated': statistics
            }
            
        except Exception as e:
            logger.error(f"❌ Statistics calculation failed for {geography}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_region_statistics(self, region: Dict, statistics: List[str], timeseries: List[str], geography: str) -> Dict:
        """
        Calculate statistics for a single region.
        
        Args:
            region (Dict): Region data with raw_time_series
            statistics (List[str]): Statistics to calculate
            timeseries (List[str]): Time series calculations to perform
            geography (str): Geography level for metadata lookup
            
        Returns:
            Dict: Region with calculated statistics
        """
        # Start with basic region information
        region_stats = {
            'RegionID': region['RegionID'],
            'RegionName': region['RegionName'],
            'SizeRank': region['SizeRank']
        }
        
        # Add geography-specific fields
        if 'StateName' in region:
            region_stats['StateName'] = region['StateName']
        if 'Metro' in region:
            region_stats['Metro'] = region['Metro']
        if 'CountyName' in region:
            region_stats['CountyName'] = region['CountyName']
        
        # Calculate statistics for each date
        raw_time_series = region.get('raw_time_series', {})
        calculated_time_series = {}
        
        # Get sorted dates for time series calculations
        sorted_dates = sorted(raw_time_series.keys())
        
        # Get data periodicity from metadata and filter meaningful time series calculations
        periodicity = self._get_data_periodicity_from_metadata(geography)
        meaningful_timeseries = self._get_meaningful_timeseries(periodicity, timeseries)
        
        if meaningful_timeseries != timeseries:
            logger.info(f"📊 Using {periodicity} data periodicity from metadata for {region['RegionName']}")
            logger.info(f"📊 Filtered time series calculations: {timeseries} → {meaningful_timeseries}")
        
        for i, date in enumerate(sorted_dates):
            values = raw_time_series[date]
            if not values:  # Skip empty arrays
                continue
                
            date_stats = {}
            
            # Calculate basic statistics (skip for ZIP level since it's single values)
            if geography != 'zip':
                for stat in statistics:
                    if stat in self.statistics_methods:
                        try:
                            stat_value = self.statistics_methods[stat]['function'](values)
                            date_stats[stat] = stat_value
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to calculate {stat} for {region['RegionName']} on {date}: {str(e)}")
                            date_stats[stat] = None
            else:
                # For ZIP level, we still need some basic values for time series calculations
                # Use the single value as the "average" for time series calculations
                if values:
                    date_stats['avg'] = float(values[0])  # Single value as average
            
            # Calculate meaningful time series statistics only
            for ts_method in meaningful_timeseries:
                if ts_method in self.timeseries_methods:
                    try:
                        ts_value = self.timeseries_methods[ts_method]['function'](raw_time_series, sorted_dates, i, date_stats)
                        if ts_value is not None:
                            date_stats[ts_method] = ts_value
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to calculate {ts_method} for {region['RegionName']} on {date}: {str(e)}")
                        date_stats[ts_method] = None
            
            # Calculate advanced statistics that are meaningful for single-value time series
            if geography == 'zip':
                for stat in statistics:
                    if stat in ['linear_trend', 'trend_strength', 'volatility_trend', 'momentum_3m', 'momentum_6m', 'momentum_12m', 'positive_change_pct', 'above_median_pct', 'price_efficiency', 'percentile_rank', 'z_score', 'relative_strength']:
                        if stat in self.statistics_methods:
                            try:
                                # For advanced statistics, we need to pass the entire time series
                                stat_value = self.statistics_methods[stat]['function'](raw_time_series, sorted_dates, i)
                                if stat_value is not None:
                                    date_stats[stat] = stat_value
                            except Exception as e:
                                logger.warning(f"⚠️  Failed to calculate {stat} for {region['RegionName']} on {date}: {str(e)}")
                                date_stats[stat] = None
            
            calculated_time_series[date] = date_stats
        
        region_stats['calculated_statistics'] = calculated_time_series
        return region_stats
    
    def _calculate_average(self, values: List[float]) -> float:
        """Calculate arithmetic mean."""
        return float(np.mean(values))
    
    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median."""
        return float(np.median(values))
    
    def _calculate_q1(self, values: List[float]) -> float:
        """Calculate first quartile (25th percentile)."""
        return float(np.percentile(values, 25))
    
    def _calculate_q3(self, values: List[float]) -> float:
        """Calculate third quartile (75th percentile)."""
        return float(np.percentile(values, 75))
    
    def _calculate_min(self, values: List[float]) -> float:
        """Calculate minimum value."""
        return float(np.min(values))
    
    def _calculate_max(self, values: List[float]) -> float:
        """Calculate maximum value."""
        return float(np.max(values))
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        return float(np.std(values))
    
    def _calculate_count(self, values: List[float]) -> int:
        """Calculate count of values."""
        return int(len(values))
    
    # Percentile calculations
    def _calculate_p10(self, values: List[float]) -> float:
        """Calculate 10th percentile."""
        return float(np.percentile(values, 10))
    
    def _calculate_p25(self, values: List[float]) -> float:
        """Calculate 25th percentile."""
        return float(np.percentile(values, 25))
    
    def _calculate_p75(self, values: List[float]) -> float:
        """Calculate 75th percentile."""
        return float(np.percentile(values, 75))
    
    def _calculate_p90(self, values: List[float]) -> float:
        """Calculate 90th percentile."""
        return float(np.percentile(values, 90))
    
    def _calculate_p95(self, values: List[float]) -> float:
        """Calculate 95th percentile."""
        return float(np.percentile(values, 95))
    
    def _calculate_p99(self, values: List[float]) -> float:
        """Calculate 99th percentile."""
        return float(np.percentile(values, 99))
    
    # Distribution shape calculations
    def _calculate_skewness(self, values: List[float]) -> float:
        """Calculate skewness."""
        from scipy import stats
        return float(stats.skew(values))
    
    def _calculate_kurtosis(self, values: List[float]) -> float:
        """Calculate kurtosis."""
        from scipy import stats
        return float(stats.kurtosis(values))
    
    # Volatility & risk metrics
    def _calculate_coefficient_of_variation(self, values: List[float]) -> float:
        """Calculate coefficient of variation."""
        mean_val = np.mean(values)
        if mean_val == 0:
            return 0.0
        return float(np.std(values) / mean_val)
    
    def _calculate_range(self, values: List[float]) -> float:
        """Calculate range (max - min)."""
        return float(np.max(values) - np.min(values))
    
    def _calculate_interquartile_range(self, values: List[float]) -> float:
        """Calculate interquartile range (Q3 - Q1)."""
        return float(np.percentile(values, 75) - np.percentile(values, 25))
    
    def _calculate_mad(self, values: List[float]) -> float:
        """Calculate mean absolute deviation."""
        mean_val = np.mean(values)
        return float(np.mean(np.abs(values - mean_val)))
    
    def _calculate_var_95(self, values: List[float]) -> float:
        """Calculate Value at Risk (95%)."""
        return float(np.percentile(values, 5))
    
    def _calculate_var_99(self, values: List[float]) -> float:
        """Calculate Value at Risk (99%)."""
        return float(np.percentile(values, 1))
    
    # Time series trend analysis (simplified versions for now)
    def _calculate_linear_trend(self, values_or_timeseries, sorted_dates=None, current_index=None) -> float:
        """Calculate linear trend slope."""
        try:
            from scipy import stats
            # Handle both single values and time series data
            if isinstance(values_or_timeseries, list):
                values = values_or_timeseries
            else:
                # Extract values from time series
                values = []
                for date in sorted_dates:
                    if date in values_or_timeseries and values_or_timeseries[date]:
                        values.append(values_or_timeseries[date][0])  # Single value per date
            
            if len(values) < 2:
                return 0.0
                
            x = np.arange(len(values))
            slope, _, _, _, _ = stats.linregress(x, values)
            return float(slope)
        except:
            return 0.0
    
    def _calculate_trend_strength(self, values_or_timeseries, sorted_dates=None, current_index=None) -> float:
        """Calculate trend strength (R-squared)."""
        try:
            from scipy import stats
            # Handle both single values and time series data
            if isinstance(values_or_timeseries, list):
                values = values_or_timeseries
            else:
                # Extract values from time series
                values = []
                for date in sorted_dates:
                    if date in values_or_timeseries and values_or_timeseries[date]:
                        values.append(values_or_timeseries[date][0])  # Single value per date
            
            if len(values) < 2:
                return 0.0
                
            x = np.arange(len(values))
            _, _, r_value, _, _ = stats.linregress(x, values)
            return float(r_value ** 2)
        except:
            return 0.0
    
    def _calculate_volatility_trend(self, values: List[float]) -> float:
        """Calculate volatility trend (simplified)."""
        if len(values) < 4:
            return 0.0
        # Calculate rolling volatility and its trend
        half = len(values) // 2
        first_half_std = np.std(values[:half])
        second_half_std = np.std(values[half:])
        if first_half_std == 0:
            return 0.0
        return float((second_half_std - first_half_std) / first_half_std)
    
    def _calculate_momentum_3m(self, values_or_timeseries, sorted_dates=None, current_index=None) -> float:
        """Calculate 3-month momentum (simplified)."""
        try:
            # Handle both single values and time series data
            if isinstance(values_or_timeseries, list):
                values = values_or_timeseries
            else:
                # Extract values from time series
                values = []
                for date in sorted_dates:
                    if date in values_or_timeseries and values_or_timeseries[date]:
                        values.append(values_or_timeseries[date][0])  # Single value per date
            
            if len(values) < 4:
                return 0.0
            # Use last 25% of data vs first 25% as proxy for 3-month momentum
            quarter = len(values) // 4
            if quarter == 0:
                return 0.0
            recent_avg = np.mean(values[-quarter:])
            older_avg = np.mean(values[:quarter])
            if older_avg == 0:
                return 0.0
            return float((recent_avg - older_avg) / older_avg * 100)
        except:
            return 0.0
    
    def _calculate_momentum_6m(self, values: List[float]) -> float:
        """Calculate 6-month momentum (simplified)."""
        if len(values) < 4:
            return 0.0
        # Use last 25% of data vs middle 25% as proxy for 6-month momentum
        quarter = len(values) // 4
        if quarter == 0:
            return 0.0
        recent_avg = np.mean(values[-quarter:])
        middle_avg = np.mean(values[quarter:quarter*2])
        if middle_avg == 0:
            return 0.0
        return float((recent_avg - middle_avg) / middle_avg * 100)
    
    def _calculate_momentum_12m(self, values: List[float]) -> float:
        """Calculate 12-month momentum (simplified)."""
        if len(values) < 4:
            return 0.0
        # Use last 25% of data vs first 25% as proxy for 12-month momentum
        quarter = len(values) // 4
        if quarter == 0:
            return 0.0
        recent_avg = np.mean(values[-quarter:])
        older_avg = np.mean(values[:quarter])
        if older_avg == 0:
            return 0.0
        return float((recent_avg - older_avg) / older_avg * 100)
    
    # Market health indicators
    def _calculate_positive_change_pct(self, values: List[float]) -> float:
        """Calculate percentage of positive changes."""
        if len(values) < 2:
            return 0.0
        changes = [values[i] - values[i-1] for i in range(1, len(values))]
        positive_changes = sum(1 for change in changes if change > 0)
        return float(positive_changes / len(changes) * 100)
    
    def _calculate_above_median_pct(self, values: List[float]) -> float:
        """Calculate percentage of values above median."""
        if len(values) == 0:
            return 0.0
        median_val = np.median(values)
        above_median = sum(1 for val in values if val > median_val)
        return float(above_median / len(values) * 100)
    
    def _calculate_price_efficiency(self, values: List[float]) -> float:
        """Calculate price efficiency (how close values are to trend line)."""
        if len(values) < 3:
            return 0.0
        from scipy import stats
        x = np.arange(len(values))
        slope, intercept, r_value, _, _ = stats.linregress(x, values)
        trend_line = slope * x + intercept
        mse = np.mean((values - trend_line) ** 2)
        variance = np.var(values)
        if variance == 0:
            return 1.0
        return float(1 - (mse / variance))
    
    # Comparative analysis
    def _calculate_percentile_rank(self, values: List[float]) -> float:
        """Calculate percentile rank of current value."""
        if len(values) == 0:
            return 0.0
        current_val = values[-1]  # Assume last value is current
        below_current = sum(1 for val in values if val < current_val)
        return float(below_current / len(values) * 100)
    
    def _calculate_z_score(self, values: List[float]) -> float:
        """Calculate Z-score of current value."""
        if len(values) == 0:
            return 0.0
        current_val = values[-1]  # Assume last value is current
        mean_val = np.mean(values)
        std_val = np.std(values)
        if std_val == 0:
            return 0.0
        return float((current_val - mean_val) / std_val)
    
    def _calculate_relative_strength(self, values: List[float]) -> float:
        """Calculate relative strength (simplified)."""
        if len(values) < 2:
            return 1.0
        # Simple relative strength: current value vs average
        current_val = values[-1]
        avg_val = np.mean(values)
        if avg_val == 0:
            return 1.0
        return float(current_val / avg_val)
    
    def _get_data_periodicity_from_metadata(self, geography: str) -> str:
        """
        Get the data periodicity from DataConnection metadata.
        
        Args:
            geography: Geography level (e.g., 'state', 'zip')
            
        Returns:
            str: Data periodicity ('daily', 'weekly', 'monthly', 'quarterly', 'annual', 'irregular')
        """
        try:
            # Use cached data connection if available, otherwise create new one
            if not hasattr(self, '_data_connection'):
                from data_connection import REDataConnection
                self._data_connection = REDataConnection()
            
            # Get metadata for ZHVI data (assuming we're working with ZHVI)
            metadata = self._data_connection.get_metadata('zillow', 'zhvi', 'all_homes_smoothed_seasonally_adjusted', geography)
            
            # Map frequency to periodicity
            frequency = metadata.frequency.lower()
            if 'daily' in frequency:
                return 'daily'
            elif 'weekly' in frequency:
                return 'weekly'
            elif 'monthly' in frequency:
                return 'monthly'
            elif 'quarterly' in frequency:
                return 'quarterly'
            elif 'annual' in frequency or 'yearly' in frequency:
                return 'annual'
            else:
                return 'irregular'
                
        except Exception as e:
            logger.warning(f"⚠️  Could not get periodicity from metadata: {str(e)}")
            return 'monthly'  # Default to monthly for Zillow data
    
    def _get_meaningful_timeseries(self, periodicity: str, requested_timeseries: List[str]) -> List[str]:
        """
        Filter time series calculations to only include those that provide meaningful insights
        for the detected data periodicity.
        
        Args:
            periodicity: Detected data periodicity
            requested_timeseries: List of requested time series calculations
            
        Returns:
            List[str]: Filtered list of meaningful time series calculations
        """
        meaningful_timeseries = []
        
        for ts in requested_timeseries:
            if ts == 'pop':
                # Period over Period is always meaningful
                meaningful_timeseries.append(ts)
            elif ts == 'yoy':
                # Year over Year is always meaningful
                meaningful_timeseries.append(ts)
            elif ts == 'mom':
                # Month over Month is meaningful for daily, weekly, or monthly data
                if periodicity in ['daily', 'weekly', 'monthly']:
                    meaningful_timeseries.append(ts)
            elif ts == 'qoq':
                # Quarter over Quarter is meaningful for daily, weekly, monthly, or quarterly data
                if periodicity in ['daily', 'weekly', 'monthly', 'quarterly']:
                    meaningful_timeseries.append(ts)
        
        return meaningful_timeseries
    
    def _calculate_storage_usage(self) -> Dict:
        """
        Calculate current storage usage across all statistics files.
        
        Returns:
            Dict: Storage usage information
        """
        try:
            total_size_bytes = 0
            file_count = 0
            geography_sizes = {}
            
            # Check all geography levels
            geography_levels = ['zipcodes', 'states', 'state_regions', 'regions', 'counties', 'cities', 'neighborhoods']
            
            for geography in geography_levels:
                geography_path = self.statistics_path / geography
                if geography_path.exists():
                    geography_size = 0
                    geography_files = 0
                    
                    for file_path in geography_path.glob('*.json'):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            geography_size += file_size
                            geography_files += 1
                    
                    if geography_size > 0:
                        geography_sizes[geography] = {
                            'size_bytes': geography_size,
                            'size_mb': geography_size / (1024 * 1024),
                            'file_count': geography_files
                        }
                        total_size_bytes += geography_size
                        file_count += geography_files
            
            # Calculate total size
            total_size_mb = total_size_bytes / (1024 * 1024)
            total_size_gb = total_size_mb / 1024
            
            return {
                'total_size_bytes': total_size_bytes,
                'total_size_mb': total_size_mb,
                'total_size_gb': total_size_gb,
                'file_count': file_count,
                'geography_sizes': geography_sizes,
                'threshold_gb': self.storage_threshold_gb,
                'warning_gb': self.storage_warning_gb
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate storage usage: {str(e)}")
            return {
                'total_size_gb': 0,
                'error': str(e)
            }
    
    def _check_storage_thresholds(self, storage_info: Dict) -> Dict:
        """
        Check if storage usage exceeds thresholds and provide recommendations.
        
        Args:
            storage_info: Storage usage information
            
        Returns:
            Dict: Threshold check results and recommendations
        """
        total_gb = storage_info.get('total_size_gb', 0)
        threshold_gb = storage_info.get('threshold_gb', 50.0)
        warning_gb = storage_info.get('warning_gb', 40.0)
        
        status = 'ok'
        message = ''
        recommendations = []
        
        if total_gb >= threshold_gb:
            status = 'critical'
            message = f"🚨 CRITICAL: Storage usage ({total_gb:.2f}GB) exceeds threshold ({threshold_gb}GB)"
            recommendations = [
                "Move to cloud storage (AWS S3, Google Cloud, Azure)",
                "Implement database solution (PostgreSQL, MongoDB)",
                "Enable data compression (gzip)",
                "Archive older data (keep only 2-3 years)",
                "Remove unused geography levels",
                "Consider data retention policies"
            ]
        elif total_gb >= warning_gb:
            status = 'warning'
            message = f"⚠️  WARNING: Storage usage ({total_gb:.2f}GB) approaching threshold ({threshold_gb}GB)"
            recommendations = [
                "Consider moving to cloud storage soon",
                "Enable data compression",
                "Review data retention policies",
                "Monitor storage growth trends"
            ]
        else:
            status = 'ok'
            message = f"✅ Storage usage ({total_gb:.2f}GB) is within limits"
            recommendations = [
                "Continue current storage approach",
                "Monitor storage growth",
                "Consider compression for optimization"
            ]
        
        return {
            'status': status,
            'message': message,
            'recommendations': recommendations,
            'usage_percentage': (total_gb / threshold_gb) * 100
        }
    
    def _log_storage_report(self, storage_info: Dict, threshold_check: Dict):
        """
        Log comprehensive storage report.
        
        Args:
            storage_info: Storage usage information
            threshold_check: Threshold check results
        """
        logger.info("=" * 60)
        logger.info("📊 STORAGE USAGE REPORT")
        logger.info("=" * 60)
        
        # Overall usage
        logger.info(f"📁 Total Storage: {storage_info['total_size_gb']:.2f}GB ({storage_info['total_size_mb']:.1f}MB)")
        logger.info(f"📄 Total Files: {storage_info['file_count']}")
        logger.info(f"🎯 Threshold: {storage_info['threshold_gb']}GB")
        logger.info(f"📊 Usage: {threshold_check['usage_percentage']:.1f}% of threshold")
        
        # Status and message
        if threshold_check['status'] == 'critical':
            logger.error(threshold_check['message'])
        elif threshold_check['status'] == 'warning':
            logger.warning(threshold_check['message'])
        else:
            logger.info(threshold_check['message'])
        
        # Geography breakdown
        if storage_info.get('geography_sizes'):
            logger.info("\n📊 Storage by Geography Level:")
            for geography, info in storage_info['geography_sizes'].items():
                logger.info(f"  {geography}: {info['size_mb']:.1f}MB ({info['file_count']} files)")
        
        # Recommendations
        if threshold_check['recommendations']:
            logger.info(f"\n💡 Recommendations:")
            for i, rec in enumerate(threshold_check['recommendations'], 1):
                logger.info(f"  {i}. {rec}")
        
        logger.info("=" * 60)
    
    # Time series calculation methods
    def _calculate_period_over_period(self, raw_time_series: Dict, sorted_dates: List[str], current_index: int, current_stats: Dict) -> Optional[float]:
        """
        Calculate period over period change.
        
        Args:
            raw_time_series: All time series data
            sorted_dates: Sorted list of dates
            current_index: Current date index
            current_stats: Current period statistics
            
        Returns:
            Period over period change as percentage
        """
        if current_index == 0:
            return None  # No previous period
        
        previous_date = sorted_dates[current_index - 1]
        previous_values = raw_time_series.get(previous_date, [])
        
        if not previous_values or not current_stats.get('avg'):
            return None
        
        # Use average for comparison
        current_avg = current_stats['avg']
        previous_avg = np.mean(previous_values)
        
        if previous_avg == 0:
            return None
        
        return float((current_avg - previous_avg) / previous_avg * 100)
    
    def _calculate_year_over_year(self, raw_time_series: Dict, sorted_dates: List[str], current_index: int, current_stats: Dict) -> Optional[float]:
        """
        Calculate year over year change with smart periodicity detection.
        
        Args:
            raw_time_series: All time series data
            sorted_dates: Sorted list of dates
            current_index: Current date index
            current_stats: Current period statistics
            
        Returns:
            Year over year change as percentage
        """
        if current_index == 0:
            return None
        
        current_date = sorted_dates[current_index]
        current_values = raw_time_series.get(current_date, [])
        
        if not current_values or not current_stats.get('avg'):
            return None
        
        # Parse current date
        try:
            current_dt = pd.to_datetime(current_date)
        except:
            return None
        
        # Find same period last year
        last_year_date = None
        for i in range(current_index - 1, -1, -1):
            try:
                candidate_dt = pd.to_datetime(sorted_dates[i])
                # Check if it's approximately the same period last year
                if (current_dt.year - candidate_dt.year == 1 and 
                    abs((current_dt - candidate_dt).days) <= 45):  # Within 45 days
                    last_year_date = sorted_dates[i]
                    break
            except:
                continue
        
        if not last_year_date:
            return None
        
        last_year_values = raw_time_series.get(last_year_date, [])
        if not last_year_values:
            return None
        
        # Calculate YoY change
        current_avg = current_stats['avg']
        last_year_avg = np.mean(last_year_values)
        
        if last_year_avg == 0:
            return None
        
        return float((current_avg - last_year_avg) / last_year_avg * 100)
    
    def _calculate_month_over_month(self, raw_time_series: Dict, sorted_dates: List[str], current_index: int, current_stats: Dict) -> Optional[float]:
        """
        Calculate month over month change.
        
        Args:
            raw_time_series: All time series data
            sorted_dates: Sorted list of dates
            current_index: Current date index
            current_stats: Current period statistics
            
        Returns:
            Month over month change as percentage
        """
        if current_index == 0:
            return None
        
        current_date = sorted_dates[current_index]
        
        # Find previous month
        try:
            current_dt = pd.to_datetime(current_date)
            previous_month_dt = current_dt - pd.DateOffset(months=1)
            
            # Find closest date to previous month
            previous_month_date = None
            min_diff = float('inf')
            
            for i in range(current_index - 1, -1, -1):
                try:
                    candidate_dt = pd.to_datetime(sorted_dates[i])
                    diff = abs((candidate_dt - previous_month_dt).days)
                    if diff < min_diff and diff <= 15:  # Within 15 days
                        min_diff = diff
                        previous_month_date = sorted_dates[i]
                except:
                    continue
            
            if not previous_month_date:
                return None
            
            previous_values = raw_time_series.get(previous_month_date, [])
            if not previous_values or not current_stats.get('avg'):
                return None
            
            # Calculate MoM change
            current_avg = current_stats['avg']
            previous_avg = np.mean(previous_values)
            
            if previous_avg == 0:
                return None
            
            return float((current_avg - previous_avg) / previous_avg * 100)
            
        except:
            return None
    
    def _calculate_quarter_over_quarter(self, raw_time_series: Dict, sorted_dates: List[str], current_index: int, current_stats: Dict) -> Optional[float]:
        """
        Calculate quarter over quarter change.
        
        Args:
            raw_time_series: All time series data
            sorted_dates: Sorted list of dates
            current_index: Current date index
            current_stats: Current period statistics
            
        Returns:
            Quarter over quarter change as percentage
        """
        if current_index == 0:
            return None
        
        current_date = sorted_dates[current_index]
        
        # Find previous quarter
        try:
            current_dt = pd.to_datetime(current_date)
            previous_quarter_dt = current_dt - pd.DateOffset(months=3)
            
            # Find closest date to previous quarter
            previous_quarter_date = None
            min_diff = float('inf')
            
            for i in range(current_index - 1, -1, -1):
                try:
                    candidate_dt = pd.to_datetime(sorted_dates[i])
                    diff = abs((candidate_dt - previous_quarter_dt).days)
                    if diff < min_diff and diff <= 45:  # Within 45 days
                        min_diff = diff
                        previous_quarter_date = sorted_dates[i]
                except:
                    continue
            
            if not previous_quarter_date:
                return None
            
            previous_values = raw_time_series.get(previous_quarter_date, [])
            if not previous_values or not current_stats.get('avg'):
                return None
            
            # Calculate QoQ change
            current_avg = current_stats['avg']
            previous_avg = np.mean(previous_values)
            
            if previous_avg == 0:
                return None
            
            return float((current_avg - previous_avg) / previous_avg * 100)
            
        except:
            return None
    
    def _save_statistics_csv(self, statistics_data: List[Dict], output_file: Path):
        """
        Save statistics data in CSV format.
        
        Args:
            statistics_data (List[Dict]): Statistics data
            output_file (Path): Output file path
        """
        # Flatten the data for CSV format
        flattened_data = []
        
        for region in statistics_data:
            base_info = {
                'RegionID': region['RegionID'],
                'RegionName': region['RegionName'],
                'SizeRank': region['SizeRank']
            }
            
            # Add geography-specific fields
            if 'StateName' in region:
                base_info['StateName'] = region['StateName']
            if 'Metro' in region:
                base_info['Metro'] = region['Metro']
            if 'CountyName' in region:
                base_info['CountyName'] = region['CountyName']
            
            # Add statistics for each date
            calculated_stats = region.get('calculated_statistics', {})
            for date, stats in calculated_stats.items():
                row = base_info.copy()
                row['Date'] = date
                
                for stat_name, stat_value in stats.items():
                    row[stat_name] = stat_value
                
                flattened_data.append(row)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_file, index=False)
    
    def _generate_statistics_metadata(self, results: Dict, statistics: List[str], geography_levels: List[str], timeseries: List[str]) -> Dict:
        """
        Generate metadata for the statistics calculation process.
        
        Args:
            results (Dict): Statistics results
            statistics (List[str]): Statistics calculated
            geography_levels (List[str]): Geography levels processed
            timeseries (List[str]): Time series calculations performed
            
        Returns:
            Dict: Statistics metadata
        """
        # Create serializable statistics methods info
        statistics_methods_info = {}
        for key, method in self.statistics_methods.items():
            statistics_methods_info[key] = {
                'name': method['name'],
                'description': method['description']
            }
        
        # Create serializable time series methods info
        timeseries_methods_info = {}
        for key, method in self.timeseries_methods.items():
            timeseries_methods_info[key] = {
                'name': method['name'],
                'description': method['description']
            }
        
        # Analyze which statistics were actually calculated vs requested
        actually_calculated_stats = set()
        actually_calculated_timeseries = set()
        
        for geography, result in results.items():
            if result.get('success'):
                # Load the actual statistics file to see what was calculated
                try:
                    output_file = result.get('output_file')
                    if output_file and Path(output_file).exists():
                        with open(output_file, 'r') as f:
                            data = json.load(f)
                        
                        # Sample a few records to see what statistics are present
                        for record in data[:3]:  # Check first 3 records
                            if 'calculated_statistics' in record:
                                for date, stats in record['calculated_statistics'].items():
                                    for stat_name in stats.keys():
                                        if stat_name in self.statistics_methods:
                                            actually_calculated_stats.add(stat_name)
                                        elif stat_name in self.timeseries_methods:
                                            actually_calculated_timeseries.add(stat_name)
                except Exception as e:
                    logger.warning(f"⚠️  Could not analyze calculated statistics for {geography}: {str(e)}")
        
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'statistics_requested': statistics,
            'statistics_calculated': list(actually_calculated_stats),
            'statistics_failed': list(set(statistics) - actually_calculated_stats),
            'timeseries_requested': timeseries,
            'timeseries_calculated': list(actually_calculated_timeseries),
            'timeseries_failed': list(set(timeseries) - actually_calculated_timeseries),
            'geography_levels': geography_levels,
            'statistics_methods': statistics_methods_info,
            'timeseries_methods': timeseries_methods_info,
            'graceful_degradation': {
                'enabled': True,
                'description': 'Statistics that failed to calculate are omitted from the JSON output',
                'frontend_handling': 'Check metadata to see which statistics are available before consuming data'
            },
            'results_summary': {}
        }
    
        # Add results summary
        for geography, result in results.items():
            if result.get('success'):
                metadata['results_summary'][geography] = {
                    'region_count': result.get('region_count', 0),
                    'statistics_calculated': result.get('statistics_calculated', []),
                    'output_file': result.get('output_file', '')
                }
    
        # Save metadata
        metadata_file = self.statistics_path / "statistics_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Also save a frontend-friendly availability summary
        availability_summary = {
            'timestamp': metadata['timestamp'],
            'available_statistics': {
                'basic': [stat for stat in metadata['statistics_calculated'] if stat in ['avg', 'median', 'min', 'max', 'std', 'count']],
                'percentiles': [stat for stat in metadata['statistics_calculated'] if stat.startswith('p')],
                'distribution': [stat for stat in metadata['statistics_calculated'] if stat in ['skewness', 'kurtosis']],
                'volatility': [stat for stat in metadata['statistics_calculated'] if stat in ['coefficient_of_variation', 'range', 'interquartile_range', 'mad', 'var_95', 'var_99']],
                'trend': [stat for stat in metadata['statistics_calculated'] if stat in ['linear_trend', 'trend_strength', 'volatility_trend']],
                'momentum': [stat for stat in metadata['statistics_calculated'] if stat.startswith('momentum_')],
                'market_health': [stat for stat in metadata['statistics_calculated'] if stat in ['positive_change_pct', 'above_median_pct', 'price_efficiency']],
                'comparative': [stat for stat in metadata['statistics_calculated'] if stat in ['percentile_rank', 'z_score', 'relative_strength']]
            },
            'available_timeseries': metadata['timeseries_calculated'],
            'failed_statistics': metadata['statistics_failed'],
            'failed_timeseries': metadata['timeseries_failed'],
            'geography_levels': metadata['geography_levels']
        }
        
        availability_file = self.statistics_path / "statistics_availability.json"
        with open(availability_file, 'w') as f:
            json.dump(availability_summary, f, indent=2)
        
        logger.info(f"📋 Statistics metadata generated: {metadata_file}")
        logger.info(f"📋 Statistics availability summary generated: {availability_file}")
        return metadata

def main():
    """Main entry point for the statistical calculation script."""
    parser = argparse.ArgumentParser(description='RE Market Tool Statistical Calculations')
    parser.add_argument('--statistics', default='avg,median,q1,q3,min,max,std,count',
                       help='Comma-separated list of statistics to calculate')
    parser.add_argument('--timeseries', default='',
                       help='Comma-separated list of time series calculations (pop,yoy,mom,qoq)')
    parser.add_argument('--geography-levels', default='zip,state,state_region,region',
                       help='Comma-separated list of geography levels')
    parser.add_argument('--output-format', default='json',
                       choices=['json', 'csv'],
                       help='Output format')
    
    args = parser.parse_args()
    
    # Set up statistics path
    statistics_path = Path(__file__).parent.parent / "statistics"
    
    # Parse statistics, time series, and geography levels
    statistics = [s.strip() for s in args.statistics.split(',')]
    timeseries = [s.strip() for s in args.timeseries.split(',')] if args.timeseries else []
    geography_levels = [s.strip() for s in args.geography_levels.split(',')]
    
    # Initialize and run calculations
    calculation = StatisticalCalculation(statistics_path)
    result = calculation.run(statistics, geography_levels, args.output_format, timeseries)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()

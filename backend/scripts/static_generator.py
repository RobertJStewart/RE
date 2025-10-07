#!/usr/bin/env python3
"""
RE Market Tool - Static File Generator
=====================================

Copies existing ETL output files for GitHub Pages deployment.
This allows the frontend to work in static mode without requiring a server.

Usage:
    python static_generator.py [--output-dir DIR]
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from connection_manager import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StaticFileGenerator:
    """
    Copies existing ETL output files for static frontend deployment.
    
    This class copies the pre-calculated files from the ETL pipeline
    to the frontend static_data directory for GitHub Pages deployment.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the static file generator.
        
        Args:
            output_dir: Directory to write static files to
        """
        if output_dir is None:
            # Default to frontend/static_data directory
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / "frontend" / "static_data"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define source directories
        self.backend_path = Path(__file__).parent.parent
        self.aggregations_path = self.backend_path / "aggregations"
        self.statistics_path = self.backend_path / "statistics"
        self.registry_path = self.backend_path / "dataconnections.json"
        
        logger.info(f"StaticFileGenerator initialized with output directory: {self.output_dir}")
    
    def copy_all_files(self) -> Dict[str, str]:
        """
        Copy all ETL output files to static directory.
        
        Returns:
            Dictionary mapping filename to file path
        """
        copied_files = {}
        
        try:
            # Copy aggregations
            aggregations_files = self.copy_aggregations()
            copied_files.update(aggregations_files)
            
            # Copy statistics
            statistics_files = self.copy_statistics()
            copied_files.update(statistics_files)
            
            # Copy connection registry
            registry_file = self.copy_connection_registry()
            copied_files['connections'] = registry_file
            
            # Generate frontend-compatible data sources file
            data_sources_file = self.generate_data_sources_file()
            copied_files['data_sources'] = data_sources_file
            
            logger.info(f"Copied {len(copied_files)} static files")
            return copied_files
            
        except Exception as e:
            logger.error(f"Failed to copy static files: {e}")
            raise
    
    def copy_aggregations(self) -> Dict[str, str]:
        """
        Copy aggregation files to static directory.
        
        Returns:
            Dictionary mapping filename to file path
        """
        copied_files = {}
        
        try:
            if self.aggregations_path.exists():
                # Copy all JSON files from aggregations
                for json_file in self.aggregations_path.rglob("*.json"):
                    relative_path = json_file.relative_to(self.aggregations_path)
                    output_file = self.output_dir / "aggregations" / relative_path
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(json_file, output_file)
                    copied_files[f"aggregations/{relative_path}"] = str(output_file)
                
                logger.info(f"Copied {len(copied_files)} aggregation files")
            else:
                logger.warning("Aggregations directory not found")
            
            return copied_files
            
        except Exception as e:
            logger.error(f"Failed to copy aggregations: {e}")
            raise
    
    def copy_statistics(self) -> Dict[str, str]:
        """
        Copy statistics files to static directory.
        
        Returns:
            Dictionary mapping filename to file path
        """
        copied_files = {}
        
        try:
            if self.statistics_path.exists():
                # Copy all JSON files from statistics
                for json_file in self.statistics_path.rglob("*.json"):
                    relative_path = json_file.relative_to(self.statistics_path)
                    output_file = self.output_dir / "statistics" / relative_path
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(json_file, output_file)
                    copied_files[f"statistics/{relative_path}"] = str(output_file)
                
                logger.info(f"Copied {len(copied_files)} statistics files")
            else:
                logger.warning("Statistics directory not found")
            
            return copied_files
            
        except Exception as e:
            logger.error(f"Failed to copy statistics: {e}")
            raise
    
    def copy_connection_registry(self) -> str:
        """
        Copy connection registry to static directory.
        
        Returns:
            Path to copied file
        """
        try:
            if self.registry_path.exists():
                output_file = self.output_dir / "connections.json"
                shutil.copy2(self.registry_path, output_file)
                
                logger.info("Copied connection registry")
                return str(output_file)
            else:
                logger.warning("Connection registry not found")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to copy connection registry: {e}")
            raise
    
    def generate_data_sources_file(self) -> str:
        """
        Generate data_sources.json file (compatible with existing frontend).
        
        Returns:
            Path to generated file
        """
        try:
            # Load connection registry
            if not self.registry_path.exists():
                logger.warning("Connection registry not found, creating empty data sources file")
                data_sources_data = {
                    'timestamp': datetime.now().isoformat(),
                    'total_count': 0,
                    'data_sources': []
                }
            else:
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
                
                connections = registry_data.get('connections', {})
                
                # Convert to format expected by existing frontend
                data_sources = []
                for conn_id, conn_data in connections.items():
                    if conn_data.get('status') == 'active':
                        data_sources.append({
                            'id': conn_data['id'],
                            'name': conn_data['name'],
                            'data_source': conn_data['data_source'],
                            'data_type': conn_data['data_type'],
                            'sub_type': conn_data.get('sub_type'),
                            'geography': conn_data['geography'],
                            'update_frequency': conn_data['update_frequency'],
                            'status': conn_data['status'],
                            'description': conn_data.get('flexible_metadata', {}).get('description', ''),
                            'data_quality': conn_data.get('flexible_metadata', {}).get('data_quality', 'unknown'),
                            'coverage': conn_data.get('flexible_metadata', {}).get('coverage', 'unknown')
                        })
                
                # Prepare data for frontend
                data_sources_data = {
                    'timestamp': datetime.now().isoformat(),
                    'total_count': len(data_sources),
                    'data_sources': data_sources
                }
            
            # Write to file
            output_file = self.output_dir / "data_sources.json"
            with open(output_file, 'w') as f:
                json.dump(data_sources_data, f, indent=2)
            
            logger.info(f"Generated data_sources.json with {data_sources_data['total_count']} data sources")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate data sources file: {e}")
            raise
    
    def generate_readme(self) -> str:
        """
        Generate README.md for the static data directory.
        
        Returns:
            Path to generated file
        """
        try:
            readme_content = f"""# Static Data Files

This directory contains static JSON files copied from the ETL pipeline for GitHub Pages deployment.

## Files

- `connections.json` - Connection registry with full metadata
- `data_sources.json` - Data sources in frontend-compatible format
- `aggregations/` - Geographic aggregation data
- `statistics/` - Statistical calculations

## Generation

These files are automatically copied by running:
```bash
python backend/scripts/static_generator.py
```

## Last Updated

Generated on: {datetime.now().isoformat()}

## Usage

These files are used by the static frontend mode to provide data without requiring a server.
"""
            
            # Write to file
            output_file = self.output_dir / "README.md"
            with open(output_file, 'w') as f:
                f.write(readme_content)
            
            logger.info("Generated README.md")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to generate README: {e}")
            raise

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Copy ETL files for static frontend deployment')
    parser.add_argument('--output-dir', type=str, help='Output directory for static files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize generator
        output_dir = Path(args.output_dir) if args.output_dir else None
        generator = StaticFileGenerator(output_dir)
        
        # Copy all files
        print("🚀 Copying ETL files for static frontend deployment...")
        copied_files = generator.copy_all_files()
        
        # Generate README
        generator.generate_readme()
        
        # Print summary
        print(f"\n✅ Successfully copied {len(copied_files)} static files:")
        for name, path in copied_files.items():
            print(f"   {name}: {path}")
        
        print(f"\n📁 Output directory: {generator.output_dir}")
        print("🎯 Ready for GitHub Pages deployment!")
        
    except Exception as e:
        logger.error(f"Failed to copy static files: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

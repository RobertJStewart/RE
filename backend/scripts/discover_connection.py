#!/usr/bin/env python3
"""
RE Market Tool - Data Connection Discovery CLI
==============================================

Command-line interface for discovering and configuring new data connections.

Usage:
    python discover_connection.py --url "https://example.com/data.csv"
    python discover_connection.py --description "Zillow home value data for ZIP codes"
    python discover_connection.py --interactive
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.new_data_connection import NewDataConnection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def interactive_discovery():
    """Interactive data connection discovery."""
    print("🔍 Interactive Data Connection Discovery")
    print("=" * 50)
    
    discovery = NewDataConnection()
    
    while True:
        print("\nOptions:")
        print("1. Discover from URL")
        print("2. Discover from description")
        print("3. List existing connections")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            url = input("Enter the data URL: ").strip()
            if url:
                source_name = input("Enter source name (optional): ").strip() or None
                result = discovery.discover_connection(url=url, source_name=source_name)
                print_discovery_result(result)
            else:
                print("❌ URL is required")
        
        elif choice == '2':
            description = input("Enter data description: ").strip()
            if description:
                source_name = input("Enter source name (optional): ").strip() or None
                result = discovery.discover_connection(description=description, source_name=source_name)
                print_discovery_result(result)
            else:
                print("❌ Description is required")
        
        elif choice == '3':
            list_existing_connections(discovery)
        
        elif choice == '4':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-4.")

def print_discovery_result(result):
    """Print discovery result in a formatted way."""
    print("\n" + "=" * 60)
    print("DISCOVERY RESULT")
    print("=" * 60)
    
    if result.success:
        print(f"✅ Success: {result.source_name}")
        print(f"   Data Type: {result.data_type}")
        print(f"   Geography: {result.geography}")
        print(f"   Critical Columns: {', '.join(result.critical_columns)}")
        print(f"   Connection Methods: {len(result.connection_methods)}")
        print(f"   Fallback Procedures: {len(result.fallback_procedures)}")
        
        if result.sample_data is not None:
            print(f"   Sample Data: {len(result.sample_data)} rows, {len(result.sample_data.columns)} columns")
        
        print("\n📊 Connection Methods:")
        for i, method in enumerate(result.connection_methods, 1):
            print(f"   {i}. {method['method']} ({method['status']})")
            if 'notes' in method:
                print(f"      {method['notes']}")
        
        print("\n🔄 Fallback Procedures:")
        for i, procedure in enumerate(result.fallback_procedures, 1):
            print(f"   {i}. {procedure['type']}: {procedure['description']}")
        
    else:
        print(f"❌ Failed: {result.error}")
    
    print("=" * 60)

def list_existing_connections(discovery):
    """List existing connection configurations."""
    print("\n📁 Existing Connection Configurations:")
    print("-" * 40)
    
    config_files = list(discovery.config_path.glob("*.json"))
    
    if not config_files:
        print("   No existing connections found.")
        return
    
    for config_file in config_files:
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"   📄 {config_file.name}")
            print(f"      Source: {config.get('source_name', 'Unknown')}")
            print(f"      Data Type: {config.get('data_type', 'Unknown')}")
            print(f"      Geography: {config.get('geography', 'Unknown')}")
            print(f"      Discovered: {config.get('discovery_date', 'Unknown')}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error reading {config_file.name}: {str(e)}")

def main():
    """Main entry point for the discovery CLI."""
    parser = argparse.ArgumentParser(description='Discover and configure new data connections')
    parser.add_argument('--url', help='URL to data source')
    parser.add_argument('--description', help='Description of data source')
    parser.add_argument('--source-name', help='Name for the data source')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--list', action='store_true', help='List existing connections')
    
    args = parser.parse_args()
    
    discovery = NewDataConnection()
    
    if args.list:
        list_existing_connections(discovery)
        return
    
    if args.interactive:
        interactive_discovery()
        return
    
    if not args.url and not args.description:
        print("❌ Error: Either --url, --description, or --interactive must be provided")
        parser.print_help()
        sys.exit(1)
    
    # Discover connection
    result = discovery.discover_connection(
        url=args.url,
        description=args.description,
        source_name=args.source_name
    )
    
    # Print result
    print_discovery_result(result)
    
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)

if __name__ == "__main__":
    main()

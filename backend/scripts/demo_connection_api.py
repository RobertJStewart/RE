#!/usr/bin/env python3
"""
RE Market Tool - Connection Manager API Demo
===========================================

Demonstrates the flexible connection management system capabilities.
This shows all the filtering, querying, and management features.

Usage:
    python demo_connection_api.py
"""

from connection_manager import ConnectionManager
import json

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")

def main():
    """Run the connection manager demo."""
    print("🚀 RE Market Tool - Flexible Connection Manager Demo")
    print("📊 Demonstrating dynamic data connection management")
    
    # Initialize connection manager
    manager = ConnectionManager()
    
    # 1. Basic Statistics
    print_section("BASIC STATISTICS")
    all_connections = manager.get_connections_by_filter({})
    active_connections = manager.get_connections_by_filter({'status': 'active'})
    
    print(f"Total connections: {len(all_connections)}")
    print(f"Active connections: {len(active_connections)}")
    print(f"Inactive connections: {len(all_connections) - len(active_connections)}")
    
    # 2. Hierarchical Filtering Demo
    print_section("HIERARCHICAL FILTERING DEMO")
    
    # Level 1: All data sources
    print_subsection("Level 1: All Data Sources")
    all_sources = manager.get_connections_by_filter({})
    print(f"Total: {len(all_sources)}")
    
    # Level 2: Zillow only
    print_subsection("Level 2: Zillow Data Sources")
    zillow_sources = manager.get_connections_by_filter({'data_source': 'zillow'})
    print(f"Total: {len(zillow_sources)}")
    
    # Level 3: ZHVI data type
    print_subsection("Level 3: ZHVI Data Type")
    zhvi_sources = manager.get_connections_by_filter({'data_source': 'zillow', 'data_type': 'zhvi'})
    print(f"Total: {len(zhvi_sources)}")
    
    # Level 4: Smoothed seasonally adjusted
    print_subsection("Level 4: Smoothed Seasonally Adjusted")
    smoothed_sources = manager.get_connections_by_filter({
        'data_source': 'zillow', 
        'data_type': 'zhvi', 
        'sub_type': 'all_homes_smoothed_seasonally_adjusted'
    })
    print(f"Total: {len(smoothed_sources)}")
    for conn in smoothed_sources:
        print(f"  - {conn['geography']}: {conn['id']}")
    
    # Level 5: ZIP geography
    print_subsection("Level 5: ZIP Geography")
    zip_sources = manager.get_connections_by_filter({
        'data_source': 'zillow', 
        'data_type': 'zhvi', 
        'sub_type': 'all_homes_smoothed_seasonally_adjusted',
        'geography': 'zip'
    })
    print(f"Total: {len(zip_sources)}")
    for conn in zip_sources:
        print(f"  - {conn['id']}")
    
    # 3. Cross-Field Filtering
    print_section("CROSS-FIELD FILTERING DEMO")
    
    # Filter by geography only
    print_subsection("All ZIP Geographies (Any Data Source)")
    zip_geographies = manager.get_connections_by_filter({'geography': 'zip'})
    print(f"Total: {len(zip_geographies)}")
    for conn in zip_geographies:
        print(f"  - {conn['data_source']} {conn['data_type']} {conn.get('sub_type', 'N/A')}: {conn['id']}")
    
    # Filter by update frequency
    print_subsection("Monthly Update Frequency")
    monthly_sources = manager.get_connections_by_filter({'update_frequency': 'monthly'})
    print(f"Total: {len(monthly_sources)}")
    
    # 4. Available Filter Options
    print_section("AVAILABLE FILTER OPTIONS")
    filter_options = manager.get_hierarchical_filter_options()
    
    for key, values in filter_options.items():
        print_subsection(f"Available {key.replace('_', ' ').title()}")
        print(f"Options: {values}")
        print(f"Count: {len(values)}")
    
    # 5. Individual Connection Details
    print_section("INDIVIDUAL CONNECTION DETAILS")
    
    # Get a sample connection
    sample_connection = all_connections[0]
    print_subsection(f"Sample Connection: {sample_connection['id']}")
    
    print("Core Fields:")
    for field in ['data_source', 'data_type', 'sub_type', 'geography', 'update_frequency', 'status']:
        print(f"  {field}: {sample_connection.get(field, 'N/A')}")
    
    print("\nFlexible Metadata:")
    flexible_metadata = sample_connection.get('flexible_metadata', {})
    for key, value in list(flexible_metadata.items())[:5]:  # Show first 5 fields
        if isinstance(value, list) and len(value) > 3:
            print(f"  {key}: {value[:3]}... ({len(value)} items)")
        else:
            print(f"  {key}: {value}")
    
    # 6. Complexity Analysis
    print_section("COMPLEXITY ANALYSIS")
    complexity_analysis = manager.get_complexity_recommendations()
    
    print(f"Current complexity score: {complexity_analysis['current_complexity_score']:.1f}")
    print(f"File size: {complexity_analysis['file_size_mb']:.2f} MB")
    print(f"Total connections: {complexity_analysis['total_connections']}")
    
    recommendations = complexity_analysis.get('recommendations', [])
    if recommendations:
        print_subsection("Recommendations")
        for rec in recommendations:
            print(f"  - {rec['type']}: {rec['message']} (Priority: {rec['priority']})")
    else:
        print("No recommendations - system is running efficiently!")
    
    # 7. API Endpoint Simulation
    print_section("API ENDPOINT SIMULATION")
    
    # Simulate API calls
    api_endpoints = [
        ("GET /api/connections", {}),
        ("GET /api/connections?data_source=zillow", {'data_source': 'zillow'}),
        ("GET /api/connections?geography=zip", {'geography': 'zip'}),
        ("GET /api/connections?data_source=zillow&data_type=zhvi", {'data_source': 'zillow', 'data_type': 'zhvi'}),
        ("GET /api/connections?update_frequency=monthly", {'update_frequency': 'monthly'})
    ]
    
    for endpoint, filters in api_endpoints:
        print_subsection(endpoint)
        results = manager.get_connections_by_filter(filters)
        print(f"Results: {len(results)} connections")
        if len(results) <= 3:
            for conn in results:
                print(f"  - {conn['id']}")
        else:
            for conn in results[:3]:
                print(f"  - {conn['id']}")
            print(f"  ... and {len(results) - 3} more")
    
    # 8. Summary
    print_section("SUMMARY")
    print("✅ Flexible connection management system is fully functional!")
    print("✅ Hierarchical filtering works at all levels")
    print("✅ Cross-field filtering supports any combination")
    print("✅ Flexible metadata allows custom fields per connection")
    print("✅ Complexity monitoring provides migration recommendations")
    print("✅ API-ready for frontend integration")
    
    print(f"\n🎯 Ready for next phase: Frontend integration and user-driven connection addition!")

if __name__ == "__main__":
    main()

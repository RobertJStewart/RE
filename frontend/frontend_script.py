#!/usr/bin/env python3
"""
RE Market Tool - Frontend Server
===============================

This is the main frontend server that orchestrates all frontend functionality.
It provides a web interface for the RE Market Tool with three main pages:
- Overview: Market analysis and key metrics
- Time Series: Historical trends and period-over-period changes  
- Add New: Connect new data sources

The server integrates with the backend DataConnection classes to provide
real-time data source information and statistics.

Usage:
    python frontend_script.py [--port PORT] [--host HOST] [--debug]

Examples:
    python frontend_script.py                    # Start on localhost:5000
    python frontend_script.py --port 8080        # Start on port 8080
    python frontend_script.py --host 0.0.0.0     # Allow external connections
    python frontend_script.py --debug            # Enable debug mode
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add backend scripts to path
backend_path = Path(__file__).parent.parent / "backend" / "scripts"
sys.path.insert(0, str(backend_path))

try:
    from flask import Flask, render_template, jsonify, request, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("❌ Flask not installed. Installing required packages...")
    os.system("pip install flask flask-cors")
    from flask import Flask, render_template, jsonify, request, send_from_directory
    from flask_cors import CORS

try:
    from data_connection import REDataConnection
    from connection_manager import ConnectionManager
    DATA_CONNECTION_AVAILABLE = True
    CONNECTION_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import DataConnection or ConnectionManager: {e}")
    DATA_CONNECTION_AVAILABLE = False
    CONNECTION_MANAGER_AVAILABLE = False

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'frontend_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FrontendServer:
    """Main frontend server class that orchestrates all frontend functionality."""
    
    def __init__(self, host: str = 'localhost', port: int = 5000, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)
        
        # Initialize data connection and connection manager
        self.data_connection = None
        self.connection_manager = None
        
        if DATA_CONNECTION_AVAILABLE:
            try:
                self.data_connection = REDataConnection()
                logger.info("✅ DataConnection initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize DataConnection: {e}")
                self.data_connection = None
        
        if CONNECTION_MANAGER_AVAILABLE:
            try:
                registry_path = Path(__file__).parent.parent / "backend" / "dataconnections.json"
                self.connection_manager = ConnectionManager(registry_path)
                logger.info("✅ ConnectionManager initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ConnectionManager: {e}")
                self.connection_manager = None
        
        # Setup routes
        self.setup_routes()
        
        logger.info(f"🚀 Frontend server initialized on {host}:{port}")
    
    def setup_routes(self):
        """Setup all Flask routes for the frontend."""
        
        @self.app.route('/')
        def index():
            """Main page - Overview with data source selector."""
            return render_template('index.html')
        
        @self.app.route('/api/data-sources')
        def get_data_sources():
            """API endpoint to get available data sources from DataConnection."""
            try:
                if not self.data_connection:
                    return jsonify({
                        'success': False,
                        'error': 'DataConnection not available',
                        'data_sources': []
                    })
                
                # Get all available combinations from DataConnection
                combinations = self.data_connection.get_all_available_combinations()
                
                # Transform into frontend-friendly format
                data_sources = []
                for data_source, data_type, sub_type, geography in combinations:
                    # Get metadata for this combination
                    try:
                        metadata = self.data_connection.get_metadata(
                            data_source, data_type, sub_type, geography
                        )
                        
                        # Create unique ID
                        source_id = f"{data_source}_{data_type}_{sub_type}"
                        
                        # Check if we already have this data source
                        existing_source = next(
                            (ds for ds in data_sources if ds['id'] == source_id), 
                            None
                        )
                        
                        if not existing_source:
                            # Create new data source entry
                            data_sources.append({
                                'id': source_id,
                                'name': f"{metadata.source_name} - {metadata.data_type}",
                                'description': f"{metadata.data_type} data from {metadata.source_name}",
                                'data_source': data_source,
                                'data_type': data_type,
                                'sub_type': sub_type,
                                'geographies': [geography],
                                'frequency': metadata.frequency,
                                'critical_columns': metadata.critical_columns
                            })
                        else:
                            # Add geography to existing source
                            if geography not in existing_source['geographies']:
                                existing_source['geographies'].append(geography)
                    
                    except Exception as e:
                        logger.warning(f"⚠️  Could not get metadata for {data_source}-{data_type}-{sub_type}-{geography}: {e}")
                        continue
                
                logger.info(f"📊 Retrieved {len(data_sources)} data sources")
                return jsonify({
                    'success': True,
                    'data_sources': data_sources,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting data sources: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'data_sources': []
                })
        
        @self.app.route('/api/data/<source_id>')
        def get_data_for_source(source_id):
            """API endpoint to get data for a specific source."""
            try:
                # Parse source ID
                parts = source_id.split('_')
                if len(parts) < 3:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid source ID format'
                    })
                
                data_source = parts[0]
                data_type = parts[1]
                sub_type = '_'.join(parts[2:])
                
                # Get available geographies for this source
                if not self.data_connection:
                    return jsonify({
                        'success': False,
                        'error': 'DataConnection not available'
                    })
                
                # Find all geographies for this data source/type combination
                combinations = self.data_connection.get_all_available_combinations()
                geographies = [
                    geo for ds, dt, st, geo in combinations 
                    if ds == data_source and dt == data_type and st == sub_type
                ]
                
                # For now, return mock data structure
                # In a real implementation, this would load actual data
                mock_data = {
                    'source_info': {
                        'id': source_id,
                        'data_source': data_source,
                        'data_type': data_type,
                        'sub_type': sub_type,
                        'geographies': geographies
                    },
                    'statistics': {
                        'total_regions': 1234,
                        'avg_price': 450000,
                        'price_trend': 5.2,
                        'market_health': 'Strong'
                    },
                    'regions': [
                        {'id': 1, 'name': 'New York, NY', 'avg_price': 750000},
                        {'id': 2, 'name': 'Los Angeles, CA', 'avg_price': 650000},
                        {'id': 3, 'name': 'Chicago, IL', 'avg_price': 350000},
                        {'id': 4, 'name': 'Houston, TX', 'avg_price': 280000},
                        {'id': 5, 'name': 'Phoenix, AZ', 'avg_price': 320000}
                    ]
                }
                
                return jsonify({
                    'success': True,
                    'data': mock_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting data for source {source_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/statistics/<source_id>/<geography>')
        def get_statistics_for_geography(source_id, geography):
            """API endpoint to get statistics for a specific source and geography."""
            try:
                # Parse source ID
                parts = source_id.split('_')
                if len(parts) < 3:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid source ID format'
                    })
                
                data_source = parts[0]
                data_type = parts[1]
                sub_type = '_'.join(parts[2:])
                
                # Check if statistics file exists
                stats_dir = Path(__file__).parent.parent / "backend" / "statistics"
                geography_dir = "zipcodes" if geography == "zip" else f"{geography}s"
                stats_file = stats_dir / geography_dir / f"{geography_dir}_statistics.json"
                
                if stats_file.exists():
                    with open(stats_file, 'r') as f:
                        statistics_data = json.load(f)
                    
                    return jsonify({
                        'success': True,
                        'data': statistics_data,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Statistics file not found for {geography}',
                        'data': []
                    })
                
            except Exception as e:
                logger.error(f"❌ Error getting statistics for {source_id}/{geography}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/add-data-source', methods=['POST'])
        def add_data_source():
            """API endpoint to add a new data source."""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['name', 'description', 'url', 'data_type', 'geography_levels']
                for field in required_fields:
                    if field not in data or not data[field]:
                        return jsonify({
                            'success': False,
                            'error': f'Missing required field: {field}'
                        })
                
                # For now, just log the request
                # In a real implementation, this would integrate with the DataConnection system
                logger.info(f"➕ New data source request: {data['name']}")
                logger.info(f"   URL: {data['url']}")
                logger.info(f"   Type: {data['data_type']}")
                logger.info(f"   Geographies: {data['geography_levels']}")
                
                return jsonify({
                    'success': True,
                    'message': 'Data source request received. It will be processed and added to the system.',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error adding data source: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        # ConnectionManager API endpoints
        @self.app.route('/api/connections')
        def get_connections():
            """Get connections with optional filtering."""
            try:
                if not self.connection_manager:
                    return jsonify({
                        'success': False,
                        'error': 'ConnectionManager not available',
                        'connections': []
                    })
                
                # Get query parameters for filtering
                filters = {}
                for key in ['data_source', 'data_type', 'sub_type', 'geography', 'status']:
                    if request.args.get(key):
                        filters[key] = request.args.get(key)
                
                # Get connections with filters
                connections = self.connection_manager.get_connections_by_filter(filters)
                
                return jsonify({
                    'success': True,
                    'connections': connections,
                    'total_count': len(connections),
                    'filters_applied': filters,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting connections: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/connections/filter-options')
        def get_filter_options():
            """Get available filter options for connections."""
            try:
                if not self.connection_manager:
                    return jsonify({
                        'success': False,
                        'error': 'ConnectionManager not available',
                        'filter_options': {}
                    })
                
                filter_options = self.connection_manager.get_hierarchical_filter_options()
                
                return jsonify({
                    'success': True,
                    'filter_options': filter_options,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting filter options: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/connections/hierarchy')
        def get_connections_hierarchy():
            """Get hierarchical breakdown of connections."""
            try:
                if not self.connection_manager:
                    return jsonify({
                        'success': False,
                        'error': 'ConnectionManager not available',
                        'hierarchy': {}
                    })
                
                hierarchy = self.connection_manager.get_hierarchical_breakdown()
                
                return jsonify({
                    'success': True,
                    'hierarchy': hierarchy,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting hierarchy: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/connections/<connection_id>')
        def get_connection(connection_id):
            """Get specific connection by ID."""
            try:
                if not self.connection_manager:
                    return jsonify({
                        'success': False,
                        'error': 'ConnectionManager not available'
                    })
                
                connection = self.connection_manager.get_connection(connection_id)
                
                if not connection:
                    return jsonify({
                        'success': False,
                        'error': f'Connection {connection_id} not found'
                    })
                
                return jsonify({
                    'success': True,
                    'connection': connection,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting connection {connection_id}: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/connections/complexity')
        def get_complexity_analysis():
            """Get complexity analysis of the connection registry."""
            try:
                if not self.connection_manager:
                    return jsonify({
                        'success': False,
                        'error': 'ConnectionManager not available'
                    })
                
                complexity = self.connection_manager.analyze_complexity()
                
                return jsonify({
                    'success': True,
                    'complexity': complexity,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Error getting complexity analysis: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/discover-connection', methods=['POST'])
        def discover_connection():
            """Discover and validate a new data connection."""
            try:
                if not self.connection_manager:
                    return jsonify({
                        'success': False,
                        'error': 'ConnectionManager not available'
                    })
                
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['name', 'data_source', 'data_type', 'geography', 'url']
                for field in required_fields:
                    if field not in data or not data[field]:
                        return jsonify({
                            'success': False,
                            'error': f'Missing required field: {field}'
                        })
                
                # Create connection metadata
                from connection_manager import ConnectionMetadata
                connection = ConnectionMetadata(
                    id=f"{data['data_source']}_{data['data_type']}_{data['geography']}",
                    name=data['name'],
                    data_source=data['data_source'],
                    data_type=data['data_type'],
                    sub_type=data.get('sub_type', 'default'),
                    geography=data['geography'],
                    update_frequency=data.get('update_frequency', 'monthly'),
                    status='pending',
                    created=datetime.now().isoformat(),
                    last_updated=datetime.now().isoformat(),
                    last_tested=None,
                    test_status='pending',
                    backup_version=None,
                    flexible_metadata={
                        'url': data['url'],
                        'description': data.get('description', ''),
                        'discovered_at': datetime.now().isoformat()
                    }
                )
                
                # Attempt auto-discovery
                discovery_result = self.connection_manager._auto_discover_metadata(connection)
                
                if discovery_result:
                    # Auto-discovery successful
                    connection.flexible_metadata.update(discovery_result)
                    connection.test_status = 'passed'
                    
                    return jsonify({
                        'success': True,
                        'discovery_status': 'auto_discovered',
                        'connection': {
                            'id': connection.id,
                            'name': connection.name,
                            'data_source': connection.data_source,
                            'data_type': connection.data_type,
                            'sub_type': connection.sub_type,
                            'geography': connection.geography,
                            'update_frequency': connection.update_frequency,
                            'flexible_metadata': connection.flexible_metadata
                        },
                        'message': 'Connection auto-discovered successfully. Ready to add to registry.',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    # Auto-discovery failed, return basic validation
                    basic_validation = self.connection_manager._basic_metadata_validation(connection)
                    
                    return jsonify({
                        'success': True,
                        'discovery_status': 'basic_validation',
                        'connection': {
                            'id': connection.id,
                            'name': connection.name,
                            'data_source': connection.data_source,
                            'data_type': connection.data_type,
                            'sub_type': connection.sub_type,
                            'geography': connection.geography,
                            'update_frequency': connection.update_frequency,
                            'flexible_metadata': connection.flexible_metadata
                        },
                        'validation': basic_validation,
                        'message': 'Auto-discovery failed. Basic validation completed. Manual review required.',
                        'timestamp': datetime.now().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"❌ Error discovering connection: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/connections', methods=['POST'])
        def add_connection():
            """Add a new connection to the registry."""
            try:
                if not self.connection_manager:
                    return jsonify({
                        'success': False,
                        'error': 'ConnectionManager not available'
                    })
                
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['name', 'data_source', 'data_type', 'geography']
                for field in required_fields:
                    if field not in data or not data[field]:
                        return jsonify({
                            'success': False,
                            'error': f'Missing required field: {field}'
                        })
                
                # Create connection metadata
                from connection_manager import ConnectionMetadata
                connection = ConnectionMetadata(
                    id=f"{data['data_source']}_{data['data_type']}_{data['geography']}",
                    name=data['name'],
                    data_source=data['data_source'],
                    data_type=data['data_type'],
                    sub_type=data.get('sub_type', 'default'),
                    geography=data['geography'],
                    update_frequency=data.get('update_frequency', 'monthly'),
                    status='active',
                    created=datetime.now().isoformat(),
                    last_updated=datetime.now().isoformat(),
                    last_tested=datetime.now().isoformat(),
                    test_status='passed',
                    backup_version=None,
                    flexible_metadata=data.get('flexible_metadata', {})
                )
                
                # Add connection to registry
                success = self.connection_manager.add_connection(connection, auto_discover=True)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Connection {connection.name} added successfully',
                        'connection_id': connection.id,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to add connection to registry'
                    })
                
            except Exception as e:
                logger.error(f"❌ Error adding connection: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'data_connection_available': DATA_CONNECTION_AVAILABLE and self.data_connection is not None,
                'connection_manager_available': CONNECTION_MANAGER_AVAILABLE and self.connection_manager is not None,
                'timestamp': datetime.now().isoformat()
            })
    
    def run(self):
        """Start the Flask development server."""
        logger.info(f"🌐 Starting frontend server on http://{self.host}:{self.port}")
        logger.info("📊 Available endpoints:")
        logger.info("   GET  /                    - Main frontend interface")
        logger.info("   GET  /api/data-sources    - Get available data sources")
        logger.info("   GET  /api/data/<source_id> - Get data for specific source")
        logger.info("   GET  /api/statistics/<source_id>/<geography> - Get statistics")
        logger.info("   POST /api/add-data-source  - Add new data source")
        logger.info("   GET  /api/health          - Health check")
        logger.info("")
        logger.info("🔗 ConnectionManager API endpoints:")
        logger.info("   GET  /api/connections     - Get connections with filtering")
        logger.info("   GET  /api/connections/filter-options - Get filter options")
        logger.info("   GET  /api/connections/hierarchy - Get hierarchical breakdown")
        logger.info("   GET  /api/connections/<id> - Get specific connection")
        logger.info("   GET  /api/connections/complexity - Get complexity analysis")
        logger.info("   POST /api/discover-connection - Discover new connection")
        logger.info("   POST /api/connections     - Add new connection to registry")
        
        try:
            self.app.run(host=self.host, port=self.port, debug=self.debug)
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            raise

def main():
    """Main function to run the frontend server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='RE Market Tool Frontend Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create and run server
    server = FrontendServer(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
    
    server.run()

if __name__ == '__main__':
    main()

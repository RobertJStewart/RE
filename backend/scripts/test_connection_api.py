#!/usr/bin/env python3
"""
RE Market Tool - Connection Manager API Test
===========================================

Simple Flask API to test the flexible connection management system.
This demonstrates the hierarchical filtering and querying capabilities.

Usage:
    python test_connection_api.py
    # Then visit http://localhost:5001/api/connections
"""

from flask import Flask, jsonify, request
from connection_manager import ConnectionManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize connection manager
connection_manager = ConnectionManager()

@app.route('/api/connections', methods=['GET'])
def get_connections():
    """Get connections with flexible filtering."""
    try:
        # Get query parameters
        filters = {}
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        # Build filters from query parameters
        for key in ['data_source', 'data_type', 'sub_type', 'geography', 'update_frequency', 'status']:
            value = request.args.get(key)
            if value:
                filters[key] = value
        
        # Get connections
        connections = connection_manager.get_connections_by_filter(filters, include_inactive)
        
        return jsonify({
            'success': True,
            'count': len(connections),
            'filters_applied': filters,
            'connections': connections
        })
        
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connections/filter-options', methods=['GET'])
def get_filter_options():
    """Get hierarchical filter options."""
    try:
        options = connection_manager.get_hierarchical_filter_options()
        
        return jsonify({
            'success': True,
            'filter_options': options
        })
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connections/hierarchy', methods=['GET'])
def get_hierarchy():
    """Get hierarchical breakdown of connections."""
    try:
        # Get all active connections
        all_connections = connection_manager.get_connections_by_filter({})
        
        # Build hierarchy
        hierarchy = {}
        
        for conn in all_connections:
            data_source = conn.get('data_source', 'unknown')
            data_type = conn.get('data_type', 'unknown')
            sub_type = conn.get('sub_type', 'unknown')
            geography = conn.get('geography', 'unknown')
            
            if data_source not in hierarchy:
                hierarchy[data_source] = {}
            
            if data_type not in hierarchy[data_source]:
                hierarchy[data_source][data_type] = {}
            
            if sub_type not in hierarchy[data_source][data_type]:
                hierarchy[data_source][data_type][sub_type] = {}
            
            if geography not in hierarchy[data_source][data_type][sub_type]:
                hierarchy[data_source][data_type][sub_type][geography] = []
            
            hierarchy[data_source][data_type][sub_type][geography].append({
                'id': conn.get('id'),
                'name': conn.get('name'),
                'status': conn.get('status')
            })
        
        return jsonify({
            'success': True,
            'hierarchy': hierarchy
        })
        
    except Exception as e:
        logger.error(f"Error getting hierarchy: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connections/complexity', methods=['GET'])
def get_complexity():
    """Get complexity analysis and recommendations."""
    try:
        recommendations = connection_manager.get_complexity_recommendations()
        
        return jsonify({
            'success': True,
            'complexity_analysis': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error getting complexity analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connections/<connection_id>', methods=['GET'])
def get_connection(connection_id):
    """Get a specific connection by ID."""
    try:
        connections = connection_manager.get_connections_by_filter({'id': connection_id})
        
        if not connections:
            return jsonify({
                'success': False,
                'error': f'Connection {connection_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'connection': connections[0]
        })
        
    except Exception as e:
        logger.error(f"Error getting connection {connection_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'total_connections': len(connection_manager.connections),
        'active_connections': len([c for c in connection_manager.connections.values() if c.get('status') == 'active'])
    })

if __name__ == '__main__':
    print("🚀 Starting Connection Manager API Test Server")
    print("📊 Available endpoints:")
    print("   GET /api/connections - Get connections with filtering")
    print("   GET /api/connections/filter-options - Get filter options")
    print("   GET /api/connections/hierarchy - Get hierarchical breakdown")
    print("   GET /api/connections/complexity - Get complexity analysis")
    print("   GET /api/connections/<id> - Get specific connection")
    print("   GET /api/health - Health check")
    print()
    print("🔍 Example queries:")
    print("   http://localhost:5001/api/connections")
    print("   http://localhost:5001/api/connections?data_source=zillow")
    print("   http://localhost:5001/api/connections?data_source=zillow&data_type=zhvi")
    print("   http://localhost:5001/api/connections?geography=zip")
    print("   http://localhost:5001/api/connections/filter-options")
    print("   http://localhost:5001/api/connections/hierarchy")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=True)

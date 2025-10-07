#!/usr/bin/env python3
"""
RE Market Tool - Flexible Connection Manager
===========================================

This module provides a flexible data connection management system that supports:
- Dynamic addition/removal of connections
- Hierarchical filtering and querying
- Flexible metadata structure
- Auto-discovery with fallback
- Complexity monitoring with database migration suggestions
- Versioning with auto-revert on test failure

Usage:
    from connection_manager import ConnectionManager
    manager = ConnectionManager()
    connections = manager.get_connections_by_filter({"data_source": "zillow"})
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetadata:
    """Flexible metadata structure for data connections."""
    id: str
    name: str
    data_source: str
    data_type: str
    sub_type: Optional[str] = None
    geography: str = ""
    update_frequency: str = "monthly"
    status: str = "active"
    created: str = ""
    last_updated: str = ""
    last_tested: str = ""
    test_status: str = "unknown"
    backup_version: Optional[Dict] = None
    flexible_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.flexible_metadata is None:
            self.flexible_metadata = {}
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = self.created

@dataclass
class RegistryMetadata:
    """Registry-level metadata for monitoring and management."""
    timestamp: str
    version: str
    description: str
    schema_version: str
    total_connections: int
    active_connections: int
    inactive_connections: int
    file_size_bytes: int
    complexity_score: float
    last_complexity_check: str

class ConnectionManager:
    """
    Flexible data connection management system.
    
    Features:
    - Dynamic connection addition/removal
    - Hierarchical filtering and querying
    - Flexible metadata structure
    - Auto-discovery with fallback
    - Complexity monitoring
    - Versioning with auto-revert
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize the connection manager.
        
        Args:
            registry_path: Path to the connections registry file
        """
        if registry_path is None:
            # Default to backend directory
            backend_path = Path(__file__).parent.parent
            registry_path = backend_path / "dataconnections.json"
        
        self.registry_path = registry_path
        self.backup_path = registry_path.with_suffix('.json.backup')
        self.registry_data = None
        self.registry_metadata = None
        self.connections = {}
        
        # Load existing registry or create new one
        self._load_registry()
        
        logger.info(f"ConnectionManager initialized with registry: {self.registry_path}")
    
    def _load_registry(self) -> None:
        """Load the connections registry from file."""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    self.registry_data = json.load(f)
                
                # Extract registry metadata
                self.registry_metadata = RegistryMetadata(**self.registry_data.get('registry_metadata', {}))
                
                # Extract connections
                self.connections = self.registry_data.get('connections', {})
                
                logger.info(f"Loaded {len(self.connections)} connections from registry")
            else:
                # Create new registry
                self._create_new_registry()
                
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            # Try to load backup
            self._load_backup()
    
    def _create_new_registry(self) -> None:
        """Create a new empty registry."""
        self.registry_metadata = RegistryMetadata(
            timestamp=datetime.now().isoformat(),
            version="1.0",
            description="Flexible Data Connection Registry for RE Market Tool",
            schema_version="1.0",
            total_connections=0,
            active_connections=0,
            inactive_connections=0,
            file_size_bytes=0,
            complexity_score=0.0,
            last_complexity_check=datetime.now().isoformat()
        )
        
        self.connections = {}
        self.registry_data = {
            'registry_metadata': asdict(self.registry_metadata),
            'connections': self.connections
        }
        
        self._save_registry()
        logger.info("Created new empty registry")
    
    def _load_backup(self) -> None:
        """Load registry from backup file."""
        try:
            if self.backup_path.exists():
                with open(self.backup_path, 'r') as f:
                    self.registry_data = json.load(f)
                
                self.registry_metadata = RegistryMetadata(**self.registry_data.get('registry_metadata', {}))
                self.connections = self.registry_data.get('connections', {})
                
                logger.warning(f"Loaded registry from backup: {self.backup_path}")
            else:
                logger.error("No backup file available, creating new registry")
                self._create_new_registry()
                
        except Exception as e:
            logger.error(f"Failed to load backup: {e}")
            self._create_new_registry()
    
    def _save_registry(self) -> None:
        """Save the registry to file with backup."""
        try:
            # Create backup of current file
            if self.registry_path.exists():
                shutil.copy2(self.registry_path, self.backup_path)
            
            # Update registry metadata
            self.registry_metadata.timestamp = datetime.now().isoformat()
            self.registry_metadata.total_connections = len(self.connections)
            self.registry_metadata.active_connections = len([c for c in self.connections.values() if c.get('status') == 'active'])
            self.registry_metadata.inactive_connections = len([c for c in self.connections.values() if c.get('status') == 'inactive'])
            
            # Calculate file size and complexity
            self._update_complexity_metrics()
            
            # Prepare data for saving
            self.registry_data = {
                'registry_metadata': asdict(self.registry_metadata),
                'connections': self.connections
            }
            
            # Save to file
            with open(self.registry_path, 'w') as f:
                json.dump(self.registry_data, f, indent=2)
            
            logger.info(f"Registry saved successfully: {self.registry_path}")
            
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            raise
    
    def _update_complexity_metrics(self) -> None:
        """Update file size and complexity metrics."""
        try:
            # Calculate file size
            if self.registry_path.exists():
                self.registry_metadata.file_size_bytes = self.registry_path.stat().st_size
            
            # Calculate complexity score
            complexity_factors = {
                'total_connections': len(self.connections),
                'file_size_mb': self.registry_metadata.file_size_bytes / (1024 * 1024),
                'flexible_metadata_fields': sum(len(conn.get('flexible_metadata', {})) for conn in self.connections.values()),
                'nested_structures': sum(1 for conn in self.connections.values() 
                                       if any(isinstance(v, (dict, list)) for v in conn.get('flexible_metadata', {}).values()))
            }
            
            # Simple complexity scoring (can be enhanced)
            self.registry_metadata.complexity_score = (
                complexity_factors['total_connections'] * 0.1 +
                complexity_factors['file_size_mb'] * 0.3 +
                complexity_factors['flexible_metadata_fields'] * 0.05 +
                complexity_factors['nested_structures'] * 0.2
            )
            
            self.registry_metadata.last_complexity_check = datetime.now().isoformat()
            
            # Check if database migration is recommended
            if self.registry_metadata.complexity_score > 50.0:
                logger.warning(f"High complexity score ({self.registry_metadata.complexity_score:.1f}). Consider migrating to database.")
            
        except Exception as e:
            logger.error(f"Failed to update complexity metrics: {e}")
    
    def add_connection(self, connection: ConnectionMetadata, auto_discover: bool = True) -> bool:
        """
        Add a new connection to the registry.
        
        Args:
            connection: Connection metadata to add
            auto_discover: Whether to attempt auto-discovery of metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if connection already exists
            if connection.id in self.connections:
                logger.warning(f"Connection {connection.id} already exists")
                return False
            
            # Auto-discover metadata if requested
            if auto_discover:
                discovered_metadata = self._auto_discover_metadata(connection)
                if discovered_metadata:
                    connection.flexible_metadata.update(discovered_metadata)
            
            # Add to connections
            self.connections[connection.id] = asdict(connection)
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Added connection: {connection.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add connection {connection.id}: {e}")
            return False
    
    def update_connection(self, connection_id: str, updates: Dict[str, Any], test_after_update: bool = True) -> bool:
        """
        Update an existing connection.
        
        Args:
            connection_id: ID of connection to update
            updates: Dictionary of fields to update
            test_after_update: Whether to test connection after update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if connection_id not in self.connections:
                logger.error(f"Connection {connection_id} not found")
                return False
            
            # Create backup of current connection
            current_connection = self.connections[connection_id].copy()
            self.connections[connection_id]['backup_version'] = current_connection
            
            # Apply updates
            for key, value in updates.items():
                if key == 'flexible_metadata' and isinstance(value, dict):
                    # Merge flexible metadata
                    current_flexible = self.connections[connection_id].get('flexible_metadata', {})
                    current_flexible.update(value)
                    self.connections[connection_id]['flexible_metadata'] = current_flexible
                else:
                    self.connections[connection_id][key] = value
            
            # Update timestamp
            self.connections[connection_id]['last_updated'] = datetime.now().isoformat()
            
            # Test connection if requested
            if test_after_update:
                test_result = self._test_connection(connection_id)
                if not test_result:
                    # Revert on test failure
                    logger.warning(f"Test failed for {connection_id}, reverting changes")
                    self.connections[connection_id] = current_connection
                    return False
                else:
                    self.connections[connection_id]['test_status'] = 'passed'
                    self.connections[connection_id]['last_tested'] = datetime.now().isoformat()
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Updated connection: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update connection {connection_id}: {e}")
            return False
    
    def remove_connection(self, connection_id: str, delete_data_files: bool = True) -> bool:
        """
        Remove a connection (mark as inactive and optionally delete data files).
        
        Args:
            connection_id: ID of connection to remove
            delete_data_files: Whether to delete associated data files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if connection_id not in self.connections:
                logger.error(f"Connection {connection_id} not found")
                return False
            
            # Mark as inactive
            self.connections[connection_id]['status'] = 'inactive'
            self.connections[connection_id]['last_updated'] = datetime.now().isoformat()
            
            # Delete data files if requested
            if delete_data_files:
                self._delete_connection_data_files(connection_id)
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Removed connection: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove connection {connection_id}: {e}")
            return False
    
    def get_connections_by_filter(self, filters: Dict[str, Any], include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get connections matching the specified filters.
        
        Args:
            filters: Dictionary of field:value filters
            include_inactive: Whether to include inactive connections
            
        Returns:
            List of matching connections
        """
        try:
            results = []
            
            for conn_id, conn_data in self.connections.items():
                # Skip inactive connections unless requested
                if not include_inactive and conn_data.get('status') == 'inactive':
                    continue
                
                # Check if connection matches all filters
                matches = True
                for filter_key, filter_value in filters.items():
                    if filter_key == 'flexible_metadata':
                        # Special handling for flexible metadata filters
                        if not self._matches_flexible_metadata(conn_data.get('flexible_metadata', {}), filter_value):
                            matches = False
                            break
                    else:
                        # Direct field matching
                        if conn_data.get(filter_key) != filter_value:
                            matches = False
                            break
                
                if matches:
                    results.append(conn_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to filter connections: {e}")
            return []
    
    def get_hierarchical_filter_options(self) -> Dict[str, List[str]]:
        """
        Get hierarchical filter options for the UI.
        
        Returns:
            Dictionary of filter levels and available options
        """
        try:
            filter_options = {
                'data_sources': set(),
                'data_types': set(),
                'sub_types': set(),
                'geographies': set(),
                'update_frequencies': set(),
                'statuses': set()
            }
            
            for conn_data in self.connections.values():
                if conn_data.get('status') == 'active':
                    filter_options['data_sources'].add(conn_data.get('data_source', ''))
                    filter_options['data_types'].add(conn_data.get('data_type', ''))
                    filter_options['sub_types'].add(conn_data.get('sub_type', ''))
                    filter_options['geographies'].add(conn_data.get('geography', ''))
                    filter_options['update_frequencies'].add(conn_data.get('update_frequency', ''))
                    filter_options['statuses'].add(conn_data.get('status', ''))
            
            # Convert sets to sorted lists
            return {k: sorted(list(v)) for k, v in filter_options.items()}
            
        except Exception as e:
            logger.error(f"Failed to get hierarchical filter options: {e}")
            return {}
    
    def _auto_discover_metadata(self, connection: ConnectionMetadata) -> Optional[Dict[str, Any]]:
        """
        Auto-discover metadata for a connection.
        
        Args:
            connection: Connection to discover metadata for
            
        Returns:
            Discovered metadata or None if discovery fails
        """
        try:
            # Import the existing discovery functionality
            from data_connection import REDataConnection
            
            # Try dynamic discovery first
            re_conn = REDataConnection()
            discovery_result = re_conn.discover_columns(
                connection.data_source,
                connection.data_type,
                connection.sub_type,
                connection.geography
            )
            
            if discovery_result.success:
                return {
                    'discovered_columns': discovery_result.discovered_columns,
                    'critical_columns': discovery_result.critical_columns,
                    'date_columns': discovery_result.date_columns,
                    'discovery_confidence': discovery_result.confidence_score,
                    'discovery_method': 'dynamic_abstraction'
                }
            else:
                # Fallback to basic validation
                return self._basic_metadata_validation(connection)
                
        except Exception as e:
            logger.warning(f"Auto-discovery failed for {connection.id}: {e}")
            return self._basic_metadata_validation(connection)
    
    def _basic_metadata_validation(self, connection: ConnectionMetadata) -> Dict[str, Any]:
        """
        Basic metadata validation as fallback.
        
        Args:
            connection: Connection to validate
            
        Returns:
            Basic metadata
        """
        return {
            'discovery_method': 'basic_validation',
            'discovery_confidence': 0.5,
            'validation_status': 'basic',
            'requires_manual_review': True
        }
    
    def _test_connection(self, connection_id: str) -> bool:
        """
        Test a connection to ensure it's working.
        
        Args:
            connection_id: ID of connection to test
            
        Returns:
            bool: True if test passes, False otherwise
        """
        try:
            # Basic connection test - can be enhanced
            conn_data = self.connections.get(connection_id)
            if not conn_data:
                return False
            
            # For now, just check if required fields are present
            required_fields = ['data_source', 'data_type', 'geography', 'update_frequency']
            for field in required_fields:
                if not conn_data.get(field):
                    logger.warning(f"Missing required field {field} for {connection_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed for {connection_id}: {e}")
            return False
    
    def _delete_connection_data_files(self, connection_id: str) -> None:
        """
        Delete data files associated with a connection.
        
        Args:
            connection_id: ID of connection to delete files for
        """
        try:
            # Define data file patterns to delete
            data_patterns = [
                f"{connection_id}_raw.csv",
                f"{connection_id}_processed.csv",
                f"{connection_id}_master.csv",
                f"{connection_id}_metadata.json"
            ]
            
            # Define directories to search
            backend_path = Path(__file__).parent.parent
            search_dirs = [
                backend_path / "data" / "raw",
                backend_path / "data" / "processed",
                backend_path / "aggregations",
                backend_path / "statistics"
            ]
            
            deleted_files = []
            for search_dir in search_dirs:
                if search_dir.exists():
                    for pattern in data_patterns:
                        file_path = search_dir / pattern
                        if file_path.exists():
                            file_path.unlink()
                            deleted_files.append(str(file_path))
            
            if deleted_files:
                logger.info(f"Deleted {len(deleted_files)} data files for {connection_id}")
            else:
                logger.info(f"No data files found to delete for {connection_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete data files for {connection_id}: {e}")
    
    def _matches_flexible_metadata(self, flexible_metadata: Dict[str, Any], filter_value: Any) -> bool:
        """
        Check if flexible metadata matches a filter value.
        
        Args:
            flexible_metadata: Flexible metadata to check
            filter_value: Filter value to match against
            
        Returns:
            bool: True if matches, False otherwise
        """
        try:
            if isinstance(filter_value, dict):
                # Nested filter - check if all key-value pairs match
                for key, value in filter_value.items():
                    if flexible_metadata.get(key) != value:
                        return False
                return True
            else:
                # Simple value match - check if any flexible metadata value matches
                return filter_value in flexible_metadata.values()
                
        except Exception as e:
            logger.error(f"Failed to match flexible metadata: {e}")
            return False
    
    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific connection by ID.
        
        Args:
            connection_id: The ID of the connection to retrieve
            
        Returns:
            Connection data or None if not found
        """
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                return {
                    'id': connection.id,
                    'name': connection.name,
                    'data_source': connection.data_source,
                    'data_type': connection.data_type,
                    'sub_type': connection.sub_type,
                    'geography': connection.geography,
                    'update_frequency': connection.update_frequency,
                    'status': connection.status,
                    'created': connection.created,
                    'last_updated': connection.last_updated,
                    'last_tested': connection.last_tested,
                    'test_status': connection.test_status,
                    'flexible_metadata': connection.flexible_metadata
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get connection {connection_id}: {e}")
            return None
    
    def get_hierarchical_breakdown(self) -> Dict[str, Any]:
        """
        Get hierarchical breakdown of connections.
        
        Returns:
            Dictionary with hierarchical structure
        """
        try:
            breakdown = {
                'by_data_source': {},
                'by_data_type': {},
                'by_geography': {},
                'by_status': {}
            }
            
            for connection in self.connections.values():
                # By data source
                if connection.data_source not in breakdown['by_data_source']:
                    breakdown['by_data_source'][connection.data_source] = 0
                breakdown['by_data_source'][connection.data_source] += 1
                
                # By data type
                if connection.data_type not in breakdown['by_data_type']:
                    breakdown['by_data_type'][connection.data_type] = 0
                breakdown['by_data_type'][connection.data_type] += 1
                
                # By geography
                if connection.geography not in breakdown['by_geography']:
                    breakdown['by_geography'][connection.geography] = 0
                breakdown['by_geography'][connection.geography] += 1
                
                # By status
                if connection.status not in breakdown['by_status']:
                    breakdown['by_status'][connection.status] = 0
                breakdown['by_status'][connection.status] += 1
            
            return breakdown
        except Exception as e:
            logger.error(f"Failed to get hierarchical breakdown: {e}")
            return {}
    
    def analyze_complexity(self) -> Dict[str, Any]:
        """
        Analyze the complexity of the connection registry.
        
        Returns:
            Dictionary with complexity analysis
        """
        try:
            return {
                'total_connections': len(self.connections),
                'active_connections': len([c for c in self.connections.values() if c.status == 'active']),
                'inactive_connections': len([c for c in self.connections.values() if c.status == 'inactive']),
                'file_size_bytes': self.registry_metadata.file_size_bytes,
                'file_size_mb': self.registry_metadata.file_size_bytes / (1024 * 1024),
                'complexity_score': self.registry_metadata.complexity_score,
                'last_complexity_check': self.registry_metadata.last_complexity_check,
                'recommendations': self.get_complexity_recommendations()
            }
        except Exception as e:
            logger.error(f"Failed to analyze complexity: {e}")
            return {}
    
    def get_complexity_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations based on current complexity.
        
        Returns:
            Dictionary with complexity analysis and recommendations
        """
        try:
            recommendations = {
                'current_complexity_score': self.registry_metadata.complexity_score,
                'file_size_mb': self.registry_metadata.file_size_bytes / (1024 * 1024),
                'total_connections': self.registry_metadata.total_connections,
                'recommendations': []
            }
            
            # Generate recommendations based on complexity
            if self.registry_metadata.complexity_score > 50.0:
                recommendations['recommendations'].append({
                    'type': 'database_migration',
                    'priority': 'high',
                    'message': 'Consider migrating to SQLite database for better performance and querying capabilities',
                    'threshold_exceeded': 'complexity_score'
                })
            
            if self.registry_metadata.file_size_bytes > 10 * 1024 * 1024:  # 10MB
                recommendations['recommendations'].append({
                    'type': 'file_size',
                    'priority': 'medium',
                    'message': 'Registry file is getting large, consider database migration',
                    'threshold_exceeded': 'file_size'
                })
            
            if self.registry_metadata.total_connections > 100:
                recommendations['recommendations'].append({
                    'type': 'connection_count',
                    'priority': 'medium',
                    'message': 'High number of connections, consider database for better management',
                    'threshold_exceeded': 'connection_count'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get complexity recommendations: {e}")
            return {'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    # Initialize connection manager
    manager = ConnectionManager()
    
    # Get all connections
    all_connections = manager.get_connections_by_filter({})
    print(f"Total connections: {len(all_connections)}")
    
    # Get Zillow connections
    zillow_connections = manager.get_connections_by_filter({"data_source": "zillow"})
    print(f"Zillow connections: {len(zillow_connections)}")
    
    # Get hierarchical filter options
    filter_options = manager.get_hierarchical_filter_options()
    print(f"Available data sources: {filter_options.get('data_sources', [])}")
    
    # Get complexity recommendations
    recommendations = manager.get_complexity_recommendations()
    print(f"Complexity score: {recommendations.get('current_complexity_score', 0):.1f}")

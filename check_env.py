#!/usr/bin/env python3
"""
RE Market Tool - Environment Validation Script
============================================
Validates that the development environment is properly set up
"""

import sys
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print(f"❌ Python {version.major}.{version.minor} not supported. Need Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_package(package_name, min_version=None):
    """Check if package is installed and version"""
    try:
        module = importlib.import_module(package_name)
        if hasattr(module, '__version__'):
            version = module.__version__
            print(f"✅ {package_name}: {version}")
            if min_version and version < min_version:
                print(f"⚠️  {package_name} version {version} is below recommended {min_version}")
                return False
            return True
        else:
            print(f"✅ {package_name}: installed")
            return True
    except ImportError:
        print(f"❌ {package_name}: not installed")
        return False

def check_file_structure():
    """Check if required directories exist"""
    required_dirs = [
        "backend/data/raw",
        "backend/data/processed", 
        "backend/data/coordinates",
        "backend/aggregations/regions",
        "backend/aggregations/state_regions",
        "backend/aggregations/states",
        "backend/aggregations/zipcodes",
        "backend/statistics",
        "backend/logs",
        "frontend/overview",
        "frontend/timeseries",
        "frontend/shared/components",
        "frontend/shared/utils",
        "config"
    ]
    
    all_good = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory: {directory}")
        else:
            print(f"❌ Missing directory: {directory}")
            all_good = False
    
    return all_good

def check_config_files():
    """Check if configuration files exist"""
    config_files = [
        "config/pipeline_config.json",
        "config/geographic.json",
        "config/statistical.json"
    ]
    
    all_good = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ Config: {config_file}")
        else:
            print(f"⚠️  Missing config: {config_file} (will be created)")
            all_good = False
    
    return all_good

def check_environment_variables():
    """Check if required environment variables are set"""
    # Add any required environment variables here
    required_env_vars = []
    
    all_good = True
    for env_var in required_env_vars:
        if env_var in os.environ:
            print(f"✅ Environment variable: {env_var}")
        else:
            print(f"⚠️  Environment variable not set: {env_var}")
            all_good = False
    
    return all_good

def main():
    """Run complete environment validation"""
    print("🔍 Validating RE Market Tool environment...")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check Python version
    print("\n🐍 Python Version Check:")
    if not check_python_version():
        all_checks_passed = False
    
    # Check required packages
    print("\n📦 Package Dependencies:")
    required_packages = [
        ('pandas', '2.0.0'),
        ('numpy', '1.20.0'),
        ('duckdb', '1.0.0'),
        ('geopandas', '0.13.0'),
        ('shapely', '2.0.0'),
        ('h3', '3.7.0'),
        ('requests', '2.25.0'),
        ('pyarrow', '10.0.0')
    ]
    
    for package, min_version in required_packages:
        if not check_package(package, min_version):
            all_checks_passed = False
    
    # Check file structure
    print("\n📁 File Structure Check:")
    if not check_file_structure():
        all_checks_passed = False
    
    # Check configuration files
    print("\n⚙️ Configuration Files:")
    if not check_config_files():
        all_checks_passed = False
    
    # Check environment variables
    print("\n🌍 Environment Variables:")
    if not check_environment_variables():
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 Environment validation passed!")
        print("✅ All systems ready for development")
        print("\n💡 Next steps:")
        print("   1. Run the ETL pipeline: python backend/scripts/main_etl_pipeline.py")
        print("   2. Start the frontend: python -m http.server 8080")
        print("   3. Open http://localhost:8080 in your browser")
    else:
        print("❌ Environment validation failed!")
        print("💡 Fix the issues above and run this script again")
        print("\n🔧 Common fixes:")
        print("   - Run 'pip install -r requirements.txt' to install missing packages")
        print("   - Run 'mkdir -p backend/data/raw' to create missing directories")
        print("   - Check that you're in the correct project directory")
    
    return all_checks_passed

if __name__ == "__main__":
    import os
    main()

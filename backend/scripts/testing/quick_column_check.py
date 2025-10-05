#!/usr/bin/env python3
"""
Quick Zillow Column Check
=========================

Quick script to check the first few rows of Zillow files to see column structure.
"""

import pandas as pd
import requests
from io import StringIO

def check_zhvi_columns():
    """Check ZHVI columns."""
    print("🔍 Checking ZHVI columns...")
    url = "https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_Zhvi_AllHomes.csv"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Read just the first few rows to get column names
        df = pd.read_csv(StringIO(response.text), nrows=5)
        
        print(f"✅ ZHVI columns ({len(df.columns)} total):")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. {col}")
        
        # Check for our expected critical columns
        expected = ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank']
        missing = [col for col in expected if col not in df.columns]
        present = [col for col in expected if col in df.columns]
        
        print(f"\n📊 Critical columns analysis:")
        print(f"   Present: {present}")
        if missing:
            print(f"   Missing: {missing}")
        else:
            print(f"   ✅ All critical columns present!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking ZHVI: {e}")
        return False

def check_zori_columns():
    """Check ZORI columns."""
    print("\n🔍 Checking ZORI columns...")
    url = "https://files.zillowstatic.com/research/public_csvs/zori/Zip_ZORI_AllHomesPlusMultifamily.csv"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Read just the first few rows to get column names
        df = pd.read_csv(StringIO(response.text), nrows=5)
        
        print(f"✅ ZORI columns ({len(df.columns)} total):")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. {col}")
        
        # Check for our expected critical columns
        expected = ['RegionID', 'RegionName', 'StateName', 'Metro', 'CountyName', 'SizeRank']
        missing = [col for col in expected if col not in df.columns]
        present = [col for col in expected if col in df.columns]
        
        print(f"\n📊 Critical columns analysis:")
        print(f"   Present: {present}")
        if missing:
            print(f"   Missing: {missing}")
        else:
            print(f"   ✅ All critical columns present!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking ZORI: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Zillow Column Check")
    print("=" * 40)
    
    zhvi_success = check_zhvi_columns()
    zori_success = check_zori_columns()
    
    print(f"\n📋 Summary:")
    print(f"   ZHVI: {'✅' if zhvi_success else '❌'}")
    print(f"   ZORI: {'✅' if zori_success else '❌'}")

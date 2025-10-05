#!/usr/bin/env python3
"""
Find Zillow Data URLs
=====================

Script to find working Zillow data URLs and check their column structure.
"""

import requests
import pandas as pd
from io import StringIO

def test_url(url, name):
    """Test a URL and return column info if successful."""
    print(f"🔍 Testing {name}: {url}")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Try to read as CSV
            df = pd.read_csv(StringIO(response.text), nrows=5)
            print(f"✅ {name} - Found {len(df.columns)} columns")
            print(f"   Columns: {list(df.columns)[:10]}...")  # Show first 10 columns
            return True, list(df.columns)
        else:
            print(f"❌ {name} - HTTP {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ {name} - Error: {str(e)[:50]}...")
        return False, []

def main():
    """Test various Zillow data URLs."""
    print("🚀 Searching for Zillow Data URLs")
    print("=" * 50)
    
    # Common Zillow data URL patterns
    urls_to_test = [
        ("ZHVI All Homes", "https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_Zhvi_AllHomes.csv"),
        ("ZHVI All Homes (Alt)", "https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_Zhvi_AllHomesPlusMultifamily.csv"),
        ("ZORI All Homes", "https://files.zillowstatic.com/research/public_csvs/zori/Zip_ZORI_AllHomesPlusMultifamily.csv"),
        ("ZHVI Metro", "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_Zhvi_AllHomes.csv"),
        ("ZORI Metro", "https://files.zillowstatic.com/research/public_csvs/zori/Metro_ZORI_AllHomesPlusMultifamily.csv"),
        ("ZHVI State", "https://files.zillowstatic.com/research/public_csvs/zhvi/State_Zhvi_AllHomes.csv"),
        ("ZORI State", "https://files.zillowstatic.com/research/public_csvs/zori/State_ZORI_AllHomesPlusMultifamily.csv"),
    ]
    
    working_urls = []
    
    for name, url in urls_to_test:
        success, columns = test_url(url, name)
        if success:
            working_urls.append((name, url, columns))
        print()
    
    print("📋 SUMMARY")
    print("=" * 50)
    if working_urls:
        print(f"✅ Found {len(working_urls)} working URLs:")
        for name, url, columns in working_urls:
            print(f"   {name}: {url}")
            print(f"      Columns: {len(columns)}")
    else:
        print("❌ No working URLs found")
        print("💡 Suggestion: Check Zillow's research page for current data URLs")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Main Data Acquisition Script for PHM Health Inequalities Tool.

This script orchestrates the fetching of all data sources:
1. OHID Fingertips API - Health indicators
2. MHCLG IMD 2019 - Deprivation scores
3. ONS/Nomis - Socioeconomic data (Census 2021)

Usage:
    python data_fetch.py --fetch-all
    python data_fetch.py --fetch-imd
    python data_fetch.py --fetch-fingertips --indicators life_expectancy_birth smoking_prevalence
    python data_fetch.py --test
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_acquisition.fingertips_api import FingertipsAPI
from data_acquisition.imd_fetcher import IMDFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_fetch.log')
    ]
)
logger = logging.getLogger(__name__)


class DataFetchOrchestrator:
    """
    Orchestrates data acquisition from multiple sources.
    
    Coordinates fetching of health indicators, deprivation data,
    and geographic lookups for the PHM dashboard.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            data_dir: Root directory for data storage
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize fetchers
        self.fingertips = FingertipsAPI()
        self.imd = IMDFetcher(data_dir=self.data_dir / "raw")
        
        logger.info(f"Data directory: {self.data_dir}")
    
    def fetch_imd_data(self, save_to_db: bool = True) -> dict:
        """
        Fetch Index of Multiple Deprivation 2019 data.
        
        Args:
            save_to_db: Whether to save processed data to database
            
        Returns:
            Dictionary with fetch results and metadata
        """
        logger.info("=" * 60)
        logger.info("FETCHING IMD 2019 DATA")
        logger.info("=" * 60)
        
        try:
            # Fetch combined IMD data
            imd_df = self.imd.get_combined_imd_data()
            
            # Save to parquet for efficient storage
            self.imd.save_to_parquet(imd_df, "imd2019_clean.parquet")
            
            # Get Core 20% areas
            core20 = self.imd.get_core20_areas(imd_df)
            
            # Get LA summary
            la_summary = self.imd.get_summary_by_la(imd_df)
            
            result = {
                'success': True,
                'lsoa_count': len(imd_df),
                'core20_count': len(core20),
                'la_count': len(la_summary),
                'quintile_distribution': imd_df['imd_quintile'].value_counts().to_dict(),
                'files_created': [
                    str(self.data_dir / "processed" / "imd2019_clean.parquet")
                ]
            }
            
            logger.info(f"✓ IMD data fetch complete: {result['lsoa_count']} LSOAs")
            return result
            
        except Exception as e:
            logger.error(f"✗ IMD data fetch failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def fetch_fingertips_data(
        self,
        indicators: Optional[List[str]] = None,
        area_type_id: int = 7,
        save_raw: bool = True
    ) -> dict:
        """
        Fetch health indicators from OHID Fingertips API.
        
        Args:
            indicators: List of indicator keys to fetch, or None for key indicators
            area_type_id: Geographic level (7=LTLA, 6=UTLA, 302=LSOA, 15=ICB)
            save_raw: Whether to save raw data to CSV
            
        Returns:
            Dictionary with fetch results
        """
        logger.info("=" * 60)
        logger.info("FETCHING FINGERTIPS HEALTH DATA")
        logger.info("=" * 60)
        
        try:
            # Determine which indicators to fetch
            if indicators is None:
                # Fetch key indicators for Core20PLUS5 analysis
                indicator_list = [
                    'life_expectancy_birth',
                    'smoking_prevalence',
                    'hypertension_prevalence',
                    'cancer_emergency_presentations',
                    'severe_mental_illness',
                    'copd_prevalence',
                    'maternity_early_access',
                ]
            else:
                indicator_list = indicators
            
            # Map to indicator IDs
            indicator_ids = [
                FingertipsAPI.KEY_INDICATORS[k]
                for k in indicator_list
                if k in FingertipsAPI.KEY_INDICATORS
            ]
            
            logger.info(f"Fetching {len(indicator_ids)} indicators for area type {area_type_id}")
            
            # Fetch data
            df = self.fingertips.get_data_for_multiple_indicators(
                indicator_ids=indicator_ids,
                area_type_id=area_type_id,
                parent_area_code="E92000001"  # England
            )
            
            # Save raw data
            if save_raw and len(df) > 0:
                output_file = self.data_dir / "raw" / f"fingertips_area{area_type_id}.csv"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_file, index=False)
                logger.info(f"Saved raw data: {output_file}")
            
            # Get unique indicators fetched
            unique_indicators = df['Indicator ID'].unique().tolist() if 'Indicator ID' in df.columns else []
            
            result = {
                'success': True,
                'record_count': len(df),
                'indicator_count': len(unique_indicators),
                'indicators_fetched': unique_indicators,
                'area_type_id': area_type_id,
            }
            
            logger.info(f"✓ Fingertips data fetch complete: {result['record_count']} records")
            return result
            
        except Exception as e:
            logger.error(f"✗ Fingertips data fetch failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def fetch_all(self) -> dict:
        """
        Fetch all data sources.
        
        Returns:
            Dictionary with results from all fetch operations
        """
        logger.info("=" * 60)
        logger.info("FETCHING ALL DATA SOURCES")
        logger.info("=" * 60)
        
        results = {
            'imd': self.fetch_imd_data(),
            'fingertips_ltla': self.fetch_fingertips_data(area_type_id=7),  # LTLA
            'fingertips_icb': self.fetch_fingertips_data(area_type_id=15),   # ICB
        }
        
        # Overall success if all succeeded
        results['overall_success'] = all(
            r.get('success', False) for r in results.values() 
            if isinstance(r, dict)
        )
        
        logger.info("=" * 60)
        logger.info(f"ALL DATA FETCH COMPLETE - Success: {results['overall_success']}")
        logger.info("=" * 60)
        
        return results
    
    def test_connections(self) -> dict:
        """
        Test all data source connections without downloading full datasets.
        
        Returns:
            Dictionary with test results
        """
        logger.info("=" * 60)
        logger.info("TESTING DATA SOURCE CONNECTIONS")
        logger.info("=" * 60)
        
        results = {
            'fingertips_api': {'success': False},
            'imd_gov_uk': {'success': False},
        }
        
        # Test 1: Fingertips API
        logger.info("\n1. Testing OHID Fingertips API...")
        try:
            area_types = self.fingertips.get_area_types()
            results['fingertips_api'] = {
                'success': True,
                'area_types_count': len(area_types),
                'sample_areas': area_types[['Id', 'Name']].head(3).to_dict('records')
            }
            logger.info(f"   ✓ Connected - {len(area_types)} area types available")
        except Exception as e:
            results['fingertips_api']['error'] = str(e)
            logger.error(f"   ✗ Connection failed: {e}")
        
        # Test 2: IMD data source
        logger.info("\n2. Testing IMD 2019 data source...")
        try:
            import requests
            response = requests.head(self.imd.GOV_UK_IMD_URL, timeout=10)
            results['imd_gov_uk'] = {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'content_length': response.headers.get('content-length')
            }
            if response.status_code == 200:
                size_mb = int(response.headers.get('content-length', 0)) / (1024 * 1024)
                logger.info(f"   ✓ Accessible - File size: {size_mb:.1f} MB")
            else:
                logger.warning(f"   ⚠ Status code: {response.status_code}")
        except Exception as e:
            results['imd_gov_uk']['error'] = str(e)
            logger.error(f"   ✗ Connection failed: {e}")
        
        # Overall status
        results['all_connected'] = all(r['success'] for r in results.values() if isinstance(r, dict))
        
        logger.info("\n" + "=" * 60)
        logger.info(f"CONNECTION TEST COMPLETE - All connected: {results['all_connected']}")
        logger.info("=" * 60)
        
        return results
    
    def print_status(self, results: dict):
        """Print a formatted status report."""
        print("\n" + "=" * 60)
        print("DATA FETCH STATUS REPORT")
        print("=" * 60)
        
        for source, result in results.items():
            if source == 'overall_success':
                continue
                
            print(f"\n{source.upper()}:")
            if isinstance(result, dict):
                if result.get('success'):
                    print(f"  ✓ Success")
                    for key, value in result.items():
                        if key not in ['success', 'error']:
                            print(f"    - {key}: {value}")
                else:
                    print(f"  ✗ Failed")
                    if 'error' in result:
                        print(f"    - Error: {result['error']}")
        
        if 'overall_success' in results:
            print("\n" + "=" * 60)
            print(f"OVERALL: {'✓ SUCCESS' if results['overall_success'] else '✗ FAILED'}")
            print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Fetch data for PHM Health Inequalities Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --test                    Test all connections
  %(prog)s --fetch-all               Fetch all data sources
  %(prog)s --fetch-imd               Fetch only IMD 2019 data
  %(prog)s --fetch-fingertips        Fetch Fingertips health indicators
  %(prog)s --fetch-fingertips --indicators life_expectancy_birth smoking_prevalence
        """
    )
    
    parser.add_argument('--test', action='store_true',
                       help='Test connections without downloading data')
    parser.add_argument('--fetch-all', action='store_true',
                       help='Fetch all data sources')
    parser.add_argument('--fetch-imd', action='store_true',
                       help='Fetch IMD 2019 data only')
    parser.add_argument('--fetch-fingertips', action='store_true',
                       help='Fetch Fingertips health indicators')
    parser.add_argument('--indicators', nargs='+',
                       help='Specific indicator keys to fetch')
    parser.add_argument('--area-type', type=int, default=7,
                       help='Area type ID (7=LTLA, 6=UTLA, 302=LSOA, 15=ICB)')
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = DataFetchOrchestrator()
    
    # Execute requested action
    if args.test:
        results = orchestrator.test_connections()
        orchestrator.print_status(results)
        
    elif args.fetch_all:
        results = orchestrator.fetch_all()
        orchestrator.print_status(results)
        
    elif args.fetch_imd:
        results = {'imd': orchestrator.fetch_imd_data()}
        orchestrator.print_status(results)
        
    elif args.fetch_fingertips:
        results = {
            'fingertips': orchestrator.fetch_fingertips_data(
                indicators=args.indicators,
                area_type_id=args.area_type
            )
        }
        orchestrator.print_status(results)
        
    else:
        parser.print_help()
        print("\nNo action specified. Use --test to verify connections or --fetch-all to download data.")


if __name__ == "__main__":
    main()
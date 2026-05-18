"""
Index of Multiple Deprivation (IMD) 2019 Data Fetcher.

This module downloads and processes the English Index of Multiple Deprivation 2019
data from the Ministry of Housing, Communities and Local Government (MHCLG).

The IMD is the official measure of relative deprivation for small areas in England.
It combines information from 7 domains to produce an overall relative measure of 
deprivation: Income, Employment, Education, Health, Crime, Barriers to Housing & 
Services, and Living Environment.

Data source: https://opendatacommunities.org/resource/imd-2019
"""

import pandas as pd
import requests
import zipfile
import io
import logging
from pathlib import Path
from typing import Optional, Dict, List
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IMDFetcher:
    """
    Fetcher for Index of Multiple Deprivation 2019 data.
    
    Downloads IMD data from MHCLG open data portal and processes it into
    a clean DataFrame format suitable for analysis.
    """
    
    # MHCLG Open Data Communities - IMD 2019
    IMD_FILE_1_URL = "https://opendatacommunities.org/downloads/1d743de91d5f40ab9a47ff9c17a9c8fa/IMD2019_Index_of_Multiple_Deprivation.xlsx"
    IMD_FILE_2_URL = "https://opendatacommunities.org/downloads/343f7220e7944f22b7af3a2f36c49e9f/IMD2019_Domains_of_Deprivation.xlsx"
    
    # Alternative: Direct download from GOV.UK
    GOV_UK_IMD_URL = "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/833970/File_1_-_IMD2019_Index_of_Multiple_Deprivation.xlsx"
    GOV_UK_DOMAINS_URL = "https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/833971/File_2_-_IMD2019_Domains_of_Deprivation.xlsx"
    
    # Geographic lookup files
    LSOA_LOOKUP_URL = "https://opendatacommunities.org/downloads/cb5b9f3a73d84c0b96a8d0c43cc5a5d6/LSOA11_WD19_LAD19_EW_LU.csv"
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the IMD fetcher.
        
        Args:
            data_dir: Directory to store downloaded data. 
                     Defaults to 'data/raw' relative to current directory.
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory: {self.data_dir}")
    
    def download_file(self, url: str, filename: str, force: bool = False) -> Path:
        """
        Download a file from URL if it doesn't exist locally.
        
        Args:
            url: URL to download from
            filename: Local filename to save as
            force: If True, re-download even if file exists
            
        Returns:
            Path to the downloaded file
        """
        filepath = self.data_dir / filename
        
        if filepath.exists() and not force:
            logger.info(f"File already exists: {filepath}")
            return filepath
        
        logger.info(f"Downloading from {url}...")
        
        try:
            response = requests.get(url, timeout=120, stream=True)
            response.raise_for_status()
            
            # Get total size for progress
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) < 8192:  # Log every ~1MB
                                logger.info(f"  Downloaded: {percent:.1f}%")
            
            logger.info(f"Downloaded successfully: {filepath}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            raise
    
    def fetch_imd_main_data(self, use_gov_uk: bool = True) -> pd.DataFrame:
        """
        Fetch the main IMD 2019 data (ranks and scores).
        
        Args:
            use_gov_uk: If True, use GOV.UK source, otherwise use OpenDataCommunities
            
        Returns:
            DataFrame with IMD 2019 data for all LSOAs in England
        """
        url = self.GOV_UK_IMD_URL if use_gov_uk else self.IMD_FILE_1_URL
        filename = "imd2019_main.xlsx"
        
        try:
            filepath = self.download_file(url, filename)
        except requests.exceptions.RequestException:
            # Try alternative source
            logger.warning("Primary source failed, trying alternative...")
            url = self.IMD_FILE_1_URL if use_gov_uk else self.GOV_UK_IMD_URL
            filepath = self.download_file(url, filename)
        
        logger.info("Reading IMD 2019 main data...")
        
        # Read the Excel file - try both possible sheet names
        # The GOV.UK file uses 'IMD2019' without a space
        try:
            df = pd.read_excel(filepath, sheet_name='IMD2019', header=0)
        except ValueError:
            # Try alternative sheet name
            df = pd.read_excel(filepath, sheet_name='IMD 2019', header=0)
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Standardize column names
        column_mapping = {
            'LSOA code (2011)': 'lsoa11cd',
            'LSOA name (2011)': 'lsoa11nm',
            'Local Authority District code (2019)': 'lad19cd',
            'Local Authority District name (2019)': 'lad19nm',
            'Index of Multiple Deprivation (IMD) Rank': 'imd_rank',
            'Index of Multiple Deprivation (IMD) Decile': 'imd_decile',
            'Index of Multiple Deprivation (IMD) Score': 'imd_score',
            'Income Rank (where 1 is most deprived)': 'income_rank',
            'Income Score (rate)': 'income_score',
            'Employment Rank (where 1 is most deprived)': 'employment_rank',
            'Employment Score (rate)': 'employment_score',
            'Education, Skills and Training Rank': 'education_rank',
            'Education, Skills and Training Score': 'education_score',
            'Health Deprivation and Disability Rank': 'health_rank',
            'Health Deprivation and Disability Score': 'health_score',
            'Crime Rank': 'crime_rank',
            'Crime Score': 'crime_score',
            'Barriers to Housing and Services Rank': 'housing_rank',
            'Barriers to Housing and Services Score': 'housing_score',
            'Living Environment Rank': 'environment_rank',
            'Living Environment Score': 'environment_score',
        }
        
        # Apply mapping for columns that exist
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        # Ensure LSOA code is string
        if 'lsoa11cd' in df.columns:
            df['lsoa11cd'] = df['lsoa11cd'].astype(str).str.strip()
        
        # Calculate quintiles (1 = most deprived, 5 = least deprived)
        if 'imd_rank' in df.columns:
            df['imd_quintile'] = pd.qcut(
                df['imd_rank'], 
                q=5, 
                labels=[1, 2, 3, 4, 5]
            ).astype(int)
        
        logger.info(f"Loaded IMD data: {len(df)} LSOAs")
        return df
    
    def fetch_imd_domains(self, use_gov_uk: bool = True) -> pd.DataFrame:
        """
        Fetch detailed domain scores for IMD 2019.
        
        Args:
            use_gov_uk: If True, use GOV.UK source
            
        Returns:
            DataFrame with detailed domain scores
        """
        url = self.GOV_UK_DOMAINS_URL if use_gov_uk else self.IMD_FILE_2_URL
        filename = "imd2019_domains.xlsx"
        
        try:
            filepath = self.download_file(url, filename)
        except requests.exceptions.RequestException:
            logger.warning("Primary source failed, trying alternative...")
            url = self.IMD_FILE_2_URL if use_gov_uk else self.GOV_UK_DOMAINS_URL
            filepath = self.download_file(url, filename)
        
        logger.info("Reading IMD 2019 domains data...")
        
        # Read the Excel file - Domains sheet
        df = pd.read_excel(
            filepath,
            sheet_name='IMD 2019 Domains',
            header=0
        )
        
        # Clean and standardize
        df.columns = [str(col).strip() for col in df.columns]
        
        # Standard column mapping
        column_mapping = {
            'LSOA code (2011)': 'lsoa11cd',
            'LSOA name (2011)': 'lsoa11nm',
            'Local Authority District code (2019)': 'lad19cd',
            'Local Authority District name (2019)': 'lad19nm',
        }
        
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_cols)
        
        if 'lsoa11cd' in df.columns:
            df['lsoa11cd'] = df['lsoa11cd'].astype(str).str.strip()
        
        logger.info(f"Loaded domain data: {len(df)} LSOAs")
        return df
    
    def fetch_geographic_lookup(self) -> pd.DataFrame:
        """
        Fetch LSOA to Local Authority and ICB lookup.
        
        This provides the geographic hierarchy for joining data.
        
        Returns:
            DataFrame with geographic codes
        """
        filename = "lsoa_geographic_lookup.csv"
        
        try:
            filepath = self.download_file(self.LSOA_LOOKUP_URL, filename)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not download lookup file: {e}")
            logger.info("Creating basic lookup from IMD data...")
            return pd.DataFrame()
        
        df = pd.read_csv(filepath)
        logger.info(f"Loaded geographic lookup: {len(df)} LSOAs")
        return df
    
    def get_combined_imd_data(self) -> pd.DataFrame:
        """
        Get combined IMD 2019 data with all scores and geographic information.
        
        This is the main method to retrieve clean, analysis-ready IMD data.
        
        Returns:
            DataFrame with IMD scores, ranks, quintiles, and geographic codes
        """
        logger.info("Fetching combined IMD 2019 dataset...")
        
        # Fetch main IMD data
        main_df = self.fetch_imd_main_data()
        
        # Select key columns for analysis
        core_columns = [
            'lsoa11cd', 'lsoa11nm', 'lad19cd', 'lad19nm',
            'imd_rank', 'imd_decile', 'imd_quintile', 'imd_score',
            'income_rank', 'income_score',
            'employment_rank', 'employment_score',
            'education_rank', 'education_score',
            'health_rank', 'health_score',
            'crime_rank', 'crime_score',
            'housing_rank', 'housing_score',
            'environment_rank', 'environment_score',
        ]
        
        # Filter to columns that exist
        available_cols = [c for c in core_columns if c in main_df.columns]
        df = main_df[available_cols].copy()
        
        # Add quintile labels
        quintile_labels = {
            1: '1 - Most Deprived',
            2: '2 - More Deprived',
            3: '3 - Average',
            4: '4 - Less Deprived',
            5: '5 - Least Deprived'
        }
        
        if 'imd_quintile' in df.columns:
            df['imd_quintile_label'] = df['imd_quintile'].map(quintile_labels)
        
        logger.info(f"Combined dataset ready: {len(df)} LSOAs")
        logger.info(f"Quintile distribution:\n{df['imd_quintile'].value_counts().sort_index()}")
        
        return df
    
    def save_to_parquet(self, df: pd.DataFrame, filename: str = "imd2019_clean.parquet"):
        """
        Save processed IMD data to Parquet format for efficient storage.
        
        Args:
            df: DataFrame to save
            filename: Output filename
        """
        output_path = self.data_dir.parent / "processed" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(output_path, index=False, compression='snappy')
        logger.info(f"Saved to Parquet: {output_path}")
    
    def get_core20_areas(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Get LSOAs in the Core 20% (most deprived quintile).
        
        The Core20PLUS5 framework identifies the most deprived 20% of areas
        for targeted intervention.
        
        Args:
            df: IMD DataFrame, or None to fetch fresh data
            
        Returns:
            DataFrame with only Core 20% LSOAs
        """
        if df is None:
            df = self.get_combined_imd_data()
        
        core20 = df[df['imd_quintile'] == 1].copy()
        logger.info(f"Core 20% (most deprived): {len(core20)} LSOAs")
        return core20
    
    def get_summary_by_la(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Summarize IMD data by Local Authority.
        
        Args:
            df: IMD DataFrame, or None to fetch fresh data
            
        Returns:
            DataFrame with LA-level summary statistics
        """
        if df is None:
            df = self.get_combined_imd_data()
        
        summary = df.groupby(['lad19cd', 'lad19nm']).agg({
            'imd_score': ['mean', 'median', 'min', 'max', 'std'],
            'imd_rank': ['mean', 'median'],
            'lsoa11cd': 'count'
        }).reset_index()
        
        # Flatten column names
        summary.columns = [
            'lad19cd', 'lad19nm',
            'imd_score_mean', 'imd_score_median', 'imd_score_min', 
            'imd_score_max', 'imd_score_std',
            'imd_rank_mean', 'imd_rank_median',
            'lsoa_count'
        ]
        
        # Add proportion in each quintile
        quintile_props = df.groupby(['lad19cd', 'imd_quintile']).size().unstack(fill_value=0)
        quintile_props = quintile_props.div(quintile_props.sum(axis=1), axis=0)
        quintile_props.columns = [f'pct_quintile_{c}' for c in quintile_props.columns]
        
        summary = summary.merge(quintile_props, left_on='lad19cd', right_index=True)
        
        logger.info(f"LA summary: {len(summary)} Local Authorities")
        return summary


def test_imd_fetcher():
    """Test the IMD fetcher functionality."""
    print("=" * 60)
    print("Testing IMD 2019 Data Fetcher")
    print("=" * 60)
    
    fetcher = IMDFetcher()
    
    # Test 1: Fetch main data
    print("\n1. Fetching main IMD 2019 data...")
    try:
        df = fetcher.fetch_imd_main_data()
        print(f"   ✓ Retrieved {len(df)} LSOAs")
        print(f"   Columns: {list(df.columns)[:10]}...")
        print(f"   Sample data:")
        print(df[['lsoa11cd', 'lsoa11nm', 'imd_rank', 'imd_quintile']].head())
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Get combined data
    print("\n2. Getting combined IMD dataset...")
    try:
        combined = fetcher.get_combined_imd_data()
        print(f"   ✓ Combined dataset: {len(combined)} LSOAs")
        print(f"   Quintile distribution:")
        print(combined['imd_quintile'].value_counts().sort_index())
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Get Core 20%
    print("\n3. Identifying Core 20% most deprived areas...")
    try:
        core20 = fetcher.get_core20_areas(combined)
        print(f"   ✓ Core 20%: {len(core20)} LSOAs")
        print(f"   Most deprived LSOAs (top 5 by rank):")
        print(core20.nsmallest(5, 'imd_rank')[['lsoa11nm', 'lad19nm', 'imd_rank', 'imd_score']])
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: LA Summary
    print("\n4. Generating Local Authority summary...")
    try:
        la_summary = fetcher.get_summary_by_la(combined)
        print(f"   ✓ LA summary: {len(la_summary)} Local Authorities")
        print(f"   Most deprived LAs (by mean IMD score):")
        print(la_summary.nlargest(5, 'imd_score_mean')[['lad19nm', 'imd_score_mean', 'pct_quintile_1']])
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Save to parquet
    print("\n5. Saving to Parquet format...")
    try:
        fetcher.save_to_parquet(combined)
        print("   ✓ Saved successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("IMD Fetcher test complete!")
    print("=" * 60)
    
    return combined


if __name__ == "__main__":
    test_imd_fetcher()
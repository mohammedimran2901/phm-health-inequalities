"""
OHID Fingertips API Client.

This module provides a Python interface to the Office for Health Improvement 
and Disparities (OHID) Fingertips API for accessing public health indicators.

API Documentation: https://fingertips.phe.org.uk/api
"""

import requests
import pandas as pd
from typing import List, Dict, Optional, Union
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FingertipsAPI:
    """
    Client for the OHID Fingertips API.
    
    Provides methods to fetch health indicators, profiles, and area data
    for analyzing health inequalities in England.
    """
    
    BASE_URL = "https://fingertips.phe.org.uk/api/"
    
    # Key indicator IDs for Core20PLUS5 and health inequality analysis
    KEY_INDICATORS = {
        # Life Expectancy
        'life_expectancy_male': 90366,
        'life_expectancy_female': 90367,
        'life_expectancy_birth': 93505,
        
        # Smoking
        'smoking_prevalence': 92443,
        'smoking_quit_rates': 92444,
        
        # Cardiovascular
        'cvd_prevalence': 93088,
        'hypertension_prevalence': 241,
        'stroke_prevalence': 243,
        
        # Cancer
        'cancer_emergency_presentations': 91156,
        'cancer_screening_breast': 22401,
        'cancer_screening_cervical': 22003,
        
        # Mental Health
        'severe_mental_illness': 93095,
        'depression_prevalence': 848,
        
        # Respiratory
        'copd_prevalence': 250,
        'asthma_prevalence': 246,
        
        # Maternity
        'maternity_early_access': 93741,
        'low_birth_weight': 93715,
        
        # Inequality-related
        'healthy_life_expectancy': 90362,
        'infant_mortality': 93744,
        'premature_mortality': 91102,
    }
    
    def __init__(self):
        """Initialize the Fingertips API client."""
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'PHM-Health-Inequalities-Tool/0.1.0'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request to the Fingertips API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = urljoin(self.BASE_URL, endpoint)
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_indicator_metadata(self, indicator_id: Union[int, str]) -> Dict:
        """
        Get metadata for a specific indicator.
        
        Args:
            indicator_id: Fingertips indicator ID
            
        Returns:
            Indicator metadata dictionary
        """
        endpoint = f"indicator_metadata/{indicator_id}"
        return self._make_request(endpoint)
    
    def get_available_indicators(self) -> pd.DataFrame:
        """
        Get list of all available indicators.
        
        Returns:
            DataFrame with indicator information
        """
        data = self._make_request("indicator_names")
        return pd.DataFrame(data)
    
    def get_data_for_indicator(
        self,
        indicator_id: Union[int, str],
        area_type_id: int = 7,  # 7 = Lower Tier Local Authorities
        parent_area_code: Optional[str] = None,
        time_period: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch data for a specific indicator.
        
        Args:
            indicator_id: Fingertips indicator ID
            area_type_id: Area type (7=LTLA, 6=UTLA, 302=LSOA, 15=ICB)
            parent_area_code: Filter by parent area (e.g., 'E92000001' for England)
            time_period: Specific time period or None for latest
            
        Returns:
            DataFrame with indicator data
        """
        # Build the data endpoint
        # Format: /all_data/csv/by_indicator_id?indicator_id=X&child_area_type_id=Y
        params = {
            'indicator_id': indicator_id,
            'child_area_type_id': area_type_id
        }
        
        if parent_area_code:
            params['parent_area_code'] = parent_area_code
            
        logger.info(f"Fetching indicator {indicator_id} for area type {area_type_id}")
        
        # The Fingertips API returns CSV for data endpoints
        url = urljoin(self.BASE_URL, "all_data/csv/by_indicator_id")
        
        try:
            response = self.session.get(url, params=params, timeout=120)
            response.raise_for_status()
            
            # Parse CSV response
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            logger.info(f"Retrieved {len(df)} records for indicator {indicator_id}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch indicator data: {e}")
            raise
    
    def get_data_for_multiple_indicators(
        self,
        indicator_ids: List[Union[int, str]],
        area_type_id: int = 7,
        parent_area_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch data for multiple indicators and combine into single DataFrame.
        
        Args:
            indicator_ids: List of indicator IDs
            area_type_id: Area type ID
            parent_area_code: Parent area filter
            
        Returns:
            Combined DataFrame with all indicators
        """
        all_data = []
        
        for indicator_id in indicator_ids:
            try:
                df = self.get_data_for_indicator(
                    indicator_id=indicator_id,
                    area_type_id=area_type_id,
                    parent_area_code=parent_area_code
                )
                all_data.append(df)
            except Exception as e:
                logger.warning(f"Failed to fetch indicator {indicator_id}: {e}")
                continue
        
        if not all_data:
            logger.warning("No data retrieved for any indicators")
            return pd.DataFrame()
        
        combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined data: {len(combined)} total records")
        return combined
    
    def get_area_types(self) -> pd.DataFrame:
        """
        Get available area types (geographic hierarchies).
        
        Returns:
            DataFrame with area type information
        """
        data = self._make_request("area_types")
        return pd.DataFrame(data)
    
    def get_areas(self, area_type_id: int) -> pd.DataFrame:
        """
        Get areas for a specific area type.
        
        Args:
            area_type_id: Area type ID
            
        Returns:
            DataFrame with area information
        """
        data = self._make_request(f"areas/area_type/{area_type_id}")
        return pd.DataFrame(data)
    
    def get_latest_data_for_key_indicators(
        self,
        area_type_id: int = 7,
        indicators: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Convenience method to fetch latest data for key indicators.
        
        Args:
            area_type_id: Area type to fetch data for
            indicators: List of indicator keys from KEY_INDICATORS dict, 
                       or None for all key indicators
            
        Returns:
            DataFrame with key indicator data
        """
        if indicators is None:
            indicator_ids = list(self.KEY_INDICATORS.values())
        else:
            indicator_ids = [
                self.KEY_INDICATORS[k] 
                for k in indicators 
                if k in self.KEY_INDICATORS
            ]
        
        return self.get_data_for_multiple_indicators(
            indicator_ids=indicator_ids,
            area_type_id=area_type_id
        )
    
    @staticmethod
    def get_indicator_descriptions() -> pd.DataFrame:
        """
        Get a DataFrame describing all key indicators.
        
        Returns:
            DataFrame with indicator names and descriptions
        """
        descriptions = {
            'life_expectancy_male': 'Life expectancy at birth (male)',
            'life_expectancy_female': 'Life expectancy at birth (female)',
            'life_expectancy_birth': 'Life expectancy at birth (persons)',
            'smoking_prevalence': 'Smoking prevalence in adults',
            'smoking_quit_rates': 'Successful quit rate for smoking',
            'cvd_prevalence': 'Cardiovascular disease prevalence (QOF)',
            'hypertension_prevalence': 'Hypertension prevalence (QOF)',
            'stroke_prevalence': 'Stroke prevalence (QOF)',
            'cancer_emergency_presentations': 'Emergency cancer presentations',
            'cancer_screening_breast': 'Breast cancer screening coverage',
            'cancer_screening_cervical': 'Cervical cancer screening coverage',
            'severe_mental_illness': 'Severe mental illness prevalence',
            'depression_prevalence': 'Depression prevalence (QOF)',
            'copd_prevalence': 'COPD prevalence (QOF)',
            'asthma_prevalence': 'Asthma prevalence (QOF)',
            'maternity_early_access': 'Early access to maternity services',
            'low_birth_weight': 'Low birth weight births',
            'healthy_life_expectancy': 'Healthy life expectancy at birth',
            'infant_mortality': 'Infant mortality rate',
            'premature_mortality': 'Premature mortality rate (under 75)',
        }
        
        return pd.DataFrame([
            {
                'indicator_key': key,
                'indicator_id': FingertipsAPI.KEY_INDICATORS[key],
                'description': desc
            }
            for key, desc in descriptions.items()
        ])


if __name__ == "__main__":
    # Test the API client
    print("Testing Fingertips API Client...")
    
    api = FingertipsAPI()
    
    # Test 1: Get available indicators (first 5)
    print("\n1. Fetching available indicators...")
    try:
        indicators = api.get_available_indicators()
        print(f"   Found {len(indicators)} total indicators")
        print(f"   Sample: {indicators[['IndicatorId', 'IndicatorName']].head()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Get area types
    print("\n2. Fetching area types...")
    try:
        area_types = api.get_area_types()
        print(f"   Found {len(area_types)} area types")
        print(f"   Sample:\n{area_types[['Id', 'Name']].head(10)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get metadata for a key indicator (Life Expectancy)
    print("\n3. Fetching indicator metadata...")
    try:
        metadata = api.get_indicator_metadata(90366)
        print(f"   Indicator: {metadata.get('IndicatorName', 'N/A')}")
        print(f"   Description: {metadata.get('Definition', 'N/A')[:100]}...")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Get sample data for Life Expectancy (just a few areas)
    print("\n4. Fetching sample data for Life Expectancy...")
    try:
        # Fetch for England as parent to get subset
        df = api.get_data_for_indicator(
            indicator_id=90366,
            area_type_id=7,  # LTLA
            parent_area_code="E92000001"  # England
        )
        print(f"   Retrieved {len(df)} records")
        print(f"   Columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"   Sample data:\n{df[['AreaName', 'Time period', 'Value']].head()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✓ API client test complete!")
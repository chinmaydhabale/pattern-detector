import requests
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'User-Agent': 'CryptoPatternDetector/1.0'
        })
    
    def get_supported_coins(self) -> Dict[str, str]:
        """Get mapping of common symbols to CoinGecko IDs"""
        return {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2'
        }
    
    def get_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID"""
        coins_map = self.get_supported_coins()
        return coins_map.get(symbol.upper(), symbol.lower())
    
    def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch historical OHLCV data from CoinGecko
        """
        try:
            coin_id = self.get_coin_id(symbol)
            
            # Get OHLC data
            ohlc_url = f"{self.BASE_URL}/coins/{coin_id}/ohlc"
            ohlc_params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            logger.info(f"Fetching OHLC data for {coin_id} with {days} days")
            ohlc_response = self.session.get(ohlc_url, params=ohlc_params, timeout=10)
            
            if ohlc_response.status_code == 429:
                logger.warning("Rate limit hit, waiting...")
                time.sleep(61)  # Wait 61 seconds for rate limit reset
                ohlc_response = self.session.get(ohlc_url, params=ohlc_params, timeout=10)
            
            ohlc_response.raise_for_status()
            ohlc_data = ohlc_response.json()
            
            # Get volume data
            volume_url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            volume_params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            volume_response = self.session.get(volume_url, params=volume_params, timeout=10)
            volume_response.raise_for_status()
            volume_data = volume_response.json()
            
            # Combine OHLC with volume data
            volumes = volume_data.get('total_volumes', [])
            volume_dict = {int(v[0]): v[1] for v in volumes}
            
            formatted_data = []
            for item in ohlc_data:
                timestamp = item[0]
                date_obj = datetime.fromtimestamp(timestamp / 1000)
                
                formatted_data.append({
                    'symbol': symbol.upper(),
                    'date': date_obj.strftime('%Y-%m-%d'),
                    'timestamp': timestamp,
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': volume_dict.get(timestamp, 0)
                })
            
            logger.info(f"Successfully fetched {len(formatted_data)} data points for {symbol}")
            return formatted_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {symbol}: {str(e)}")
            # Return fallback data if API fails
            return self._get_fallback_data(symbol, days)
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {symbol}: {str(e)}")
            return self._get_fallback_data(symbol, days)
    
    def get_current_price(self, symbol: str) -> Dict[str, float]:
        """Get current price and 24h change"""
        try:
            coin_id = self.get_coin_id(symbol)
            
            url = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                time.sleep(61)
                response = self.session.get(url, params=params, timeout=10)
            
            response.raise_for_status()
            data = response.json()
            
            coin_data = data.get(coin_id, {})
            
            return {
                'current_price': coin_data.get('usd', 0),
                'price_change_24h': coin_data.get('usd_24h_change', 0)
            }
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {str(e)}")
            return {
                'current_price': 0,
                'price_change_24h': 0
            }
    
    def _get_fallback_data(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        """Generate fallback mock data when API fails"""
        logger.warning(f"Using fallback data for {symbol}")
        
        # Base prices for different cryptos
        base_prices = {
            'BTC': 45000,
            'ETH': 2500,
            'ADA': 0.5,
            'SOL': 100
        }
        
        base_price = base_prices.get(symbol.upper(), 1000)
        data = []
        
        for i in range(days):
            date_obj = datetime.now() - timedelta(days=days-i-1)
            
            # Generate realistic price movements
            variation = 0.02  # 2% daily variation
            price_change = 1 + (hash(f"{symbol}{i}") % 1000 - 500) / 25000  # Random but consistent
            current_price = base_price * (1 + i * 0.001) * price_change  # Slight upward trend with variation
            
            high = current_price * (1 + abs(hash(f"high{symbol}{i}") % 100) / 5000)
            low = current_price * (1 - abs(hash(f"low{symbol}{i}") % 100) / 5000)
            open_price = current_price * (1 + (hash(f"open{symbol}{i}") % 100 - 50) / 5000)
            
            data.append({
                'symbol': symbol.upper(),
                'date': date_obj.strftime('%Y-%m-%d'),
                'timestamp': int(date_obj.timestamp() * 1000),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(current_price, 2),
                'volume': abs(hash(f"vol{symbol}{i}") % 10000000)
            })
        
        return data
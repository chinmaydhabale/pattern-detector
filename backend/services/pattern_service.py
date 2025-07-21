import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class PatternDetectionService:
    
    def __init__(self):
        pass
    
    def detect_head_and_shoulders(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect Head and Shoulders patterns in crypto data
        """
        if not data or len(data) < 20:
            return []
        
        patterns = []
        prices = [float(item['close']) for item in data]
        
        # Look for head and shoulders patterns
        for i in range(15, len(data) - 15):
            pattern = self._analyze_head_and_shoulders_at_index(data, prices, i)
            if pattern:
                patterns.append(pattern)
        
        # Remove overlapping patterns (keep the one with highest confidence)
        patterns = self._remove_overlapping_patterns(patterns)
        
        return patterns
    
    def _analyze_head_and_shoulders_at_index(self, data: List[Dict], prices: List[float], center_idx: int) -> Dict[str, Any]:
        """Analyze potential head and shoulders pattern at given index"""
        
        # Define search windows
        left_shoulder_window = (center_idx - 12, center_idx - 6)
        head_window = (center_idx - 3, center_idx + 3)
        right_shoulder_window = (center_idx + 6, center_idx + 12)
        
        # Find peaks in each window
        left_shoulder = self._find_peak_in_window(prices, *left_shoulder_window)
        head = self._find_peak_in_window(prices, *head_window)
        right_shoulder = self._find_peak_in_window(prices, *right_shoulder_window)
        
        if not all([left_shoulder, head, right_shoulder]):
            return None
        
        left_price = left_shoulder['price']
        head_price = head['price']
        right_price = right_shoulder['price']
        
        # Head and shoulders criteria
        if not (head_price > left_price and head_price > right_price):
            return None
        
        # Calculate pattern characteristics
        confidence = self._calculate_confidence(left_price, head_price, right_price, data[center_idx])
        
        if confidence < 60:  # Minimum confidence threshold
            return None
        
        # Determine signal and strength
        signal_info = self._determine_signal(data, center_idx, head_price, left_price, right_price)
        
        return {
            'symbol': data[0]['symbol'],
            'pattern_type': signal_info['type'],
            'left_shoulder': left_price,
            'head': head_price,
            'right_shoulder': right_price,
            'confidence': confidence,
            'signal': signal_info['signal'],
            'strength': signal_info['strength'],
            'start_index': left_shoulder['index'],
            'center_index': center_idx,
            'end_index': right_shoulder['index']
        }
    
    def _find_peak_in_window(self, prices: List[float], start: int, end: int) -> Dict[str, Any]:
        """Find the highest price in a given window"""
        start = max(0, start)
        end = min(len(prices), end)
        
        if start >= end:
            return None
        
        window_prices = prices[start:end]
        max_price = max(window_prices)
        max_index = start + window_prices.index(max_price)
        
        # Verify it's actually a local peak
        if max_index > 0 and max_index < len(prices) - 1:
            if prices[max_index] <= prices[max_index - 1] or prices[max_index] <= prices[max_index + 1]:
                # Not a true peak, find the actual peak nearby
                for i in range(max(0, max_index - 2), min(len(prices), max_index + 3)):
                    if i > 0 and i < len(prices) - 1:
                        if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                            return {'price': prices[i], 'index': i}
        
        return {'price': max_price, 'index': max_index}
    
    def _calculate_confidence(self, left_price: float, head_price: float, right_price: float, center_data: Dict) -> int:
        """Calculate confidence score for the pattern"""
        confidence = 60  # Base confidence
        
        # Shoulder similarity increases confidence
        shoulder_diff = abs(left_price - right_price) / max(left_price, right_price)
        if shoulder_diff < 0.03:  # Within 3%
            confidence += 20
        elif shoulder_diff < 0.05:  # Within 5%
            confidence += 10
        
        # Head prominence increases confidence
        head_prominence = (head_price - max(left_price, right_price)) / head_price
        if head_prominence > 0.05:  # Head is 5%+ higher
            confidence += 15
        elif head_prominence > 0.03:  # Head is 3%+ higher
            confidence += 10
        
        # Volume confirmation (mock implementation)
        volume = center_data.get('volume', 0)
        if volume > 1000000:  # High volume
            confidence += 5
        
        return min(confidence, 95)
    
    def _determine_signal(self, data: List[Dict], center_idx: int, head_price: float, left_price: float, right_price: float) -> Dict[str, str]:
        """Determine the trading signal and pattern type"""
        
        # Look at recent trend
        recent_data = data[max(0, center_idx - 5):center_idx + 1]
        if len(recent_data) > 1:
            recent_trend = recent_data[-1]['close'] - recent_data[0]['close']
        else:
            recent_trend = 0
        
        # Determine pattern type and signal
        if recent_trend > 0:
            pattern_type = "Head & Shoulders Top"
            signal = "Bearish Reversal"
        else:
            pattern_type = "Inverse Head & Shoulders"
            signal = "Bullish Reversal"
        
        # Determine strength
        head_to_shoulder_ratio = (head_price - max(left_price, right_price)) / head_price
        
        if head_to_shoulder_ratio > 0.08:
            strength = "Strong"
        elif head_to_shoulder_ratio > 0.05:
            strength = "Moderate"
        else:
            strength = "Weak"
        
        return {
            'type': pattern_type,
            'signal': signal,
            'strength': strength
        }
    
    def _remove_overlapping_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """Remove overlapping patterns, keeping the one with highest confidence"""
        if len(patterns) <= 1:
            return patterns
        
        # Sort by confidence (descending)
        patterns.sort(key=lambda p: p['confidence'], reverse=True)
        
        filtered_patterns = []
        
        for pattern in patterns:
            overlap = False
            for existing in filtered_patterns:
                # Check if patterns overlap significantly
                if abs(pattern['center_index'] - existing['center_index']) < 10:
                    overlap = True
                    break
            
            if not overlap:
                filtered_patterns.append(pattern)
        
        return filtered_patterns
import { SMA } from 'technicalindicators';

export const detectHeadAndShoulders = (data) => {
  if (!data || data.length < 20) {
    return [];
  }

  const patterns = [];
  const prices = data.map(d => d.close);
  
  // Calculate simple moving average for trend identification
  const sma20 = SMA.calculate({ period: 20, values: prices });
  
  // Look for head and shoulders pattern
  for (let i = 10; i < data.length - 10; i++) {
    const leftShoulder = findLocalPeak(prices, i - 8, i - 4);
    const head = findLocalPeak(prices, i - 2, i + 2);
    const rightShoulder = findLocalPeak(prices, i + 4, i + 8);
    
    if (leftShoulder && head && rightShoulder) {
      const pattern = analyzeHeadAndShoulders(
        leftShoulder,
        head,
        rightShoulder,
        i,
        data
      );
      
      if (pattern) {
        patterns.push(pattern);
      }
    }
  }
  
  return patterns;
};

const findLocalPeak = (prices, start, end) => {
  if (start < 0 || end >= prices.length) return null;
  
  let peakIndex = start;
  let peakValue = prices[start];
  
  for (let i = start + 1; i <= end; i++) {
    if (prices[i] > peakValue) {
      peakValue = prices[i];
      peakIndex = i;
    }
  }
  
  // Verify it's actually a local peak
  const leftOk = peakIndex === start || prices[peakIndex - 1] < peakValue;
  const rightOk = peakIndex === end || prices[peakIndex + 1] < peakValue;
  
  if (leftOk && rightOk) {
    return { index: peakIndex, value: peakValue };
  }
  
  return null;
};

const analyzeHeadAndShoulders = (leftShoulder, head, rightShoulder, centerIndex, data) => {
  const leftShoulderPrice = leftShoulder.value;
  const headPrice = head.value;
  const rightShoulderPrice = rightShoulder.value;
  
  // Head and shoulders criteria:
  // 1. Head should be higher than both shoulders
  // 2. Shoulders should be roughly at similar levels
  // 3. There should be valleys between peaks
  
  const headHigherThanShoulders = headPrice > leftShoulderPrice && headPrice > rightShoulderPrice;
  const shouldersSimilar = Math.abs(leftShoulderPrice - rightShoulderPrice) / Math.max(leftShoulderPrice, rightShoulderPrice) < 0.05;
  
  if (!headHigherThanShoulders) {
    return null;
  }
  
  // Calculate confidence based on pattern characteristics
  let confidence = 60; // Base confidence
  
  if (shouldersSimilar) {
    confidence += 20;
  }
  
  // Check for volume confirmation (mock implementation)
  const avgVolume = data.slice(centerIndex - 5, centerIndex + 5)
    .reduce((sum, d) => sum + (d.volume || 1000000), 0) / 10;
  
  if (data[head.index]?.volume > avgVolume * 1.2) {
    confidence += 10;
  }
  
  // Determine signal strength
  const headToShoulderRatio = (headPrice - Math.max(leftShoulderPrice, rightShoulderPrice)) / headPrice;
  let strength = 'Weak';
  
  if (headToShoulderRatio > 0.05) {
    strength = 'Moderate';
  }
  if (headToShoulderRatio > 0.1) {
    strength = 'Strong';
  }
  
  // Determine signal type
  const recentTrend = data.slice(centerIndex - 5, centerIndex + 1)
    .map(d => d.close);
  const isUptrend = recentTrend[recentTrend.length - 1] > recentTrend[0];
  
  const signal = isUptrend ? 'Bearish Reversal' : 'Continuation Pattern';
  const type = isUptrend ? 'Head & Shoulders Top' : 'Head & Shoulders Bottom';
  
  return {
    type,
    leftShoulder: leftShoulderPrice,
    head: headPrice,
    rightShoulder: rightShoulderPrice,
    confidence: Math.min(confidence, 95),
    signal,
    strength,
    centerIndex,
    startIndex: leftShoulder.index,
    endIndex: rightShoulder.index
  };
};
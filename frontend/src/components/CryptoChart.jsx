import React, { useState, useEffect } from 'react';
import { ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, LineChart } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { TrendingUp, TrendingDown, Activity, RefreshCw } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CryptoChart = () => {
  const [selectedCrypto, setSelectedCrypto] = useState('BTC');
  const [chartData, setChartData] = useState([]);
  const [detectedPatterns, setDetectedPatterns] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [priceChange24h, setPriceChange24h] = useState(0);
  const [priceChangePercentage24h, setPriceChangePercentage24h] = useState(0);
  const [supportedCryptos, setSupportedCryptos] = useState([
    { symbol: 'BTC', name: 'Bitcoin' },
    { symbol: 'ETH', name: 'Ethereum' },
    { symbol: 'ADA', name: 'Cardano' },
    { symbol: 'SOL', name: 'Solana' },
  ]);

  const { toast } = useToast();

  useEffect(() => {
    fetchSupportedCryptos();
  }, []);

  useEffect(() => {
    if (selectedCrypto) {
      analyzeCrypto(selectedCrypto);
    }
  }, [selectedCrypto]);

  const fetchSupportedCryptos = async () => {
    try {
      const response = await axios.get(`${API}/crypto/supported`);
      const cryptos = response.data.supported_cryptos.map(crypto => ({
        symbol: crypto.symbol,
        name: crypto.name
      }));
      setSupportedCryptos(cryptos);
    } catch (error) {
      console.error('Error fetching supported cryptos:', error);
      // Keep default cryptos if API fails
    }
  };

  const analyzeCrypto = async (symbol, days = 30) => {
    setIsAnalyzing(true);
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API}/crypto/analyze`, {
        symbol: symbol,
        days: days
      });

      const data = response.data;
      
      // Format data for the chart
      const formattedData = data.data.map(item => ({
        date: item.date,
        open: item.open_price || item.open,
        high: item.high_price || item.high,
        low: item.low_price || item.low,
        close: item.close_price || item.close,
        volume: item.volume
      }));

      setChartData(formattedData);
      setDetectedPatterns(data.patterns || []);
      setCurrentPrice(data.current_price);
      setPriceChange24h(data.price_change_24h);
      setPriceChangePercentage24h(data.price_change_percentage_24h);

      toast({
        title: "Analysis Complete",
        description: `Found ${data.patterns?.length || 0} Head & Shoulders patterns for ${symbol}`,
        duration: 3000,
      });

    } catch (error) {
      console.error('Error analyzing crypto:', error);
      toast({
        title: "Analysis Failed",
        description: error.response?.data?.detail || "Failed to analyze cryptocurrency data",
        variant: "destructive",
        duration: 5000,
      });
      
      // Clear data on error
      setChartData([]);
      setDetectedPatterns([]);
      setCurrentPrice(0);
      setPriceChange24h(0);
      setPriceChangePercentage24h(0);
    } finally {
      setIsAnalyzing(false);
      setIsLoading(false);
    }
  };

  const formatPrice = (price) => {
    if (price === 0) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: price < 1 ? 6 : 2
    }).format(price);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="font-medium">{`Date: ${label}`}</p>
          <p className="text-green-600">{`Open: ${formatPrice(data.open)}`}</p>
          <p className="text-red-600">{`Close: ${formatPrice(data.close)}`}</p>
          <p className="text-blue-600">{`High: ${formatPrice(data.high)}`}</p>
          <p className="text-purple-600">{`Low: ${formatPrice(data.low)}`}</p>
          <p className="text-gray-600">{`Volume: ${data.volume?.toLocaleString()}`}</p>
        </div>
      );
    }
    return null;
  };

  const currentPrice = chartData.length > 0 ? chartData[chartData.length - 1].close : 0;
  const previousPrice = chartData.length > 1 ? chartData[chartData.length - 2].close : 0;
  const priceChange = currentPrice - previousPrice;
  const priceChangePercent = previousPrice ? (priceChange / previousPrice) * 100 : 0;

  return (
    <div className="space-y-6 p-6 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            Crypto Pattern Detector
          </h1>
          <p className="text-lg text-gray-600">Advanced Head & Shoulders Pattern Analysis</p>
        </div>

        {/* Controls */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-600" />
                <Select value={selectedCrypto} onValueChange={setSelectedCrypto}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Select Cryptocurrency" />
                  </SelectTrigger>
                  <SelectContent>
                    {cryptoOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <Button 
                onClick={() => analyzePatterns(chartData)}
                disabled={isAnalyzing}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                {isAnalyzing ? 'Analyzing...' : 'Detect Patterns'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Price Info */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-600 mb-2">Current Price</h3>
                <p className="text-3xl font-bold text-gray-900">{formatPrice(currentPrice)}</p>
              </div>
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-600 mb-2">24h Change</h3>
                <div className="flex items-center justify-center gap-2">
                  {priceChange >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-green-600" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-red-600" />
                  )}
                  <span className={`text-2xl font-bold ${priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {priceChange >= 0 ? '+' : ''}{formatPrice(priceChange)} ({priceChangePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-600 mb-2">Patterns Found</h3>
                <p className="text-3xl font-bold text-blue-600">{detectedPatterns.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Chart */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              {selectedCrypto} Candlestick Chart
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e0e7ff" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#6b7280"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    domain={['dataMin - 50', 'dataMax + 50']}
                    stroke="#6b7280"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `$${value}`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line 
                    type="monotone" 
                    dataKey="high" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="High"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="low" 
                    stroke="#ef4444" 
                    strokeWidth={2}
                    name="Low"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="close" 
                    stroke="#3b82f6" 
                    strokeWidth={3}
                    name="Close"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="open" 
                    stroke="#8b5cf6" 
                    strokeWidth={2}
                    name="Open"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Pattern Detection Results */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Head & Shoulders Pattern Detection
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isAnalyzing ? (
              <div className="text-center py-8">
                <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-600">Analyzing chart patterns...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {detectedPatterns.length > 0 ? (
                  detectedPatterns.map((pattern, index) => (
                    <div key={index} className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-purple-50">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-lg">Head & Shoulders Pattern</h4>
                        <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                          {pattern.type}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-600">Left Shoulder:</span>
                          <p className="font-mono">{formatPrice(pattern.leftShoulder)}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Head:</span>
                          <p className="font-mono">{formatPrice(pattern.head)}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Right Shoulder:</span>
                          <p className="font-mono">{formatPrice(pattern.rightShoulder)}</p>
                        </div>
                        <div>
                          <span className="font-medium text-gray-600">Confidence:</span>
                          <p className="font-semibold text-green-600">{pattern.confidence}%</p>
                        </div>
                      </div>
                      <div className="mt-3 p-3 bg-white rounded border-l-4 border-l-blue-500">
                        <p className="text-sm text-gray-700">
                          <strong>Signal:</strong> {pattern.signal} | 
                          <strong className="ml-2">Strength:</strong> {pattern.strength}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Activity className="w-8 h-8 text-gray-400" />
                    </div>
                    <p className="text-gray-600 text-lg">No Head & Shoulders patterns detected</p>
                    <p className="text-gray-500 text-sm mt-2">Try analyzing a different time period or cryptocurrency</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CryptoChart;
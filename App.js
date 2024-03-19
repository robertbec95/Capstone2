// App.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ApexCharts from 'apexcharts';
import 'apexcharts/dist/apexcharts.css';
import styles from './CandlestickChart.module.css';

// Use environment variables for API URL
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const fetchData = async (stockSymbol) => {
  try {
    const response = await axios.get(`${BASE_URL}/stock/${stockSymbol.toUpperCase()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching stock data:', error);
    throw error; // Re-throw the error after logging it
  }
};

const fetchPortfolio = async (username) => {
  try {
    const response = await axios.get(`${BASE_URL}/api/portfolio?user=${username}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching portfolio:', error);
    throw error;
  }
};

const fetchHomepage = async () => {
  try {
    const response = await axios.get(`${BASE_URL}/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching homepage:', error);
    throw error;
  }
};

const CandlestickChart = () => {
  const [data, setData] = useState(null);
  const [homepage, setHomepage] = useState('');
  const [selectedStock, setSelectedStock] = useState('msft');
  const [portfolio, setPortfolio] = useState(null);
  const chartRef = useRef(null);

  const fetchAndUpdateData = async () => {
    try {
      const fetchedData = await fetchData(selectedStock);
      setData(fetchedData);
    } catch (error) {
      // Handle or display the error as needed
    }
  };

  const fetchAndUpdateHomepage = async () => {
    try {
      const fetchedHomepage = await fetchHomepage();
      setHomepage(fetchedHomepage);
    } catch (error) {
      // Handle or display the error as needed
    }
  };

  const fetchAndUpdatePortfolio = async (username) => {
    try {
      const fetchedPortfolio = await fetchPortfolio(username);
      setPortfolio(fetchedPortfolio);
    } catch (error) {
      // Handle or display the error as needed
    }
  };

  useEffect(() => {
    fetchAndUpdateData();
    fetchAndUpdateHomepage();
    fetchAndUpdatePortfolio('testUser');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedStock]);

  const timeSeriesData = data ? data["TimeSeries (Daily)"] : null;
  const candlesticks = timeSeriesData ? Object.entries(timeSeriesData).map(([timestamp, values]) => {
    return {
      x: new Date(timestamp),
      y: [parseFloat(values["1. open"]), parseFloat(values["2. high"]), parseFloat(values["3. low"]), parseFloat(values["4. close"])]
    };
  }) : [];

  const options = {
    series: [{
      name: selectedStock.toUpperCase(),
      type: 'candlestick',
      data: candlesticks
    }],
    chart: {
      type: 'candlestick',
      height: 350
    },
    title: {
      text: `${selectedStock.toUpperCase()} Daily Prices`,
      align: 'left'
    },
    xaxis: {
      type: 'datetime'
    },
    yaxis: {
      title: {
        text: 'Price ($)'
      }
    }
  };

  useEffect(() => {
    if (chartRef.current) {
      const chart = new ApexCharts(chartRef.current, options);
      chart.render();
    }
  }, [data]);

  const handleStockSelection = (event) => {
    setSelectedStock(event.target.value);
  };

  const handlePortfolioButtonClick = () => {
    window.open(`${BASE_URL}/api/portfolio?user=testUser`, '_blank');
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Wealthwise</h1>
      </header>
      <select id="stock-select" name="stock" value={selectedStock} onChange={handleStockSelection}>
        <option value="MSFT">Microsoft</option>
        <option value="aapl">Apple</option>
        <option value="googl">Google</option>
        <option value="tsla">Tesla</option>
        <option value="nvda">Nvidia</option>
      </select>
      <button className={styles.portfolioButton} onClick={handlePortfolioButtonClick}>
        View Portfolio
      </button>
      <div className={styles.homepage} dangerouslySetInnerHTML={{ __html: homepage }}></div>
      <div className={styles.portfolio}>
        
      </div>
      <div ref={chartRef}></div>
      <div className={styles.footer}>
        <p>WealthWise 2024</p>
      </div>
    </div>
  );
};

export default CandlestickChart;
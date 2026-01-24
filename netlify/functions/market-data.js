// Netlify Function to fetch market data from Alpha Vantage
const https = require('https');

const SYMBOLS = {
  'SPY': 'S&P 500',
  'DIA': 'Dow Jones',
  'QQQ': 'NASDAQ'
};

function fetchQuote(symbol, apiKey) {
  return new Promise((resolve, reject) => {
    const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${apiKey}`;
    
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json['Global Quote']) {
            const quote = json['Global Quote'];
            resolve({
              symbol: symbol,
              name: SYMBOLS[symbol],
              price: parseFloat(quote['05. price']).toFixed(2),
              change: parseFloat(quote['09. change']).toFixed(2),
              changePercent: quote['10. change percent'].replace('%', ''),
              volume: parseInt(quote['06. volume']).toLocaleString()
            });
          } else {
            resolve(null);
          }
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', reject);
  });
}

exports.handler = async function(event, context) {
  const apiKey = process.env.ALPHA_VANTAGE_API_KEY;
  
  if (!apiKey) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'API key not configured' })
    };
  }

  try {
    // Fetch all quotes in parallel
    const quotes = await Promise.all(
      Object.keys(SYMBOLS).map(symbol => fetchQuote(symbol, apiKey))
    );
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300' // Cache for 5 minutes
      },
      body: JSON.stringify({
        quotes: quotes.filter(q => q !== null),
        timestamp: new Date().toISOString()
      })
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};

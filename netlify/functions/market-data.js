// Netlify Function to fetch market data from Alpha Vantage
const https = require('https');

const SYMBOLS = [
  { symbol: 'SPY', name: 'S&P 500' },
  { symbol: 'DIA', name: 'Dow Jones' },
  { symbol: 'QQQ', name: 'NASDAQ' }
];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function fetchQuote(symbol, apiKey) {
  return new Promise((resolve, reject) => {
    const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=${apiKey}`;
    
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json['Global Quote'] && json['Global Quote']['05. price']) {
            const quote = json['Global Quote'];
            resolve({
              symbol: symbol,
              price: parseFloat(quote['05. price']).toFixed(2),
              change: parseFloat(quote['09. change']).toFixed(2),
              changePercent: quote['10. change percent'].replace('%', '')
            });
          } else {
            console.log(`No data for ${symbol}:`, json);
            resolve(null);
          }
        } catch (e) {
          console.log(`Error parsing ${symbol}:`, e);
          resolve(null);
        }
      });
    }).on('error', (e) => {
      console.log(`Fetch error for ${symbol}:`, e);
      resolve(null);
    });
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
    const quotes = [];
    
    // Fetch sequentially with delay to avoid rate limits
    for (const item of SYMBOLS) {
      const quote = await fetchQuote(item.symbol, apiKey);
      if (quote) {
        quote.name = item.name;
        quotes.push(quote);
      }
      // Wait 1.5 seconds between requests to respect rate limits
      if (SYMBOLS.indexOf(item) < SYMBOLS.length - 1) {
        await sleep(1500);
      }
    }
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=300' // Cache for 5 minutes
      },
      body: JSON.stringify({
        quotes: quotes,
        timestamp: new Date().toISOString()
      })
    };
  } catch (error) {
    console.log('Handler error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};

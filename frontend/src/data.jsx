import React, { useEffect, useState } from 'react';

function Data() {
  const [searchData, setSearchData] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [email] = useState(localStorage.getItem('email'));
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('http://localhost:5000/api/add_search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          search_query: searchQuery,
          email: email
        }),
      });

      if (!response.ok) {
        throw new Error('Frontend Post to Backend Failed');
      }

      const data = await response.json();
      console.log('Search Query:', data);
    } catch (error) {
      setError(error.message);
    }
  };

  useEffect(() => {
    const fetchSearchHistory = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/get_search/${encodeURIComponent(email)}`);

        if (!response.ok) {
          throw new Error('Backend Fetch to Frontend Failed');
        }

        const data = await response.json();
        setSearchData(data.search_history || []);
      } catch (error) {
        setError(error.message);
      }
    };

    fetchSearchHistory();
  }, [email]);

  return (
    <div
      className="container mt-5"

    >
      {/* Page Header */}
      <div className="text-center">
        <h1>Data Page</h1>
        <p>This is where the searches and results will be displayed. (Search History Also?)</p>
      </div>

      <div className="row mt-4">
        <div className="col-md-4">
          <h2>Subreddit Search</h2>
          <p>(Query should include parameter options from wireframe)</p>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <input
                type="text"
                className="form-control"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter your search here"
              />
            </div>
          </form>

          <div className="mt-4">
          <h2>Sentiment Keywords</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <input
                type="text"
                className="form-control"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter your search here"
              />
            </div>
          </form>
          </div>
          
          <div className="mt-4">
          <h2>Dates</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <input
                type="text"
                className="form-control"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter your search here"
              />
            </div>
          </form>
          </div>

          <div className="mt-4">
          <button type="submit" className="btn btn-primary mt-2">
              Submit
          </button>
          </div>



          {error && <p className="text-danger mt-3">Error: {error}</p>}

          {/* Search History */}
        </div>

        {/* Timeline*/}
        <div className="col-md-8">
          <h2>Sentiment Analysis</h2>
          <p>Posts containing value (PLACEHOLDER DATE RANGE)</p>

          {/* Chart */}
          <div
            style={{
              backgroundColor: '#333',
              height: '350px',
              borderRadius: '8px',
              marginBottom: '1rem'
            }}
          >
            {/* PUT CHART HERE*/}
          </div>

          <button className="btn btn-secondary">Save as PNG</button>
        </div>
      </div>


      <div className="mt-5">
            <h2>Search History</h2>
            {searchData.length === 0 ? (
              <p>Error: Failed to Fetch</p>
            ) : (
              <ul>
                {searchData.map((item, index) => (
                  <li key={index} style={{ marginBottom: '1rem' }}>
                    <strong>Search:</strong> {item.search_query}
                    <br />
                    <strong>Date:</strong> {item.created_utc}
                  </li>
                ))}
              </ul>
            )}
          </div>
    </div>
    
  );
}

export default Data;

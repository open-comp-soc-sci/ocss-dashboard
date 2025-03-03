import React, { useEffect, useState } from 'react';
import ReactDatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';


function Data() {
  const [searchData, setSearchData] = useState([]);
  const [subreddit, setSubreddit] = useState('');
  const [sentimentKeywords, setSentimentKeywords] = useState('');

  const [dates, setDates] = useState('');
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());

  const [searchTerms, setSearchTerms] = useState([]);

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
          subreddit: `r/${subreddit}`,
          sentimentKeywords: sentimentKeywords,
          startDate: startDate, 
          endDate: endDate,
          dateText: dates,
          searchTerms: searchTerms,
          email: email,
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

  const handleKeywordKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const newTerm = e.target.value.trim();
      if (newTerm && !searchTerms.includes(newTerm)) {
        setSearchTerms((prevTerms) => [...prevTerms, newTerm]);
      }
      e.target.value = '';
    }
  };

  const removeTerm = (term) => {
    setSearchTerms(searchTerms.filter((t) => t !== term));
  };

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
              <label>Subreddit</label>
              <div className="input-group">            
                <span className="input-group-text text-muted">r/</span>
                <input
                  type="text"
                  className="form-control"
                  value={subreddit}
                  onChange={(e) => setSubreddit(e.target.value)}
                  placeholder="Enter subreddit (e.g. survivor)"
                />
              </div>
            </div>

          <div className="mt-4">
          <h2>Sentiment Keywords</h2>
          <div className="form-group">
                <label>Type a keyword and press Enter</label>
                <input
                  type="text"
                  className="form-control"
                  onKeyDown={handleKeywordKeyDown}
                  placeholder="e.g. happy"
                />
              </div>
              {/* Display search terms as removable chips */}
              <div className="mt-2">
                {searchTerms.map((term, index) => (
                  <span
                    key={index}
                    className="badge bg-primary me-2"
                    style={{ cursor: 'pointer' }}
                    onClick={() => removeTerm(term)}
                  >
                    {term} <span className="ms-1">&times;</span>
                  </span>
                ))}
              </div>
            </div>
          
          <div className="mt-4">
          <h2>Dates</h2>
              <div className="mt-3">
                <label>Select Start Date:        </label>
                <ReactDatePicker
                  selected={startDate}
                  onChange={(date) => setStartDate(date)}
                  selectsStart
                  startDate={startDate}
                  endDate={endDate}
                  className="form-control"
                  placeholderText="Start Date"
                />
              </div>
              <div className="mt-3">
                <label>Select End Date:    </label>
                <ReactDatePicker
                  selected={endDate}
                  onChange={(date) => setEndDate(date)}
                  selectsEnd
                  startDate={startDate}
                  endDate={endDate}
                  minDate={startDate} // ensures end date isn't before start date
                  className="form-control"
                  placeholderText="End Date"
                />
              </div>
            </div>

          <div className="mt-4">
          <button type="submit" className="btn btn-primary mt-2">
              Submit
          </button>
          </div>
          </form>


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

import React, { useEffect, useState } from 'react';

function Data() {
  const [searchData, setSearchData] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [email] = useState(localStorage.getItem('email'));
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    //temporary fix, seems to keep refreshing to the index page /
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
    <div className="container mt-5">
      <div className="text-center">
        <h1>Data Page</h1>
        <p>This is where the searches and results will be displayed. (Search History Also?)</p>
      </div>

      <div>
        <h1>OCSS Search</h1>
        <p>(Query should include parameter options from wireframe)</p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter your search here"
          />
          <button type="submit">Submit</button>
        </form>
        {error && <p>Error: {error}</p>}
      </div>

      <br />
      <h1>Search History</h1>
      {error && <p>Error: {error}</p>}
      <ul>
        {searchData.map((item, index) => (
          <li key={index}>
            <strong>Search:</strong> {item.search_query}
            <br />
            <strong>Date:</strong> {item.created_utc}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Data;
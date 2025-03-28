import React, { useEffect, useState } from 'react';
import ReactDatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import $ from 'jquery';
import 'datatables.net';

function Data() {
  const [searchData, setSearchData] = useState([]);
  const [subreddit, setSubreddit] = useState('');
  const [sentimentKeywords, setSentimentKeywords] = useState('');
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [searchTerms, setSearchTerms] = useState([]);
  const [email] = useState(localStorage.getItem('email'));
  const [error, setError] = useState(null);
  const [clickData, setClickData] = useState([]);
  const [option, setOption] = useState("reddit_submissions");
  const [selectedOption, setSelectedOption] = useState("reddit_submissions");
  const [allClickData, setAllClickData] = useState([]);

  const fetchSearchHistory = async () => {
    try {
      const response = await fetch(`/api/get_search/${encodeURIComponent(email)}`);

      if (!response.ok) {
        throw new Error('Backend Fetch Failed');
      }

      const data = await response.json();
      setSearchData(data.search_history || []);
    } catch (error) {
      if (error.message !== 'Backend Fetch Failed') {
        setError(error.message);
      }
    }
  };

  const fetchClickData = async () => {
    try {
      const response = await fetch(`/api/get_click?subreddit=${encodeURIComponent(subreddit)}&option=${encodeURIComponent(selectedOption)}`);

      if (!response.ok) {
        throw new Error('ClickHouse fetch failed.');
      }

      const data = await response.json();
      setClickData(data);
    } catch (error) {
      setError(error.message);
    }
  };

  const AddSearch = async () => {
    try {
      const response = await fetch('/api/add_search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subreddit: `r/${subreddit}`,
          sentimentKeywords: sentimentKeywords,
          startDate: startDate,
          endDate: endDate,
          //sorry for commenting out, i am unsure of when this is used
          //dateText: dates,
          searchTerms: searchTerms,
          email: email,
        }),
      });

      if (!response.ok) {
        throw new Error('Frontend Post to Backend Failed');
      }

      const data = await response.json();
      console.log('Search Query:', data);

      fetchSearchHistory();
    } catch (error) {
      setError(error.message);
    }
  }

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

  useEffect(() => {
    if (email) {
      fetchSearchHistory();
    }
  }, [email]);

  useEffect(() => {
    const fetchData = async (start, length, draw) => {
      try {
        //start = start || 0;
        //length = length || 10;
        //draw = draw || 1;
        console.log(`Fetching data with start=${start}, length=${length}, draw=${draw}`);
        const response = await fetch(`/api/get_all_click?length=${length}&start=${start}&draw=${draw}`);
        const data = await response.json();
        return data;
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    const initDataTable = () => {
      $("#click-table").DataTable({
        processing: true,
        serverSide: true,
        paging: true,
        ajax: function (data, callback, settings) {
          const { start = 0, length = 10, draw = 1 } = settings;

          console.log("start:", start, "length:", length, "draw:", draw);

          fetchData(start, length, draw).then((apiData) => {
            if (apiData && Array.isArray(apiData.data)) {
              callback({
                draw: apiData.draw,
                recordsTotal: apiData.recordsTotal,
                recordsFiltered: apiData.recordsFiltered,
                data: apiData.data.map((row) => ({
                  subreddit: row[0],
                  title: row[1],
                  selftext: row[2],
                  created_utc: row[3],
                })),
              });
            } else {
              console.error("API data is not in expected format:", apiData);
              callback({
                draw: apiData.draw,
                recordsTotal: 0,
                recordsFiltered: 0,
                data: [],
              });
            }
          }).catch((error) => {
            console.error("Error fetching data:", error);
            callback({
              draw: 1,
              recordsTotal: 0,
              recordsFiltered: 0,
              data: [],
            });
          });
        },
        columns: [
          { data: "subreddit", title: "Subreddit" },
          { data: "title", title: "Title" },
          { data: "selftext", title: "Body" },
          { data: "created_utc", title: "Created UTC" },
        ],
        pageLength: 10,
        lengthChange: true, //hide page length selector until paging works
        deferRender: true,
        responsive: true,
        scrollY: "400px",
        scrollX: false,
        scroller: true,
        autoWidth: false,
        dom: '<"top">rt<"bottom"p><"clear">', //hide search bar until implemented
        columnDefs: [
          {
            targets: '_all',
            createdCell: function (td, cellData, rowData, row, col) {
              $(td).css('border-right', '1px solid #333');
            }
          }
        ],

      });
    };

    initDataTable();

    return () => {
      if ($.fn.dataTable.isDataTable("#click-table")) {
        $("#click-table").DataTable().destroy();
      }
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setOption(selectedOption);
    setError(null);
    await fetchClickData();
    await AddSearch();
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
                {/* Temporarily added value={sentimentKeywords} just to clear on search until dropdown list. */}
                <input
                  type="text"
                  className="form-control"
                  onKeyDown={handleKeywordKeyDown}
                  value={sentimentKeywords}
                  onChange={(e) => setSentimentKeywords(e.target.value)}
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
              <h2>Search Options</h2>
              <div className="form-group">
                <label>Choose to view Reddit submissions or comments.</label>
                <div>
                  <label className="form-check-label">
                    <input
                      type="radio"
                      className="form-check-input"
                      name="option"
                      value="reddit_submissions"
                      checked={selectedOption === "reddit_submissions"}
                      onChange={() => setSelectedOption("reddit_submissions")}
                    />
                    Submissions
                  </label>
                </div>
                <div>
                  <label className="form-check-label">
                    <input
                      type="radio"
                      className="form-check-input"
                      name="option"
                      value="reddit_comments"
                      checked={selectedOption === "reddit_comments"}
                      onChange={() => setSelectedOption("reddit_comments")}
                    />
                    Comments
                  </label>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <button type="submit" className="btn btn-primary mt-2">
                Submit
              </button>
            </div>
          </form>
          {error && <p className="text-danger mt-3">Error: {error}</p>}
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

      {/* DataTables */}
      <div>
        <table id="click-table" className="display">
          <thead>
          </thead>
          <tbody>
          </tbody>
        </table>
      </div>

      <div className="mt-5">
        <h2>ClickHouse Data Print Test</h2>
        {searchData.length === 0 ? (
          <p>----------</p>
        ) : (
          <ul>
            {clickData.map((item, index) => (
              <li key={index} style={{ marginBottom: '1rem' }}>
                {option === "reddit_submissions" ? (
                  <>
                    <strong>Subreddit: </strong> r/{item[1]}
                    <br />
                    <strong>Title: </strong> {item[2]}
                    <br />
                    <strong>Body: </strong> {item[3]}
                    <br />
                    <strong>Link: </strong>
                    <a
                      href={`https://reddit.com/r/${item[1]}/comments/${item[0]}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      reddit.com/r/{item[1]}/comments/{item[0]}
                    </a>
                    <br />
                    <strong>Created_UTC: </strong> {item[4]}
                    <br />
                  </>
                ) : (
                  <>
                    <strong>Subreddit: </strong> r/{item[2]}
                    <br />
                    <strong>Comment: </strong> {item[3]}
                    <br />
                    <strong>Link: </strong>
                    <a
                      href={`https://reddit.com/r/${item[2]}/comments/${item[1]}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      reddit.com/r/{item[2]}/comments/{item[1]}
                    </a>
                    <br />
                    <strong>Created_UTC: </strong> {item[4]}
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>


      <div className="mt-5">
        <h2>Search History</h2>
        {searchData.length === 0 ? (
          <p>No search history.</p>
        ) : (
          <ul>
            {searchData.map((item, index) => (
              <li key={index} style={{ marginBottom: '1rem' }}>
                <strong>Reddit:</strong> {item.subreddit}
                <br />
                <strong>Terms:</strong> {item.sentimentKeywords}
                <br />
                <strong>Time Range:</strong> {new Date(item.startDate).toLocaleDateString('en-US')} - {new Date(item.endDate).toLocaleDateString('en-US')}
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

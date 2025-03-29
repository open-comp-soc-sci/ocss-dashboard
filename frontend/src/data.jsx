import React, { useEffect, useState, useRef } from 'react';
import ReactDatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import $ from 'jquery';
import 'datatables.net-bs5';

function Data() {
  const [subreddit, setSubreddit] = useState('survivor');
  const [sentimentKeywords, setSentimentKeywords] = useState('');
  const [startDate, setStartDate] = useState(new Date('2024-12-01'));
  const [endDate, setEndDate] = useState(new Date('2024-12-30'));
  const [searchTerms, setSearchTerms] = useState([]);
  const [email] = useState(localStorage.getItem('email'));
  const [error, setError] = useState(null);
  const [option, setOption] = useState("reddit_submissions");
  const [selectedOption, setSelectedOption] = useState("reddit_submissions");
  const [sentimentResults, setSentimentResults] = useState(null);
  const [loadingSentiment, setLoadingSentiment] = useState(false);
  const [searchData, setSearchData] = useState([]);

  // This ref controls whether the main results DataTable should fetch data
  const tableInitializedRef = useRef(false);

  // Fetch search history immediately on mount.
  useEffect(() => {
    const fetchSearchHistory = async () => {
      try {
        const response = await fetch(`/api/get_search/${encodeURIComponent(email)}`);
        if (!response.ok) throw new Error('Backend Fetch Failed');
        const data = await response.json();
        setSearchData(data.search_history || []);
      } catch (error) {
        if (error.message !== 'Backend Fetch Failed') {
          setError(error.message);
        }
      }
    };
    fetchSearchHistory();
  }, [email]);

  const AddSearch = async () => {
    try {
      const response = await fetch('/api/add_search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subreddit: `r/${subreddit}`,
          sentimentKeywords: sentimentKeywords,
          startDate: startDate,
          endDate: endDate,
          searchTerms: searchTerms,
          email: email,
        }),
      });
      if (!response.ok) throw new Error('Frontend Post to Backend Failed');
      const data = await response.json();
      console.log('Search Query:', data);
      // Refresh search history after adding a search.
      const response2 = await fetch(`/api/get_search/${encodeURIComponent(email)}`);
      const data2 = await response2.json();
      setSearchData(data2.search_history || []);
    } catch (error) {
      setError(error.message);
    }
  };

  const handleKeywordKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const newTerm = e.target.value.trim();
      if (newTerm && !searchTerms.includes(newTerm)) {
        setSearchTerms(prevTerms => [...prevTerms, newTerm]);
      }
      e.target.value = '';
    }
  };

  const removeTerm = (term) => {
    setSearchTerms(searchTerms.filter(t => t !== term));
  };

  // Initialize main results DataTable on mount or when dependencies change.
  useEffect(() => {
    const fetchData = async (start, length, draw, searchValue) => {
      try {
        const response = await fetch(
          `/api/get_all_click?length=${length}&start=${start}&draw=${draw}` +
          `&subreddit=${encodeURIComponent(subreddit)}` +
          `&option=${encodeURIComponent(selectedOption)}` +
          `&search_value=${encodeURIComponent(searchValue)}` +
          `&sentimentKeywords=${encodeURIComponent(sentimentKeywords)}` +
          `&startDate=${encodeURIComponent(startDate.toISOString())}` +
          `&endDate=${encodeURIComponent(endDate.toISOString())}`
        );
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
        pagingType: "full_numbers",
        // Remove the built-in search field from the dom and disable searching.
        dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
        searching: false,
        ajax: function (data, callback, settings) {
          if (!tableInitializedRef.current) {
            callback({
              draw: data.draw,
              recordsTotal: 0,
              recordsFiltered: 0,
              data: []
            });
            return;
          }
          const { start, length, draw, search } = data;
          // Use current state values when fetching data.
          fetchData(start, length, draw, search.value).then(apiData => {
            if (apiData && Array.isArray(apiData.data)) {
              callback({
                draw: apiData.draw,
                recordsTotal: apiData.recordsTotal,
                recordsFiltered: apiData.recordsFiltered,
                data: apiData.data.map(row => ({
                  subreddit: row[0],
                  title: row[1],
                  selftext: row[2],
                  created_utc: row[3],
                  id: row[4],
                }))
              });
            } else {
              console.error("API data is not in expected format:", apiData);
              callback({
                draw: data.draw,
                recordsTotal: 0,
                recordsFiltered: 0,
                data: []
              });
            }
          }).catch(error => {
            console.error("Error fetching data:", error);
            callback({ draw: data.draw, recordsTotal: 0, recordsFiltered: 0, data: [] });
          });
        },
        columns: [
          { data: "subreddit", title: "Subreddit", width: '10%' },
          { data: "title", title: "Title", width: '20%' },
          { data: "selftext", title: "Body", width: '50%' },
          { data: "created_utc", title: "Created UTC", width: '150px' },
          {
            data: "id",
            title: "Post Link",
            width: '150px',
            render: function (data, type, row) {
              const postLink = `https://reddit.com/r/${row.subreddit}/comments/${data}`;
              return `<a href="${postLink}" target="_blank">View Post</a>`;
            }
          }
        ],
        pageLength: 10,
        lengthChange: true,
        deferRender: true,
        responsive: true,
        autoWidth: false,
        columnDefs: [
          {
            targets: '_all',
            createdCell: function (td) {
              $(td).css('border', '1px solid #333');
            }
          }
        ],
        buttons: ['copy', 'csv', 'excel', 'pdf', 'print'],
        language: {
          paginate: {
            first: "<<",
            previous: "<",
            next: ">",
            last: ">>"
          }
        }
      });
  
      $("#goToPageButton").on("click", function () {
        const page = parseInt($("#pageInput").val(), 10) - 1;
        if (!isNaN(page) && page >= 0) {
          $("#click-table").DataTable().page(page).draw('page');
        } else {
          alert("Please enter a valid page number.");
        }
      });
    };

    // Reinitialize the DataTable whenever these dependencies change.
    initDataTable();

    return () => {
      if ($.fn.DataTable.isDataTable("#click-table")) {
        $("#click-table").DataTable().destroy();
      }
    };
  }, [subreddit, selectedOption, sentimentKeywords, startDate, endDate]);

  // When Submit is clicked, mark table as initialized and reload the DataTable.
  const handleSubmit = async (e) => {
    e.preventDefault();
    setOption(selectedOption);
    setError(null);
    await AddSearch();
    tableInitializedRef.current = true;
    if ($.fn.DataTable.isDataTable("#click-table")) {
      $("#click-table").DataTable().ajax.reload();
    }
  };

  const runSentimentAnalysis = async () => {
    setLoadingSentiment(true);
    setError(null);
    try {
      const response = await fetch("/api/run_sentiment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subreddit: subreddit,
          option: selectedOption,
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString()
        })
      });
      if (!response.ok) throw new Error("Sentiment analysis failed.");
      const resultData = await response.json();
      setSentimentResults(resultData.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSentiment(false);
    }
  };

  // Initialize search history DataTable when searchData changes.
  useEffect(() => {
    if (searchData.length > 0) {
      if ($.fn.DataTable.isDataTable("#search-history-table")) {
        $("#search-history-table").DataTable().destroy();
      }
      $("#search-history-table").DataTable({
        data: searchData,
        columns: [
          { data: "subreddit", title: "Subreddit" },
          { data: "sentimentKeywords", title: "Keywords" },
          { 
            data: "startDate", 
            title: "Start Date",
            render: function(data) {
              return new Date(data).toLocaleDateString('en-US');
            }
          },
          { 
            data: "endDate", 
            title: "End Date",
            render: function(data) {
              return new Date(data).toLocaleDateString('en-US');
            }
          },
          { data: "created_utc", title: "Created Date" }
        ],
        paging: true,
        searching: false,
        ordering: true,
        info: true,
        autoWidth: false,
        language: {
          emptyTable: "No search history available."
        },
        dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>"
      });
    }
  }, [searchData]);

  return (
    <div className="container mt-5">
      {/* Page Header */}
      <div className="text-center">
        <h1>Data Page</h1>
        <p>This is where the searches, results and search history will be displayed.</p>
      </div>

      <div className="row mt-4">
        {/* Search Form */}
        <div className="col-md-4">
          <h2>Subreddit Search</h2>
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
                  placeholder="Enter subreddit (e.g. news)"
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
                  value={sentimentKeywords}
                  onChange={(e) => setSentimentKeywords(e.target.value)}
                  placeholder="e.g. happy"
                />
              </div>
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
                <label>Select Start Date:</label>
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
                <label>Select End Date:</label>
                <ReactDatePicker
                  selected={endDate}
                  onChange={(date) => setEndDate(date)}
                  selectsEnd
                  startDate={startDate}
                  endDate={endDate}
                  minDate={startDate}
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
              <button type="submit" className="btn btn-primary mt-2">Submit</button>
            </div>
          </form>
          {error && <p className="text-danger mt-3">Error: {error}</p>}
        </div>

        {/* Sentiment Analysis Section */}
        <div className="col-md-8">
          <h2>Sentiment Analysis</h2>
          <p>Posts within the selected date range.</p>
          <div
            style={{
              backgroundColor: '#333',
              height: '350px',
              borderRadius: '8px',
              marginBottom: '1rem'
            }}
          >
            {/* PUT CHART HERE */}
          </div>
          <button className="btn btn-secondary">Save as PNG</button>
          <div className="mt-4">
            <button className="btn btn-success" onClick={runSentimentAnalysis}>
              {loadingSentiment ? 'Analyzing...' : 'Run Sentiment Analysis'}
            </button>
          </div>
          {sentimentResults && (
            <div className="mt-3">
              <h4>Sentiment Analysis Results:</h4>
              <pre>{JSON.stringify(sentimentResults, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>

      {/* Main Results DataTable */}
      <div className="mt-5">
        <h2>Results</h2>
        <div>
          <table id="click-table" className="display">
            <thead>
              <tr>
                <th>Subreddit</th>
                <th>Title</th>
                <th>Body</th>
                <th>Created UTC</th>
                <th>Post Link</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
          <input type="number" id="pageInput" placeholder="Enter page number" />
          <button id="goToPageButton">Go to page</button>
        </div>
      </div>

      {/* Search History DataTable */}
      <div className="mt-5">
        <h2>Search History</h2>
        <div>
          <table id="search-history-table" className="display">
            <thead>
              <tr>
                <th>Subreddit</th>
                <th>Keywords</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Created Date</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Data;

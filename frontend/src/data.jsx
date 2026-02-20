import React, { useEffect, useState, useRef } from 'react';
import { ToastContainer } from 'react-toastify';

import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

import { Bar } from 'react-chartjs-2';
import ReactDatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import $ from 'jquery';
import 'datatables.net-bs5';

import 'datatables.net';
import 'datatables.net-buttons';

import 'datatables.net-bs5/css/dataTables.bootstrap5.min.css';


import * as Arrow from 'apache-arrow';
import 'pdfmake/build/vfs_fonts.js';
import 'datatables.net-buttons/js/buttons.html5.min';
import 'datatables.net-buttons/js/buttons.print.min';
import TopicTablesContainer from './Components/TopicTablesContainer';
import handleNotify from './Components/Toast';
import SearchSuggestions from './Components/SearchSuggestions';
import SearchHistory from './Components/SearchHistory';
import { FirstKeywordSentimentChart, WeightedSentimentChart } from './Components/ChartComponents';



ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);


function Data() {
  // Main Search Components
  const [subreddit, setSubreddit] = useState('TrigeminalNeuralgia');
  const [startDate, setStartDate] = useState(new Date(2024, 11, 2)); // December 2, 2024
  const [endDate, setEndDate] = useState(new Date(2024, 11, 31));     // December 31, 2024
  const [email] = useState(localStorage.getItem('email'));
  const [option, setOption] = useState("reddit_submissions, reddit_comments");
  const [includeSubmissions, setIncludeSubmissions] = useState(true);
  const [includeComments, setIncludeComments] = useState(true);
  const [debouncedSubreddit, setDebouncedSubreddit] = useState(subreddit);
  const isOptionValid = includeSubmissions || includeComments;

  const [dataMessage, setDataMessage] = useState(false);
  const [subredditIcon, setSubredditIcon] = useState(null);
  const prevSubredditRef = useRef(null);

  const [clusteringResults, setClusteringResults] = useState(null);
  const [progressMessage, setProgressMessage] = useState(""); // e.g., "Fetching Data"
  const [progressPercent, setProgressPercent] = useState(0);  // 0 to 1

  const [topicResult, setTopicResult] = useState(null);
  const [sentimentResult, setSentimentResult] = useState(null);
  const [loadingTopic, setLoadingTopic] = useState(false);
  const [loadingSentiment, setLoadingSentiment] = useState(false);
  const [error, setError] = useState(null);


  // Search History Variables
  const [isDeleting, setIsDeleting] = useState(false);
  const [searchData, setSearchData] = useState([]);
  const historyInitializedRef = useRef(false);
  const [searchError, setSearchError] = useState(null);
  const [dataLoadMessage, setDataLoadMessage] = useState(false);

  // This ref controls whether the main results DataTable should fetch data
  const tableInitializedRef = useRef(false);
  const subredditRef = useRef(subreddit);
  const startDateRef = useRef(startDate);
  const endDateRef = useRef(endDate);
  const optionRef = useRef(option);
  useEffect(() => { subredditRef.current = subreddit; }, [subreddit]);
  useEffect(() => { startDateRef.current = startDate; }, [startDate]);
  useEffect(() => { endDateRef.current = endDate; }, [endDate]);
  useEffect(() => { optionRef.current = option; }, [option]);


  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSubreddit(subreddit);
    }, 1000);
    return () => clearTimeout(handler);
  }, [subreddit]);

  const fetchArrowData = async (start, length, draw, searchValue, setError) => {
    try {
      const adjustedEndDate = new Date(endDate);
      adjustedEndDate.setHours(23, 59, 59, 999);

      // Example for fetchArrowData:
      let url = `/api/get_arrow?subreddit=${encodeURIComponent(debouncedSubreddit)}&option=${encodeURIComponent(option)}&startDate=${encodeURIComponent(startDate.toISOString())}&endDate=${encodeURIComponent(adjustedEndDate.toISOString())}`;

      if (searchValue) {
        url += `&search_value=${encodeURIComponent(searchValue)}`;
      }

      const response = await fetch(url);

      // Get the binary data
      const arrayBuffer = await response.arrayBuffer();

      if (!response.ok) {
        const errorText = new TextDecoder().decode(arrayBuffer);
        try {
          const errorJson = JSON.parse(errorText);
          setError(errorJson.error || `Error ${response.status}`);
        } catch (e) {
          setError(`Error ${response.status}: ${errorText}`);
        }

        return {
          draw: draw,
          recordsTotal: 0,
          recordsFiltered: 0,
          data: []
        };
      } else {
        setError(null);
      }

      // Use Arrow.tableFromIPC (or your preferred method) to parse the data.
      const table = await Arrow.tableFromIPC(new Uint8Array(arrayBuffer));

      // Debug the schema to verify column names.
      //console.log("Arrow table schema:", table.schema.fields.map(f => f.name));

      // Instead of converting all rows, only convert the ones for the requested page.
      const paginatedData = [];
      const totalRows = table.numRows;
      const endIndex = Math.min(totalRows, start + length);
      for (let i = start; i < endIndex; i++) {
        const row = {};
        for (let j = 0; j < table.schema.fields.length; j++) {
          const columnName = table.schema.fields[j].name;
          const value = table.getChildAt(j).get(i);
          // If this is the created_utc column, convert from Unix ms to a string.
          if (columnName === 'created_utc' && typeof value === 'number') {
            row[columnName] = new Date(value).toLocaleString();
          } else {
            row[columnName] = value;
          }
        }
        paginatedData.push(row);
      }

      return {
        draw: draw,
        recordsTotal: totalRows,
        recordsFiltered: totalRows,
        data: paginatedData
      };
    } catch (error) {
      console.error("Error processing Arrow data:", error);
      throw error;
    }
  };

  // Amplification factor for sentiment scores.
  // Adjust this value based on the typical magnitude of your scores.
  const amplifyFactor = 5;

  const getBarColor = (score) => {
    // Amplify the score.
    const amplified = score * amplifyFactor;
    // Clamp the amplified score between -1 and 1.
    const clamped = Math.max(-1, Math.min(1, amplified));
    // Map the clamped score to a hue value between 0 (red) and 120 (green).
    // If clamped == -1, hue = 0 (red)
    // If clamped == 0, hue = 60 (yellow)
    // If clamped == 1, hue = 120 (green)
    const hue = ((clamped + 1) / 2) * 120;
    // Adjust saturation and lightness as desired. Here we choose 70% saturation and 50% lightness.
    return {
      background: `hsla(${hue}, 70%, 50%, 0.5)`,
      border: `hsl(${hue}, 70%, 50%)`
    };
  };

  const getBackgroundColor = (index) => `rgba(${baseColors[index % baseColors.length]}, 0.2)`;
  const getBorderColor = (index) => `rgb(${baseColors[index % baseColors.length]})`;

  const baseColors = [
    '255, 99, 132',
    '255, 159, 64',
    '255, 205, 86',
    '75, 192, 192',
    '54, 162, 235',
    '153, 102, 255',
    '201, 203, 207'
  ];

  const staticLabels = ["#1", "#2", "#3", "#4", "#5", "#6", "#7"];
  const staticBackgroundColors = staticLabels.map((_, index) => getBackgroundColor(index));
  const staticBorderColors = staticLabels.map((_, index) => getBorderColor(index));

  const staticChartData = {
    labels: staticLabels,
    datasets: [{
      label: 'My First Dataset',
      data: [65, 59, 80, 81, 56, 55, 40],
      backgroundColor: staticBackgroundColors,
      borderColor: staticBorderColors,
      borderWidth: 1
    }]
  };

  const staticChartOptions = {
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  // 1) topic‐chart
  let topicChartData, topicChartOptions;
  if (topicResult?.groups) {
    const labels = topicResult.groups.map(g => g.llmLabel);
    const data = topicResult.groups.map(g => g.postCount);
    topicChartData = { labels, datasets: [{ label: "Posts per Cluster", data, backgroundColor: labels.map((_, i) => getBackgroundColor(i)), borderColor: labels.map((_, i) => getBorderColor(i)), borderWidth: 1 }] };
    topicChartOptions = { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: "Count" } }, x: { title: { display: true, text: "Cluster" } } }, plugins: { legend: { position: "bottom" } } };
  }

  // 2) sentiment‐chart
  // let sentimentChartData, sentimentChartOptions;
  // if (Array.isArray(sentimentResult)) {
  //   const labels = sentimentResult.map(r => `Topic ${r.topic}`);
  //   const data = sentimentResult.map(r => r.score);
  //   sentimentChartData = { labels, datasets: [{ label: "Sentiment Score", data, backgroundColor: data.map(v => getBarColor(v).background), borderColor: data.map(v => getBarColor(v).border), borderWidth: 1 }] };
  //   sentimentChartOptions = { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: "Score" } }, x: { title: { display: true, text: "Topic" } } }, plugins: { legend: { position: "bottom" } } };
  // }

  let dynamicChartData, dynamicChartOptions;

  if (clusteringResults && clusteringResults.sentiment && Array.isArray(clusteringResults.sentiment)) {
    const sentimentArray = clusteringResults.sentiment;
    const dynamicLabels = sentimentArray.map(result => `Topic ${result.topic}`);
    const dynamicData = sentimentArray.map(result => result.score);
    // Use the getBarColor function to compute colors based on the amplified score.
    const dynamicBackgroundColors = sentimentArray.map(result => getBarColor(result.score).background);
    const dynamicBorderColors = sentimentArray.map(result => getBarColor(result.score).border);


    dynamicChartData = {
      labels: dynamicLabels,
      datasets: [{
        label: 'Sentiment Score',
        data: dynamicData,
        backgroundColor: dynamicBackgroundColors,
        borderColor: dynamicBorderColors,
        borderWidth: 1
      }]
    };

    dynamicChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Sentiment Score' }
        },
        x: {
          title: { display: true, text: 'Topic' }
        }
      },
      plugins: {
        title: { display: true, text: 'Topic Sentiment Analysis' },
        legend: { position: 'bottom' }
      }
    };
  }


  // figure out which chart we actually want to show
  const isSentiment = Array.isArray(sentimentResult);
  const isTopic = !isSentiment && Array.isArray(topicResult?.groups);

  // Initialize main results DataTable on mount or when dependencies change.
  useEffect(() => {
    const initDataTable = () => {
      $("#click-table").DataTable({
        processing: true,
        serverSide: true,
        paging: true,
        pagingType: "full_numbers",
        dom: "<'row'<'col-sm-12 col-md-6'fB><'col-sm-12 col-md-6'l>>" +
          "<'row'<'col-sm-12'tr>>" +
          "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
        searching: true,
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
          // Use the Arrow endpoint instead of the old JSON endpoint.
          fetchArrowData(start, length, draw, search.value, setError)
            .then(apiData => {
              callback(apiData);
              //console.log(apiData.recordsFiltered)
              if (apiData.recordsFiltered <= 3000 && apiData.recordsFiltered > 0) {
                setDataMessage(true);
              } else {
                setDataMessage(false);
              }

              if (apiData.data && apiData.data.length > 0) {
                setDataLoadMessage(true);
                getSubredditIcon(apiData.data[0].subreddit);
              }
              else {
                setDataLoadMessage(false);
                setSubredditIcon('../public/reddit-1.svg');
              }
            })
            .catch(error => {
              console.error("Error fetching Arrow data:", error);
              callback({
                draw: data.draw,
                recordsTotal: 0,
                recordsFiltered: 0,
                data: []
              });
            });
        },
        columns: [
          { data: "subreddit", title: "Subreddit", width: '10%' },
          { data: "title", title: "Title", width: '20%' },
          {
            data: "selftext",
            title: "Body",
            width: '50%',
            className: 'wrap-text'
          },
          { data: "created_utc", title: "Created UTC", width: '150px' },
          {
            data: "id",
            title: "Post Link",
            width: '150px',
            render: {
              display: function (data, type, row) {
                return `<a href="https://reddit.com/r/${row.subreddit}/comments/${data}" target="_blank">View Post</a>`;
              },
              export: function (data, type, row) {
                return `https://reddit.com/r/${row.subreddit}/comments/${data}`;
              }
            }
          }
        ],
        pageLength: 10,
        lengthChange: true,
        deferRender: true,
        responsive: true,
        autoWidth: false,
        scrollY: '600px',
        scrollCollapse: true,
        scroller: true,
        columnDefs: [
          {
            targets: '_all',
            createdCell: function (td) {
              $(td).css('border', '1px solid #333');
            }
          }
        ],
        buttons: [
          {
            text: 'Excel',
            action: function () {
              const dt = $("#click-table").DataTable(); // Get the DataTables instance.
              const search_value = dt.search() || "";
              window.open(
                `/api/export_data?format=excel&subreddit=${subreddit}` +
                `&option=${option}` +
                `&startDate=${startDate.toISOString()}&endDate=${endDate.toISOString()}` +
                `&search_value=${encodeURIComponent(search_value)}`,
                '_blank'
              );
            }
          },
          {
            text: 'CSV',
            action: function () {
              const dt = $("#click-table").DataTable(); // Get the DataTables instance.
              const search_value = dt.search() || "";
              window.open(
                `/api/export_data?format=csv&subreddit=${subreddit}` +
                `&option=${option}` +
                `&startDate=${startDate.toISOString()}&endDate=${endDate.toISOString()}` +
                `&search_value=${encodeURIComponent(search_value)}`,
                '_blank'
              );
            }
          },
          {
            text: 'JSON',
            action: function () {
              const dt = $("#click-table").DataTable(); // Get the DataTables instance.
              const search_value = dt.search() || "";
              window.open(
                `/api/export_data?format=json&subreddit=${subreddit}` +
                `&option=${option}` +
                `&startDate=${startDate.toISOString()}&endDate=${endDate.toISOString()}` +
                `&search_value=${encodeURIComponent(search_value)}`,
                '_blank'
              );
            }
          },
          {
            extend: 'pdfHtml5',
            title: 'Table Export',
            orientation: 'landscape',
            pageSize: 'LEGAL',
            exportOptions: {
              modifier: {
                selected: null
              },
              columns: ':visible',
              orthogonal: 'export'
            },
          },
          {
            extend: 'copy',
            exportOptions: {
              columns: ':visible',
              orthogonal: 'export'
            }
          },
        ],
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
        $("#click-table").empty();
      }
    };
  }, [debouncedSubreddit, option, startDate, endDate]);

  useEffect(() => {
    if (clusteringResults && clusteringResults.groups) {
      clusteringResults.groups.forEach((group, index) => {
        const tableSelector = `#sentiment-table-${index}`;
        setTimeout(() => {
          if ($(tableSelector).length) {
            // Destroy any previous instance (if re-initializing)
            if ($.fn.DataTable.isDataTable(tableSelector)) {
              $(tableSelector).DataTable().destroy();
            }
            // Initialize DataTable on this table
            $(tableSelector).DataTable({
              paging: true,
              searching: true,
              responsive: true,
              autoWidth: false,
              scrollY: '600px',
              scrollCollapse: true,
              scroller: true,
              fixedHeader: true,
              // Add any additional DataTable options as needed.
            });
          }
        }, 500); // Delay to allow DOM updates
      });
    }
  }, [clusteringResults]);

  //Join the options for both main and search history tables to work.
  useEffect(() => {
    const selectedOptions = [];
    if (includeSubmissions) selectedOptions.push("reddit_submissions");
    if (includeComments) selectedOptions.push("reddit_comments");

    setOption(selectedOptions.join(", "));
  }, [includeSubmissions, includeComments]);

  //Issues with moving this to SearchHistory.jsx
  const AddSearch = async () => {
    try {
      const response = await fetch('/api/add_search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subreddit: `r/${subreddit}`,
          startDate: startDate,
          endDate: endDate,
          option: option,
          email: email,
        }),
      });

      if (!response.ok) {
        setError('Failed to submit and add search.');
      }
      else {
        setError(null);
      }

      const response2 = await fetch(`/api/get_search/${encodeURIComponent(email)}`);
      const data2 = await response2.json();
      setSearchData(data2.search_history || []);
    } catch (error) {
      setSearchError(error.message);
    }
  };

  // When Submit is clicked, mark table as initialized and reload the DataTable.
  const handleSubmit = async (e) => {
    e.preventDefault();
    setClusteringResults(null);
    // Build a comma-separated string, e.g., "reddit_submissions,reddit_comments"

    setError(null);
    await AddSearch();  // (Make sure AddSearch also passes along the chosen option if needed.)

  };

  useEffect(() => {
    const searchValue = `${subreddit} ${startDate.toISOString()} ${endDate.toISOString()}`;

    // Run fetchArrowData immediately
    fetchArrowData(0, 10, 1, searchValue, setError)
      .then(() => {
        tableInitializedRef.current = true;
        if ($.fn.DataTable.isDataTable("#click-table")) {
          $("#click-table").DataTable().ajax.reload();
        }
        if (subreddit) {
          getSubredditIcon(subreddit);
        }
      })
      .catch((error) => {
        console.error("Error fetching data for main datatables:", error);
      });

    // Check if SuggestionsModel is empty and populate if needed
    // For future updates either removes this check or drop the table and rebuild
    
  }, []);

    const runTopicClustering = async () => {
        const options = [
            includeSubmissions && "reddit_submissions",
            includeComments && "reddit_comments"
        ].filter(Boolean).join(",");

        setLoadingTopic(true);
        setError(null);
        setTopicResult(null);
        setProgressMessage("Submitting job...");
        setProgressPercent(0);

        try {
            // Submit the job
            const response = await fetch("/api/run_topic", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    subreddit,
                    option: options,
                    startDate: startDate.toISOString(),
                    endDate: endDate.toISOString()
                })
            });

            if (!response.ok) throw new Error("Failed to submit topic job.");

            const { job_id } = await response.json();

            // Poll for progress
            const interval = setInterval(async () => {
                try {
                    const progressRes = await fetch(`/api/progress/${job_id}`);
                    const progress = await progressRes.json();

                    if (progress.message) setProgressMessage(progress.message);
                    if (progress.percent !== undefined) setProgressPercent(progress.percent);

                    // If done, fetch the result
                    if (progress.stage === "done") {
                        clearInterval(interval);

                        const resultRes = await fetch(`/api/get_result/${job_id}`);
                        const resultData = await resultRes.json();

                        setTopicResult(resultData.result);
                        setProgressMessage("Completed");
                        setProgressPercent(1);
                        setLoadingTopic(false);
                        handleNotify("Topic Clustering complete!");
                    }

                } catch (err) {
                    clearInterval(interval);
                    setError("Progress polling failed.");
                    setLoadingTopic(false);
                }
            }, 1000); // poll every second

        } catch (err) {
            setError(err.message);
            setLoadingTopic(false);
        }
    };


  const runSentimentAnalysis = async () => {
    if (!topicResult) return;

    setLoadingSentiment(true);
    setError(null);
    setSentimentResult(null);
    setProgressMessage("Submitting job...");
    setProgressPercent(0);

    try {
      // Submit sentiment job
      const response = await fetch("/api/run_sentiment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_result: topicResult })
      });

      if (!response.ok) throw new Error("Failed to submit sentiment job.");

      const { job_id } = await response.json();

      // Poll for progress
      const interval = setInterval(async () => {
        try {
          const progressRes = await fetch(`/api/progress/${job_id}`);
          const progress = await progressRes.json();

          if (progress.message) setProgressMessage(progress.message);
          if (progress.percent !== undefined) setProgressPercent(progress.percent);

          // When done, fetch the results
          if (progress.stage === "done") {
            clearInterval(interval);

            const resultRes = await fetch(`/api/get_result/${job_id}`);
            const resultData = await resultRes.json();

            // Extract sentiment array
            const sentimentArray = Array.isArray(resultData.result)
              ? resultData.result
              : resultData.result?.sentiment || [];

            setSentimentResult(sentimentArray);
            setProgressMessage("Completed");
            setProgressPercent(1);
            setLoadingSentiment(false);
            handleNotify("Sentiment Analysis complete!");
          }
        } catch (err) {
          clearInterval(interval);
          setError("Progress polling failed.");
          setLoadingSentiment(false);
        }
      }, 1000); // poll every second

    } catch (err) {
      setError(err.message);
      setLoadingSentiment(false);
    }
  };

  useEffect(() => {
    if (clusteringResults) {
      handleNotify();
    }
  }, [clusteringResults]);

  const getSubredditIcon = async (subreddit) => {
    try {
      //console.log('Test Icon')
      if (subreddit === prevSubredditRef.current) {
        //console.log('Same subreddit, skipping API call');
        return;
      }
      //console.log('Called')
      const response = await fetch(`https://www.reddit.com/r/${subreddit}/about.json`);
      const data = await response.json();
      let subredditIcon = data.data.community_icon;

      // Remove query parameters from the URL by cutting off at the question mark
      if (subredditIcon && subredditIcon.includes('?')) {
        subredditIcon = subredditIcon.split('?')[0];
      }

      if (!subredditIcon) {
        setSubredditIcon('../public/reddit-1.svg');
      } else {
        setSubredditIcon(subredditIcon);
      }
      prevSubredditRef.current = subreddit;
    } catch (error) {
      setSubredditIcon('../public/reddit-1.svg');
    }
  };

  const handleSaveResults = async () => {
    try {
      console.log(topicResult)
      const response = await fetch("/api/save_result", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email,
          subreddit,
          startDate: startDate.toISOString().split("T")[0],
          endDate: endDate.toISOString().split("T")[0],
          groups: topicResult.groups
        })
      });

      const result = await response.json();

      if (!response.ok) {
        setError(`Failed to save: ${result.error}`);
      }
    } catch (error) {
      console.error("Error saving result:", error);
      setError("An error occurred while saving the result.");
    }
  };

  const [isTyping, setIsTyping] = useState(false);
  const handleChange = (e) => {
    setIsTyping(true);
    setSubreddit(e.target.value);
  }

  useEffect(() => {
    if (clusteringResults?.sentiment) {
      console.log("Sentiment Structure Check:", clusteringResults.sentiment);
    }
  }, [clusteringResults]);

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
                  onChange={handleChange}
                  placeholder="Enter subreddit (e.g. news)"
                />
              </div>

              {!subreddit.trim() && (
                <div className="text-danger mt-2">
                  Please enter a subreddit.
                </div>
              )}

              <SearchSuggestions
                subreddit={subreddit}
                setSubreddit={setSubreddit}
                getSubredditIcon={getSubredditIcon}
                isTyping={isTyping}
                setIsTyping={setIsTyping}
                dataLoadMessage={dataLoadMessage}
              />
            </div>

            {/* Maybe hardcode the */}
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
                  showMonthDropdown
                  showYearDropdown
                  dropdownMode="select"
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
                  showMonthDropdown
                  showYearDropdown
                  dropdownMode="select"
                />
              </div>
            </div>

            <div className="mt-4">
              <h2>Search Options</h2>
              <div className="form-group">
                <label>Choose which data to view:</label>
                <div>
                  <label className="form-check-label">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      checked={includeSubmissions}
                      onChange={() => setIncludeSubmissions(!includeSubmissions)}
                    />
                    Submissions
                  </label>
                </div>
                <div>
                  <label className="form-check-label">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      checked={includeComments}
                      onChange={() => setIncludeComments(!includeComments)}
                    />
                    Comments
                  </label>
                </div>
                {!isOptionValid && (
                  <div className="text-danger mt-2">
                    Please select at least one option.
                  </div>
                )}
              </div>
            </div>


            <div className="mt-2">
              <button type="submit" className="btn btn-primary mt-2" disabled={!isOptionValid || !subreddit.trim()}>
                Save Search
              </button>
            </div>
          </form>
          {/* {error && <p className="text-danger mt-3">Error: {error}</p>} */}
        </div>

        {/* Sentiment Analysis Section */}

        <div className="col-md-8">
          <h2>Sentiment Analysis</h2>
          <p>Posts within the selected date range.</p>

          <div style={{ backgroundColor: '#333', borderRadius: 8, padding: '1rem', marginBottom: '2rem' }}>
            {Array.isArray(sentimentResult) ? (
              <>
                <FirstKeywordSentimentChart sentiment={sentimentResult} />
                <div style={{ marginTop: '2rem', marginBottom: '2rem' }}>
                  <WeightedSentimentChart sentiment={sentimentResult} />
                </div>

              </>
            ) : topicResult?.groups ? (
              <Bar data={topicChartData} options={topicChartOptions} />
            ) : (
              <Bar data={staticChartData} options={staticChartOptions} />
            )}
          </div>



          <div className="mt-4">
            {!topicResult ? (
              <>
                <button
                  className="btn btn-success"
                  onClick={runTopicClustering}
                  disabled={loadingTopic}
                >
                  {loadingTopic ? 'Analyzing Topics…' : 'Run Topic Clustering'}
                </button>

                {loadingTopic && (
                  <div style={{ marginTop: "15px" }}>
                    <div>{progressMessage}</div>
                    <div><strong>Progress:</strong> {(progressPercent * 100).toFixed(0)}%</div>
                    <progress
                      value={progressPercent}
                      max="1"
                      style={{ width: "100%" }}
                    />
                  </div>
                )}

                {error && (
                  <div style={{ color: "red", marginTop: "10px" }}>
                    {error}
                  </div>
                )}
              </>
            ) : !sentimentResult ? (
              // Sentiment step after topic clustering
              <>
                <button
                  className="btn btn-purple"
                  onClick={runSentimentAnalysis}
                  disabled={loadingSentiment}
                >
                  {loadingSentiment ? 'Analyzing Sentiment…' : 'Start Sentiment Analysis'}
                </button>

                {loadingSentiment && (
                  <div style={{ marginTop: "15px" }}>
                    <div>{progressMessage}</div>
                    <div><strong>Progress:</strong> {(progressPercent * 100).toFixed(0)}%</div>
                    <progress
                      value={progressPercent}
                      max="1"
                      style={{ width: "100%" }}
                    />
                  </div>
                )}

                {error && (
                  <div style={{ color: "red", marginTop: "10px" }}>
                    {error}
                  </div>
                )}
              </>
            ) : (
              // All done—allow reset
              <button
                className="btn btn-outline-secondary"
                onClick={() => {
                  setTopicResult(null);
                  setSentimentResult(null);
                }}
              >
                New Analysis
              </button>
            )}
          </div>

          <ToastContainer />

        </div>

      </div>

      {/* {clusteringResults && (
  <pre>{JSON.stringify(clusteringResults, null, 2)}</pre>
)} */}

      {topicResult?.groups && (
        <div className="row mt-4">
          <div className="col-md-12">
            <h2>Topic Clustering Results
              <img src="../public/cluster.svg"
                alt="Topic Clustering Icon"
                style={{
                  maxWidth: '100px',
                  maxHeight: '100px',
                  border: '5px solid grey',
                  borderRadius: '30%',
                  marginLeft: '20px'
                }} /></h2>
            <TopicTablesContainer
              groups={topicResult.groups}
              handleSaveResults={handleSaveResults}
            />

          </div>
        </div>
      )}



      {/* Main Results DataTable */}
      <div className="mt-5">
        <div className="mt-4 text-left d-flex">
          <h2>Raw Data for r/{subreddit}</h2>
          {subredditIcon && (
            <img
              src={subredditIcon}
              alt="Subreddit Icon"
              style={{
                maxWidth: '100px',
                maxHeight: '100px',
                border: '5px solid white',
                borderRadius: '50%',
                transform: 'translateY(-30px)',
                marginLeft: '10px'
              }}
            />
          )}
        </div>
        <h5>{dataMessage && <div style={{ color: 'orange' }}>Data contains 3000 rows or less and may be insufficient for insightful topic clustering.</div>}</h5>
        <h5>{error && <div style={{ color: 'red', marginTop: '1rem' }}>Error: {error}</div>}</h5>

        <div>
          <table id="click-table" className="display">
            <thead>
              {/* <tr>
                <th>Subreddit</th>
                <th>Title</th>
                <th>Body</th>
                <th>Created UTC</th>
                <th>Post Link</th>
              </tr> */}
            </thead>
            <tbody></tbody>
          </table>
          <input type="number" id="pageInput" placeholder="Enter page number" />
          <button id="goToPageButton">Go to page</button>
        </div>
      </div>

      {/* Search History DataTable */}
      <SearchHistory
        email={email}
        setIncludeSubmissions={setIncludeSubmissions}
        setIncludeComments={setIncludeComments}
        setDebouncedSubreddit={setDebouncedSubreddit}
        setSubreddit={setSubreddit}
        setStartDate={setStartDate}
        setEndDate={setEndDate}
        setOption={setOption}
        fetchArrowData={fetchArrowData}
        setError={setError}
        tableInitializedRef={tableInitializedRef}
        getSubredditIcon={getSubredditIcon}
        searchData={searchData}
        setSearchData={setSearchData}
        searchError={searchError}
        setSearchError={setSearchError}
        historyInitializedRef={historyInitializedRef}
        setIsDeleting={setIsDeleting}
      />
    </div>
  );
}

export default Data;
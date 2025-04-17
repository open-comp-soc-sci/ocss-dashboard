import React, { useEffect, useState, useRef } from 'react';
import ReactDatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import $ from 'jquery';
import 'datatables.net-bs5';

import 'datatables.net';
import 'datatables.net-buttons';
import JSZip from 'jszip';
import pdfMake from 'pdfmake';
import * as Arrow from 'apache-arrow';
import 'pdfmake/build/vfs_fonts.js';
import 'datatables.net-buttons/js/buttons.html5.min';
import 'datatables.net-buttons/js/buttons.print.min';
import TopicTablesContainer from './TopicTablesContainer';
import handleNotify from './toast';
import SearchSuggestions from './SearchSuggestions';
import { ToastContainer } from 'react-toastify';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function Data() {
  const [subreddit, setSubreddit] = useState('TrigeminalNeuralgia');
  const [sentimentKeywords, setSentimentKeywords] = useState('');
  const [startDate, setStartDate] = useState(new Date(2024, 11, 2)); // December 2, 2024
  const [endDate, setEndDate] = useState(new Date(2024, 11, 31));     // December 31, 2024
  const [searchTerms, setSearchTerms] = useState([]);
  const [email] = useState(localStorage.getItem('email'));
  const [error, setError] = useState(null);
  const [searchError, setSearchError] = useState(null);
  const [option, setOption] = useState("reddit_submissions, reddit_comments");
  const [clusteringResults, setClusteringResults] = useState(null);
  const [loadingSentiment, setLoadingSentiment] = useState(false);
  const [searchData, setSearchData] = useState([]);
  const [dataMessage, setDataMessage] = useState(false);
  const [subredditIcon, setSubredditIcon] = useState(null);
  // Add these new state variables at the top along with your others.
  const [includeSubmissions, setIncludeSubmissions] = useState(true);
  const [includeComments, setIncludeComments] = useState(true);
  const [debouncedSubreddit, setDebouncedSubreddit] = useState(subreddit);
  const isOptionValid = includeSubmissions || includeComments;

  // This ref controls whether the main results DataTable should fetch data
  const tableInitializedRef = useRef(false);
  const subredditRef = useRef(subreddit);
  const sentimentRef = useRef(sentimentKeywords);
  const startDateRef = useRef(startDate);
  const endDateRef = useRef(endDate);
  const optionRef = useRef(option);
  useEffect(() => { subredditRef.current = subreddit; }, [subreddit]);
  useEffect(() => { sentimentRef.current = sentimentKeywords; }, [sentimentKeywords]);
  useEffect(() => { startDateRef.current = startDate; }, [startDate]);
  useEffect(() => { endDateRef.current = endDate; }, [endDate]);
  useEffect(() => { optionRef.current = option; }, [option]);



  // Fetch search history immediately on mount.
  useEffect(() => {
    const fetchSearchHistory = async () => {
      try {
        const response = await fetch(`/api/get_search/${encodeURIComponent(email)}`);

        if (!response.ok) {
          setSearchError('Search history failed to fetch from Flask.');
        }
        else {
          setSearchError(null);
        }

        const data = await response.json();
        setSearchData(data.search_history || []);
      } catch (error) {
        setSearchError(error.message);
      }
    };
    fetchSearchHistory();
  }, [email]);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSubreddit(subreddit);
    }, 1000);
    return () => clearTimeout(handler);
  }, [subreddit]);

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

      const data = await response.json();
      //console.log('Search Query:', data);
      // Refresh search history after adding a search.
      const response2 = await fetch(`/api/get_search/${encodeURIComponent(email)}`);
      const data2 = await response2.json();
      setSearchData(data2.search_history || []);
    } catch (error) {
      setSearchError(error.message);
    }
  };

  const [isDeleting, setIsDeleting] = useState(false);
  const historyInitializedRef = useRef(false);

  const RemoveSearch = async (searchId) => {
    try {
      setSearchData((prevData) => prevData.filter((item) => item.id !== searchId));
      setIsDeleting(true);

      const response = await fetch(`/api/remove_search/${searchId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        setSearchError('Failed to remove search ${searchId}.');
      }
      else {
        setSearchError(null);
      }

      //console.log(`Search ID ${searchId} successfully removed from backend.`);
    } catch (error) {
      setSearchError(error.message);
    } finally {
      const response = await fetch(`/api/get_search/${encodeURIComponent(email)}`);

      if (!response.ok) {
        setSearchError('Failed to fetch updated search history.');
      }
      else {
        setSearchError(null);
      }

      const data = await response.json();
      setSearchData(data.search_history || []);
      setIsDeleting(false);
    }
  };

  const ClearAllSearch = async () => {
    const button = document.getElementById("clear-all-btn");

    try {
      button.disabled = true;
      setIsDeleting(true);
      const response = await fetch(`/api/clear_all/${encodeURIComponent(email)}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        setSearchError("Failed to clear all searches.");
      }
      else {
        setSearchError(null);
      }

      setSearchData([]);
    } catch (error) {
    } finally {
      const response = await fetch(`/api/get_search/${encodeURIComponent(email)}`);

      if (!response.ok) {
        setSearchError("Failed to fetch updated search history.");
      }
      else {
        setSearchError(null);
      }

      const data = await response.json();
      setSearchData(data.search_history || []);
      setIsDeleting(false);
      button.disabled = false;
    }
  };

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



  // Initialize search history DataTable when searchData changes.
  useEffect(() => {
    //console.log(searchData);
    if (searchData.length === 0) {
      document.getElementById("clear-all-container").style.display = 'none';
    } else {
      document.getElementById("clear-all-container").style.display = 'block';
    }

    if (!searchData.length) {
      if ($.fn.DataTable.isDataTable("#search-history-table")) {
        $("#search-history-table").DataTable().clear().draw();
      } else {
        $("#search-history-table").DataTable({
          data: [],
          columns: [
            { data: "subreddit", title: "Subreddit" },
            {
              data: "sentimentKeywords",
              title: "Keywords",
              render: function (data) {
                return `<span class="truncate-text" title="${data}">${data}</span>`;
              }
            },
            {
              data: "startDate",
              title: "Start Date",
              render: function (data) {
                return new Date(data).toLocaleDateString('en-US');
              }
            },
            {
              data: "endDate",
              title: "End Date",
              render: function (data) {
                return new Date(data).toLocaleDateString('en-US');
              }
            },
            {
              data: "option",
              title: "Post Option",
              render: function (data) {
                if (!data) return "";

                const options = data.split(",").map(opt => opt.trim());
                const labels = options.map(opt => {
                  if (opt === "reddit_comments") return "Comments";
                  if (opt === "reddit_submissions") return "Submissions";
                  return opt;
                });

                return labels.join(", ");
              }
            },
            { data: "created_utc", title: "Created UTC" },
            {
              data: null,
              title: "Actions",
              render: function (data, type, row) {
                const searchButton = `<a href="#" class="btn btn-primary go-to-btn" data-search-id="${row.search_id}" data-subreddit="${row.subreddit}" data-sentiment="${row.sentimentKeywords}" data-start-date="${row.startDate}" data-end-date="${row.endDate}" data-option="${row.option}" disabled>Go To Search</a>`;
                const deleteButton = `<button class="btn btn-danger delete-btn" data-search-id="${row.search_id}" disabled>Delete</button>`;
                return searchButton + " " + deleteButton;
              }
            }
          ],
          order: [[5, 'desc']],
          paging: false,
          searching: false,
          ordering: false,
          info: false,
          autoWidth: false,
          language: {
            emptyTable: "No search history available."
          },
          dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
            "<'row'<'col-sm-12'tr>>" +
            "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>"
        });
      }
      return;
    }

    if ($.fn.DataTable.isDataTable("#search-history-table")) {
      $("#search-history-table").DataTable().destroy();
    }

    $("#search-history-table").DataTable({
      data: searchData,
      columns: [
        { data: "subreddit", title: "Subreddit" },
        {
          data: "sentimentKeywords",
          title: "Keywords",
          render: function (data) {
            return `<span class="truncate-text" title="${data}">${data}</span>`;
          }
        },
        {
          data: "startDate",
          title: "Start Date",
          render: function (data) {
            return new Date(data).toLocaleDateString('en-US');
          }
        },
        {
          data: "endDate",
          title: "End Date",
          render: function (data) {
            return new Date(data).toLocaleDateString('en-US');
          }
        },
        {
          data: "option",
          title: "Post Option",
          render: function (data) {
            if (!data) return "";

            const options = data.split(",").map(opt => opt.trim());
            const labels = options.map(opt => {
              if (opt === "reddit_comments") return "Comments";
              if (opt === "reddit_submissions") return "Submissions";
              return opt;
            });

            return labels.join(", ");
          }
        },
        { data: "created_utc", title: "Created UTC" },
        {
          data: null,
          title: "Actions",
          render: function (data, type, row) {
            const searchButton = `<a href="#" class="btn btn-primary go-to-btn" data-search-id="${row.search_id}" data-subreddit="${row.subreddit}" data-sentiment="${row.sentimentKeywords}" data-start-date="${row.startDate}" data-end-date="${row.endDate}" data-option="${row.option}" disabled>Go To Search</a>`;
            const deleteButton = `<button class="btn btn-danger delete-btn" data-search-id="${row.search_id}">Delete</button>`;
            return searchButton + " " + deleteButton;
          }
        }
      ],
      order: [[5, 'desc']],
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

    if (!historyInitializedRef.current) {
      historyInitializedRef.current = true;

      $(document).on("click", ".delete-btn", function () {
        const searchId = $(this).data("search-id");
        RemoveSearch(searchId);
      });
    }

    $(document).on("click", ".go-to-btn", function () {
      const subredditGo = $(this).data("subreddit").replace(/^r\//, '');
      const sentimentGo = $(this).data("sentiment");
      const startDateGo = new Date($(this).data("start-date"));
      const endDateGo = new Date($(this).data("end-date"));
      const optionGo = $(this).data("option");
      const searchValue = `${subredditGo} ${sentimentGo} ${startDateGo.toISOString()} ${endDateGo.toISOString()} ${optionGo}`;

      if (optionGo.includes('reddit_submissions')) {
        setIncludeSubmissions(true);
      }
      else {
        setIncludeSubmissions(false);
      }

      if (optionGo.includes('reddit_comments')) {
        setIncludeComments(true);
      }
      else {
        setIncludeComments(false);
      }

      setDebouncedSubreddit(subredditGo);
      setSubreddit(subredditGo);
      setSentimentKeywords(sentimentGo);
      setStartDate(startDateGo);
      setEndDate(endDateGo);
      setOption(optionGo);

      //issue where go to needs to be clicked twice
      setTimeout(() => {
        fetchArrowData(0, 10, 1, searchValue, setError).then(() => {
          tableInitializedRef.current = true;
          if ($.fn.DataTable.isDataTable("#click-table")) {
            $("#click-table").DataTable().ajax.reload();
          }
          if (subredditGo) {
            getSubredditIcon(subredditGo);
          }
        });
      }, 50);

    });

    $("#clear-all-btn").on("click", ClearAllSearch);

  }, [searchData]);

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
                getSubredditIcon(apiData.data[0].subreddit);
              }
              else {
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
                `&option=${option}&sentimentKeywords=${sentimentKeywords}` +
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
                `&option=${option}&sentimentKeywords=${sentimentKeywords}` +
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
                `&option=${option}&sentimentKeywords=${sentimentKeywords}` +
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
  }, [debouncedSubreddit, option, sentimentKeywords, startDate, endDate]);

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

  // When Submit is clicked, mark table as initialized and reload the DataTable.
  const handleSubmit = async (e) => {
    e.preventDefault();
    setClusteringResults(null);
    // Build a comma-separated string, e.g., "reddit_submissions,reddit_comments"
    const options = [];
    if (includeSubmissions) options.push("reddit_submissions");
    if (includeComments) options.push("reddit_comments");
    const combinedOption = options.join(",");
    setOption(combinedOption);

    setError(null);
    await AddSearch();  // (Make sure AddSearch also passes along the chosen option if needed.)
    tableInitializedRef.current = true;
    if ($.fn.DataTable.isDataTable("#click-table")) {
      $("#click-table").DataTable().ajax.reload();
    }
    if (subreddit) {
      getSubredditIcon(subreddit);
    }
  };

  useEffect(() => {
    // Automatically run the search on page load. Adjust to only fetch data and not add to search history.
    const searchValue = `${subreddit} ${sentimentKeywords} ${startDate.toISOString()} ${endDate.toISOString()}`;

    fetchArrowData(0, 10, 1, searchValue, setError).then(() => {
      tableInitializedRef.current = true;
      if ($.fn.DataTable.isDataTable("#click-table")) {
        $("#click-table").DataTable().ajax.reload();
      }
      if (subreddit) {
        getSubredditIcon(subreddit);
      }
    }).catch((error) => {
      console.error("Error fetching data for main datatables:", error);
    });
  }, []);

  const runTopicClustering = async () => {
    // Recalculate the combined option on the fly based on current checkbox values.
    let combinedOption = "";
    if (includeSubmissions && includeComments) {
      combinedOption = "reddit_submissions,reddit_comments";
    } else if (includeSubmissions) {
      combinedOption = "reddit_submissions";
    } else if (includeComments) {
      combinedOption = "reddit_comments";
    } else {
      combinedOption = "";
    }

    // Clear previous results to show fresh results.
    setClusteringResults(null);
    setLoadingSentiment(true);  // You might consider renaming this to reflect topic clustering loading.
    setError(null);

    try {
      const response = await fetch("/api/run_topic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subreddit,
          option: combinedOption,
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString()
        })
      });
      if (!response.ok) throw new Error("Topic clustering failed.");
      const resultData = await response.json();
      console.log("Topic Clustering Result:", resultData.result);
      setClusteringResults(resultData.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSentiment(false);
    }
  };


  const runSentimentAnalysis = async () => {
    setLoadingSentiment(true);
    setError(null);

    try {
      const response = await fetch("/api/run_sentiment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Pass the topic clustering result to the sentiment endpoint
        body: JSON.stringify({
          topic_result: clusteringResults
        })
      });
      if (!response.ok) throw new Error("Sentiment analysis failed.");
      const resultData = await response.json();
      console.log("Sentiment Analysis Result:", resultData.result);
      // Update state with the new sentiment analysis result if needed
      setClusteringResults(resultData.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSentiment(false);
    }
  };



  useEffect(() => {
    if (clusteringResults) {
      handleNotify();
    }
  }, [clusteringResults]);

  const getSubredditIcon = async (subReddit) => {
    try {
      const response = await fetch(`https://www.reddit.com/r/${subReddit}/about.json`);
      const data = await response.json();
      let subredditIcon = data.data.community_icon;

      // Remove query parameters from the URL by cutting off at the question mark
      if (subredditIcon && subredditIcon.includes('?')) {
        subredditIcon = subredditIcon.split('?')[0];
      }

      //console.log('Cleaned Subreddit Icon:', subredditIcon);

      if (!subredditIcon) {
        setSubredditIcon('../public/reddit-1.svg');
      } else {
        setSubredditIcon(subredditIcon);
      }
    } catch (error) {
      setSubredditIcon('../public/reddit-1.svg');
    }
  };

  const handleSaveResults = async () => {
    try {
      console.log(clusteringResults)
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
          groups: clusteringResults.groups
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

  const baseColors = [
    '255, 99, 132',
    '255, 159, 64',
    '255, 205, 86',
    '75, 192, 192',
    '54, 162, 235',
    '153, 102, 255',
    '201, 203, 207'
  ];

  const getBackgroundColor = (index) => `rgba(${baseColors[index % baseColors.length]}, 0.2)`;
  const getBorderColor = (index) => `rgb(${baseColors[index % baseColors.length]})`;

  const staticLabels = ["January", "February", "March", "April", "May", "June", "July"];
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
              />
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
          <div
            style={{
              backgroundColor: '#333',
              height: '350px',
              borderRadius: '8px',
              marginBottom: '1rem',
              padding: '1rem'
            }}
          >
            {clusteringResults && clusteringResults.sentiment && Array.isArray(clusteringResults.sentiment) ? (
              <Bar data={dynamicChartData} options={dynamicChartOptions} />
            ) : (
              <Bar data={staticChartData} options={staticChartOptions} />
            )}
          </div>



          <button className="btn btn-secondary">Save as PNG</button>

          <div className="mt-4">
            {/* If clusteringResults is not yet available, show the topic clustering button */}
            {!clusteringResults ? (
              <button
                className="btn btn-success"
                onClick={runTopicClustering}
                disabled={loadingSentiment}
              >
                {loadingSentiment ? 'Analyzing Topics...' : 'Run Topic Clustering'}
              </button>
            ) : (
              // Once clusteringResults is set, show the sentiment analysis button.
              <button
                className="btn btn-purple"  // make sure to define this class in your CSS
                onClick={runSentimentAnalysis}
                disabled={loadingSentiment}
              >
                {loadingSentiment ? 'Analyzing Sentiment...' : 'Start Sentiment Analysis'}
              </button>
            )}
          </div>

          <ToastContainer />

        </div>

      </div>

      {/* {clusteringResults && (
  <pre>{JSON.stringify(clusteringResults, null, 2)}</pre>
)} */}

      {clusteringResults && clusteringResults.groups && (
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
              groups={clusteringResults.groups}
              handleSaveResults={handleSaveResults}
            />

          </div>
        </div>
      )}



      {/* Main Results DataTable */}
      <div className="mt-5">
        <div className="mt-4 text-left d-flex">
          <h2>Results for r/{subreddit}</h2>
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
      <div className="mt-5">
        <h2><i className="fas fa-search me-1"></i> Search History</h2>
        {searchError && <p className="text-danger mt-3">Error: {searchError}</p>}
        <div id="clear-all-container" style={{ position: 'relative' }}>
          <button id="clear-all-btn" className="btn btn-danger" style={{ position: 'absolute', right: '50px' }}>Clear All Searches</button>
        </div>
        <div>
          <table id="search-history-table" className="display">
            <thead>
              <tr>
                <th></th>
                <th></th>
                <th></th>
                <th></th>
                <th></th>
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
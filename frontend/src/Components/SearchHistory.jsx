import React, { useState, useEffect, useRef } from 'react';
import $ from 'jquery';

const SearchHistory = ({
    email,
    setIncludeSubmissions,
    setIncludeComments,
    setDebouncedSubreddit,
    setSubreddit,
    setStartDate,
    setEndDate,
    setOption,
    fetchArrowData,
    setError,
    tableInitializedRef,
    getSubredditIcon,
    searchData,
    setSearchData,
    searchError,
    setSearchError,
    historyInitializedRef,
    setIsDeleting
}) => {
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

    useEffect(() => {
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
                                const searchButton = `<a href="#" class="btn btn-primary go-to-btn" data-search-id="${row.search_id}" data-subreddit="${row.subreddit}" data-start-date="${row.startDate}" data-end-date="${row.endDate}" data-option="${row.option}" disabled>Go To Search</a>`;
                                const deleteButton = `<button class="btn btn-danger delete-btn" data-search-id="${row.search_id}" disabled>Delete</button>`;
                                return searchButton + " " + deleteButton;
                            }
                        }
                    ],
                    order: [[4, 'desc']],
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
                        const searchButton = `<a href="#" class="btn btn-primary go-to-btn" data-search-id="${row.search_id}" data-subreddit="${row.subreddit}" data-start-date="${row.startDate}" data-end-date="${row.endDate}" data-option="${row.option}" disabled>Go To Search</a>`;
                        const deleteButton = `<button class="btn btn-danger delete-btn" data-search-id="${row.search_id}">Delete</button>`;
                        return searchButton + " " + deleteButton;
                    }
                }
            ],
            order: [[4, 'desc']],
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
            const startDateGo = new Date($(this).data("start-date"));
            const endDateGo = new Date($(this).data("end-date"));
            const optionGo = $(this).data("option");
            const searchValue = `${subredditGo} ${startDateGo.toISOString()} ${endDateGo.toISOString()} ${optionGo}`;

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
            setStartDate(startDateGo);
            setEndDate(endDateGo);
            setOption(optionGo);

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

    return (
        <div className="mt-5">
            <h2>
                <i className="fas fa-search me-1"></i> Search History
            </h2>
            {searchError && <p className="text-danger mt-3">Error: {searchError}</p>}
            <div id="clear-all-container" style={{ position: 'relative' }}>
                <button id="clear-all-btn" className="btn btn-danger" style={{ position: 'absolute', right: '50px' }} onClick={ClearAllSearch}>
                    Clear All Searches
                </button>
            </div>
            <div>
                <table id="search-history-table" className="display">
                    <thead>
                        <tr>
                            <th>Subreddit</th>
                            <th>Start Date</th>
                            <th>End Date</th>
                            <th>Post Option</th>
                            <th>Created UTC</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    );
};

export default SearchHistory;
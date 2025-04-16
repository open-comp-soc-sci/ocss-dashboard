import React, { useEffect, useState } from "react";

const Results = () => {
    const [results, setResults] = useState([]);
    const [error, setError] = useState(null);
    const [email] = useState(localStorage.getItem('email'));
    const [topicsCard, setTopicsCard] = useState([]);
    //console.log("Local email:", email);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const response = await fetch("/api/get_result");
                const data = await response.json();
                //console.log(data)
                setResults(data.results);
                setError(null);
            } catch (err) {
                setError("Failed to fetch results:", err);
            }
        };

        fetchResults();
    }, []);

    const groupResults = (results, groupSize) => {
        return results.reduce((acc, curr, index) => {
            const groupIndex = Math.floor(index / groupSize);
            if (!acc[groupIndex]) acc[groupIndex] = [];
            acc[groupIndex].push(curr);
            return acc;
        }, []);
    };

    const groupedResults = groupResults(results, 3);

    const handleRemoveResult = async (id) => {
        try {
            const response = await fetch(`/api/remove_result/${id}`, {
                method: "DELETE",
            });

            if (!response.ok) {
                setError("Error removing result.");
            } else {
                setResults((prev) => prev.filter((r) => r.id !== id));
                setError(null);
            }
        } catch (error) {
            console.error("Error removing result:", error);
        }
    };

    const handleShowTopicInfo = async (resultId) => {
        try {
            const response = await fetch(`/api/get_topics/${resultId}`);
            const data = await response.json();
            console.log(data.topics);

            if (data.error) {
                setError("Error fetching Topic Clustering data for this result.");
            } else {
                setTopicsCard(data.topics);
                setError(null);
            }
        } catch (err) {
            setError("Error fetching Topic Clustering data for this result.");
        }
    };

    return (
        <div className="container py-4">
            <div className="container py-4">
                <h1 className="mb-4">
                    <i className="fas fa-poll me-2"></i>Results
                </h1>
                {error && <p className="text-danger mt-3">Error: {error}</p>}
                <div className="overflow-auto" style={{ maxHeight: "70vh" }}>
                    {results.length === 0 && !error && (
                        <p className="text-muted">No results found.</p>
                    )}
                    {groupedResults.map((group, rowIndex) => (
                        <div className="row my-4 d-flex align-items-stretch" key={rowIndex}>
                            {group.map((resultCard, columnIndex) => (
                                <div className="col-md-4" key={columnIndex}>
                                    <div className="card h-100 p-3 shadow-lg">
                                        <h5 className="card-title">Experiment</h5>
                                        <p className="card-text"><span className="text-decoration-underline">User:</span> {resultCard.email}</p>

                                        <h5 className="card-title mt-3">Search Parameters</h5>
                                        <p className="card-text mb-0"><span className="text-decoration-underline">Subreddit:</span> r/{resultCard.subreddit}</p>
                                        <p className="card-text mb-0">
                                            <span className="text-decoration-underline">Date Range:</span> {new Date(resultCard.startDate).toLocaleDateString()} - {new Date(resultCard.endDate).toLocaleDateString()}
                                        </p>
                                        <p className="card-text mb-0">
                                            <span className="text-decoration-underline">Created:</span>{" "}
                                            {new Date(resultCard.created_utc).toLocaleString()}
                                        </p>

                                        <h5 className="card-title mt-3">Popular Topics</h5>
                                        <p className="card-text mb-0"><span className="text-decoration-underline">Topic 1 ({resultCard.topic1Count}):</span> {resultCard.topic1 || "N/A"}</p>
                                        <p className="card-text mb-0"><span className="text-decoration-underline">Topic 2 ({resultCard.topic2Count}):</span> {resultCard.topic2 || "N/A"}</p>
                                        <p className="card-text mb-0"><span className="text-decoration-underline">Topic 3 ({resultCard.topic3Count}):</span> {resultCard.topic3 || "N/A"}</p>

                                        <button
                                            type="button"
                                            className="btn btn-primary mt-2"
                                            data-bs-toggle="modal"
                                            data-bs-target="#showTopics"
                                            onClick={() => handleShowTopicInfo(resultCard.id)}
                                        >
                                            Show Topic Info
                                        </button>

                                        <div
                                            className="modal fade"
                                            id="showTopics"
                                            tabIndex="-1"
                                            aria-labelledby="showTopics"
                                            aria-hidden="true"
                                        >
                                            <div className="modal-dialog modal-lg">
                                                <div className="modal-content">
                                                    <div className="modal-header">
                                                        <h5 className="modal-title" id="showTopics">Topic Clustering Information</h5>
                                                        <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                                    </div>
                                                    <div className="modal-body">
                                                        <h1>(Testing) See if example posts can be added as well.</h1>
                                                        {error && <p className="text-danger">{error}</p>}

                                                        {!error && topicsCard.length === 0 && (
                                                            <p>No topic data available for this result.</p>
                                                        )}

                                                        {!error && topicsCard.length > 0 && (
                                                            <div className="row">
                                                                {[...topicsCard]
                                                                    .sort((a, b) => {
                                                                        if (a.group_number !== b.group_number) {
                                                                            return a.group_number - b.group_number;
                                                                        }
                                                                        return a.id - b.id;
                                                                    }).map((topic) => (
                                                                        <div key={topic.id} className="col-md-4 mb-3">
                                                                            <div className="card h-100">
                                                                                <div className="card-body">
                                                                                    <h6 className="card-title">
                                                                                        Group {topic.group_number}: {topic.topic_label}
                                                                                    </h6>
                                                                                    <p className="card-text">
                                                                                        Posts: {topic.post_count}
                                                                                    </p>
                                                                                    <ul className="small">
                                                                                        {topic.topics && topic.topics.map((word, index) => (
                                                                                            <li key={index}>{word}</li>
                                                                                        ))}
                                                                                    </ul>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                    ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {email === resultCard.email && (
                                            <button
                                                className="btn btn-danger mt-3"
                                                onClick={() => handleRemoveResult(resultCard.id)}
                                            >
                                                Remove Result
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
            </div>
        </div>


    );
};

export default Results;

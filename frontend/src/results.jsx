import React, { useEffect, useState } from "react";

const Results = () => {
    const [results, setResults] = useState([]);
    const [error, setError] = useState(null);
    const [email] = useState(localStorage.getItem('email'));
    console.log("Local email:", email);
    useEffect(() => {
        const fetchResults = async () => {
            try {
                const response = await fetch("/api/get_result");
                const data = await response.json();
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

    return (
        <div className="container py-4">
            <div className="container py-4">
                <h1 className="mb-4">
                    <i className="fas fa-poll me-2"></i>Results
                </h1>
                {error && <p className="text-danger mt-3">Error: {error}</p>}
                <div className="overflow-auto" style={{ maxHeight: "70vh" }}>
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

                                        <h5 className="card-title mt-3">Top 3 Topics</h5>
                                        <p className="card-text mb-0">Topic 1: {resultCard.topic1 || "N/A"}</p>
                                        <p className="card-text mb-0">Topic 2: {resultCard.topic2 || "N/A"}</p>
                                        <p className="card-text mb-0">Topic 3: {resultCard.topic3 || "N/A"}</p>

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

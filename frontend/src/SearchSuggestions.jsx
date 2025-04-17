import React, { useEffect, useRef, useState } from "react";

const SearchSuggestions = ({ subreddit, setSubreddit, getSubredditIcon, isTyping, setIsTyping }) => {
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [suggestionLoading, setSuggestionLoading] = useState(false);
    const suggestionCounter = useRef(0);

    const fetchSubreddits = async (query) => {
        try {
            const response = await fetch(`/api/search_list?subreddit=${query}`);
            const data = await response.json();
            return data || [];
        } catch (error) {
            console.error("Error fetching subreddits:", error);
            return [];
        }
    };

    useEffect(() => {
        if (subreddit.length > 0 && isTyping) {
            const timer = setTimeout(async () => {
                const suggestionCounterId = ++suggestionCounter.current;
                setSuggestionLoading(true);
                const subreddit_list = await fetchSubreddits(subreddit);

                if (suggestionCounterId === suggestionCounter.current) {
                    setSuggestions(subreddit_list);
                    setShowSuggestions(subreddit_list.length > 0);
                    setSuggestionLoading(false);
                }
            }, 150);

            return () => clearTimeout(timer);
        } else {
            setSuggestions([]);
            setShowSuggestions(false);
        }
    }, [subreddit, isTyping]);

    const handleSuggestionClick = (suggestion) => {
        setSubreddit(suggestion);
        getSubredditIcon(suggestion);
        setSuggestions([]);
        setShowSuggestions(false);
        setIsTyping(false);
    };

    return (
        <>
            {suggestionLoading && (
                <div className="mt-2 text-warning">Loading...</div>
            )}

            {showSuggestions && suggestions.length > 0 && (
                <ul
                    className="list-group mt-2"
                    style={{ maxHeight: "200px", overflowY: "auto" }}
                >
                    {suggestions.map((suggestion, index) => (
                        <li
                            key={index}
                            className="list-group-item"
                            style={{ cursor: "pointer" }}
                            onClick={() => handleSuggestionClick(suggestion)}
                        >
                            r/{suggestion}
                        </li>
                    ))}
                </ul>
            )}

            {!suggestions.length && !suggestionLoading && isTyping && (
                <div className="text-danger mt-2">No subreddits match the search.</div>
            )}
        </>
    );
};

export default SearchSuggestions;

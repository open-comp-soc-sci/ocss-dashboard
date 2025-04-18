import React from 'react';

const About = () => {
    return (
        <div>
            <h1>About This App</h1>

            <div>
                {/* Table of Contents */}
                <div className="mb-6">
                    <h2 className="mb-2">Contents</h2>
                    <p className="p-2">
                        Note: Only keep if we add more information, don't really think it would be necessary to have if the page is not expanded. Should we also include photos to help? Maybe photos to help describe the chart.
                    </p>
                    <ul className="list-disc list-inside text-blue-600">
                        <li><a href="#search">Subreddit Search</a></li>
                        <li><a href="#clustering">Topic Clustering</a></li>
                        <li><a href="#sentiment">Sentiment Analysis</a></li>
                        <li><a href="#datatable">Result Data Table</a></li>
                        <li><a href="#export">Data Export</a></li>
                        <li><a href="#history">Search History</a></li>
                        <li><a href="#results">Results Page</a></li>
                    </ul>
                </div>

                {/* Subreddit Search Section */}
                <section id="search" className="p-4 rounded shadow">
                    <h2 className="mb-2">
                        <i className="fas fa-search me-2"></i> Subreddit Search
                    </h2>
                    <p>
                        Use this section to look up Reddit submissions or comments from specific subreddits.
                        You can filter by date and type of post (submission or comment). The subreddit search bar will
                        give a list of the 10 most popular subreddits that match the text you have inputted.
                    </p>
                </section>

                {/* Topic Clustering Section */}
                <section id="clustering" className="p-4 rounded shadow">
                    <h2 className="mb-2">
                        <i className="fas fa-project-diagram me-2"></i> Topic Clustering
                    </h2>
                    <p>
                        Topic Clustering can be after you have selected your parameters. The posts will be grouped into topics using NLP techniques.
                        Once the topic clusters have loaded, you will have the option to view example posts, which are posts that most accurately represent the topic cluster.
                        You can also choose to publish the result, saving all of this information to the results page.
                    </p>
                </section>

                {/* Sentiment Analysis Section */}
                <section id="sentiment" className="p-4 rounded shadow">
                    <h2 className="mb-2">
                        <i className="fas fa-smile me-2"></i> Sentiment Analysis
                    </h2>
                    <p>
                        After the topic clustering completes, you can perform sentiment analysis to determine whether topic keywords are positive, negative, or neutral,
                        which will be displayed in the Sentiment Analysis Chart.
                    </p>
                </section>

                {/* Result Data Table Section */}
                <section id="results" className="p-4 rounded shadow">
                    <h2 className="mb-2">
                        <i className="fas fa-table me-2"></i> Result Data Table
                    </h2>
                    <p>
                        The results data table retrieves the data from our ClickHouse database based on your search parameters. Each post will contain a title or comment to indicate the type of post,
                        along with the post text, UTC date of when it was created, and a link (which may not work if the post has been deleted).
                    </p>
                    <p>
                        The data tables search bar will allow you to filter results based on their body text. The table uses pagination to handle large datasets. You can navigate the pages using the page buttons, the "Go to page" input, and adjust the entries per page.
                    </p>
                </section>

                {/* Data Export Section */}
                <section id="export" className="p-4 rounded shadow">
                    <h2 className="mb-2">
                        <i className="fas fa-file-export me-2"></i> Data Export
                    </h2>
                    <p>
                        Use the Excel, CSV, and JSON buttons to export your entire data search.
                        The PDF and COPY buttons will use only the visible results from the main data table based on the entries per page.
                    </p>
                </section>

                {/* Search History Section */}
                <section id="history" className="p-4 rounded shadow">
                    <h2 className="mb-2">
                        <i className="fas fa-history me-2"></i> Search History
                    </h2>
                    <p>
                        You can save your search parameters for future reference. These parameters will be stored in a table near the bottom of the data page, where you can see what you've used and easily reload the search.
                    </p>
                </section>

                {/* Results Page Section */}
                <section id="results" className="p-4 rounded shadow">
                    <h2 className="mb-2">
                        <i className="fas fa-poll me-2"></i> Results Page
                    </h2>
                    <p>
                        This page not only saves your results, but also those of other users. You will be able to see user information, their search parameters,
                        and the top 3 topics from the topic clustering result they retrieved. Each card allows you to click "Show Topic Info" to display the full data for each topic cluster.
                    </p>
                </section>
            </div>
        </div>
    );
};

export default About;

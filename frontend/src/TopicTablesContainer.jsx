import React, { useState } from 'react';
import TopicTable from './TopicTable'; // Adjust the import path if necessary

const TopicTablesContainer = ({ groups, handleSaveResults }) => {
  const [showPosts, setShowPosts] = useState(false);

  const togglePosts = () => {
    setShowPosts(prevShow => !prevShow);
  };

  return (
    <div>
      {/* Single Toggle Button for all groups */}
      <button className="btn btn-secondary mb-2" onClick={togglePosts}>
        {showPosts ? "Hide Posts" : "Show Posts"}
      </button>

      <button className="btn btn-success" onClick={handleSaveResults} style={{ marginLeft: '20px', marginBottom: '9px' }}>
        Publish Results
      </button>

      {groups.map((group, index) => (
        <div key={index} className="group-section mt-3">
          <h4>Group {group.group}: {group.llmLabel}</h4>
          <TopicTable group={group} showPosts={showPosts} />
        </div>
      ))}
    </div>
  );
};

export default TopicTablesContainer;

import React, { useEffect, useRef } from 'react';
import $ from 'jquery';
import 'datatables.net-bs5';

console.log("TopicTable component loaded");

const TopicTable = ({ group, showPosts }) => {
  const tableRef = useRef(null);

  useEffect(() => {
    console.log("TopicTable component mounted for group:", group);
    // DataTables initialization (if needed) can go here.
  }, [group]);

  return (
    <div>
      <table ref={tableRef} className="display">
        <thead>
          <tr>
            <th>Topic Number</th>
            <th>Topic Label</th>
            <th>Keywords</th>
            <th>Post Count</th>
            {showPosts && <th>Sample Posts</th>}
          </tr>
        </thead>
        <tbody>
          {group.topics.map((topic, index) => (
            <tr key={index}>
              <td>{topic.topicNumber}</td>
              <td>{topic.topicLabel}</td>
              <td>{topic.ctfidfKeywords}</td>
              <td>{topic.postCount}</td>
              {showPosts && (
                <td>
                  <pre style={{ whiteSpace: 'pre-wrap' }}>
                    {topic.samplePosts}
                  </pre>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TopicTable;

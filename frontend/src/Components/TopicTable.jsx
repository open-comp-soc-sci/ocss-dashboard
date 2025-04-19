import React, { useEffect, useRef } from 'react';
import $ from 'jquery';
import 'datatables.net-bs5';

const TopicTable = ({ group, showPosts }) => {
  const tableRef = useRef(null);

  useEffect(() => {
    // turn this table into a DataTable
    const dt = $(tableRef.current).DataTable({
      
      responsive: true,
      searching: false,
      paging: false,
      fixedHeader: true,

    });
    return () => {
      dt.destroy();
    };
  }, [group]);  // re‑init when the group changes

  return (
    <div >
      <table
        ref={tableRef}
        className="table table-dark table-striped table-bordered"
      >
        <thead>
          <tr>
            <th>Topic #</th>
            <th>Label</th>
            <th>Keywords</th>
            <th>Count</th>
            {showPosts && <th>Sample Posts</th>}
          </tr>
        </thead>
        <tbody>
          {group.topics.map((topic, i) => (
            <tr key={i}>
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

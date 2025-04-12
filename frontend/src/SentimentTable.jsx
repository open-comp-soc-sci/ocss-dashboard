import React, { useEffect, useRef } from 'react';
import $ from 'jquery';
import 'datatables.net-bs5';

console.log("SentimentTable component loaded");

const SentimentTable = ({ group }) => {
  // Declare tableRef using useRef
  const tableRef = useRef(null);

  useEffect(() => {
    console.log("SentimentTable component mounted for group:", group);
    // If you want to initialize DataTables later, you can do so here.
  }, [group]);

  return (
    <div>
      <table ref={tableRef} className="display">
        <thead>
          <tr>
            <th>Topic Number</th>
            <th>Topic Label</th>
            <th>Keywords</th>
          </tr>
        </thead>
        <tbody>
          {group.topics.map((topic, index) => (
            <tr key={index}>
              <td>{topic.topicNumber}</td>
              <td>{topic.topicLabel}</td>
              <td>{topic.ctfidfKeywords}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default SentimentTable;

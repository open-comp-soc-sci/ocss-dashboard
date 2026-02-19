import React, { useRef } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// Utility to map a score (-1 to 1) to an HSL color
function getBarColor(score) {
  const clamped = Math.max(-1, Math.min(1, score));
  const hue = ((clamped + 1) / 2) * 120;
  return {
    background: `hsla(${hue},70%,50%,0.6)`,
    border:     `hsl(${hue},70%,50%)`
  };
}

export function FirstKeywordSentimentChart({ sentiment }) {
  const chartRef = useRef(null);

  const normalized = (Array.isArray(sentiment) ? sentiment : []).map(item => {
    const s = item?.sentiment?.[0]?.sentiment || {};
    return {
      label:
        item?.sentiment?.[0]?.keyword ||
        item?.ctfidfKeywords?.split(',')[0]?.trim() ||
        `Topic ${item?.topicNumber ?? ""}`,
      negative: s.negative || { count: 0, avg_score: 0 },
      neutral: s.neutral || { count: 0, avg_score: 0 },
      positive: s.positive || { count: 0, avg_score: 0 }
    };
  });

  const filtered = normalized.filter(item => {
    const total = (item.negative.count || 0) + (item.neutral.count || 0) + (item.positive.count || 0);
    return total >= 10;
  });

  const labels = filtered.map(item => item.label);
  const negCounts = filtered.map(i => i.negative.count);
  const neuCounts = filtered.map(i => i.neutral.count);
  const posCounts = filtered.map(i => i.positive.count);
  const negScores = filtered.map(i => i.negative.avg_score);
  const neuScores = filtered.map(i => i.neutral.avg_score);
  const posScores = filtered.map(i => i.positive.avg_score);

  const data = {
    labels,
    datasets: [
      { type: 'bar',  label: 'Negative Count', data: negCounts, backgroundColor: 'rgba(255,99,132,0.5)', yAxisID: 'yCounts' },
      { type: 'bar',  label: 'Neutral Count',  data: neuCounts, backgroundColor: 'rgba(201,203,207,0.5)', yAxisID: 'yCounts' },
      { type: 'bar',  label: 'Positive Count', data: posCounts, backgroundColor: 'rgba(75,192,192,0.5)',  yAxisID: 'yCounts' },
      { type: 'line', label: 'Negative Avg',   data: negScores, borderColor: 'rgb(255,99,132)', backgroundColor: 'transparent', yAxisID: 'yScore' },
      { type: 'line', label: 'Neutral Avg',    data: neuScores, borderColor: 'rgb(201,203,207)', backgroundColor: 'transparent', yAxisID: 'yScore' },
      { type: 'line', label: 'Positive Avg',   data: posScores, borderColor: 'rgb(75,192,192)',  backgroundColor: 'transparent', yAxisID: 'yScore' },
    ]
  };

  const options = {
    responsive: true,
    scales: {
      yCounts: { type: 'linear', position: 'left', beginAtZero: true, title: { display: true, text: 'Count' } },
      yScore:  { type: 'linear', position: 'right', beginAtZero: true, grid: { drawOnChartArea: false }, title: { display: true, text: 'Avg Score' } },
      x:       { title: { display: true, text: 'Top Keyword' } }
    },
    plugins: { legend: { position: 'bottom' } }
  };

  const handleDownload = () => {
    const chart = chartRef.current;
    if (!chart) return;
    
    // Fix for React-ChartJS-2 v4+ with Chart.js v3+
    const instance = chart.current ? chart.current : chart;
    
    // This is the right way to access the chart with newer versions
    const url = instance.toBase64Image();
    const a = document.createElement('a');
    a.href = url;
    a.download = 'first-keyword-sentiment.png';
    a.click();
  };

  return (
    <div>
      <Bar ref={chartRef} data={data} options={options} />
      <button 
        onClick={handleDownload} 
        className="btn btn-secondary mt-2"
      >
        <i className="bi bi-download me-1"></i> Download First‑Keyword Chart
      </button>
    </div>
  );
}


export function WeightedSentimentChart({ sentiment }) {
  const chartRef = useRef(null);

  const normalized = (Array.isArray(sentiment) ? sentiment : []).map(item => {
    const s = item?.sentiment?.[0]?.sentiment || {};
    return {
      label:
        item?.sentiment?.[0]?.keyword ||
        item?.ctfidfKeywords?.split(',')[0]?.trim() ||
        `Topic ${item?.topicNumber ?? ""}`,
      negative: s.negative || { count: 0, avg_score: 0 },
      neutral: s.neutral || { count: 0, avg_score: 0 },
      positive: s.positive || { count: 0, avg_score: 0 }
    };
  });

  const filtered = normalized.filter(item => {
    const total = (item.negative.count || 0) + (item.neutral.count || 0) + (item.positive.count || 0);
    return total >= 10;
  });

  const labels   = filtered.map(item => item.label);
  const weighted = filtered.map(item => {
    const neg = (item.negative.count || 0) * -(item.negative.avg_score || 0);
    const pos = (item.positive.count || 0) *  (item.positive.avg_score || 0);
    const total = (item.negative.count || 0) + (item.neutral.count || 0) + (item.positive.count || 0);
    return total > 0 ? (neg + pos) / total : 0;
  });
  const bg = weighted.map(v => getBarColor(v).background);
  const bd = weighted.map(v => getBarColor(v).border);

  const data = {
    labels,
    datasets: [{
      label: 'Weighted Sentiment',
      data: weighted,
      backgroundColor: bg,
      borderColor: bd,
      borderWidth: 1
    }]
  };

  const options = {
    responsive: true,
    scales: {
      y: { min: -1, max: 1, beginAtZero: true, title: { display: true, text: 'Weighted Score' } },
      x: { title: { display: true, text: 'Top Keyword' } }
    },
    plugins: { legend: { position: 'bottom' } }
  };

  const handleDownloadWeighted = () => {
    const chart = chartRef.current;
    if (!chart) return;
    
    // Same fix for the second chart
    const instance = chart.current ? chart.current : chart;
    
    const url = instance.toBase64Image();
    const a = document.createElement('a');
    a.href = url;
    a.download = 'weighted-sentiment-chart.png';
    a.click();
  };

  return (
    <div>
      <Bar ref={chartRef} data={data} options={options} />
      <button 
        onClick={handleDownloadWeighted} 
        className="btn btn-secondary mt-2"
      >
        <i className="bi bi-download me-1"></i> Download Weighted Chart
      </button>
    </div>
  );
}

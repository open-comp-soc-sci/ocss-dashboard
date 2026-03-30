import React, { useRef } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Chart } from 'react-chartjs-2';
import 'chartjs-chart-box-and-violin-plot/build/Chart.BoxPlot.js';

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

export function FirstKeywordSentimentChart({ sentiment, minCountThreshold = 10 }) {
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
    return total >= minCountThreshold;
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


export function SignedSentimentChart({
  sentiment,
  minCountThreshold = 10,
  showMatchCounts = false
}) {
  const chartRef = useRef(null);

  const normalized = (Array.isArray(sentiment) ? sentiment : []).map(item => {
    const s = item?.sentiment?.[0]?.sentiment || {};
    return {
      label:
        item?.sentiment?.[0]?.keyword ||
        item?.ctfidfKeywords?.split(',')[0]?.trim() ||
        `Topic ${item?.topicNumber ?? ""}`,
      signed_sentiment_mean: item?.sentiment?.[0]?.sentiment?.signed_sentiment_mean,
      signed_sentiment_median: item?.sentiment?.[0]?.sentiment?.signed_sentiment_median,
      negative: s.negative || { count: 0, avg_score: 0 },
      neutral: s.neutral || { count: 0, avg_score: 0 },
      positive: s.positive || { count: 0, avg_score: 0 }
    };
  });

  const filtered = normalized.filter(item => {
    const total = (item.negative.count || 0) + (item.neutral.count || 0) + (item.positive.count || 0);
    return total >= minCountThreshold;
  });

  const labels   = filtered.map(item => item.label);
  const totals = filtered.map(item =>
    (item.negative.count || 0) + (item.neutral.count || 0) + (item.positive.count || 0)
  );
  const signedMean = filtered.map(item => {
    const signed = item?.signed_sentiment_mean;
    if (typeof signed === 'number' && Number.isFinite(signed)) {
      return signed;
    }

    // Fallback for older payloads that do not yet include signed sentiment.
    const neg = (item.negative.count || 0) * -(item.negative.avg_score || 0);
    const pos = (item.positive.count || 0) *  (item.positive.avg_score || 0);
    const total = (item.negative.count || 0) + (item.neutral.count || 0) + (item.positive.count || 0);
    return total > 0 ? (neg + pos) / total : 0;
  });
  const signedMedian = filtered.map(item => {
    const signed = item?.signed_sentiment_median;
    return typeof signed === 'number' && Number.isFinite(signed) ? signed : null;
  });
  const bg = signedMean.map(v => getBarColor(v).background);
  const bd = signedMean.map(v => getBarColor(v).border);

  const data = {
    labels,
    datasets: [{
      label: 'Mean Sentiment',
      data: signedMean,
      backgroundColor: bg,
      borderColor: bd,
      borderWidth: 1
    }]
  };

  const options = {
    responsive: true,
    animation: {
      onComplete: (anim) => {
        if (!showMatchCounts) return;
        const chart = anim.chart;
        const meta = chart.getDatasetMeta(0);
        const { ctx, chartArea } = chart;
        ctx.save();
        ctx.font = '12px sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        meta.data.forEach((barElement, index) => {
          const countValue = totals[index];
          if (typeof countValue !== 'number') return;
          const topOfBar = Math.min(barElement.y, barElement.base);
          const y = Math.max(topOfBar - 6, chartArea.top + 12);
          ctx.fillText(String(countValue), barElement.x, y);
        });
        ctx.restore();
      }
    },
    scales: {
      y: { min: -1, max: 1, beginAtZero: true, title: { display: true, text: 'Mean Signed Sentiment' } },
      x: { title: { display: true, text: 'Top Keyword' } }
    },
    plugins: {
      legend: { position: 'bottom' },
      tooltip: {
        callbacks: {
          label: (context) => {
            const index = context.dataIndex;
            const lines = [`Mean sentiment: ${signedMean[index].toFixed(3)}`];
            if (typeof signedMedian[index] === 'number') {
              lines.push(`Median sentiment: ${signedMedian[index].toFixed(3)}`);
            }
            lines.push(`Classified posts/comments: ${totals[index]}`);
            return lines;
          }
        }
      }
    }
  };

  const handleDownloadWeighted = () => {
    const chart = chartRef.current;
    if (!chart) return;
    
    // Same fix for the second chart
    const instance = chart.current ? chart.current : chart;
    
    const url = instance.toBase64Image();
    const a = document.createElement('a');
    a.href = url;
    a.download = 'signed-sentiment-chart.png';
    a.click();
  };

  return (
    <div>
      {showMatchCounts && (
        <div className="small text-muted mb-2">
          Numbers above bars show classified posts/comments per keyword.
        </div>
      )}
      <Bar
        ref={chartRef}
        data={data}
        options={options}
      />
      <button 
        onClick={handleDownloadWeighted} 
        className="btn btn-secondary mt-2"
      >
        <i className="bi bi-download me-1"></i> Download Signed Sentiment Chart
      </button>
    </div>
  );
}

export function SentimentDistributionChart({ sentiment, minCountThreshold = 10 }) {
  const chartRef = useRef(null);

  const normalized = (Array.isArray(sentiment) ? sentiment : []).map(item => {
    const s = item?.sentiment?.[0]?.sentiment || {};
    const signedScores = Array.isArray(s.signed_scores)
      ? s.signed_scores.filter((score) => typeof score === 'number' && Number.isFinite(score))
      : [];

    return {
      label:
        item?.sentiment?.[0]?.keyword ||
        item?.ctfidfKeywords?.split(',')[0]?.trim() ||
        `Topic ${item?.topicNumber ?? ""}`,
      signedScores,
      signed_sentiment_mean: s.signed_sentiment_mean,
      signed_sentiment_median: s.signed_sentiment_median,
      total:
        (s.negative?.count || 0) +
        (s.neutral?.count || 0) +
        (s.positive?.count || 0)
    };
  });

  const filtered = normalized.filter((item) =>
    item.total >= minCountThreshold && item.signedScores.length > 0
  );

  const data = {
    labels: filtered.map((item) => item.label),
    datasets: [{
      label: 'Sentiment Distribution',
      data: filtered.map((item) => item.signedScores),
      backgroundColor: filtered.map((item) => getBarColor(item.signed_sentiment_mean || 0).background),
      borderColor: filtered.map((item) => getBarColor(item.signed_sentiment_mean || 0).border),
      borderWidth: 1,
      outlierColor: '#ffffff',
      padding: 10,
      itemRadius: 0
    }]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        min: -1,
        max: 1,
        title: { display: true, text: 'Signed Sentiment Distribution' }
      },
      x: { title: { display: true, text: 'Top Keyword' } }
    },
    plugins: {
      legend: { position: 'bottom' },
      tooltip: {
        callbacks: {
          label: (context) => {
            const item = filtered[context.dataIndex];
            const mean = typeof item?.signed_sentiment_mean === 'number'
              ? item.signed_sentiment_mean.toFixed(3)
              : 'N/A';
            const median = typeof item?.signed_sentiment_median === 'number'
              ? item.signed_sentiment_median.toFixed(3)
              : 'N/A';
            return [
              `Classified posts/comments: ${item?.total ?? 0}`,
              `Mean sentiment: ${mean}`,
              `Median sentiment: ${median}`
            ];
          }
        }
      }
    }
  };

  const handleDownload = () => {
    const chart = chartRef.current;
    if (!chart) return;

    const instance = chart.current ? chart.current : chart;
    const url = instance.toBase64Image();
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sentiment-distribution-boxplot.png';
    a.click();
  };

  if (filtered.length === 0) {
    return (
      <div className="text-muted">
        No distribution data available for the current sentiment results.
      </div>
    );
  }

  return (
    <div>
      <div className="small text-muted mb-2">
        Box-and-whisker plots show how widely sentiment varies across the classified posts/comments for each keyword.
      </div>
      <div style={{ height: 420 }}>
        <Chart
          ref={chartRef}
          type="boxplot"
          data={data}
          options={options}
        />
      </div>
      <button
        onClick={handleDownload}
        className="btn btn-secondary mt-2"
      >
        <i className="bi bi-download me-1"></i> Download Distribution Chart
      </button>
    </div>
  );
}

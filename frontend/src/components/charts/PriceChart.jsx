import { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

function calculateSMA(data, period) {
  if (!data || data.length < period) return [];
  const sma = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      sma.push(null);
    } else {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      sma.push(sum / period);
    }
  }
  return sma;
}

export default function PriceChart({ data, height = 300, mode = 'intermediate' }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !data || data.length === 0) return;

    if (chartRef.current) {
      try {
        chartRef.current.remove();
      } catch (e) {
        console.warn('Failed to remove chart:', e);
      }
      chartRef.current = null;
    }

    try {
      const chart = createChart(containerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: 'transparent' },
          textColor: '#8a8fa8',
        },
        grid: {
          vertLines: { color: 'rgba(255,255,255,0.05)' },
          horzLines: { color: 'rgba(255,255,255,0.05)' },
        },
        width: containerRef.current.clientWidth,
        height: height,
        timeScale: {
          timeVisible: true,
          secondsVisible: false,
        },
      });

      const chartData = data
        .filter(d => d && d.date && d.close != null && !isNaN(d.close))
        .map(d => ({
          time: d.date,
          open: (d.open != null && !isNaN(d.open)) ? d.open : d.close,
          high: (d.high != null && !isNaN(d.high)) ? d.high : d.close,
          low: (d.low != null && !isNaN(d.low)) ? d.low : d.close,
          close: d.close,
        }));

      if (chartData.length === 0) {
        console.warn('No valid data for chart');
        chart.remove();
        return;
      }

      if (mode === 'beginner') {
        const lineSeries = chart.addLineSeries({
          color: '#daa520',
          lineWidth: 2,
        });
        lineSeries.setData(chartData.map(d => ({ time: d.time, value: d.close })));
      } else {
        const candlestickSeries = chart.addCandlestickSeries({
          upColor: '#8FBC8F',
          downColor: '#e05b5b',
          borderUpColor: '#8FBC8F',
          borderDownColor: '#e05b5b',
          wickUpColor: '#8FBC8F',
          wickDownColor: '#e05b5b',
        });
        candlestickSeries.setData(chartData);

        if (mode === 'expert') {
          const sma200 = calculateSMA(data, 200);
          const smaLineData = chartData.map((d, i) => ({
            time: d.time,
            value: sma200[i],
          })).filter(d => d.value !== null);
          
          const smaSeries = chart.addLineSeries({
            color: '#4a90d9',
            lineWidth: 1,
          });
          smaSeries.setData(smaLineData);
        }
      }

      chart.timeScale().fitContent();
      chartRef.current = chart;

      const handleResize = () => {
        if (containerRef.current && chartRef.current) {
          try {
            chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
          } catch (e) {
            console.warn('Failed to resize chart:', e);
          }
        }
      };

      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartRef.current) {
          try {
            chartRef.current.remove();
          } catch (e) {
            console.warn('Failed to remove chart on cleanup:', e);
          }
          chartRef.current = null;
        }
      };
    } catch (e) {
      console.error('Failed to create chart:', e);
    }
  }, [data, height, mode]);

  if (!data || data.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card2)', borderRadius: '10px', color: 'var(--text-muted)' }}>
        No data available
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: '100%', height }} />;
}
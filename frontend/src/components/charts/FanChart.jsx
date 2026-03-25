import { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

export default function FanChart({ 
  historicalData, 
  percentile25, 
  percentile50, 
  percentile75, 
  horizonDays, 
  height = 300 
}) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (chartRef.current) {
      chartRef.current.remove();
    }

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
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.08)',
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#8FBC8F',
      downColor: '#e05b5b',
      borderUpColor: '#8FBC8F',
      borderDownColor: '#e05b5b',
      wickUpColor: '#8FBC8F',
      wickDownColor: '#e05b5b',
    });

    if (historicalData && historicalData.length > 0) {
      const candleData = historicalData.map(d => ({
        time: d.date || d.time,
        open: d.open ?? d.close - 1,
        high: d.high ?? d.close + 2,
        low: d.low ?? d.close - 2,
        close: d.close,
      }));
      candlestickSeries.setData(candleData);
    }

    const p25Line = chart.addLineSeries({
      color: '#e05b5b',
      lineWidth: 1,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
    });

    const p50Line = chart.addLineSeries({
      color: '#DAA520',
      lineWidth: 2,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
    });

    const p75Line = chart.addLineSeries({
      color: '#4caf82',
      lineWidth: 1,
      lineStyle: 2,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
    });

    if (percentile50 && percentile50.length > 0) {
      const startTime = historicalData?.[historicalData.length - 1]?.date || Date.now() / 1000;
      const daySeconds = 86400;
      
      const p25Data = percentile25?.map((val, i) => ({
        time: startTime + (i + 1) * daySeconds,
        value: val,
      })) || [];

      const p50Data = percentile50.map((val, i) => ({
        time: startTime + (i + 1) * daySeconds,
        value: val,
      }));

      const p75Data = percentile75?.map((val, i) => ({
        time: startTime + (i + 1) * daySeconds,
        value: val,
      })) || [];

      p25Line.setData(p25Data);
      p50Line.setData(p50Data);
      p75Line.setData(p75Data);
    }

    chart.timeScale().fitContent();

    chartRef.current = chart;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [historicalData, percentile25, percentile50, percentile75, horizonDays, height]);

  const hasData = (percentile50 && percentile50.length > 0) || (historicalData && historicalData.length > 0);

  if (!hasData) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card2)', borderRadius: '10px', color: 'var(--text-muted)' }}>
        No prediction data
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: '100%', height }} />;
}
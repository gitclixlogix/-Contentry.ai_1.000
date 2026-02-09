'use client';

import { useRef, useEffect, useCallback, useId } from 'react';
import dynamic from 'next/dynamic';

const ApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

/**
 * ClickableBarChart - A wrapper around ApexCharts bar chart that handles click events
 * specifically for drill-down functionality.
 */
export default function ClickableBarChart({ 
  chartData, 
  chartOptions, 
  onBarClick,
  categories = []
}) {
  const chartRef = useRef(null);
  const chartId = useId();

  // Create a stable callback reference
  const handleBarClick = useCallback((index, category) => {
    if (onBarClick && index >= 0) {
      onBarClick(index, category);
    }
  }, [onBarClick]);

  // Enhanced options with click handling
  const enhancedOptions = {
    ...chartOptions,
    chart: {
      ...chartOptions?.chart,
      id: chartId,
      toolbar: { show: false },
      selection: { enabled: true },
      events: {
        dataPointSelection: (event, chartContext, config) => {
          if (config.dataPointIndex >= 0) {
            const category = categories[config.dataPointIndex] || config.dataPointIndex;
            handleBarClick(config.dataPointIndex, category);
          }
        },
        click: (event, chartContext, config) => {
          // Handle clicks on chart area - try to determine which bar was clicked
          if (config?.dataPointIndex !== undefined && config.dataPointIndex >= 0) {
            const category = categories[config.dataPointIndex] || config.dataPointIndex;
            handleBarClick(config.dataPointIndex, category);
          }
        }
      }
    },
    states: {
      hover: { 
        filter: { type: 'lighten', value: 0.1 } 
      },
      active: { 
        filter: { type: 'darken', value: 0.2 },
        allowMultipleDataPointsSelection: false
      }
    }
  };

  // Add click listener to the chart container for fallback handling
  useEffect(() => {
    const container = chartRef.current;
    if (!container) return;

    const handleChartClick = (e) => {
      // Prevent event bubbling that might cause navigation
      e.stopPropagation();
      
      // Only handle clicks within this specific chart container
      const chartContainer = e.target.closest(`[data-chart-id="${chartId}"]`);
      if (!chartContainer) return;
      
      // Try to find the clicked bar element
      const barElement = e.target.closest('.apexcharts-bar-area');
      if (barElement) {
        // Get the data index from the bar's attributes or position
        const seriesGroup = barElement.closest('.apexcharts-series');
        if (seriesGroup) {
          // Find all bars in this series and determine index
          const bars = seriesGroup.querySelectorAll('.apexcharts-bar-area');
          const index = Array.from(bars).indexOf(barElement);
          if (index >= 0) {
            const category = categories[index] || index;
            handleBarClick(index, category);
            e.preventDefault();
          }
        }
      }
    };

    // Use capture phase to intercept clicks
    container.addEventListener('click', handleChartClick, true);
    
    return () => {
      container.removeEventListener('click', handleChartClick, true);
    };
  }, [handleBarClick, categories, chartId]);

  return (
    <div 
      ref={chartRef} 
      data-chart-id={chartId}
      style={{ height: '100%', width: '100%', cursor: 'pointer' }}
    >
      <ApexChart
        type="bar"
        options={enhancedOptions}
        series={chartData}
        height="100%"
        width="100%"
      />
    </div>
  );
}

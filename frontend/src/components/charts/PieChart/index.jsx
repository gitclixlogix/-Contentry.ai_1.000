'use client';
import dynamic from 'next/dynamic';
const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

const PieChart = (props) => {
  const { chartData, chartOptions } = props;

  return (
    <Chart
      options={chartOptions}
      series={chartData}
      type="pie"
      width="100%"
      height="100%"
    />
  );
};

export default PieChart;

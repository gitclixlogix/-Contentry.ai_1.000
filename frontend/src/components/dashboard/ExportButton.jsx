'use client';

import { Button, Icon, Tooltip, useToast } from '@chakra-ui/react';
import { FaFileDownload, FaSpinner } from 'react-icons/fa';
import { useState } from 'react';
import { createAuthenticatedAxios } from '@/lib/api';

/**
 * ExportButton - Universal export to CSV button for dashboard widgets
 * 
 * @param {string} widgetType - Type of widget to export: overview, team-performance, content-strategy, approval-kpis, action-items, top-posts
 * @param {string} dateRange - Current date range filter
 * @param {string} customStart - Custom start date (if applicable)
 * @param {string} customEnd - Custom end date (if applicable)
 * @param {string} format - Export format: csv or json
 * @param {string} size - Button size
 */
export default function ExportButton({
  widgetType,
  dateRange = 'last_30_days',
  customStart,
  customEnd,
  format = 'csv',
  size = 'sm',
  variant = 'ghost',
  label = 'Export',
  showLabel = false,
}) {
  const [isExporting, setIsExporting] = useState(false);
  const toast = useToast();

  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      // Use authenticated axios with HttpOnly cookie (ARCH-022)
      const api = createAuthenticatedAxios();
      const userId = localStorage.getItem('userId');
      
      let url = `/dashboard/export/${widgetType}?date_range=${dateRange}&format=${format}`;
      
      if (customStart && customEnd) {
        url += `&custom_start=${customStart}&custom_end=${customEnd}`;
      }

      const response = await api.get(url, {
        headers: {
          'x-user-id': userId,
        },
      });

      const data = response.data;

      if (format === 'csv') {
        // Create and download CSV file
        const blob = new Blob([data.data], { type: 'text/csv' });
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = data.filename || `export_${widgetType}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
      } else {
        // Download JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `export_${widgetType}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
      }

      toast({
        title: 'Export successful',
        description: `${widgetType} data exported to ${format.toUpperCase()}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Export error:', error);
      toast({
        title: 'Export failed',
        description: 'Could not export data. Please try again.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Tooltip label={`Export to ${format.toUpperCase()}`} hasArrow>
      <Button
        size={size}
        variant={variant}
        onClick={handleExport}
        isLoading={isExporting}
        loadingText="Exporting..."
        leftIcon={isExporting ? <FaSpinner /> : <FaFileDownload />}
        aria-label={`Export ${widgetType} to ${format}`}
      >
        {showLabel && label}
      </Button>
    </Tooltip>
  );
}

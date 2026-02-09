/**
 * DataTable - Enhanced Reusable table component
 * 
 * Features:
 * - Server-side and client-side pagination
 * - Sorting and filtering
 * - Row selection with bulk actions
 * - Export to CSV/JSON
 * - Customizable columns and actions
 * 
 * Props:
 * - data (array, required): Table data
 * - columns (array, required): Column definitions [{key, label, sortable, render, exportable}]
 * - pagination (object): Pagination config {type: 'server'|'client', pageSize, currentPage, totalCount, onPageChange}
 * - sorting (object): Sorting config {enabled, sortKey, sortOrder, onSortChange}
 * - filtering (object): Filtering config {enabled, searchKey, searchValue, onSearchChange, placeholder}
 * - isLoading (boolean): Loading state
 * - emptyMessage (string): Message when no data
 * - onRowClick (function): Row click handler
 * - selectable (object): Selection config {enabled, selectedIds, onSelectionChange}
 * - actions (function): Row actions renderer (row) => ReactNode
 * - bulkActions (array): Bulk action buttons [{label, icon, colorScheme, onClick}]
 * - exportable (object): Export config {enabled, filename, formats: ['csv', 'json']}
 * - title (string): Table title
 * - toolbar (ReactNode): Custom toolbar content
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Flex,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Button,
  HStack,
  VStack,
  Checkbox,
  Skeleton,
  Icon,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Badge,
  Tooltip,
  useColorModeValue,
  useToast
} from '@chakra-ui/react';
import { 
  Search, 
  ChevronUp, 
  ChevronDown, 
  ChevronLeft, 
  ChevronRight,
  Download,
  MoreVertical,
  Trash2,
  CheckSquare,
  XSquare,
  FileText,
  FileJson
} from 'lucide-react';

// Export utilities
const exportToCSV = (data, columns, filename) => {
  const exportableCols = columns.filter(c => c.exportable !== false);
  const headers = exportableCols.map(c => c.label || c.key);
  const rows = data.map(row => 
    exportableCols.map(c => {
      const value = row[c.key];
      // Handle values that might contain commas or quotes
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value ?? '';
    })
  );
  
  const csvContent = [
    headers.join(','),
    ...rows.map(r => r.join(','))
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
};

const exportToJSON = (data, columns, filename) => {
  const exportableCols = columns.filter(c => c.exportable !== false);
  const exportData = data.map(row => {
    const obj = {};
    exportableCols.forEach(c => {
      obj[c.key] = row[c.key];
    });
    return obj;
  });
  
  const jsonContent = JSON.stringify(exportData, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
};

export function DataTable({
  data = [],
  columns = [],
  pagination = {},
  sorting = {},
  filtering = {},
  isLoading = false,
  emptyMessage = 'No data available',
  onRowClick,
  selectable = {},
  actions,
  bulkActions = [],
  exportable = {},
  title,
  toolbar,
  stickyHeader = false,
  size = 'md',
  variant = 'simple'
}) {
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const headerBg = useColorModeValue('gray.50', 'gray.700');
  const selectedBg = useColorModeValue('blue.50', 'blue.900');
  const toolbarBg = useColorModeValue('gray.50', 'gray.700');
  
  // Client-side pagination state
  const [clientPage, setClientPage] = useState(1);
  const [clientSearch, setClientSearch] = useState('');
  const [clientSort, setClientSort] = useState({ key: null, order: 'asc' });
  
  const isServerPagination = pagination.type === 'server';
  const pageSize = pagination.pageSize || 10;
  
  // Process data for client-side operations
  const processedData = useMemo(() => {
    if (isServerPagination) return data;
    
    let result = [...data];
    
    // Client-side search
    if (filtering.enabled && clientSearch) {
      const searchLower = clientSearch.toLowerCase();
      result = result.filter(row => {
        const searchKey = filtering.searchKey;
        if (searchKey) {
          return String(row[searchKey]).toLowerCase().includes(searchLower);
        }
        // Search all string fields
        return Object.values(row).some(
          val => String(val).toLowerCase().includes(searchLower)
        );
      });
    }
    
    // Client-side sorting
    if (sorting.enabled && clientSort.key) {
      result.sort((a, b) => {
        const aVal = a[clientSort.key];
        const bVal = b[clientSort.key];
        const order = clientSort.order === 'asc' ? 1 : -1;
        
        if (aVal === bVal) return 0;
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;
        
        return aVal > bVal ? order : -order;
      });
    }
    
    return result;
  }, [data, clientSearch, clientSort, filtering, sorting, isServerPagination]);
  
  // Paginated data for client-side
  const paginatedData = useMemo(() => {
    if (isServerPagination) return processedData;
    
    const startIndex = (clientPage - 1) * pageSize;
    return processedData.slice(startIndex, startIndex + pageSize);
  }, [processedData, clientPage, pageSize, isServerPagination]);
  
  // Total pages calculation
  const totalCount = isServerPagination ? pagination.totalCount : processedData.length;
  const totalPages = Math.ceil(totalCount / pageSize);
  const currentPage = isServerPagination ? pagination.currentPage : clientPage;
  
  // Selection helpers
  const selectedCount = selectable.selectedIds?.length || 0;
  const hasSelection = selectedCount > 0;
  
  // Handlers
  const handlePageChange = (newPage) => {
    if (isServerPagination && pagination.onPageChange) {
      pagination.onPageChange(newPage);
    } else {
      setClientPage(newPage);
    }
  };
  
  const handleSearch = (value) => {
    if (isServerPagination && filtering.onSearchChange) {
      filtering.onSearchChange(value);
    } else {
      setClientSearch(value);
      setClientPage(1);
    }
  };
  
  const handleSort = (key) => {
    if (!sorting.enabled) return;
    
    const column = columns.find(c => c.key === key);
    if (!column?.sortable) return;
    
    if (isServerPagination && sorting.onSortChange) {
      const newOrder = sorting.sortKey === key && sorting.sortOrder === 'asc' ? 'desc' : 'asc';
      sorting.onSortChange(key, newOrder);
    } else {
      setClientSort(prev => ({
        key,
        order: prev.key === key && prev.order === 'asc' ? 'desc' : 'asc'
      }));
    }
  };
  
  const handleSelectAll = useCallback(() => {
    if (!selectable.enabled || !selectable.onSelectionChange) return;
    
    const allIds = paginatedData.map(row => row.id);
    const allSelected = allIds.every(id => selectable.selectedIds?.includes(id));
    
    if (allSelected) {
      selectable.onSelectionChange([]);
    } else {
      selectable.onSelectionChange(allIds);
    }
  }, [paginatedData, selectable]);
  
  const handleSelectRow = useCallback((id) => {
    if (!selectable.enabled || !selectable.onSelectionChange) return;
    
    const newSelection = selectable.selectedIds?.includes(id)
      ? selectable.selectedIds.filter(i => i !== id)
      : [...(selectable.selectedIds || []), id];
    
    selectable.onSelectionChange(newSelection);
  }, [selectable]);
  
  const handleClearSelection = useCallback(() => {
    if (selectable.onSelectionChange) {
      selectable.onSelectionChange([]);
    }
  }, [selectable]);
  
  // Export handlers
  const handleExport = useCallback((format) => {
    const filename = exportable.filename || 'export';
    const exportData = processedData; // Export all filtered data, not just current page
    
    try {
      if (format === 'csv') {
        exportToCSV(exportData, columns, filename);
      } else if (format === 'json') {
        exportToJSON(exportData, columns, filename);
      }
      
      toast({
        title: 'Export successful',
        description: `Exported ${exportData.length} rows to ${format.toUpperCase()}`,
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Export failed',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
    }
  }, [processedData, columns, exportable.filename, toast]);
  
  // Get current sort state
  const sortKey = isServerPagination ? sorting.sortKey : clientSort.key;
  const sortOrder = isServerPagination ? sorting.sortOrder : clientSort.order;
  const searchValue = isServerPagination ? filtering.searchValue : clientSearch;
  
  // Render sort icon
  const renderSortIcon = (key) => {
    if (sortKey !== key) return null;
    return sortOrder === 'asc' 
      ? <Icon as={ChevronUp} boxSize={4} ml={1} />
      : <Icon as={ChevronDown} boxSize={4} ml={1} />;
  };
  
  // Skeleton loading rows
  const renderLoadingRows = () => {
    return Array.from({ length: pageSize }).map((_, i) => (
      <Tr key={`skeleton-${i}`}>
        {selectable.enabled && <Td><Skeleton height="20px" width="20px" /></Td>}
        {columns.map((col, j) => (
          <Td key={`skeleton-${i}-${j}`}>
            <Skeleton height="20px" />
          </Td>
        ))}
        {actions && <Td><Skeleton height="20px" width="80px" /></Td>}
      </Tr>
    ));
  };

  return (
    <Box bg={bgColor} borderRadius="lg" border="1px" borderColor={borderColor} overflow="hidden">
      {/* Title & Toolbar Header */}
      {(title || toolbar || exportable.enabled || (hasSelection && bulkActions.length > 0)) && (
        <Flex 
          p={4} 
          borderBottom="1px" 
          borderColor={borderColor} 
          justify="space-between" 
          align="center"
          bg={hasSelection ? selectedBg : 'transparent'}
          flexWrap="wrap"
          gap={3}
        >
          {/* Left side: Title or Selection info */}
          <HStack spacing={3}>
            {hasSelection ? (
              <>
                <Badge colorScheme="blue" fontSize="md" px={3} py={1}>
                  {selectedCount} selected
                </Badge>
                <Tooltip label="Clear selection">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleClearSelection}
                    leftIcon={<Icon as={XSquare} boxSize={4} />}
                  >
                    Clear
                  </Button>
                </Tooltip>
              </>
            ) : title ? (
              <Text fontWeight="semibold" fontSize="lg">{title}</Text>
            ) : null}
          </HStack>
          
          {/* Right side: Bulk actions or toolbar */}
          <HStack spacing={2} flexWrap="wrap">
            {hasSelection && bulkActions.length > 0 ? (
              // Show bulk actions when items selected
              bulkActions.map((action, idx) => (
                <Button
                  key={idx}
                  size="sm"
                  colorScheme={action.colorScheme || 'gray'}
                  leftIcon={action.icon ? <Icon as={action.icon} boxSize={4} /> : undefined}
                  onClick={() => action.onClick(selectable.selectedIds)}
                  variant={action.variant || 'solid'}
                >
                  {action.label}
                </Button>
              ))
            ) : (
              // Show regular toolbar
              <>
                {toolbar}
                {exportable.enabled && (
                  <Menu>
                    <MenuButton
                      as={Button}
                      size="sm"
                      variant="outline"
                      leftIcon={<Icon as={Download} boxSize={4} />}
                    >
                      Export
                    </MenuButton>
                    <MenuList>
                      {(!exportable.formats || exportable.formats.includes('csv')) && (
                        <MenuItem 
                          icon={<Icon as={FileText} boxSize={4} />}
                          onClick={() => handleExport('csv')}
                        >
                          Export as CSV
                        </MenuItem>
                      )}
                      {(!exportable.formats || exportable.formats.includes('json')) && (
                        <MenuItem 
                          icon={<Icon as={FileJson} boxSize={4} />}
                          onClick={() => handleExport('json')}
                        >
                          Export as JSON
                        </MenuItem>
                      )}
                    </MenuList>
                  </Menu>
                )}
              </>
            )}
          </HStack>
        </Flex>
      )}
      
      {/* Search/Filter Header */}
      {filtering.enabled && (
        <Flex p={4} borderBottom="1px" borderColor={borderColor} gap={4} flexWrap="wrap">
          <InputGroup maxW="320px">
            <InputLeftElement pointerEvents="none">
              <Icon as={Search} color="gray.400" />
            </InputLeftElement>
            <Input
              placeholder={filtering.placeholder || 'Search...'}
              value={searchValue}
              onChange={(e) => handleSearch(e.target.value)}
              size={size}
            />
          </InputGroup>
          {pagination.type !== 'none' && pagination.onPageSizeChange && (
            <Select 
              maxW="120px" 
              value={pageSize}
              onChange={(e) => pagination.onPageSizeChange(Number(e.target.value))}
              size={size}
            >
              <option value={10}>10 rows</option>
              <option value={25}>25 rows</option>
              <option value={50}>50 rows</option>
              <option value={100}>100 rows</option>
            </Select>
          )}
        </Flex>
      )}
      
      {/* Table */}
      <Box overflowX="auto">
        <Table variant={variant} size={size}>
          <Thead bg={headerBg} position={stickyHeader ? 'sticky' : 'relative'} top={0} zIndex={1}>
            <Tr>
              {selectable.enabled && (
                <Th w="40px">
                  <Checkbox
                    isChecked={paginatedData.length > 0 && paginatedData.every(row => selectable.selectedIds?.includes(row.id))}
                    isIndeterminate={paginatedData.some(row => selectable.selectedIds?.includes(row.id)) && !paginatedData.every(row => selectable.selectedIds?.includes(row.id))}
                    onChange={handleSelectAll}
                  />
                </Th>
              )}
              {columns.map((col) => (
                <Th 
                  key={col.key}
                  cursor={col.sortable ? 'pointer' : 'default'}
                  onClick={() => col.sortable && handleSort(col.key)}
                  _hover={col.sortable ? { bg: hoverBg } : {}}
                  whiteSpace="nowrap"
                  width={col.width}
                >
                  <Flex align="center">
                    {col.label}
                    {col.sortable && renderSortIcon(col.key)}
                  </Flex>
                </Th>
              ))}
              {actions && <Th w="100px">Actions</Th>}
            </Tr>
          </Thead>
          <Tbody>
            {isLoading ? (
              renderLoadingRows()
            ) : paginatedData.length === 0 ? (
              <Tr>
                <Td 
                  colSpan={columns.length + (selectable.enabled ? 1 : 0) + (actions ? 1 : 0)} 
                  textAlign="center" 
                  py={8}
                >
                  <Text color="gray.500">{emptyMessage}</Text>
                </Td>
              </Tr>
            ) : (
              paginatedData.map((row, index) => (
                <Tr 
                  key={row.id || index}
                  cursor={onRowClick ? 'pointer' : 'default'}
                  onClick={() => onRowClick?.(row)}
                  _hover={{ bg: hoverBg }}
                  bg={selectable.selectedIds?.includes(row.id) ? selectedBg : 'transparent'}
                >
                  {selectable.enabled && (
                    <Td onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        isChecked={selectable.selectedIds?.includes(row.id)}
                        onChange={() => handleSelectRow(row.id)}
                      />
                    </Td>
                  )}
                  {columns.map((col) => (
                    <Td key={col.key}>
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </Td>
                  ))}
                  {actions && (
                    <Td onClick={(e) => e.stopPropagation()}>
                      {actions(row)}
                    </Td>
                  )}
                </Tr>
              ))
            )}
          </Tbody>
        </Table>
      </Box>
      
      {/* Pagination Footer */}
      {pagination.type !== 'none' && totalPages > 0 && (
        <Flex 
          p={4} 
          borderTop="1px" 
          borderColor={borderColor} 
          justify="space-between" 
          align="center"
          flexWrap="wrap"
          gap={2}
        >
          <Text fontSize="sm" color="gray.600">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} results
          </Text>
          <HStack spacing={2}>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handlePageChange(currentPage - 1)}
              isDisabled={currentPage <= 1 || isLoading}
              leftIcon={<Icon as={ChevronLeft} boxSize={4} />}
            >
              Previous
            </Button>
            <HStack spacing={1}>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                return (
                  <Button
                    key={pageNum}
                    size="sm"
                    variant={currentPage === pageNum ? 'solid' : 'outline'}
                    colorScheme={currentPage === pageNum ? 'brand' : 'gray'}
                    onClick={() => handlePageChange(pageNum)}
                    isDisabled={isLoading}
                    minW="40px"
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </HStack>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handlePageChange(currentPage + 1)}
              isDisabled={currentPage >= totalPages || isLoading}
              rightIcon={<Icon as={ChevronRight} boxSize={4} />}
            >
              Next
            </Button>
          </HStack>
        </Flex>
      )}
    </Box>
  );
}

export default DataTable;

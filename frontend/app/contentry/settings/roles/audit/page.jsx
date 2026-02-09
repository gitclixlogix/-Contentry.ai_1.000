'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Flex,
  Text,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  useColorModeValue,
  VStack,
  HStack,
  Badge,
  Icon,
  Spinner,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Select,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  Card,
  CardBody,
  Tooltip,
} from '@chakra-ui/react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Download,
  FileText,
  FileJson,
  Filter,
  ChevronLeft,
  ChevronDown,
  Activity,
  Users,
  Calendar,
  Shield,
  Edit2,
  Trash2,
  Copy,
  UserPlus,
  UserMinus,
  RefreshCw,
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

// Action type icons and colors
const ACTION_CONFIG = {
  'role.created': { icon: Shield, color: 'green', label: 'Role Created' },
  'role.updated': { icon: Edit2, color: 'blue', label: 'Role Updated' },
  'role.deleted': { icon: Trash2, color: 'red', label: 'Role Deleted' },
  'role.duplicated': { icon: Copy, color: 'blue', label: 'Role Duplicated' },
  'user.role.assigned': { icon: UserPlus, color: 'green', label: 'Role Assigned' },
  'user.role.removed': { icon: UserMinus, color: 'orange', label: 'Role Removed' },
};

export default function AuditLogPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const router = useRouter();
  const toast = useToast();

  // State
  const [auditEntries, setAuditEntries] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [page, setPage] = useState(1);
  const [totalEntries, setTotalEntries] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const limit = 20;

  // Colors
  const bgColor = useColorModeValue('white', 'navy.800');
  const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');
  const textColor = useColorModeValue('gray.800', 'white');
  const textSecondary = useColorModeValue('gray.600', 'gray.400');
  const cardBg = useColorModeValue('gray.50', 'navy.700');

  // Fetch audit data
  const fetchData = useCallback(async () => {
    if (!user?.id) return;

    setIsLoading(true);
    try {
      const [auditRes, statsRes] = await Promise.all([
        axios.get(`${getApiUrl()}/roles/audit`, {
          headers: { 'X-User-ID': user.id },
          params: { 
            page, 
            limit,
            action: actionFilter || undefined
          },
        }),
        axios.get(`${getApiUrl()}/roles/audit/statistics`, {
          headers: { 'X-User-ID': user.id },
          params: { days: 30 },
        }),
      ]);

      setAuditEntries(auditRes.data.entries || []);
      setTotalEntries(auditRes.data.total || 0);
      setStatistics(statsRes.data);
    } catch (error) {
      console.error('Error fetching audit data:', error);
      if (error.response?.status === 403) {
        toast({
          title: 'Access Denied',
          description: 'Only administrators can view audit logs',
          status: 'error',
          duration: 5000,
        });
        router.push('/contentry/settings/roles');
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load audit data',
          status: 'error',
          duration: 3000,
        });
      }
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, page, actionFilter, toast, router]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle export
  const handleExport = async (format) => {
    setIsExporting(true);
    try {
      if (format === 'csv') {
        // Download CSV file
        const response = await axios.get(`${getApiUrl()}/roles/audit/export`, {
          headers: { 'X-User-ID': user.id },
          params: { format: 'csv', limit: 10000 },
          responseType: 'blob',
        });

        // Create download link
        const blob = new Blob([response.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `audit_log_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        window.URL.revokeObjectURL(url);

        toast({
          title: 'Export Complete',
          description: 'CSV file downloaded successfully',
          status: 'success',
          duration: 3000,
        });
      } else {
        // Download JSON file
        const response = await axios.get(`${getApiUrl()}/roles/audit/export`, {
          headers: { 'X-User-ID': user.id },
          params: { format: 'json', limit: 10000 },
        });

        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json',
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `audit_log_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        window.URL.revokeObjectURL(url);

        toast({
          title: 'Export Complete',
          description: 'JSON file downloaded successfully',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      console.error('Error exporting audit log:', error);
      toast({
        title: 'Export Failed',
        description: 'Failed to export audit log',
        status: 'error',
        duration: 3000,
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Parse changes JSON
  const formatChanges = (changes) => {
    if (!changes) return '-';
    try {
      const parsed = typeof changes === 'string' ? JSON.parse(changes) : changes;
      const keys = Object.keys(parsed);
      if (keys.length === 0) return '-';
      
      // Show first 2 key-value pairs
      const preview = keys.slice(0, 2).map(k => `${k}: ${parsed[k]}`).join(', ');
      return keys.length > 2 ? `${preview}...` : preview;
    } catch {
      return typeof changes === 'string' ? changes.substring(0, 50) + '...' : '-';
    }
  };

  // Get action badge
  const getActionBadge = (action) => {
    const config = ACTION_CONFIG[action] || { icon: Activity, color: 'gray', label: action };
    const ActionIcon = config.icon;

    return (
      <Badge colorScheme={config.color} variant="subtle" px={2} py={1}>
        <HStack spacing={1}>
          <ActionIcon size={12} />
          <span>{config.label}</span>
        </HStack>
      </Badge>
    );
  };

  const totalPages = Math.ceil(totalEntries / limit);

  if (isLoading && page === 1) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    );
  }

  return (
    <Box p={{ base: 4, md: 6 }} maxW="1400px" mx="auto">
      {/* Header */}
      <Flex
        direction={{ base: 'column', md: 'row' }}
        justify="space-between"
        align={{ base: 'stretch', md: 'center' }}
        mb={6}
        gap={4}
      >
        <Box>
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ChevronLeft size={16} />}
            onClick={() => router.push('/contentry/settings/roles')}
            p={0}
            h="auto"
            minW="auto"
            color={textSecondary}
            _hover={{ color: textColor }}
            mb={2}
          >
            Back to Roles
          </Button>
          <Text fontSize="2xl" fontWeight="bold" color={textColor}>
            Audit Log
          </Text>
          <Text color={textSecondary} fontSize="sm">
            Track all permission-related changes in your enterprise
          </Text>
        </Box>

        <Menu>
          <MenuButton
            as={Button}
            leftIcon={<Download size={18} />}
            rightIcon={<ChevronDown size={16} />}
            variant="primary"
            isLoading={isExporting}
          >
            Export
          </MenuButton>
          <MenuList>
            <MenuItem icon={<FileText size={16} />} onClick={() => handleExport('csv')}>
              Export as CSV
            </MenuItem>
            <MenuItem icon={<FileJson size={16} />} onClick={() => handleExport('json')}>
              Export as JSON
            </MenuItem>
          </MenuList>
        </Menu>
      </Flex>

      {/* Statistics Cards */}
      {statistics && (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={6}>
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel color={textSecondary}>Total Events (30 days)</StatLabel>
                <StatNumber color={textColor}>{statistics.total_events}</StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <Activity size={14} />
                    <span>Permission changes</span>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel color={textSecondary}>Roles Created</StatLabel>
                <StatNumber color="green.500">
                  {statistics.action_breakdown?.['role.created'] || 0}
                </StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <Shield size={14} />
                    <span>New roles</span>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel color={textSecondary}>Roles Deleted</StatLabel>
                <StatNumber color="red.500">
                  {statistics.action_breakdown?.['role.deleted'] || 0}
                </StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <Trash2 size={14} />
                    <span>Removed roles</span>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel color={textSecondary}>Active Administrators</StatLabel>
                <StatNumber color="brand.500">
                  {statistics.top_actors?.length || 0}
                </StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <Users size={14} />
                    <span>Making changes</span>
                  </HStack>
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>
      )}

      {/* Filters */}
      <Flex gap={4} mb={6} direction={{ base: 'column', md: 'row' }}>
        <InputGroup maxW={{ base: '100%', md: '300px' }}>
          <InputLeftElement pointerEvents="none">
            <Search size={18} color="gray" />
          </InputLeftElement>
          <Input
            placeholder="Search entries..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg={bgColor}
            borderColor={borderColor}
          />
        </InputGroup>

        <Select
          placeholder="All Actions"
          value={actionFilter}
          onChange={(e) => {
            setActionFilter(e.target.value);
            setPage(1);
          }}
          maxW={{ base: '100%', md: '200px' }}
          bg={bgColor}
          borderColor={borderColor}
        >
          <option value="role.created">Role Created</option>
          <option value="role.updated">Role Updated</option>
          <option value="role.deleted">Role Deleted</option>
          <option value="role.duplicated">Role Duplicated</option>
          <option value="user.role.assigned">Role Assigned</option>
          <option value="user.role.removed">Role Removed</option>
        </Select>

        <Button
          leftIcon={<RefreshCw size={16} />}
          variant="ghost"
          onClick={fetchData}
          isLoading={isLoading}
        >
          Refresh
        </Button>
      </Flex>

      {/* Audit Table */}
      <Box
        bg={bgColor}
        border="1px solid"
        borderColor={borderColor}
        borderRadius="xl"
        overflow="hidden"
      >
        <TableContainer>
          <Table variant="simple">
            <Thead bg={cardBg}>
              <Tr>
                <Th>Timestamp</Th>
                <Th>Action</Th>
                <Th>User</Th>
                <Th>Target</Th>
                <Th>Changes</Th>
              </Tr>
            </Thead>
            <Tbody>
              {auditEntries.map((entry) => (
                <Tr key={entry.audit_id} _hover={{ bg: cardBg }}>
                  <Td fontSize="sm">
                    <VStack align="start" spacing={0}>
                      <Text>{formatTimestamp(entry.timestamp)}</Text>
                      <Text fontSize="xs" color={textSecondary}>
                        {entry.audit_id}
                      </Text>
                    </VStack>
                  </Td>
                  <Td>{getActionBadge(entry.action)}</Td>
                  <Td>
                    <VStack align="start" spacing={0}>
                      <Text fontSize="sm" fontWeight="medium">
                        {entry.actor_name || 'Unknown'}
                      </Text>
                      <Text fontSize="xs" color={textSecondary}>
                        {entry.actor_email || entry.actor_id}
                      </Text>
                    </VStack>
                  </Td>
                  <Td>
                    <VStack align="start" spacing={0}>
                      <Badge variant="outline" colorScheme="gray">
                        {entry.target_type}
                      </Badge>
                      <Text fontSize="xs" color={textSecondary}>
                        {entry.target_id}
                      </Text>
                    </VStack>
                  </Td>
                  <Td maxW="200px">
                    <Tooltip label={entry.changes} placement="top" hasArrow>
                      <Text fontSize="sm" noOfLines={2}>
                        {formatChanges(entry.changes)}
                      </Text>
                    </Tooltip>
                  </Td>
                </Tr>
              ))}

              {auditEntries.length === 0 && (
                <Tr>
                  <Td colSpan={5} textAlign="center" py={8}>
                    <VStack spacing={2}>
                      <Icon as={Activity} boxSize={8} color="gray.400" />
                      <Text color={textSecondary}>No audit entries found</Text>
                    </VStack>
                  </Td>
                </Tr>
              )}
            </Tbody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {totalPages > 1 && (
          <Flex justify="space-between" align="center" p={4} borderTop="1px solid" borderColor={borderColor}>
            <Text fontSize="sm" color={textSecondary}>
              Showing {(page - 1) * limit + 1} - {Math.min(page * limit, totalEntries)} of {totalEntries}
            </Text>
            <HStack spacing={2}>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                isDisabled={page === 1}
              >
                Previous
              </Button>
              <Text fontSize="sm" color={textSecondary}>
                Page {page} of {totalPages}
              </Text>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                isDisabled={page === totalPages}
              >
                Next
              </Button>
            </HStack>
          </Flex>
        )}
      </Box>
    </Box>
  );
}

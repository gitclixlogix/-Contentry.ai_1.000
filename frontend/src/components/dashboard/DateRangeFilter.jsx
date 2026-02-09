'use client';

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  HStack,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Input,
  VStack,
  Text,
  useColorModeValue,
  Icon,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
} from '@chakra-ui/react';
import { FaCalendarAlt, FaChevronDown } from 'react-icons/fa';

export default function DateRangeFilter({ value, onChange, showCustom = true }) {
  const { t } = useTranslation();
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [isCustomOpen, setIsCustomOpen] = useState(false);

  const DATE_RANGES = [
    { value: 'this_week', label: t('dashboard.dateFilter.thisWeek', 'This Week') },
    { value: 'this_month', label: t('dashboard.dateFilter.thisMonth', 'This Month') },
    { value: 'this_quarter', label: t('dashboard.dateFilter.thisQuarter', 'This Quarter') },
    { value: 'last_30_days', label: t('dashboard.dateFilter.last30Days', 'Last 30 Days') },
    { value: 'last_90_days', label: t('dashboard.dateFilter.last90Days', 'Last 90 Days') },
    { value: 'custom', label: t('dashboard.dateFilter.customRange', 'Custom Range') },
  ];

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const selectedRange = DATE_RANGES.find(r => r.value === value) || DATE_RANGES[3];

  const handleRangeSelect = (rangeValue) => {
    if (rangeValue === 'custom') {
      setIsCustomOpen(true);
    } else {
      onChange({ range: rangeValue });
    }
  };

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      onChange({
        range: 'custom',
        customStart,
        customEnd,
      });
      setIsCustomOpen(false);
    }
  };

  return (
    <HStack spacing={2}>
      <Icon as={FaCalendarAlt} color="brand.500" />
      <Menu>
        <MenuButton
          as={Button}
          size="sm"
          variant="outline"
          rightIcon={<FaChevronDown />}
          bg={bgColor}
          borderColor={borderColor}
        >
          {selectedRange.label}
        </MenuButton>
        <MenuList bg={bgColor} borderColor={borderColor}>
          {DATE_RANGES.filter(r => showCustom || r.value !== 'custom').map((range) => (
            <MenuItem
              key={range.value}
              onClick={() => handleRangeSelect(range.value)}
              bg={value === range.value ? 'brand.50' : 'transparent'}
              _dark={{ bg: value === range.value ? 'brand.900' : 'transparent' }}
            >
              {range.label}
            </MenuItem>
          ))}
        </MenuList>
      </Menu>

      {/* Custom Date Range Popover */}
      <Popover isOpen={isCustomOpen} onClose={() => setIsCustomOpen(false)} placement="bottom-start">
        <PopoverTrigger>
          <span />
        </PopoverTrigger>
        <PopoverContent bg={bgColor} borderColor={borderColor} w="300px">
          <PopoverArrow bg={bgColor} />
          <PopoverBody p={4}>
            <VStack spacing={3} align="stretch">
              <Text fontSize="sm" fontWeight="600">{t('dashboard.dateFilter.customDateRange', 'Custom Date Range')}</Text>
              <VStack spacing={2} align="stretch">
                <Text fontSize="xs" color="gray.500">{t('dashboard.dateFilter.startDate', 'Start Date')}</Text>
                <Input
                  type="date"
                  size="sm"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                />
              </VStack>
              <VStack spacing={2} align="stretch">
                <Text fontSize="xs" color="gray.500">{t('dashboard.dateFilter.endDate', 'End Date')}</Text>
                <Input
                  type="date"
                  size="sm"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                />
              </VStack>
              <HStack justify="flex-end" pt={2}>
                <Button size="sm" variant="ghost" onClick={() => setIsCustomOpen(false)}>
                  {t('common.cancel', 'Cancel')}
                </Button>
                <Button
                  size="sm"
                  colorScheme="brand"
                  onClick={handleCustomApply}
                  isDisabled={!customStart || !customEnd}
                >
                  {t('dashboard.dateFilter.apply', 'Apply')}
                </Button>
              </HStack>
            </VStack>
          </PopoverBody>
        </PopoverContent>
      </Popover>
    </HStack>
  );
}

// Static version for external use (without translations for initial render)
export const DATE_RANGES_STATIC = [
  { value: 'this_week', label: 'This Week' },
  { value: 'this_month', label: 'This Month' },
  { value: 'this_quarter', label: 'This Quarter' },
  { value: 'last_30_days', label: 'Last 30 Days' },
  { value: 'last_90_days', label: 'Last 90 Days' },
  { value: 'custom', label: 'Custom Range' },
];

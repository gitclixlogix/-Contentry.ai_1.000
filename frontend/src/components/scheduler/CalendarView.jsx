'use client';
import { useState, useMemo } from 'react';
import {
  Box,
  Grid,
  GridItem,
  Text,
  VStack,
  HStack,
  IconButton,
  useColorModeValue,
  Badge,
  Tooltip,
  Flex,
  Icon,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
} from '@chakra-ui/react';
import { ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';
import { FaTwitter, FaLinkedinIn, FaFacebookF, FaInstagram, FaMagic, FaCalendarAlt } from 'react-icons/fa';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const getPlatformIcon = (platform) => {
  const icons = {
    twitter: FaTwitter,
    linkedin: FaLinkedinIn,
    facebook: FaFacebookF,
    instagram: FaInstagram,
  };
  return icons[platform?.toLowerCase()] || FaTwitter;
};

const getPlatformColor = (platform) => {
  const colors = {
    twitter: '#1DA1F2',
    linkedin: '#0A66C2',
    facebook: '#1877F2',
    instagram: '#E4405F',
  };
  return colors[platform?.toLowerCase()] || '#1DA1F2';
};

// Colors for different item types
const ITEM_COLORS = {
  post: {
    bg: 'blue.600',      // Purple for scheduled posts
    hoverBg: 'blue.700',
    badge: 'blue'
  },
  prompt: {
    bg: 'teal.500',        // Teal for scheduled prompts
    hoverBg: 'teal.600',
    badge: 'teal'
  }
};

export default function CalendarView({ scheduledPosts = [], scheduledPrompts = [], onPostClick, onPromptClick }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.500', 'gray.400');
  const todayBg = useColorModeValue('brand.50', 'brand.900');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const dayHeaderBg = useColorModeValue('gray.50', 'gray.700');

  // Get calendar days for current month
  const calendarDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    const startPadding = firstDay.getDay();
    const totalDays = lastDay.getDate();
    
    const days = [];
    
    // Add padding days from previous month
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startPadding - 1; i >= 0; i--) {
      days.push({
        date: new Date(year, month - 1, prevMonthLastDay - i),
        isCurrentMonth: false,
      });
    }
    
    // Add current month days
    for (let i = 1; i <= totalDays; i++) {
      days.push({
        date: new Date(year, month, i),
        isCurrentMonth: true,
      });
    }
    
    // Add padding days from next month
    const remainingDays = 42 - days.length; // 6 rows * 7 days
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        date: new Date(year, month + 1, i),
        isCurrentMonth: false,
      });
    }
    
    return days;
  }, [currentDate]);

  // Group items by date - combining posts and prompts
  // For recurring prompts (daily, weekly), generate entries for each occurrence
  const itemsByDate = useMemo(() => {
    const grouped = {};
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth();
    
    // Get the date range for the current calendar view (6 weeks)
    const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
    const startPadding = firstDayOfMonth.getDay();
    const calendarStart = new Date(currentYear, currentMonth, 1 - startPadding);
    const calendarEnd = new Date(calendarStart);
    calendarEnd.setDate(calendarEnd.getDate() + 41); // 42 days total (6 weeks)
    
    // Add scheduled posts
    scheduledPosts.forEach(post => {
      const postDate = new Date(post.scheduled_time || post.post_time);
      const dateKey = `${postDate.getFullYear()}-${postDate.getMonth()}-${postDate.getDate()}`;
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push({
        ...post,
        itemType: 'post',
        displayTime: postDate,
        displayTitle: post.content?.substring(0, 30) || post.title || 'Scheduled Post'
      });
    });
    
    // Add scheduled prompts - expand recurring ones
    scheduledPrompts.forEach(prompt => {
      const startDate = prompt.start_date ? new Date(prompt.start_date) : new Date(prompt.next_run);
      const scheduleType = prompt.schedule_type?.toLowerCase();
      const scheduleTime = prompt.schedule_time || '09:00';
      const [hours, minutes] = scheduleTime.split(':').map(Number);
      
      if (scheduleType === 'daily') {
        // For daily prompts, add an entry for each day from start date
        let currentDay = new Date(startDate);
        currentDay.setHours(hours, minutes, 0, 0);
        
        // If start date is before calendar start, begin from calendar start
        if (currentDay < calendarStart) {
          currentDay = new Date(calendarStart);
          currentDay.setHours(hours, minutes, 0, 0);
        }
        
        while (currentDay <= calendarEnd) {
          // Show all daily prompts in calendar (both active and paused, future and past within view)
          const dateKey = `${currentDay.getFullYear()}-${currentDay.getMonth()}-${currentDay.getDate()}`;
          if (!grouped[dateKey]) {
            grouped[dateKey] = [];
          }
          grouped[dateKey].push({
            ...prompt,
            itemType: 'prompt',
            displayTime: new Date(currentDay),
            displayTitle: prompt.prompt?.substring(0, 30) || 'Scheduled Prompt',
            isRecurring: true,
            recurrenceType: 'daily'
          });
          // Move to next day
          currentDay.setDate(currentDay.getDate() + 1);
        }
      } else if (scheduleType === 'weekly') {
        // For weekly prompts, add entries for each week
        let currentDay = new Date(startDate);
        currentDay.setHours(hours, minutes, 0, 0);
        
        // If start date is before calendar start, find the next occurrence
        if (currentDay < calendarStart) {
          const daysSinceStart = Math.floor((calendarStart - currentDay) / (1000 * 60 * 60 * 24));
          const weeksSinceStart = Math.ceil(daysSinceStart / 7);
          currentDay.setDate(currentDay.getDate() + (weeksSinceStart * 7));
        }
        
        while (currentDay <= calendarEnd) {
          // Show all weekly prompts in calendar
          const dateKey = `${currentDay.getFullYear()}-${currentDay.getMonth()}-${currentDay.getDate()}`;
          if (!grouped[dateKey]) {
            grouped[dateKey] = [];
          }
          grouped[dateKey].push({
            ...prompt,
            itemType: 'prompt',
            displayTime: new Date(currentDay),
            displayTitle: prompt.prompt?.substring(0, 30) || 'Scheduled Prompt',
            isRecurring: true,
            recurrenceType: 'weekly'
          });
          // Move to next week
          currentDay.setDate(currentDay.getDate() + 7);
        }
      } else {
        // One-time prompts - just use next_run date
        const promptDate = new Date(prompt.next_run);
        const dateKey = `${promptDate.getFullYear()}-${promptDate.getMonth()}-${promptDate.getDate()}`;
        if (!grouped[dateKey]) {
          grouped[dateKey] = [];
        }
        grouped[dateKey].push({
          ...prompt,
          itemType: 'prompt',
          displayTime: promptDate,
          displayTitle: prompt.prompt?.substring(0, 30) || 'Scheduled Prompt'
        });
      }
    });
    
    // Sort items by time within each day
    Object.keys(grouped).forEach(key => {
      grouped[key].sort((a, b) => a.displayTime - b.displayTime);
    });
    
    return grouped;
  }, [scheduledPosts, scheduledPrompts, currentDate]);

  const getItemsForDate = (date) => {
    const dateKey = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
    return itemsByDate[dateKey] || [];
  };

  const isToday = (date) => {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
  };

  const goToPrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const handleItemClick = (item) => {
    if (item.itemType === 'post' && onPostClick) {
      onPostClick(item);
    } else if (item.itemType === 'prompt' && onPromptClick) {
      onPromptClick(item);
    }
  };

  return (
    <Box bg={cardBg} borderRadius="xl" borderWidth="1px" borderColor={borderColor} overflow="hidden">
      {/* Calendar Header */}
      <Flex 
        justify="space-between" 
        align="center" 
        p={4} 
        borderBottomWidth="1px" 
        borderColor={borderColor}
      >
        <HStack spacing={2}>
          <IconButton
            icon={<ChevronLeftIcon />}
            size="sm"
            variant="ghost"
            onClick={goToPrevMonth}
            aria-label="Previous month"
          />
          <Text fontSize="lg" fontWeight="700" color={textColor} minW="180px" textAlign="center">
            {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
          </Text>
          <IconButton
            icon={<ChevronRightIcon />}
            size="sm"
            variant="ghost"
            onClick={goToNextMonth}
            aria-label="Next month"
          />
        </HStack>
        <HStack spacing={2}>
          {/* Legend */}
          <HStack spacing={3} mr={4}>
            <HStack spacing={1}>
              <Box w={3} h={3} bg="blue.600" borderRadius="sm" />
              <Text fontSize="xs" color={textColorSecondary}>Posts</Text>
            </HStack>
            <HStack spacing={1}>
              <Box w={3} h={3} bg="teal.500" borderRadius="sm" />
              <Text fontSize="xs" color={textColorSecondary}>Prompts</Text>
            </HStack>
          </HStack>
          <Badge 
            colorScheme="brand" 
            cursor="pointer" 
            onClick={goToToday}
            px={3}
            py={1}
            borderRadius="md"
          >
            Today
          </Badge>
        </HStack>
      </Flex>

      {/* Day Headers */}
      <Grid templateColumns="repeat(7, 1fr)" bg={dayHeaderBg}>
        {DAYS.map(day => (
          <GridItem key={day} p={2} textAlign="center">
            <Text fontSize="xs" fontWeight="600" color={textColorSecondary} textTransform="uppercase">
              {day}
            </Text>
          </GridItem>
        ))}
      </Grid>

      {/* Calendar Grid */}
      <Grid templateColumns="repeat(7, 1fr)">
        {calendarDays.map((day, index) => {
          const items = getItemsForDate(day.date);
          const hasMultipleItems = items.length > 2;
          
          return (
            <GridItem 
              key={index}
              minH="90px"
              p={1}
              borderWidth="1px"
              borderColor={borderColor}
              bg={isToday(day.date) ? todayBg : 'transparent'}
              opacity={day.isCurrentMonth ? 1 : 0.4}
              _hover={{ bg: hoverBg }}
              transition="background 0.2s"
            >
              <VStack align="stretch" spacing={1} h="100%">
                <Text 
                  fontSize="sm" 
                  fontWeight={isToday(day.date) ? '700' : '500'}
                  color={isToday(day.date) ? 'brand.500' : textColor}
                  textAlign="right"
                  pr={1}
                >
                  {day.date.getDate()}
                </Text>
                
                {/* Show first 2 items */}
                {items.slice(0, 2).map((item, itemIndex) => {
                  const colors = ITEM_COLORS[item.itemType];
                  const ItemIcon = item.itemType === 'prompt' ? FaMagic : FaCalendarAlt;
                  
                  return (
                    <Popover key={item.id || itemIndex} trigger="hover" placement="top">
                      <PopoverTrigger>
                        <Box
                          bg={colors.bg}
                          color="white"
                          px={1.5}
                          py={0.5}
                          borderRadius="md"
                          fontSize="xs"
                          cursor="pointer"
                          onClick={() => handleItemClick(item)}
                          noOfLines={1}
                          _hover={{ bg: colors.hoverBg }}
                          opacity={item.status === 'paused' ? 0.6 : 1}
                        >
                          <HStack spacing={1}>
                            <Icon as={ItemIcon} boxSize={2.5} />
                            <Text noOfLines={1} flex="1">
                              {item.displayTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </Text>
                          </HStack>
                        </Box>
                      </PopoverTrigger>
                      <PopoverContent w="280px" bg={cardBg} shadow="xl" borderWidth="1px" borderColor={borderColor}>
                        <PopoverArrow bg={cardBg} />
                        <PopoverBody>
                          <VStack align="stretch" spacing={2}>
                            <HStack>
                              <Badge colorScheme={colors.badge} fontSize="xs">
                                {item.itemType === 'post' ? 'Scheduled Post' : 'Scheduled Prompt'}
                              </Badge>
                              {item.isRecurring && (
                                <Badge colorScheme="blue" fontSize="xs">
                                  {item.recurrenceType === 'daily' ? 'Daily' : 'Weekly'}
                                </Badge>
                              )}
                              {item.status === 'paused' && (
                                <Badge colorScheme="orange" fontSize="xs">
                                  Paused
                                </Badge>
                              )}
                            </HStack>
                            <Text fontSize="sm" fontWeight="600" noOfLines={3}>
                              {item.itemType === 'prompt' ? item.prompt : item.content}
                            </Text>
                            <HStack spacing={1} flexWrap="wrap">
                              {item.platforms?.map(platform => (
                                <Badge key={platform} size="sm" colorScheme="gray">
                                  <HStack spacing={1}>
                                    <Icon as={getPlatformIcon(platform)} boxSize={2} />
                                    <Text>{platform}</Text>
                                  </HStack>
                                </Badge>
                              ))}
                            </HStack>
                            <Text fontSize="xs" color={textColorSecondary}>
                              {item.displayTime.toLocaleString()}
                            </Text>
                            {item.itemType === 'prompt' && (
                              <Badge colorScheme={item.auto_post ? 'green' : 'gray'} fontSize="xs">
                                {item.auto_post ? 'Auto-post enabled' : 'Manual review'}
                              </Badge>
                            )}
                          </VStack>
                        </PopoverBody>
                      </PopoverContent>
                    </Popover>
                  );
                })}
                
                {/* Show "+X more" if there are additional items */}
                {hasMultipleItems && (
                  <Tooltip label={`${items.length - 2} more scheduled items`}>
                    <Text 
                      fontSize="xs" 
                      color="brand.500" 
                      fontWeight="600" 
                      cursor="pointer"
                      textAlign="center"
                    >
                      +{items.length - 2} more
                    </Text>
                  </Tooltip>
                )}
              </VStack>
            </GridItem>
          );
        })}
      </Grid>
    </Box>
  );
}

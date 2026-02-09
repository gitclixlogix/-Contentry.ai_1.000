'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  IconButton,
  Badge,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverHeader,
  PopoverCloseButton,
  VStack,
  HStack,
  Text,
  Button,
  Divider,
  Icon,
  useColorModeValue,
  useToast,
  Spinner,
  Avatar,
} from '@chakra-ui/react';
import {
  FaBell,
  FaFileAlt,
  FaCheckCircle,
  FaExclamationTriangle,
  FaUserPlus,
  FaUserCog,
  FaRocket,
  FaClock,
  FaTrash,
} from 'react-icons/fa';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { formatDistanceToNow } from 'date-fns';

// Notification type icons and colors
const NOTIFICATION_CONFIG = {
  approval_submitted: { icon: FaFileAlt, color: 'orange.500', bgColor: 'orange.50' },
  post_approved: { icon: FaCheckCircle, color: 'green.500', bgColor: 'green.50' },
  post_rejected: { icon: FaExclamationTriangle, color: 'red.500', bgColor: 'red.50' },
  invitation_accepted: { icon: FaUserPlus, color: 'blue.500', bgColor: 'blue.50' },
  role_changed: { icon: FaUserCog, color: 'blue.600', bgColor: 'blue.50' },
  post_published: { icon: FaRocket, color: 'green.500', bgColor: 'green.50' },
  post_scheduled: { icon: FaClock, color: 'blue.500', bgColor: 'blue.50' },
  default: { icon: FaBell, color: 'gray.500', bgColor: 'gray.50' },
};

export default function NotificationBell() {
  const { user } = useAuth();
  const toast = useToast();
  
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');
  const textColorSecondary = useColorModeValue('gray.600', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  
  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      const response = await api.get('/in-app-notifications/unread-count');
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  }, [user?.id]);
  
  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    if (!user?.id) return;
    
    setLoading(true);
    try {
      const response = await api.get('/in-app-notifications', {
        params: { limit: 20 }
      });
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  }, [user?.id]);
  
  // Initial fetch and polling
  useEffect(() => {
    fetchUnreadCount();
    
    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);
  
  // Fetch notifications when popover opens
  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, fetchNotifications]);
  
  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/in-app-notifications/${notificationId}/read`, {});
      
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };
  
  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await api.put('/in-app-notifications/read-all', {});
      
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
      
      toast({
        title: 'All notifications marked as read',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Failed to mark all as read',
        status: 'error',
        duration: 3000,
      });
    }
  };
  
  // Delete notification
  const deleteNotification = async (e, notificationId) => {
    e.stopPropagation();
    
    try {
      await api.delete(`/in-app-notifications/${notificationId}`);
      
      const wasUnread = notifications.find(n => n.id === notificationId)?.read === false;
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      if (wasUnread) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      toast({
        title: 'Failed to delete notification',
        status: 'error',
        duration: 3000,
      });
    }
  };
  
  // Get config for notification type
  const getNotificationConfig = (type) => {
    return NOTIFICATION_CONFIG[type] || NOTIFICATION_CONFIG.default;
  };
  
  // Format time
  const formatTime = (dateStr) => {
    try {
      return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
    } catch {
      return 'Just now';
    }
  };

  if (!user) return null;

  return (
    <Popover
      isOpen={isOpen}
      onOpen={() => setIsOpen(true)}
      onClose={() => setIsOpen(false)}
      placement="bottom-end"
    >
      <PopoverTrigger>
        <Box position="relative" display="inline-block">
          <IconButton
            icon={<FaBell />}
            variant="ghost"
            fontSize="lg"
            aria-label="Notifications"
            color={textColorSecondary}
            _hover={{ color: textColor, bg: hoverBg }}
          />
          {unreadCount > 0 && (
            <Badge
              position="absolute"
              top="-1"
              right="-1"
              colorScheme="red"
              borderRadius="full"
              fontSize="xs"
              minW="18px"
              h="18px"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Box>
      </PopoverTrigger>
      
      <PopoverContent
        w="380px"
        maxH="500px"
        bg={cardBg}
        borderColor={borderColor}
        boxShadow="xl"
      >
        <PopoverHeader borderBottomWidth="1px" fontWeight="600" py={3}>
          <HStack justify="space-between">
            <Text>Notifications</Text>
            {unreadCount > 0 && (
              <Button
                size="xs"
                variant="ghost"
                colorScheme="blue"
                onClick={markAllAsRead}
              >
                Mark all as read
              </Button>
            )}
          </HStack>
        </PopoverHeader>
        <PopoverCloseButton />
        
        <PopoverBody p={0} maxH="400px" overflowY="auto">
          {loading ? (
            <Box textAlign="center" py={8}>
              <Spinner size="md" />
            </Box>
          ) : notifications.length === 0 ? (
            <Box textAlign="center" py={8} color={textColorSecondary}>
              <Icon as={FaBell} boxSize={8} mb={2} opacity={0.5} />
              <Text>No notifications yet</Text>
            </Box>
          ) : (
            <VStack spacing={0} align="stretch" divider={<Divider />}>
              {notifications.map((notification) => {
                const config = getNotificationConfig(notification.type);
                const isRead = notification.read || notification.is_read;
                
                return (
                  <Box
                    key={notification.id}
                    p={3}
                    bg={isRead ? 'transparent' : config.bgColor}
                    _dark={{ bg: isRead ? 'transparent' : `${config.color.split('.')[0]}.900` }}
                    _hover={{ bg: hoverBg }}
                    cursor="pointer"
                    onClick={() => !isRead && markAsRead(notification.id)}
                    position="relative"
                  >
                    <HStack align="start" spacing={3}>
                      <Avatar
                        size="sm"
                        icon={<Icon as={config.icon} />}
                        bg={config.color}
                        color="white"
                      />
                      <Box flex={1}>
                        <Text
                          fontWeight={isRead ? 'normal' : '600'}
                          fontSize="sm"
                          color={textColor}
                          noOfLines={1}
                        >
                          {notification.title || 'Notification'}
                        </Text>
                        <Text fontSize="xs" color={textColorSecondary} noOfLines={2}>
                          {notification.message}
                        </Text>
                        <Text fontSize="xs" color={textColorSecondary} mt={1}>
                          {formatTime(notification.created_at)}
                        </Text>
                      </Box>
                      <IconButton
                        icon={<FaTrash />}
                        size="xs"
                        variant="ghost"
                        colorScheme="red"
                        opacity={0.5}
                        _hover={{ opacity: 1 }}
                        onClick={(e) => deleteNotification(e, notification.id)}
                        aria-label="Delete notification"
                      />
                    </HStack>
                    {!isRead && (
                      <Box
                        position="absolute"
                        left="0"
                        top="0"
                        bottom="0"
                        w="3px"
                        bg={config.color}
                        borderLeftRadius="md"
                      />
                    )}
                  </Box>
                );
              })}
            </VStack>
          )}
        </PopoverBody>
      </PopoverContent>
    </Popover>
  );
}

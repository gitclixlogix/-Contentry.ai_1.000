'use client';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  Text,
  Input,
  VStack,
  HStack,
  Flex,
  Icon,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react';
import { FaBell, FaClock } from 'react-icons/fa';
import api from '@/lib/api';


export default function Notifications() {
  const { t } = useTranslation();
  const [notifications, setNotifications] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [user, setUser] = useState(null);

  const cardBg = useColorModeValue('white', 'gray.800');

  const loadNotifications = async (userId) => {
    try {
      const response = await api.get('/in-app-notifications');
      // Handle both array and object response formats
      const data = response.data.notifications || response.data || [];
      setNotifications(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      // Empty state is not an error - just set empty array
      setNotifications([]);
    }
  };

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const savedUser = localStorage.getItem('contentry_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      loadNotifications(userData.id);
    }
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  const markAllRead = async () => {
    if (!user) return;
    try {
      await api.put('/in-app-notifications/read-all');
      loadNotifications(user.id);
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const filteredNotifications = notifications.filter(n =>
    n.message.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Heading size="lg" mb={6}>{t('notifications.title')}</Heading>

      <Card bg={cardBg}>
        <CardBody>
          <Flex gap={4} mb={8} wrap="wrap">
            <Input
              placeholder={t('notifications.searchNotifications')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              flex={1}
              minW="250px"
            />
            <Button colorScheme="brand" onClick={markAllRead}>{t('notifications.markAllRead')}</Button>
          </Flex>

          <VStack spacing={4}>
            {filteredNotifications.map((notif, idx) => (
              <Flex
                key={notif.id}
                p={6}
                bg={notif.read ? 'gray.50' : 'blue.50'}
                border={notif.read ? '1px solid' : '2px solid'}
                borderColor={notif.read ? 'gray.200' : 'brand.500'}
                borderRadius="xl"
                align="flex-start"
                gap={4}
                w="full"
              >
                <Flex
                  w="48px"
                  h="48px"
                  borderRadius="full"
                  bg={notif.type === 'alert' ? 'brand.500' : 'orange.500'}
                  color="white"
                  align="center"
                  justify="center"
                  flexShrink={0}
                >
                  <Icon as={notif.type === 'alert' ? FaBell : FaClock} />
                </Flex>
                <Box flex={1}>
                  <HStack mb={2}>
                    <Badge colorScheme={notif.type === 'alert' ? 'blue' : 'orange'}>
                      {notif.type}
                    </Badge>
                    <Text fontSize="sm" color="gray.600">
                      {new Date(notif.created_at).toLocaleString()}
                    </Text>
                  </HStack>
                  <Text lineHeight="1.6">{notif.message}</Text>
                </Box>
              </Flex>
            ))}

            {filteredNotifications.length === 0 && (
              <Box textAlign="center" py={12} color="gray.500">
                {t('notifications.noNotificationsFound')}
              </Box>
            )}
          </VStack>
        </CardBody>
      </Card>
    </Box>
  );
}
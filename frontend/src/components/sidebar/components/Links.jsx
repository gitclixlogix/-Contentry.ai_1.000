'use client';
/* eslint-disable */

// chakra imports
import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Flex,
  HStack,
  Text,
  List,
  Icon,
  ListItem,
  useColorModeValue,
  Skeleton,
} from '@chakra-ui/react';
import { FaCircle } from 'react-icons/fa';
import { IoMdAdd } from 'react-icons/io';
import NavLink from '@/components/link/NavLink';
import { useCallback, Suspense } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';

// Inner component that uses useSearchParams
function SidebarLinksInner(props) {
  //   Chakra color mode
  const pathname = usePathname();
  const searchParams = useSearchParams();
  let activeColor = useColorModeValue('navy.700', 'white');
  let inactiveColor = useColorModeValue('gray.600', 'gray.500');
  let borderColor = useColorModeValue('gray.200', 'whiteAlpha.300');
  let activeIcon = useColorModeValue('brand.500', 'white');
  let iconColor = useColorModeValue('navy.700', 'white');

  const { routes } = props;

  // verifies if routeName is the one active (in browser input)
  // Now handles query parameters like ?tab=analyze
  // Also handles parent routes being active when on child pages (e.g., /documentation when on /documentation/admin)
  const activeRoute = useCallback(
    (routeName) => {
      // Check if route has query params (e.g., /content-moderation?tab=analyze)
      if (routeName?.includes('?')) {
        const [routePath, routeQuery] = routeName.split('?');
        const routeParams = new URLSearchParams(routeQuery);
        
        // Check if pathname matches and all query params match
        if (pathname?.includes(routePath.toLowerCase())) {
          for (const [key, value] of routeParams.entries()) {
            if (searchParams?.get(key) !== value) {
              return false;
            }
          }
          return true;
        }
        return false;
      }
      
      // Normalize paths for comparison
      const normalizedRoute = routeName?.toLowerCase().replace(/\/$/, '');
      const normalizedPath = pathname?.toLowerCase().replace(/\/$/, '');
      
      // Check for exact match or if current path starts with the route
      // This ensures /documentation is active when on /documentation/admin
      if (normalizedPath === normalizedRoute) {
        return true;
      }
      
      // Check if current path is a sub-path of the route
      // e.g., /documentation/admin should make /documentation active
      if (normalizedRoute && normalizedPath?.startsWith(normalizedRoute + '/')) {
        return true;
      }
      
      // Fallback to includes check for other cases
      return pathname?.includes(routeName);
    },
    [pathname, searchParams],
  );

  // this function creates the links and collapses that appear in the sidebar (left menu)
  const createLinks = (routes) => {
    return routes.map((route, key) => {
      // Handle separator
      if (route.separator) {
        return (
          <Box
            key={key}
            h="1px"
            bg={borderColor}
            my="20px"
            mx="20px"
          />
        );
      }
      
      if (route.collapse && !route.invisible) {
        return (
          <Accordion 
            allowToggle 
            key={key} 
            defaultIndex={route.defaultOpen ? [0] : undefined}
            suppressHydrationWarning
          >
            <AccordionItem border="none" mb="14px" key={key} suppressHydrationWarning>
              <AccordionButton
                display="flex"
                alignItems="center"
                mb="4px"
                justifyContent="center"
                _hover={{
                  bg: 'unset',
                }}
                _focus={{
                  boxShadow: 'none',
                }}
                borderRadius="8px"
                w="100%"
                py="0px"
                ms={0}
                suppressHydrationWarning
              >
                {route.icon ? (
                  <Flex align="center" justifyContent="space-between" w="100%">
                    <HStack
                      spacing={
                        activeRoute(route.path.toLowerCase()) ? '22px' : '26px'
                      }
                    >
                      <Flex
                        w="100%"
                        alignItems="center"
                        justifyContent="center"
                      >
                        <Box
                          color={
                            activeRoute(route.path.toLowerCase())
                              ? activeIcon
                              : inactiveColor
                          }
                          me="12px"
                          mt="6px"
                        >
                          {route.icon}
                        </Box>
                        <Text
                          me="auto"
                          color={
                            activeRoute(route.path.toLowerCase())
                              ? activeColor
                              : 'gray.500'
                          }
                          fontWeight={activeRoute(route.path.toLowerCase()) ? '600' : '500'}
                          letterSpacing="0px"
                          fontSize="14px"
                        >
                          {route.name}
                        </Text>
                      </Flex>
                    </HStack>
                    <AccordionIcon ms="auto" color={'gray.500'} />
                  </Flex>
                ) : (
                  <Flex pt="0px" pb="10px" alignItems="center" w="100%">
                    <HStack
                      spacing={
                        activeRoute(route.path.toLowerCase()) ? '22px' : '26px'
                      }
                      ps="32px"
                    >
                      <Text
                        me="auto"
                        color={
                          activeRoute(route.path.toLowerCase())
                            ? activeColor
                            : inactiveColor
                        }
                        fontWeight={activeRoute(route.path.toLowerCase()) ? '600' : '500'}
                        letterSpacing="0px"
                        fontSize="14px"
                      >
                        {route.name}
                      </Text>
                    </HStack>
                    <AccordionIcon ms="auto" color={'gray.500'} />
                  </Flex>
                )}
              </AccordionButton>
              <AccordionPanel py="0px" ps={'8px'} pt="10px" suppressHydrationWarning>
                <List suppressHydrationWarning>
                  {
                    route.icon && route.items
                      ? createLinks(route.items) // for bullet accordion links
                      : route.items
                      ? createAccordionLinks(route.items)
                      : '' // for non-bullet accordion links
                  }
                </List>
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
        );
      } else if (!route.invisible) {
        return (
          <Box key={key}>
            {route.icon ? (
              <Flex
                align="center"
                justifyContent="space-between"
                w="100%"
                maxW="100%"
                ps="17px"
                mb="0px"
              >
                <HStack
                  w="100%"
                  mb="14px"
                  spacing={
                    activeRoute(route.path.toLowerCase()) ? '22px' : '26px'
                  }
                >
                  <NavLink
                    href={route.layout ? route.layout + route.path : route.path}
                    key={key}
                    styles={{ width: '100%' }}
                  >
                    <Flex w="100%" alignItems="center" justifyContent="center">
                      <Box
                        color={
                          activeRoute(route.path.toLowerCase())
                            ? activeIcon
                            : inactiveColor
                        }
                        me="12px"
                        mt="6px"
                      >
                        {route.icon}
                      </Box>
                      <Text
                        me="auto"
                        color={
                          activeRoute(route.path.toLowerCase())
                            ? activeColor
                            : 'gray.500'
                        }
                        fontWeight={activeRoute(route.path.toLowerCase()) ? '600' : '500'}
                        letterSpacing="0px"
                        fontSize="14px"
                      >
                        {route.name}
                      </Text>
                      {route.rightElement ? (
                        <Flex
                          border="1px solid"
                          borderColor={borderColor}
                          borderRadius="full"
                          w="34px"
                          h="34px"
                          justify={'center'}
                          align="center"
                          color={iconColor}
                          ms="auto"
                          me="10px"
                        >
                          <Icon
                            as={IoMdAdd}
                            width="20px"
                            height="20px"
                            color="inherit"
                          />
                        </Flex>
                      ) : null}
                    </Flex>
                  </NavLink>
                </HStack>
              </Flex>
            ) : (
              <ListItem ms={0}>
                <Flex ps="32px" alignItems="center" mb="8px">
                  <NavLink
                    href={route.layout ? route.layout + route.path : route.path}
                    key={key}
                  >
                    <Text
                      color={
                        activeRoute(route.path.toLowerCase())
                          ? activeColor
                          : inactiveColor
                      }
                      fontWeight={activeRoute(route.path.toLowerCase()) ? '600' : '500'}
                      fontSize="13px"
                    >
                      {route.name}
                    </Text>
                  </NavLink>
                </Flex>
              </ListItem>
            )}
          </Box>
        );
      }
    });
  };
  // this function creates the links from the secondary accordions (for example auth -> sign-in -> default)
  const createAccordionLinks = (routes) => {
    return routes.map((route, key) => {
      return (
        <ListItem
          ms="12px"
          display="flex"
          alignItems="center"
          mb="12px"
          key={key}
        >
          <NavLink href={route.layout + route.path} key={key}>
            <Text
              color={
                activeRoute(route.path.toLowerCase())
                  ? activeColor
                  : 'gray.500'
              }
              fontWeight={activeRoute(route.path.toLowerCase()) ? '600' : '500'}
              fontSize="13px"
              letterSpacing="0px"
            >
              {route.name}
            </Text>
          </NavLink>
        </ListItem>
      );
    });
  };
  //  BRAND
  return <>{createLinks(routes)}</>;
}

// Wrapper component with Suspense boundary for useSearchParams
export function SidebarLinks(props) {
  return (
    <Suspense fallback={<Box p={4}><Skeleton height="200px" /></Box>}>
      <SidebarLinksInner {...props} />
    </Suspense>
  );
}

export default SidebarLinks;

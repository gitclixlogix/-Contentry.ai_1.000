'use client';
/*eslint-disable*/

import {
  Flex,
  List,
  ListItem,
  Link,
  Text,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react';

export default function Footer() {
  const textColor = useColorModeValue('gray.500', 'white');
  const mutedTextColor = useColorModeValue('gray.400', 'gray.500');
  
  return (
    <Flex
      zIndex="3"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      px={{ base: '30px', md: '0px' }}
      pb="30px"
      gap={3}
    >
      <List display="flex" flexWrap="wrap" justifyContent="center">
        <ListItem
          me={{
            base: '10px',
            md: '32px',
          }}
        >
          <Link
            fontWeight="500"
            fontSize={{ base: 'xs', md: 'sm' }}
            color={textColor}
            href="/contentry/terms"
          >
            Terms of Service
          </Link>
        </ListItem>
        <ListItem
          me={{
            base: '10px',
            md: '32px',
          }}
        >
          <Link
            fontWeight="500"
            fontSize={{ base: 'xs', md: 'sm' }}
            color={textColor}
            href="/contentry/privacy"
          >
            Privacy Policy
          </Link>
        </ListItem>
        <ListItem>
          <Link
            fontWeight="500"
            fontSize={{ base: 'xs', md: 'sm' }}
            color={textColor}
            href="mailto:contact@contentry.ai"
          >
            Contact
          </Link>
        </ListItem>
      </List>
      <VStack spacing={0}>
        <Text
          color={textColor}
          fontSize="xs"
          fontWeight="500"
          textAlign="center"
        >
          © {new Date().getFullYear()} Contentry.ai. All rights reserved.
        </Text>
        <Text
          color={mutedTextColor}
          fontSize="xs"
          fontWeight="400"
          textAlign="center"
        >
          A product of Global InTech AS, Norway
        </Text>
      </VStack>
    </Flex>
  );
}

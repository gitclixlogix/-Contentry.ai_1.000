'use client';
/*eslint-disable*/

import {
  Flex,
  List,
  ListItem,
  Text,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react';
import Link from '@/components/link/Link';

export default function Footer() {
  const textColor = useColorModeValue('gray.500', 'white');
  const mutedTextColor = useColorModeValue('gray.400', 'gray.500');
  
  return (
    <Flex
      zIndex="3"
      flexDirection={{
        base: 'column',
        xl: 'row',
      }}
      alignItems="center"
      justifyContent="space-between"
      px={{ base: '30px', md: '50px' }}
      pb="30px"
    >
      <VStack 
        spacing={0} 
        align={{ base: 'center', xl: 'start' }}
        mb={{ base: '10px', xl: '0px' }}
      >
        <Text
          color={textColor}
          fontSize={{ base: 'xs', md: 'sm' }}
          textAlign={{
            base: 'center',
            xl: 'start',
          }}
          fontWeight="500"
        >
          &copy; {new Date().getFullYear()} Contentry.ai. All rights reserved.
        </Text>
        <Text
          color={mutedTextColor}
          fontSize={{ base: 'xs', md: 'xs' }}
          textAlign={{
            base: 'center',
            xl: 'start',
          }}
          fontWeight="400"
        >
          A product of Global InTech AS, Norway (Org. NO 935 706 998)
        </Text>
      </VStack>
      <List display="flex" flexWrap="wrap" justifyContent={{ base: 'center', xl: 'flex-end' }}>
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
    </Flex>
  );
}

'use client';
// Chakra imports
import {
  Flex,
  Stat,
  StatLabel,
  StatNumber,
  useColorModeValue,
  Text,
  Icon,
} from '@chakra-ui/react';
import { FaChevronRight } from 'react-icons/fa';
import Card from '@/components/card/Card';

export default function Default(props) {
  const { startContent, endContent, name, growth, value, onClick, isClickable } = props;
  const textColor = useColorModeValue('navy.700', 'white');
  const textColorSecondary = 'gray.500';
  const hoverBg = useColorModeValue('gray.50', 'whiteAlpha.100');

  return (
    <Card
      cursor={isClickable ? 'pointer' : 'default'}
      onClick={isClickable ? onClick : undefined}
      transition="all 0.2s"
      _hover={isClickable ? { bg: hoverBg, transform: 'translateY(-2px)', shadow: 'md' } : {}}
    >
      <Flex
        my="auto"
        h="100%"
        align={{ base: 'center', xl: 'start' }}
        justify={{ base: 'center', xl: 'center' }}
        alignItems="center"
      >
        {startContent}

        <Stat my="auto" ms={startContent ? '18px' : '0px'}>
          <StatLabel
            lineHeight="100%"
            color={textColorSecondary}
            fontSize="sm"
            mb="4px"
          >
            {name}
          </StatLabel>
          <StatNumber color={textColor} fontWeight="700" fontSize="lg">
            {value}
          </StatNumber>
          {growth ? (
            <Flex align="center">
              <Text color="green.500" fontSize="xs" fontWeight="700" me="5px">
                {growth}
              </Text>
              <Text color="gray.500" fontSize="xs" fontWeight="400">
                since last month
              </Text>
            </Flex>
          ) : null}
        </Stat>
        <Flex ms="auto" w="max-content" align="center">
          {endContent}
          {isClickable && (
            <Icon as={FaChevronRight} color={textColorSecondary} boxSize={3} ml={2} />
          )}
        </Flex>
      </Flex>
    </Card>
  );
}

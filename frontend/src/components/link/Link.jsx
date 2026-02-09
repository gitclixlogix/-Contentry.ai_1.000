'use client';
import NextLink from 'next/link';

import { Button } from '@chakra-ui/react';

function Link({ href, children, ...props }) {
  return (
    <NextLink href={href} passHref legacyBehavior>
      <Button as="a" variant="a" {...props}>
        {children}
      </Button>
    </NextLink>
  );
}

export default Link;

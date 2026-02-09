'use client';
import Link from 'next/link';
import { Button } from '@chakra-ui/react';

export default function LinkButton({
  href,
  children,
  prefetch = true,
  ...props
}) {
  return (
    <Link href={href} passHref prefetch={prefetch}>
      <Button as="a" variant="a" {...props}>
        {children}
      </Button>
    </Link>
  );
}

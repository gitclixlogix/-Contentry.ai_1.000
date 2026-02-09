'use client';
import NextLink from 'next/link';
import { useMemo } from 'react';

function NavLink({ children, styles, ...props }) {
  const memoizedStyles = useMemo(
    () => ({
      ...styles,
    }),
    [styles],
  );

  return (
    <NextLink style={memoizedStyles} {...props}>
      {children}
    </NextLink>
  );
}

export default NavLink;

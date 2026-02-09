'use client';
import { Box, BoxProps } from '@chakra-ui/react';
import NextImage, { ImageProps } from 'next/legacy/image';
import { ComponentProps } from 'react';

function parseAssetPrefix(image) {
  const alreadyHasHttp = image.match('http');
  if (alreadyHasHttp) return image;

  const prefix = process.env.NEXT_PUBLIC_BASE_PATH || '';
  const alreadyHasPrefix = image.match(prefix);

  const finalUrl = alreadyHasPrefix ? image : `${prefix}${image}`;
  return finalUrl;
}

export function Image(props) {
  const { src, alt, nextProps = {}, ...rest } = props;

  const imageUrl = typeof src === 'string' ? src : src?.src;
  return (
    <Box overflow={'hidden'} position="relative" {...rest}>
      <NextImage
        layout="fill"
        objectFit="fill"
        src={parseAssetPrefix(imageUrl)}
        alt={alt}
        {...nextProps}
      />
    </Box>
  );
}

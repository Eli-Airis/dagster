/* eslint-disable @typescript-eslint/no-var-requires */

const {PHASE_DEVELOPMENT_SERVER} = require('next/constants');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  productionBrowserSourceMaps: true,
  basePath: process.env.NEXT_PUBLIC_BASE_PATH,
  transpilePackages: ['@dagster-io/ui-components', '@dagster-io/ui-core'],
  webpack: (config, {isServer}) => {
    // Unset client-side javascript that only works server-side
    config.resolve.fallback = {fs: false, module: false};

    //https://github.com/vercel/next.js/issues/44273
    config.externals.push({
      'utf-8-validate': 'commonjs utf-8-validate',
      bufferutil: 'commonjs bufferutil',
    });

    const prefix = config.assetPrefix ?? config.basePath ?? '';
    // Use file-loader to load mp4 files.
    config.module.rules.push({
      test: /\.mp4$/,
      use: [
        {
          loader: 'file-loader',
          options: {
            publicPath: `${prefix}/_next/static/media/`,
            outputPath: `${isServer ? '../' : ''}static/media/`,
            name: '[name].[hash].[ext]',
          },
        },
      ],
    });

    return config;
  },
  compiler: {
    styledComponents: true,
  },
  distDir: 'build',
  assetPrefix: 'BUILDTIME_ASSETPREFIX_REPLACE_ME',
  experimental: {
    appDir: false,
  },
};

module.exports = (phase) => {
  if (phase === PHASE_DEVELOPMENT_SERVER) {
    // Set output to undefined in DEV mode to enable the rewrites feature
    // This allows us to redirect all routes back to our index since this is a SPA application
    return {
      ...nextConfig,
      output: undefined,
      assetPrefix: undefined,
      async rewrites() {
        return {
          fallback: [
            {
              source: '/graphql',
              destination: `${process.env.NEXT_PUBLIC_BACKEND_ORIGIN}/graphql`,
            },
            {
              source: '/:path*',
              destination: '/',
            },
          ],
        };
      },
    };
  }
  return nextConfig;
};

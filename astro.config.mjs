// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';

// Deployed to GitHub Pages as a project page, so the site lives under
// /AlphaSeek rather than at the root. Internal links go through url() in
// src/lib/url.ts, which reads BASE_URL — so moving to a custom domain
// later means changing `base` here and nothing else.
// https://astro.build/config
export default defineConfig({
  site: 'https://dreamscraper12.github.io',
  base: '/AlphaSeek',
  trailingSlash: 'ignore',
  // Research notes are MDX (CLAUDE.md section 14).
  integrations: [mdx()],
});

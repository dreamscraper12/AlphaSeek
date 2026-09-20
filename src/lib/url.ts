/**
 * Builds an internal link that respects Astro's configured `base`.
 *
 * The site deploys to GitHub Pages as a project page, so it is served from
 * /AlphaSeek, not the root. Astro does not rewrite hand-written `href="/x"`
 * strings, so every internal link goes through here. If the site later moves
 * to a custom domain, `base` becomes "/" and this returns plain paths with no
 * other change needed.
 */
export function url(path = '/'): string {
  const base = import.meta.env.BASE_URL.replace(/\/+$/, '');
  const rest = path.replace(/^\/+/, '');
  return rest ? `${base}/${rest}` : base || '/';
}

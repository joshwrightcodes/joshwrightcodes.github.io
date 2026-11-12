// Prepares a downloaded pull request build for deployment. This file always runs from main, and it writes every
// setting that reaches Cloudflare, because the deploy step holds the token and the build is untrusted.
//   node pr-preview-config.mjs <pr-number> <zone> <build-dir>
// <build-dir>/site holds the build. The Worker config goes to <build-dir>/wrangler.json.
// The host is one label under the zone, so that Universal SSL covers it.
import { existsSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const COMPATIBILITY_DATE = "2026-11-01";

const [pr, zone, dir] = process.argv.slice(2);
if (!/^\d{1,9}$/.test(pr ?? "") || !/^[a-z0-9.-]+$/.test(zone ?? "") || !dir) {
  throw new Error("usage: pr-preview-config.mjs <pr-number> <zone> <build-dir>");
}

const site = join(dir, "site");
if (!existsSync(join(site, "index.html"))) throw new Error(`${site}/index.html is missing`);

for (const name of ["_redirects", "_worker.js", ".assetsignore"]) rmSync(join(site, name), { force: true, recursive: true });
writeFileSync(join(site, "_headers"), "/*\n  X-Robots-Tag: noindex\n");
writeFileSync(join(site, "robots.txt"), "User-agent: *\nDisallow: /\n");

const name = `site-pr-${pr}`;
const host = `${name}.${zone}`;
const config = {
  name,
  compatibility_date: COMPATIBILITY_DATE,
  assets: { directory: "./site" },
  routes: [{ pattern: host, custom_domain: true }],
  workers_dev: false,
  preview_urls: false,
};
writeFileSync(join(dir, "wrangler.json"), `${JSON.stringify(config, null, 2)}\n`);
console.log(`${name} -> https://${host}`);

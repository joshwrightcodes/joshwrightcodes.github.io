import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

const script = join(import.meta.dirname, "pr-preview-config.mjs");

function build(files = { "index.html": "<!doctype html>" }) {
  const dir = mkdtempSync(join(tmpdir(), "pr-preview-"));
  mkdirSync(join(dir, "site"));
  for (const [name, body] of Object.entries(files)) writeFileSync(join(dir, "site", name), body);
  return dir;
}

function run(...args) {
  return execFileSync("node", [script, ...args], { encoding: "utf8", stdio: "pipe" });
}

test("writes a Worker config for one preview host", () => {
  const dir = build();
  run("7", "wright.codes", dir);
  const config = JSON.parse(readFileSync(join(dir, "wrangler.json"), "utf8"));
  assert.equal(config.name, "site-pr-7");
  assert.deepEqual(config.routes, [{ pattern: "site-pr-7.wright.codes", custom_domain: true }]);
  assert.deepEqual(config.assets, { directory: "./site" });
  assert.equal(config.workers_dev, false);
  assert.equal(config.preview_urls, false);
  assert.equal(config.main, undefined);
});

test("rejects a value that is not a pull request number", () => {
  assert.throws(() => run("7; rm -rf /", "wright.codes", build()), /usage/);
});

test("rejects a zone with unexpected characters", () => {
  assert.throws(() => run("7", "wright.codes/evil", build()), /usage/);
});

test("rejects a build with no index page", () => {
  assert.throws(() => run("7", "wright.codes", build({ "other.html": "x" })), /index\.html/);
});

test("keeps previews out of search results, whatever the pull request supplies", () => {
  const dir = build({ "index.html": "x", _headers: "/*\n  X-Robots-Tag: all\n", "robots.txt": "User-agent: *\nAllow: /\n" });
  run("7", "wright.codes", dir);
  assert.equal(readFileSync(join(dir, "site/_headers"), "utf8"), "/*\n  X-Robots-Tag: noindex\n");
  assert.equal(readFileSync(join(dir, "site/robots.txt"), "utf8"), "User-agent: *\nDisallow: /\n");
});

test("removes files that change how Cloudflare serves the build", () => {
  const dir = build({ "index.html": "x", _redirects: "/ /x 301", "_worker.js": "export default {}", ".assetsignore": "*" });
  run("7", "wright.codes", dir);
  for (const name of ["_redirects", "_worker.js", ".assetsignore"]) assert.equal(existsSync(join(dir, "site", name)), false, name);
});

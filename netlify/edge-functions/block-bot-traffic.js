// Edge-level traffic filter.
//
// Returns 403 for requests geo-located to a blocked country (default: Singapore)
// BEFORE they reach the site, to stop a bot flood that was polluting Google
// Analytics. In the 2026-05-10 → 2026-06-06 window, 1,002 of 1,064 "users"
// came from Singapore with a 0.2% engagement rate and 0.022s average engagement
// time — a JS-executing bot, not real traffic. This site's audience is US-only,
// so blocking Singapore has effectively zero collateral.
// See the 2026-06-07 entry in REDESIGN_NOTES.md.
//
// Safe by design:
//   - Known search / ad crawlers (Googlebot, AdSense's Mediapartners-Google,
//     AdsBot, Bingbot, …) are ALWAYS allowed, even from a blocked country, so
//     this can never harm Search indexing or AdSense.
//   - Kill switch: set env EDGE_BLOCK_ENABLED=false in the Netlify UI to disable
//     instantly, no redeploy.
//   - Configurable: env EDGE_BLOCKED_COUNTRIES (comma-separated ISO-3166 alpha-2
//     codes, default "SG") changes the blocklist with no code change.
//
// Routing is declared in netlify.toml ([[edge_functions]] path = "/*").

const DEFAULT_BLOCKED = "SG";
const OFF_VALUES = ["false", "0", "off", "no"];

// Major legitimate crawlers — never blocked, regardless of geo.
const ALLOWED_BOTS =
  /(Googlebot|Mediapartners-Google|AdsBot-Google|APIs-Google|Google-InspectionTool|Storebot-Google|FeedFetcher-Google|GoogleOther|bingbot|BingPreview|Slurp|DuckDuckBot|Applebot|YandexBot|facebookexternalhit|Twitterbot|LinkedInBot)/i;

// Read an env var across Netlify's edge runtime variants (fail-soft).
function readEnv(name) {
  try {
    if (typeof Netlify !== "undefined" && Netlify.env) {
      const v = Netlify.env.get(name);
      if (v != null) return v;
    }
  } catch (_) {
    // ignore
  }
  try {
    if (typeof Deno !== "undefined" && Deno.env) {
      return Deno.env.get(name);
    }
  } catch (_) {
    // ignore
  }
  return undefined;
}

export default async (request, context) => {
  // Kill switch — anything other than an explicit off-value leaves blocking ON,
  // so the default (env unset) is "block".
  const enabled = (readEnv("EDGE_BLOCK_ENABLED") ?? "true").trim().toLowerCase();
  if (OFF_VALUES.includes(enabled)) {
    return; // pass through to the normal response
  }

  // Never block legitimate search / ad crawlers (protects Search + AdSense).
  const ua = request.headers.get("user-agent") || "";
  if (ALLOWED_BOTS.test(ua)) {
    return;
  }

  // Resolve the blocklist (default SG) and the request's country.
  const blocked = (readEnv("EDGE_BLOCKED_COUNTRIES") ?? DEFAULT_BLOCKED)
    .split(",")
    .map((c) => c.trim().toUpperCase())
    .filter(Boolean);

  const country = (context.geo?.country?.code || "").toUpperCase();

  if (country && blocked.includes(country)) {
    const path = new URL(request.url).pathname;
    console.log(
      `[block-bot-traffic] 403 country=${country} ${request.method} ${path} ua="${ua.slice(0, 80)}"`,
    );
    return new Response("Access denied.", {
      status: 403,
      headers: {
        "content-type": "text/plain; charset=utf-8",
        "cache-control": "no-store",
      },
    });
  }

  // Default: allow.
  return;
};

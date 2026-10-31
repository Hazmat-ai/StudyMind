// Run from repository root: PUBLIC_API_ORIGIN=https://your-api.up.railway.app node scripts/configure-vercel.mjs
import { writeFileSync } from "node:fs";
const origin = new URL(process.env.PUBLIC_API_ORIGIN || "");
if (
  origin.protocol !== "https:" ||
  origin.pathname !== "/" ||
  origin.search ||
  origin.hash ||
  origin.username ||
  origin.password
)
  throw new Error("Set a canonical HTTPS PUBLIC_API_ORIGIN");
const headers = [
  ["X-Content-Type-Options", "nosniff"],
  ["X-Frame-Options", "DENY"],
  ["Referrer-Policy", "no-referrer"],
  ["Strict-Transport-Security", "max-age=31536000"],
  ["Permissions-Policy", "camera=(), microphone=(), geolocation=()"],
  [
    "Content-Security-Policy",
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
  ],
  ["Cache-Control", "no-store"],
].map(([key, value]) => ({ key, value }));
writeFileSync(
  "frontend/vercel.json",
  JSON.stringify(
    {
      buildCommand: "npm run build",
      outputDirectory: "dist",
      rewrites: [
        { source: "/api/:path*", destination: `${origin.origin}/api/:path*` },
        { source: "/(.*)", destination: "/index.html" },
      ],
      headers: [{ source: "/(.*)", headers }],
    },
    null,
    2,
  ) + "\n",
);
console.log(
  "Created frontend/vercel.json. Review and commit this public routing configuration.",
);

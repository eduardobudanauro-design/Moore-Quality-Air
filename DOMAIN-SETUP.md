# Pointing moorequalityair.com at the New Site

The new site currently lives at the GitHub Pages URL:
**https://eduardobudanauro-design.github.io/Moore-Quality-Air/**

When you're ready to make `moorequalityair.com` show the **new** site, follow the
steps below. Read the important note first.

> ⚠️ **Important — coordinate with the owners before cutover.**
> `moorequalityair.com` currently points at the **old** website. Changing the DNS
> below will replace the old site with this new one. Do this only once the owners
> have reviewed and approved the new site, and you have access to the domain's DNS
> (the registrar account — e.g. GoDaddy, Namecheap, Google Domains, etc.).
>
> We intentionally have **not** added a `CNAME` file or changed DNS yet, so the
> shareable preview link above keeps working during review.

## Step 1 — DNS records (at your domain registrar)

Add these records for `moorequalityair.com`:

**Apex domain** (`moorequalityair.com`) — four A records:
```
A   @   185.199.108.153
A   @   185.199.109.153
A   @   185.199.110.153
A   @   185.199.111.153
```
(Optional IPv6 — AAAA records:)
```
AAAA  @  2606:50c0:8000::153
AAAA  @  2606:50c0:8001::153
AAAA  @  2606:50c0:8002::153
AAAA  @  2606:50c0:8003::153
```

**www subdomain** — one CNAME record:
```
CNAME   www   eduardobudanauro-design.github.io
```

Remove any old A/CNAME records that pointed the domain at the previous host.

## Step 2 — Tell GitHub the domain

1. Add a file named `CNAME` (no extension) to the repo root containing exactly:
   ```
   moorequalityair.com
   ```
   (I can do this for you on request — say the word once DNS is ready.)
2. In the repo: **Settings → Pages → Custom domain**, enter `moorequalityair.com`,
   Save. GitHub will verify the DNS.
3. Once verified, check **Enforce HTTPS** (may take up to ~24h for the certificate).

## Step 3 — Verify

- DNS changes can take 15 minutes to 48 hours to propagate.
- When done, `https://moorequalityair.com` and `https://www.moorequalityair.com`
  both load the new site over HTTPS.

## Alternative: Netlify

If you move hosting to Netlify (free, adds built-in form handling), Netlify's
dashboard walks you through the same custom-domain step and provisions HTTPS
automatically. The DNS targets differ — use the values Netlify shows for your site.

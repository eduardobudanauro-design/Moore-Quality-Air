# Moore Quality Air

Marketing website for **Moore Quality Air**, a family-owned HVAC (heating, cooling, and indoor air quality) company.

A fast, self-contained static site — no build step, no dependencies. Just open it in a browser or deploy the folder anywhere.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Page structure and content |
| `styles.css` | All styling (responsive, mobile-first breakpoints) |
| `script.js` | Mobile nav, form validation, scroll reveals |

## Sections

- **Hero** with call-to-action and a comfort/thermostat visual
- **Services** — AC, heating, indoor air quality, maintenance, commercial, emergency
- **Why Us** — value props and trust stats
- **Process** — 4-step how-it-works
- **Reviews** — customer testimonials
- **Contact** — free-estimate request form + business details
- **Footer** — sitemap and contact info

## Running locally

Just open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploying

Drop the folder on any static host — Netlify, GitHub Pages, Cloudflare Pages, Vercel, S3, etc.

## Customizing

Update these before going live:

- **Phone / email / address** — search for `(555) 123-4242`, `service@moorequalityair.com`, and `1420 Comfort Lane` in `index.html` and `script.js`.
- **License number** — `Lic. #HVAC-000000` in the footer.
- **Brand colors** — CSS custom properties at the top of `styles.css` (`:root`).
- **Contact form** — `script.js` currently shows a demo success message. Wire the form to a real backend such as [Netlify Forms](https://docs.netlify.com/forms/setup/), [Formspree](https://formspree.io/), or your own API.

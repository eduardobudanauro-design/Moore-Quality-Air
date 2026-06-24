# Moore Quality Air — Website

Marketing website for **Moore Quality Air**, a family-owned HVAC and plumbing company in **Albuquerque, New Mexico** (founded 2013).

Fast, self-contained, multi-page **static site** — no build step, no dependencies. Deploy the folder anywhere.

## Pages

| File | Page |
|------|------|
| `index.html` | Home |
| `about.html` | About Us (company story, team, credentials) |
| `hvac-services.html` | HVAC Services (conversions, swamp coolers, AC, furnaces, heat pumps) |
| `plumbing-services.html` | Plumbing Services (water heaters, tankless, fixtures) |
| `service-area.html` | Service Area |
| `gallery.html` | Gallery (placeholder until real photos are added) |
| `reviews.html` | Reviews |
| `special-offers.html` | Special Offers (0% financing, Inventory Blowout Sale, discounts) |
| `contact.html` | Contact + estimate form |
| `license.html` | License & credentials |
| `styles.css` / `script.js` | Shared styles and behavior |
| `assets/logo.svg` | Brand logo (designed in-house; see note below) |

## Key business facts (source of truth)

- **Phone:** 505-221-6352
- **Address:** 3301-R Coors Blvd NW, Suite 200, Albuquerque, NM 87120
- **Hours:** Mon–Fri 8AM–5PM (closed weekends). **No 24/7.** Emergency service only for existing customers / new installs.
- **Service area:** Albuquerque, Rio Rancho, Corrales, Los Lunas
- **Owners:** Jonathan McDaniel (founder, 2013) and Anthony Hughes (partner, 2015)
- **Credentials:** NM MM-98 & EE-98, Universal EPA, journeyman techs, Rheem Pro Partner, Energy Star, NATE, HomeAdvisor Best of 2017 & 2018

## Running locally

```bash
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Logo

`assets/logo.svg` is a custom SVG brand mark built to match the company's
existing logo (black serif wordmark + red tornado, "Heating · Cooling · Plumbing").
If an official vector/PNG logo becomes available, replace `assets/logo.svg`
(or drop in `assets/logo.png` and update the `<img src>` references).

## Contact form

`script.js` validates the form and shows a confirmation message (front-end demo).
Before launch, wire it to a real backend — e.g. [Netlify Forms](https://docs.netlify.com/forms/setup/)
or [Formspree](https://formspree.io/) — so submissions are delivered.

## Deploying

Plain static files — host on Netlify, GitHub Pages, Cloudflare Pages, etc.
Currently published via GitHub Pages.

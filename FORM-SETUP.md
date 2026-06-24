# Activating the Contact Form (2 minutes)

The contact form on `contact.html` is fully built and ready — it just needs a free
**Formspree** endpoint so submissions are emailed to you. Formspree works on
GitHub Pages and Netlify with no server.

Right now the form is in **preview mode**: it validates and shows the
"thank you" message, but it does **not** deliver submissions yet. Console shows a
warning to that effect. Follow the steps below to turn delivery on.

## Steps

1. Go to **https://formspree.io** and sign up (free) using the email address
   where you want to **receive leads** (e.g. the Moore Quality Air business inbox,
   or your InsureTech ABQ inbox).
2. Click **+ New Form**, name it "Moore Quality Air Website", and copy the
   **form endpoint** it gives you. It looks like:
   `https://formspree.io/f/abcdwxyz`  (the `abcdwxyz` part is your form ID).
3. In `contact.html`, find this line:
   ```html
   <form class="card" id="contact-form" method="POST" action="https://formspree.io/f/YOUR_FORM_ID" novalidate>
   ```
   Replace `YOUR_FORM_ID` with your real ID, e.g.:
   ```html
   ... action="https://formspree.io/f/abcdwxyz" ...
   ```
4. Commit and push. The very next form submission will arrive in your email.
   (Formspree asks you to confirm your email once on the first submission.)

## Notes

- The form already includes a hidden **honeypot** (`_gotcha`) to reduce spam, and a
  pre-set **subject line** so leads are easy to spot in your inbox.
- The free Formspree plan covers 50 submissions/month. Paid plans add more volume,
  autoresponders, and spam filtering if you need them.
- Prefer a different tool? The same form works with **Web3Forms** or, if you move
  hosting to Netlify, **Netlify Forms** (add `data-netlify="true"` to the form
  and remove the Formspree `action`).

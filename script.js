// Mobile nav toggle
const toggle = document.querySelector('.nav__toggle');
const menu = document.getElementById('nav-menu');
if (toggle && menu) {
  toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  menu.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => {
    menu.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }));
}

// Footer year
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Contact form — submits to Formspree (see FORM-SETUP.md to activate)
const form = document.getElementById('contact-form');
const note = document.getElementById('form-note');
const SUCCESS_MSG = 'Thank you for reaching out. We will call you back within one business day. If you need immediate help, call 505-221-6352.';
function setNote(msg, type) { if (note) { note.textContent = msg; note.className = 'form__note ' + type; } }

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Validate required fields
    const required = ['firstName', 'lastName', 'phone', 'email', 'city', 'service'];
    let firstBad = null;
    required.forEach((id) => {
      const f = form.elements[id];
      if (!f) return;
      const empty = !f.value.trim();
      const badEmail = id === 'email' && f.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.value);
      if (empty || badEmail) { f.classList.add('invalid'); if (!firstBad) firstBad = f; }
      else f.classList.remove('invalid');
    });
    if (firstBad) { setNote('Please complete the required fields with a valid email and phone.', 'error'); firstBad.focus(); return; }

    const endpoint = form.getAttribute('action') || '';

    // Not yet connected to Formspree — show confirmation UX (preview mode)
    if (endpoint.includes('YOUR_FORM_ID')) {
      setNote(SUCCESS_MSG, 'success');
      form.reset();
      console.warn('[Moore Quality Air] Contact form is in PREVIEW mode — submissions are not delivered yet. See FORM-SETUP.md to connect Formspree.');
      return;
    }

    // Live: send to Formspree via AJAX
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.dataset.label = submitBtn.textContent; submitBtn.textContent = 'Sending…'; }
    setNote('Sending your request…', '');
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' },
      });
      if (res.ok) {
        setNote(SUCCESS_MSG, 'success');
        form.reset();
      } else {
        const data = await res.json().catch(() => ({}));
        const msg = (data.errors && data.errors.map((x) => x.message).join(', ')) || 'Something went wrong. Please call us at 505-221-6352.';
        setNote(msg, 'error');
      }
    } catch (err) {
      setNote('Network error — please call us at 505-221-6352.', 'error');
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = submitBtn.dataset.label || 'Send My Request'; }
    }
  });

  form.querySelectorAll('input, select, textarea').forEach((el) => el.addEventListener('input', () => el.classList.remove('invalid')));
}

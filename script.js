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

// Contact form (front-end demo — wire to a real backend before launch)
const form = document.getElementById('contact-form');
const note = document.getElementById('form-note');
function setNote(msg, type) { if (note) { note.textContent = msg; note.className = 'form__note ' + type; } }
if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const required = ['firstName', 'lastName', 'phone', 'email'];
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
    setNote('Thank you for reaching out. We will call you back within one business day. If you need immediate help, call 505-221-6352.', 'success');
    form.reset();
  });
  form.querySelectorAll('input, select, textarea').forEach((el) => el.addEventListener('input', () => el.classList.remove('invalid')));
}

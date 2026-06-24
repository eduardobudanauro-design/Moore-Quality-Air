// Mobile nav toggle
const toggle = document.querySelector('.nav__toggle');
const menu = document.getElementById('nav-menu');

if (toggle && menu) {
  toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  // Close menu when a link is tapped (mobile)
  menu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      menu.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// Current year in footer
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Estimate form validation (front-end demo — wire up to a backend/email service)
const form = document.getElementById('estimate-form');
const status = document.getElementById('form-status');

function showStatus(message, type) {
  if (!status) return;
  status.textContent = message;
  status.className = 'form__note ' + type;
}

if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const required = ['name', 'phone', 'email'];
    let firstInvalid = null;

    required.forEach((id) => {
      const field = form.elements[id];
      const empty = !field.value.trim();
      const badEmail = id === 'email' && field.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value);
      if (empty || badEmail) {
        field.classList.add('invalid');
        if (!firstInvalid) firstInvalid = field;
      } else {
        field.classList.remove('invalid');
      }
    });

    if (firstInvalid) {
      showStatus('Please fill in your name, a valid email, and phone number.', 'error');
      firstInvalid.focus();
      return;
    }

    // Demo success — replace with a real submission (Netlify Forms, Formspree, API, etc.)
    showStatus('Thanks! We received your request and will reach out shortly.', 'success');
    form.reset();
  });

  // Clear invalid state as the user types
  form.querySelectorAll('input, select, textarea').forEach((el) => {
    el.addEventListener('input', () => el.classList.remove('invalid'));
  });
}

// Reveal-on-scroll for cards/steps
const revealEls = document.querySelectorAll('.card, .step, .why__stat');
if ('IntersectionObserver' in window && revealEls.length) {
  revealEls.forEach((el) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    el.style.transition = 'opacity .5s ease, transform .5s ease';
  });
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'none';
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  revealEls.forEach((el) => io.observe(el));
}

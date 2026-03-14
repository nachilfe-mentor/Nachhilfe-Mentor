// Nachhilfe Mentor — Main JS v2

document.addEventListener('DOMContentLoaded', () => {

  // ── Navbar scroll ──────────────────────────────
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // ── Active nav link ────────────────────────────
  const navLinks = document.querySelectorAll('.nav-link[href^="#"]');
  const sections = document.querySelectorAll('section[id]');
  function updateActive() {
    const scrollY = window.scrollY + 120;
    sections.forEach(sec => {
      if (scrollY >= sec.offsetTop && scrollY < sec.offsetTop + sec.offsetHeight) {
        navLinks.forEach(l => {
          l.classList.toggle('active', l.getAttribute('href') === '#' + sec.id);
        });
      }
    });
  }
  window.addEventListener('scroll', updateActive, { passive: true });

  // ── Mobile menu ────────────────────────────────
  const toggle = document.querySelector('.mobile-toggle');
  const mobileNav = document.querySelector('.mobile-nav');
  if (toggle && mobileNav) {
    toggle.addEventListener('click', () => {
      const open = toggle.classList.toggle('open');
      mobileNav.classList.toggle('open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    });
    mobileNav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        toggle.classList.remove('open');
        mobileNav.classList.remove('open');
        document.body.style.overflow = '';
      });
    });
  }

  // ── Smooth scroll ──────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        window.scrollTo({ top: target.offsetTop - 80, behavior: 'smooth' });
      }
    });
  });

  // ── Scroll-reveal (.animate-up) ───────────────
  const revealObs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        revealObs.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.animate-up').forEach(el => revealObs.observe(el));

  // ── Counter animations ─────────────────────────
  function animateCount(el) {
    const target = parseInt(el.dataset.count, 10);
    const suffix = el.dataset.suffix || '';
    const duration = 1800;
    const start = performance.now();
    const easeOut = t => 1 - Math.pow(1 - t, 3);
    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      const value = Math.round(easeOut(progress) * target);
      el.textContent = value.toLocaleString('de-DE') + suffix;
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  const counterObs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animateCount(e.target);
        counterObs.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('.stat-number[data-count]').forEach(el => counterObs.observe(el));

  // ── Floating particles in hero ─────────────────
  const heroParticles = document.querySelector('.hero-particles');
  if (heroParticles) {
    const colors = ['rgba(79,172,254,0.7)', 'rgba(0,242,254,0.6)', 'rgba(139,92,246,0.6)'];
    function spawnParticle() {
      const p = document.createElement('span');
      const size = Math.random() * 3 + 2;
      const color = colors[Math.floor(Math.random() * colors.length)];
      const left = Math.random() * 100;
      const dur = Math.random() * 4 + 4;
      const drift = (Math.random() - 0.5) * 120;
      p.style.cssText = `
        position:absolute; bottom:0; left:${left}%;
        width:${size}px; height:${size}px;
        background:${color}; border-radius:50%;
        pointer-events:none; opacity:0;
        animation: particle-rise ${dur}s ease-in forwards;
        --drift: ${drift}px;
      `;
      heroParticles.appendChild(p);
      setTimeout(() => p.remove(), dur * 1000 + 100);
    }

    // Inject keyframe
    const s = document.createElement('style');
    s.textContent = `
      @keyframes particle-rise {
        0%   { transform: translateY(0) translateX(0); opacity: 0; }
        10%  { opacity: 1; }
        90%  { opacity: 0.6; }
        100% { transform: translateY(-80vh) translateX(var(--drift)); opacity: 0; }
      }
    `;
    document.head.appendChild(s);
    setInterval(spawnParticle, 400);
  }
});

// SCROLL REVEAL ANIMATIONS
function revealOnScroll() {
  const reveals = document.querySelectorAll('.reveal');
  const revealOptions = {
    threshold: 0.085
  };
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, revealOptions);
  reveals.forEach(reveal => {
    revealObserver.observe(reveal);
  });
}

// PAGE LOAD HERO STAGGER
window.addEventListener('DOMContentLoaded', () => {
  document.querySelector('.hero-headline').style.opacity = 1;
  document.querySelector('.hero-headline').style.transform = 'none';
  setTimeout(() => {
    document.querySelector('.hero-subtext').style.opacity = 1;
    document.querySelector('.hero-subtext').style.transform = 'none';
  }, 120);
  setTimeout(() => {
    document.querySelector('.btn-hero').style.opacity = 1;
    document.querySelector('.btn-hero').style.transform = 'none';
  }, 250);
  revealOnScroll();
});

// NAV BAR BLUR ON SCROLL
window.addEventListener('scroll', () => {
  const nav = document.querySelector('nav');
  if(window.scrollY > 14) {
    nav.style.backdropFilter = 'blur(26px) saturate(130%)';
    nav.style.background = 'rgba(25,16,8,0.82)';
  } else {
    nav.style.backdropFilter = 'blur(18px) saturate(110%)';
    nav.style.background = 'rgba(25,16,8,0.58)';
  }
});

// NEWSLETTER SUBMIT (no actual backend)
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.newsletter-form');
  if(form) {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      form.reset();
      input.blur();
      const btn = form.querySelector('button');
      btn.innerHTML = 'Subscribed!';
      btn.disabled = true;
      setTimeout(() => {
        btn.innerHTML = 'Subscribe';
        btn.disabled = false;
      }, 3800);
    });
  }
});

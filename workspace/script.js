// Navigation blur on scroll
const nav = document.querySelector('nav');
window.addEventListener('scroll', () => {
  if (window.scrollY > 22) nav.classList.add('scrolled');
  else nav.classList.remove('scrolled');
});

// Hero entrance animation
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelector('.hero').classList.add('visible');
  }, 250);
});

// Scroll reveal (features, testimonials)
const revealEls = document.querySelectorAll('.reveal');
const revealObs = new IntersectionObserver((entries, obs) => {
  entries.forEach(entry => {
    if(entry.isIntersecting) {
      entry.target.classList.add('visible');
      obs.unobserve(entry.target);
    }
  });
},{threshold:0.15});
revealEls.forEach(el => revealObs.observe(el));

// Optional: smooth scroll for nav links
const navLinks = document.querySelectorAll('.nav-links a');
navLinks.forEach(link => link.addEventListener('click', e => {
  if(link.hash && document.querySelector(link.hash)) {
    e.preventDefault();
    document.querySelector(link.hash).scrollIntoView({behavior:'smooth'});
  }
}));
// Optional: CTA hero
const ctaHero = document.getElementById('cta-hero');
if(ctaHero) ctaHero.onclick = () => {
  document.getElementById('contact').scrollIntoView({behavior:'smooth'});
};

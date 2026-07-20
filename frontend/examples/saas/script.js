// --- Scroll reveal animation using Intersection Observer ---
const observer = new window.IntersectionObserver(
  (entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.17 }
);

document.querySelectorAll('.section, .hero-content, .feature-card, .how-step, .pricing-card, .testimonial-card, .cta-banner')
  .forEach((el, i) => {
    // add a slight delay for staggered effect
    setTimeout(() => observer.observe(el), 140 + (i * 105));
  });

// Navigation blur/opacity on scroll
const nav = document.querySelector('.nav');
window.addEventListener('scroll', () => {
  if (window.scrollY > 10) {
    nav.style.background = 'rgba(10,10,10,0.88)';
    nav.style.backdropFilter = 'blur(24px) saturate(170%)';
  } else {
    nav.style.background = 'rgba(10,10,10,0.76)';
    nav.style.backdropFilter = 'blur(16px) saturate(140%)';
  }
}); // Smoothly transition nav background on scroll

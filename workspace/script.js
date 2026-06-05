// Navbar blur on scroll
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 10) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
});

// Staggered load for hero elements
window.addEventListener('DOMContentLoaded', () => {
  const heroEls = document.querySelectorAll('.hero-inner > *, .hero-visual');
  heroEls.forEach((el, i) => {
    el.style.opacity = 0;
    el.style.transform = 'translateY(28px)';
    setTimeout(() => {
      el.style.transition = 'opacity 0.8s cubic-bezier(0.16,1,0.3,1), transform 0.7s cubic-bezier(0.16,1,0.3,1)';
      el.style.opacity = 1;
      el.style.transform = 'none';
    }, 350 + i * 110);
  });
});

// IntersectionObserver for scroll reveals
const observer = new window.IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll('.scroll-reveal').forEach(el => {
  observer.observe(el);
});

// Optional: simple glowing pointer spot (radial effect)
const mesh = document.querySelector('.bg-mesh');
if(mesh && window.innerWidth > 900){
  document.addEventListener('mousemove', e => {
    mesh.style.backgroundPosition = `${e.clientX/12}px ${e.clientY/18}px, right bottom, left top`;
  });
}

// Scroll-reveal logic
const revealSelectors = [
  '.hero-inner',
  '.about h2', '.about-text',
  '.portfolio h2', '.portfolio-categories', '.portfolio-grid',
  '.services h2', '.packages',
  '.testimonials h2', '.testimonial-cards',
  '.contact h2','.contact-form'
]

document.addEventListener('DOMContentLoaded', () => {
  const revealEls = [];
  revealSelectors.forEach(sel => document.querySelectorAll(sel).forEach(el => {
    el.classList.add('reveal');
    revealEls.push(el);
  }));

  const obs = new window.IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.16 }
  )
  revealEls.forEach(el => obs.observe(el));

  // Nav blur on scroll
  const nav = document.querySelector('nav.nav');
  let last = window.scrollY;
  window.addEventListener('scroll', () => {
    if(window.scrollY > 24){
      nav.style.background = 'rgba(16,12,28,0.9)';
      nav.style.backdropFilter = 'blur(16px)';
    } else {
      nav.style.background = 'rgba(16,12,28,0.75)';
      nav.style.backdropFilter = 'blur(16px)';
    }
  })

  // Portfolio Tabs
  document.querySelectorAll('.portfolio-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.portfolio-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const group = tab.getAttribute('data-tab');
      document.querySelectorAll('.portfolio-group').forEach(g => {
        g.style.display = g.getAttribute('data-group') === group ? 'flex':'none';
      })
    })
  })

  // Contact form submit interaction (demo)
  const form = document.querySelector('.contact-form');
  form.addEventListener('submit', e => {
    e.preventDefault();
    form.querySelector('button[type="submit"]').textContent = "Sent! I'll be in touch.";
    setTimeout(()=>{
      form.querySelector('button[type="submit"]').textContent = "Send Inquiry";
    },2500);
    form.reset();
  });
})

// Animations
const style = document.createElement('style');
style.textContent = `
.reveal { opacity:0; transform:translateY(24px); transition: opacity .45s cubic-bezier(.16,1,.3,1), transform .39s cubic-bezier(.16,1,.3,1); }
.visible { opacity:1!important; transform: none!important; }
.hero-inner.visible { transition-delay: .09s; }
.hero-tagline.visible { transition-delay: .17s; }
.hero-cta.visible    { transition-delay: .28s; }
`;
document.head.appendChild(style);

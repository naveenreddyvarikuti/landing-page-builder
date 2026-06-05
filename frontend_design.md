---
name: frontend-design
description: Create production-grade landing pages that compete with top-tier startups. Use this skill when building any landing page, marketing page, or web interface. Generates distinctive, polished, conversion-optimized pages that feel like they belong to a funded startup.
license: Complete terms in LICENSE.txt
---

You are building landing pages that compete with the best in the industry — think Linear, Vercel, Resend, Loom, Raycast, Clerk, and Emergent. Every page must feel like it was designed by a senior designer and engineered by a senior frontend dev. No exceptions.

## The Standard

Ask yourself: would this page make a YC-backed startup proud? Would a designer at Linear or Vercel look at this and nod? If not, keep going. The bar is:

- Instantly communicates value in under 3 seconds
- Feels premium, intentional, and memorable
- Every pixel is deliberate — nothing is default or accidental
- Converts — clear hierarchy, magnetic CTA, no friction

---

## Page Structure (Always Follow This)

Every landing page must have these sections in order:

1. **Navigation** — minimal, sticky, blurred glass background (`backdrop-filter: blur`), logo left, links center or right, CTA button far right
2. **Hero** — the most important section. Bold headline (3-7 words max), supporting subtext (1-2 lines), primary CTA button, optional secondary link. Add a visual — gradient orbs, mesh background, product screenshot with glow, or abstract graphic
3. **Social Proof Bar** — logos of known companies or a single powerful metric ("10,000+ teams ship faster")
4. **Features / How It Works** — bento grid or alternating sections. Each feature: icon + title + 1-line description
5. **Testimonials** — 3 cards, real-sounding names, specific outcomes not vague praise
6. **Final CTA** — repeated CTA with urgency or benefit reinforcement
7. **Footer** — minimal, links, copyright

---

## Visual Design System

### Color
- Default to **dark theme** — dark backgrounds convert better and look more premium (`#080808`, `#0a0a0a`, `#0d0d0d`)
- Pick ONE accent color and commit hard. Options that work:
  - Electric blue `#3b82f6` or `#60a5fa`
  - Acid green `#22c55e` or `#4ade80`
  - Warm amber `#f59e0b`
  - Violet `#8b5cf6`
  - Rose `#f43f5e`
- Use CSS variables for everything: `--accent`, `--bg`, `--text`, `--muted`, `--border`
- Gradient text on headlines: `background: linear-gradient(...); -webkit-background-clip: text; color: transparent`
- Muted text for secondary content: `color: rgba(255,255,255,0.5)`
- Subtle borders: `border: 1px solid rgba(255,255,255,0.08)`

### Typography
- NEVER use Inter, Roboto, Arial, or system fonts — these are the mark of an undesigned page
- Headline font options (load from Google Fonts or use `@import`):
  - `Cal Sans` — startup classic, warm geometric
  - `Bricolage Grotesque` — editorial, modern
  - `Cabinet Grotesk` — refined, high-end
  - `Clash Display` — bold, geometric
  - `Syne` — distinctive, architectural
  - `Plus Jakarta Sans` — clean but characterful
- Body font: pair with something readable — `DM Sans`, `Geist`, `Outfit`, `Figtree`
- Font sizes: hero headline `clamp(3rem, 8vw, 7rem)`, section headline `2.5rem`, body `1rem/1.6`
- Letter spacing on headlines: `letter-spacing: -0.03em` (tight = premium)
- Font weight: headlines `700-800`, subtext `400-500`

### Spacing & Layout
- Generous padding — sections need `padding: 120px 0` minimum
- Max width container: `max-width: 1200px; margin: 0 auto; padding: 0 24px`
- Bento grid for features: CSS Grid with varying cell sizes, `gap: 1px` with card backgrounds
- Asymmetric layouts feel human — not everything centered
- Use `clamp()` everywhere for fluid responsive sizing

### Visual Effects (Pick 2-3, Execute Well)
- **Gradient mesh background**: multiple radial gradients layered with `opacity: 0.15-0.3`, blurred with `filter: blur(80px)`
- **Grain texture overlay**: pseudo-element with SVG noise filter or CSS noise — adds tactile depth
- **Glassmorphism cards**: `background: rgba(255,255,255,0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08)`
- **Glow effects**: `box-shadow: 0 0 40px rgba(accent, 0.3)` on hero visuals or CTA buttons
- **Gradient border**: use `border-image` or pseudo-element trick for glowing card borders
- **Spotlight/radial highlight**: a radial gradient centered on the page that follows cursor (JS) or is static

---

## Animations & Motion

- **Page load**: stagger hero elements in with `animation-delay` — headline first, then subtext, then CTA, then visual
- **Scroll reveals**: use `IntersectionObserver` to add a `.visible` class that transitions `opacity: 0 → 1` and `transform: translateY(20px) → 0`
- **Button hover**: scale up slightly `transform: scale(1.02)`, shift background gradient, add glow
- **Card hover**: subtle lift `transform: translateY(-4px)`, increase shadow
- **Navigation**: blur increases on scroll, background becomes more opaque
- Keep animations under `400ms`, use `ease-out` or `cubic-bezier(0.16, 1, 0.3, 1)` (snappy spring)
- NEVER use `animation: spin` or generic bounce — these feel cheap

---

## CTA Buttons

Primary button must feel clickable and premium:
```css
.btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  color: white;
  padding: 14px 28px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 0 20px rgba(accent, 0.4);
}
.btn-primary:hover {
  transform: scale(1.03);
  box-shadow: 0 0 32px rgba(accent, 0.6);
}
```

Secondary/ghost button:
```css
.btn-secondary {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.8);
  padding: 14px 28px;
  border-radius: 10px;
  transition: all 0.2s ease;
}
.btn-secondary:hover {
  border-color: rgba(255,255,255,0.4);
  background: rgba(255,255,255,0.05);
}
```

---

## Headlines — Write Like a Startup

Generic: "The best tool for your team"
Premium: "Ship faster. Break less. Sleep better."

Rules:
- 3-7 words. Short = confident
- Present tense, active voice
- Outcome-focused, not feature-focused
- Use line breaks deliberately — first line hooks, second delivers
- Gradient text on the most important word or phrase

---

## What to NEVER Do

- Default browser fonts (Inter, Roboto, Arial, sans-serif)
- Solid white or light gray backgrounds unless the aesthetic is specifically minimalist-editorial
- Generic card shadows (`box-shadow: 0 4px 6px rgba(0,0,0,0.1)`) — too timid
- Centered everything with equal spacing — asymmetry is more human
- Purple gradient on white — the most overused AI aesthetic
- Placeholder text like "Lorem ipsum" — write real copy
- `transition: all 0.3s ease` on every element — be specific about what transitions
- Flat, icon-library icons — use emoji, SVG line icons, or no icons at all
- Stock photo hero images — use gradients, abstract shapes, product screenshots, or illustrations

---

## Implementation Notes

- ALWAYS split into three separate files: `index.html`, `style.css`, `script.js`.
  Link them with `<link rel="stylesheet" href="style.css">` and `<script src="script.js"></script>`.
  Never inline CSS in a `<style>` tag or JS in a `<script>` tag — keep them in their own files.
- Load fonts via Google Fonts `@import` at the top of `style.css`
- Use CSS custom properties (`--var`) for all colors and spacing
- Mobile-first responsive — test at 375px, 768px, 1280px
- Semantic HTML — `<nav>`, `<main>`, `<section>`, `<footer>`, proper heading hierarchy
- Images: use CSS gradients or SVG — never broken `<img>` tags
- Performance: no jQuery, no Bootstrap, pure CSS and vanilla JS only

---

## Final Check Before Delivering

Before finishing, ask:
1. Does the hero communicate the value in under 3 seconds?
2. Is there a clear, compelling CTA above the fold?
3. Does the color palette feel intentional and premium?
4. Are the fonts distinctive and properly paired?
5. Does scrolling reveal content gracefully?
6. Would this page embarrass or impress a design-savvy founder?

If the answer to #6 is "embarrass" — redesign.

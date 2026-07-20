"""One-off script: generate the 3 showcase example sites with the real pipeline.
Run one at a time:  python gen_examples.py 0   (then 1, then 2)
"""
import sys
import shutil
from pathlib import Path

from workspace_context import set_workspace
from indexing.index_manager import set_collection_name, drop_collection
from main import run_pipeline

EXAMPLES = [
    (
        "coffee-shop",
        "Create a stunning, production-quality landing page for 'Ember & Oak', a specialty "
        "third-wave coffee roastery and cafe in Portland. Audience: local coffee lovers and "
        "remote workers. Include: a hero with the shop name, an evocative tagline about "
        "single-origin beans roasted in-house daily, and a primary call-to-action button "
        "('View Menu'); an 'Our Story' section about the roastery's craft and ethical sourcing; "
        "a 'Menu Highlights' section featuring four signature drinks (Honey Lavender Latte, "
        "Cold Brew Tonic, Single-Origin Pour-Over, Brown Butter Mocha) each with a short "
        "description and price; a 'Visit Us' section with opening hours, address, and a "
        "newsletter signup; and a footer with social links. Warm, cozy, inviting aesthetic with "
        "rich earthy tones and a hand-crafted feel. Write specific, sensory, evocative copy — "
        "absolutely no lorem ipsum or placeholder text.",
    ),
    (
        "photographer",
        "Create an elegant, editorial portfolio landing page for 'Lena Cross', a fine-art "
        "wedding and portrait photographer based in Tuscany. Audience: engaged couples planning "
        "destination weddings. Include: a full-bleed hero with her name, a refined tagline about "
        "capturing timeless, emotive moments, and a 'Book a Session' call-to-action; an 'About' "
        "section with a short first-person artist statement describing her documentary, "
        "light-driven style; a 'Portfolio' gallery grid organized into categories (Weddings, "
        "Portraits, Engagements) using tasteful placeholder image blocks with captions; a "
        "'Services & Packages' section with three tiers listing what each includes; two client "
        "testimonials; and a contact section with an inquiry form (name, email, wedding date, "
        "message). Sophisticated, minimal, editorial aesthetic with generous whitespace and "
        "refined serif typography. Write elegant, specific copy — no placeholder text.",
    ),
    (
        "saas",
        "Create a high-converting B2B product launch landing page for 'Pulse', a SaaS that turns "
        "raw product-usage data into instant, actionable insights for product teams. Audience: "
        "product managers and startup founders. Include: a hero with the product name, a sharp "
        "value-proposition headline, a supporting subheadline, and dual CTAs ('Start Free Trial' "
        "and 'Book a Demo'); a social-proof logo strip (use tasteful placeholder company names); "
        "a 'Features' section with four features, each with an icon, title, and benefit-focused "
        "description (real-time dashboards, funnel analysis, anomaly alerts, one-click "
        "integrations); a 'How It Works' three-step section; a pricing section with three tiers "
        "(Starter, Growth, Enterprise) and feature lists; a customer testimonial quote; and a "
        "final full-width CTA banner. Modern, confident, techy aesthetic. Write persuasive, "
        "benefit-driven copy — no lorem ipsum.",
    ),
]

idx = int(sys.argv[1])
slug, prompt = EXAMPLES[idx]

out = (Path(__file__).parent / "frontend" / "examples" / slug).resolve()
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

set_workspace(out)
set_collection_name(f"example_{slug}")

print(f"=== generating {slug} ===")
for event in run_pipeline(prompt):
    print(event)

drop_collection(f"example_{slug}")
print(f"=== done {slug} -> {out} ===")

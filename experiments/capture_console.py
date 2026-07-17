"""
BAg-IDS — Capture d'écran de la console HITL en fonctionnement réel
(dashboard + page Investigations avec trace agentique), puis composition
en une figure à deux panneaux pour le papier.

Prérequis : backend HITL sur :8090 + pipeline de détection démarré.
    python experiments/capture_console.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "paper_q1" / "figures"
BASE = "http://127.0.0.1:8090"

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": 1500, "height": 860},
                            device_scale_factor=2)
    # ---- login (admin)
    page.goto(BASE, wait_until="networkidle")
    page.fill("input[type='text'], input:not([type='password'])", "admin")
    page.fill("input[type='password']", "admin123")
    page.click("button[type='submit'], button.primary, form button")
    page.wait_for_url("**/", timeout=15000)
    page.wait_for_timeout(5000)          # laisser le dashboard se remplir
    page.screenshot(path=str(OUTDIR / "screen_dashboard.png"))
    print("dashboard capturé")

    # ---- page Investigations : navigation SPA via le menu (pas d'URL directe)
    page.click("a[href='/investigations'], nav >> text=Investigations")
    page.wait_for_timeout(4500)
    rows = page.locator("table tbody tr")
    n = rows.count()
    print("enquêtes listées :", n)
    # choisir une enquête traitée par le VRAI LLM (provider != rules-fallback),
    # de préférence une campagne (« Oui »)
    chosen = False
    order = sorted(range(min(n, 25)),
                   key=lambda k: "Oui" not in rows.nth(k).inner_text())
    for k in order:
        rows.nth(k).click()
        page.wait_for_timeout(900)
        panel = page.inner_text("body")
        if "openrouter" in panel:
            print(f"enquête {k} : provider openrouter ✓")
            chosen = True
            break
    if not chosen and n:
        rows.nth(0).click()
        print("!! aucune enquête openrouter trouvée — 1re enquête utilisée")
    page.wait_for_timeout(1200)
    page.screenshot(path=str(OUTDIR / "screen_investigations.png"))
    print("investigations capturé")
    browser.close()

# ---- composition : deux panneaux empilés avec étiquettes (a)/(b)
from PIL import Image, ImageDraw, ImageFont

a = Image.open(OUTDIR / "screen_dashboard.png")
b = Image.open(OUTDIR / "screen_investigations.png")
pad, label_h = 24, 66
W = max(a.width, b.width) + 2 * pad
H = a.height + b.height + 2 * label_h + 3 * pad
canvas = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("arialbd.ttf", 40)
except Exception:
    font = ImageFont.load_default()

y = pad
draw.text((pad, y), "(a) Real-time dashboard — live pipeline, 5 agents "
          "online", fill="#16223a", font=font)
y += label_h
canvas.paste(a, (pad, y)); y += a.height + pad
draw.text((pad, y), "(b) Investigations view — agentic "
          "perceive-reason-act-reflect trace of the Investigator",
          fill="#16223a", font=font)
y += label_h
canvas.paste(b, (pad, y))
out = OUTDIR / "console_screenshot.png"
canvas.save(out, dpi=(300, 300))
print("OK ->", out, canvas.size)

# Resume templates and Playwright PDF

Résumés are rendered as HTML fragments, wrapped by [`PDFGenerator`](core/generator.py) (`_create_pdf_html_document`: Tailwind Play CDN, print media emulation, `print_background: true`). The **effective layout width for media queries is often narrower than Tailwind `md` (768px) or `lg` (1024px)** because printable area depends on paper size and margins—not your browser preview width.

## Rules for multi-column shells

When a template combines a **narrow sidebar** + **wide main column** (or reorderable columns):

1. **Do not rely only on Tailwind breakpoints** (`md:flex-row`, `lg:grid-cols-12`, `print:*`) for the **outer chrome**. CDN Play may compile utilities **after** your template `<style>` block or lose cascade ties with `flex` / `flex-col` on the same element.

2. **Prefer plain CSS in the fragment** (same `<style>` as the template) scoped under one root class, e.g. `.my-template .my-shell`. For PDF, **`@media (min-width: <N>px), print`** can work, but **`@media print { ... }` alone is more reliable**: some Chromium PDF paths evaluate page width oddly, so duplicate the desktop shell rules wholesale under `@media print` (Creative Studio uses this).

3. **`backdrop-filter`, `backdrop-blur-*`, and translucent `bg-*/`** (alpha) layers can composite badly in Chromium **print-to-PDF**, sometimes yielding an “empty” main column or clipped content. For print, **strip backdrop filters** and optionally force an **opaque** `background` on those cards (Creative Studio `@media print`).

4. **Use `display: grid !important`** (or equivalently decisive rules) on the outer shell under that media query, with explicit columns like **`240px minmax(0, 1fr)`** or a **12-column** grid with `span`—see:

   - [`resume_builder/templates/resume_templates/portfolio.html`](../resume_builder/templates/resume_templates/portfolio.html) (`portfolio-shell`, `.portfolio-template`)
   - [`resume_builder/templates/resume_templates/creative_studio.html`](../resume_builder/templates/resume_templates/creative_studio.html) (`creative-studio-row`, `.creative-studio-template`)

5. **Mobile stack + desktop order**: If DOM uses `order-*` so the sidebar appears first when stacked, duplicate **desktop ordering** explicitly in PDF (Portfolio: `grid-column` + `order`; Creative Studio: implicit grid column flow sidebar then main matches DOM sidebar-first—grid places column 1 = 240px, column 2 = main).

6. **Duplicated responsive blocks** (e.g. certifications `lg:hidden` vs `hidden lg:block`): replicate **desktop** visibility in **`@media print`** with hook classes (`portfolio-certs-mobile`, `portfolio-certs-sidebar`), not only Tailwind `lg`.

7. **Single-column templates** (`professional.html`, unconditional `grid-cols-*` on the shell) avoid this class of bug altogether.

See also **`emulate_media(media="print")`** and viewport setup in [`PlaywrightPDFGenerator.generate_pdf_from_html`](core/generator.py).

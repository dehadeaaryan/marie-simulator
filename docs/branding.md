# Branding assets and reference

The primary visual reference is the user's existing `../apps.aaryandehade.com/index.html`, inspected read-only at the user's request. The simulator adopts its self-hosted Figtree font, black canvas, warm neutral surfaces, `#ff7a30` orange, rounded floating header, pill navigation, stronger typography, and restrained rounded panels. The header has the existing AD logo and a single marie. wordmark, as requested; Aaryan attribution is in the footer. Dark is the default; a matching light theme is also available. A subtle static background tint stays outside the workspace; the reference's animated blobs and grain are omitted to keep code and state readable.

`web/static/ad-logo.png` is the original `apple-touch-icon.png` copied unchanged from the apps repo. `web/static/favicon.ico` and `web/static/fonts/figtree-latin-wght-normal.woff2` also come from that repository. These assets were reused under the user's explicit authorization; no logo was redrawn or generated. Figtree's SIL Open Font License is included alongside the font.

Earlier inspection also covered public HTML from Shalendar, Pollish, and Cooldown Room and Pollish's compiled CSS. No files in those applications, the apps collection, or the portfolio were modified. Reference-app rendering was unavailable in the in-app browser in this session; the source of the apps collection provided the definitive styling reference. Simulator screenshots were reviewed through local desktop/mobile browser tests.

The orange trailing period matches `../shalendar/src/lib/components/Brand.svelte`; Shalendar was inspected read-only.

# Faster-WAM project page

A responsive, standalone research project website based on **arXiv:2608.02365v2 (6 October 2026)**. The layout follows the [original NeRF project page](https://www.matthewtancik.com/nerf): a centered paper header, simple resource icons, and a narrow white reading column. Abstract and real-world rollouts lead the page, followed by physical evaluation, method, and benchmarks. No build step or JavaScript dependencies are required.

## Preview

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

Open `http://localhost:8000`. The page also works as a local file; clipboard access may require localhost or HTTPS.

## Share a single HTML file

Send `Faster-WAM-share.html` to a coauthor. It includes the styles, scripts, fonts, figures, and all rollout snapshots, and opens directly in a browser without a server. Paper and code links lead online; model weights remain a placeholder. The video placeholder has been removed.

To regenerate it after editing the page:

```bash
python3 scripts/export_html.py
```

Exporting needs internet access to bundle the Google Fonts and their licenses. The resulting HTML needs no network access to display the page or run its interactive comparisons.

## Files

- `index.html`: paper title, authors, text, tables, resource placeholders, and citation.
- `styles.css`: responsive layout and visual styling.
- `script.js`: benchmark selector, real-time snapshot comparison, and citation copy button.
- `assets/figures/`: original paper figures converted from PDF to SVG.
- `assets/rollouts/`: Appendix G snapshots converted to WebP.
- `scripts/prepare_assets.py`: repeatable conversion of paper assets.

## Project resources

- **Code:** https://github.com/TeamFasterwam/FasterWAM (the owner-provided URL).
- **Weights:** still **Coming soon**. Replace the remaining `.resource-placeholder` span with a link when the public URL is ready.
- **Video:** omitted for now. The comparison uses the paper's recorded still images and explicitly identifies them as snapshots.

## Rollout timing

The slider uses **elapsed seconds from 0 to 140**, so equal distances represent equal durations. Play defaults to **1× speed**, with a **2× option** applied equally to all four policies. Timing uses the elapsed browser clock; switching speeds preserves the current recorded time. Dragging or changing tabs pauses playback. Arrow buttons jump to adjacent recorded snapshots without changing the time scale.

Samples occur every 5 seconds through 140 seconds, plus an additional 21-second sample for each policy. LingBot-VA includes 15 more recorded frames from the original project export, filling the gaps after 40 seconds in the arXiv package. Between samples, the previous recorded image is held and its sample time remains visible. At each policy's reported completion time (21.2, 21.6, 38.5, or 139.9 seconds), the final recorded frame is displayed and held. The file names `025s`, `040s`, and `140s` are the paper's sampled comparison slots, not a claim that completion happened at those rounded times.

## Content provenance

The source used for this draft is the matching arXiv submission in `../arxiv_submission`, rather than older drafts in the research code repository.

- `figures/main_figure.pdf` → overview in the Method section.
- `figures/method_figure.pdf` → complete architecture diagram.
- `appx/real_world_rollouts/` → interactive snapshot comparison directly after the Abstract. Images are **recorded snapshots, not a video**. The seconds-based playback preserves the original elapsed time.
- `../xvdycwvhbjrdfjmvsyddwqfbmhkdzfng.zip` → an additional 21-second sample for all four policies, plus 15 LingBot-VA snapshots at 45, 50, 55, 65, 70, 75, 85, 90, 95, 105, 110, 115, 125, 130, and 135 seconds. All 35 PNGs shared by this archive and the published source match byte for byte. No frames are synthesized or interpolated. Files after each policy's final comparison slot are excluded because the final frame is held once its task is complete.
- Tables 1–3 → benchmark and generalization results.
- Table 4 and Appendix G → physical evaluation and illustrative rollout completion times. Individual rollout times are not mean completion times.
- Appendix E → latency scope and profiling qualifications. These are model phase totals, not robot execution time; some baselines combine separately timed components.

The author display follows the PDF's names, affiliations, and contribution notes. The BibTeX author names follow the arXiv abstract metadata. Future paper updates should update both the static default benchmark values in `index.html` and the interactive values in `script.js`.

Regenerate local figures and compressed snapshots with:

```bash
python3 scripts/prepare_assets.py --source ../arxiv_submission \
  --rollout-archive ../xvdycwvhbjrdfjmvsyddwqfbmhkdzfng.zip
```

Requires `pdftocairo`, `pdftoppm`, and `ffmpeg`. This is an optional asset-preparation step; normal preview and deployment need none of these tools.

## GitHub Pages

Publish to **https://teamfasterwam.github.io/** from the repository root on the `main` branch using GitHub Pages. `.nojekyll` enables direct static-file serving. In the repository's **Settings → Pages**, select **Deploy from a branch → main → / (root)**. Subsequent pushes to `main` publish the updated page.

The current remote is `TeamFasterwam/TeamFasterwam.github.io`, so social metadata uses `https://teamfasterwam.github.io/`. Update the `og:url` and `og:image` tags if the deployment URL changes. Fonts are loaded from Google Fonts, with local sans-serif fallbacks; all scientific figures and snapshots are served locally.

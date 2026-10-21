# Example: North Loop product ad

4-shot vertical (9:16) outdoor thermos ad produced with the product-ad / pipeline skills.

## Asset notice

**AI-generated demo asset.** “North Loop” is a fictional demo brand. The product packshot and example frames were generated with Seedream / Seedance for documentation — not a real commercial SKU, not a stock-photo download, and not user photography. Swap in your own licensed or owned product stills for production work.

## Pipeline

1. **Seedream** keyframes from a product reference photo
2. **Seedance 2.0 Mini** image-to-video (4 s × 4 shots)
3. **MiniMax** HD voiceover + on-screen captions
4. Local **ffmpeg** assemble / mix / burn-in

Auth: `POWERTOKENS_API_KEY` (API key required; browser OAuth is not in this release).

## Claim sheet (demo)

| Claim | Source | Used in |
|---|---|---|
| Keeps coffee hot ~12 hours | demo brief (confirm before paid publish) | s01–s04, VO |
| Brand: North Loop | demo brief | s04, vo04 |

## Shot list

| Shot | Caption | Camera |
|---|---|---|
| s01 | 6 a.m. Still hot. | Macro bottle on wet rock, sunbeam push-in |
| s02 | Pour it. Still hot. | Gloved pour into cup lid, steam |
| s03 | 12 hours. Still hot. | Hiker on ridge, bottle in backpack |
| s04 | North Loop. Still hot. | Summit hero, slow orbit |

## Reproduce

Shotlist: [`tools/examples/northloop-ad.json`](../tools/examples/northloop-ad.json). Put a product still at `product.jpg` next to the workdir, then:

```bash
export POWERTOKENS_API_KEY="your-key"
python3 scripts/pipeline.py plan tools/examples/northloop-ad.json
# review estimate, then:
python3 scripts/pipeline.py run tools/examples/northloop-ad.json --approve-estimate <total>
```

Stills and a short compressed clip: [`assets/examples/northloop/`](../assets/examples/northloop/).

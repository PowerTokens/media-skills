# Seedream (images and keyframes)

- Formula: subject + composition + setting + lighting + lens + style. ≤ 600 English words.
- Keyframes for video: make them at the target ratio (9:16 → `--size 1440x2560`) so i2v does not crop.
- Product fidelity: pass the real packshot as `--image` and say "keep the product, label and colors
  exactly as in the reference; change only the background and lighting".
- Product-ad props: no third-party logos, wordmarks, packaging, or brand-identifiable devices
  (Apple MacBook / iPhone / logo, Nike swoosh, Starbucks cup mark, Amazon smile, Google/Microsoft
  hardware logos) unless that brand is the SKU or the user approved it. Ask for a generic stand-in
  (plain silver laptop with no logo or chin text, blank phone bezel, plain mug).
- Character sheets: one neutral full-body + one close-up face on plain background; reuse as references.
- Text in images: quote the exact words, keep them short (≤ 5 words), check the output; if garbled,
  remove text and add it in the edit (captions) instead.
- Sets: `-n 4` with `sequential_image_generation` for storyboard frames that share a look.

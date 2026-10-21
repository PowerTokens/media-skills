# Example brief (shape only)

```text
Photo: ./inputs/coast-morning.jpg
Want: 第二世界 / travel collage poster, 3:4
Figures: auto
Caption language: English (you invent the line)
```

Agent then (internally): observes wave + wet sand reflection → invents a paper pond cutout with one line figure scooping foam into a cup → caption e.g. "saving a bit for later." → builds prompt from `references/method.md` → confirms → `image.py -m seedream-5-0-260128 --size 1536x2048 --image ./inputs/coast-morning.jpg -p "..."`.

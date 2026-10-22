# Voiceover scripts (MiniMax speech)

- Write for the ear: short sentences, contractions, numbers as words when spoken ("twelve hours").
- **Original claims only.** Do not write song lyrics, a brand slogan copied verbatim, a celebrity endorsement, or a long copyrighted quote. MiniMax blocks those with `CONTENT_POLICY`. For an ad, every line comes from the approved claim sheet. Say this before spending on EN voiceover.
- Length: 15 s ≈ 30–40 English words; 30 s ≈ 70–80. Chinese ≈ 4–5 characters/s.
- One speech call per line/beat (pipeline `voiceover.lines[]`, or `speech.py --split-lines`). A blocked line must name its segment id and text; the other lines still generate. Rewrite a blocked line once, then ask the user if it is still blocked.
- Voice choice: narrator/trust → `English_Trustworthy_Man`; calm premium → `English_Graceful_Lady`;
  energetic → `English_Diligent_Man`; Mandarin → `Chinese (Mandarin)_News_Anchor` and others.
  Full list: https://docs.powertokens.ai/en/zmodelAudio/minimax/speech-2.8-turbo
- `--speed` 0.9–1.15 keeps it natural.
- Pronunciation of brand names: spell phonetically in the script if the first take is wrong.

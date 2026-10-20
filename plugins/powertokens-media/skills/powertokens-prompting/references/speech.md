# Voiceover scripts (MiniMax speech)

- Write for the ear: short sentences, contractions, numbers as words when spoken ("twelve hours").
- Length: 15 s ≈ 30–40 English words; 30 s ≈ 70–80. Chinese ≈ 4–5 characters/s.
- One file per line/beat makes timing and re-takes cheap; the pipeline concatenates them.
- Voice choice: narrator/trust → `English_Trustworthy_Man`; calm premium → `English_Graceful_Lady`;
  energetic → `English_Diligent_Man`; Mandarin → `Chinese (Mandarin)_News_Anchor` and others.
  Full list: https://docs.powertokens.ai/en/zmodelAudio/minimax/speech-2.8-turbo
- `--speed` 0.9–1.15 keeps it natural.
- Pronunciation of brand names: spell phonetically in the script if the first take is wrong.

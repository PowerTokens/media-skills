# Image and speech models

## Seedream (POST /v1/images/generations)
| Model id | Notes |
|---|---|
| `seedream-4-5-251128` | Default. `size` = `2K`, `4K` or `WxH` with total pixels between 2560×1440 and 4096×4096, aspect 1/16–16. Up to 14 reference images. |
| `seedream-5-0-260128` | Listed in PT docs; limits not re-checked here. |
| `dola-seedream-5-0-pro-260628` | Id as listed by live /v1/models (docs page name says seedream-5-0-pro); limits not re-checked. |

Prompt: Chinese or English; docs recommend ≤ 300 Chinese characters / 600 English words.
`sequential_image_generation: auto` + `max_images` returns a coherent set (storyboards).
Price: not stored in this repo — check https://powertokens.ai/models.
Source: https://docs.powertokens.ai/en/zmodelImage/byteplus/seedream-4-5-text-to-image

## MiniMax speech (POST /v1/audio/speech)
| Model id | Use |
|---|---|
| `speech-2.8-turbo` | Default, fast |
| `speech-2.8-hd` | Higher quality narration |
| `speech-2.6-*`, `speech-02-*` | Older; listed in PT docs |

Max 10,000 characters per request. Docs say non-streaming returns a 302 redirect; the live API on
2026-10-20 returned HTTP 200 JSON `{"data": {"audio": "<temporary https URL>"}}`. Scripts accept both.
Billed per 1K input characters (price not stored here). Voice ids are fixed strings, e.g.
`English_Trustworthy_Man`, `English_Graceful_Lady`, `Chinese (Mandarin)_News_Anchor`.
Source: https://docs.powertokens.ai/en/zmodelAudio/minimax/speech-2.8-turbo

Live check 2026-10-20: `seedream-4-5-251128` returned one 1440×2560 image (JPEG bytes from the result
URL); `speech-2.8-turbo` returned a 2.7 s MP3 for a 33-character line.

## Related production skill

`powertokens-travel-poster` — photo → 3:4 second-world collage; prefer `seedream-5-0-260128` at `1536x2048` with the upload as `--image`.

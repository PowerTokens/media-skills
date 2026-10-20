# Image and speech models

## Seedream (POST /v1/images/generations)
| Model id | Notes |
|---|---|
| `seedream-4-5-251128` | Default. `size` = `2K`, `4K` or `WxH` with total pixels between 2560×1440 and 4096×4096, aspect 1/16–16. Up to 14 reference images. |
| `seedream-5-0-260128` | Listed in PT docs; limits not re-checked here. |
| `seedream-5-0-pro-260628` | Listed in PT docs; limits not re-checked here. |

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

Max 10,000 characters per request. Non-streaming returns a 302 redirect to a temporary audio URL.
Billed per 1K input characters (price not stored here). Voice ids are fixed strings, e.g.
`English_Trustworthy_Man`, `English_Graceful_Lady`, `Chinese (Mandarin)_News_Anchor`.
Source: https://docs.powertokens.ai/en/zmodelAudio/minimax/speech-2.8-turbo

# Video models on PowerTokens

Limits and list prices below are copied from PowerTokens Video Studio `models.py`
(PRICE_CHECKED_DATE 2026-10-05) and the PT API docs. Prices are USD per output second for a typical
text-to-video request; billing can change and some inputs (e.g. input video) may price differently.
Always confirm on https://powertokens.ai/models before quoting a firm number.

| Model id | Seconds | Resolutions | Ratios | List USD/s | Inputs |
|---|---|---|---|---|---|
| `wan3.0-video` | 2–30 | 480p 0.05 · 720p 0.10 · 1080p 0.20 | 16:9 9:16 1:1 4:3 3:4 adaptive | see col 3 | text, first_frame, first+last frame, reference_image/video/audio |
| `wan3.0-video-prime` | 2–30 | 480p 0.068 · 720p 0.14 · 1080p 0.28 | same as Wan 3.0 | see col 3 | same as Wan 3.0, faster |
| `dreamina-seedance-2-0-fast-260128` | 4–15 | 480p 0.121 · 720p 0.121 | 16:9 9:16 1:1 4:3 3:4 21:9 adaptive | see col 3 | text, first/last frame, multimodal reference |
| `dreamina-seedance-2-5-260628` | 4–30 | 480p 0.105 · 720p 0.232 · 1080p 0.569 | same as Seedance Fast | see col 3 | text, first/last frame, reference_image/video/audio |
| `kling-v3` | 3–15 | 720p(std) 0.126 · 1080p(pro) 0.168 · 4K 0.42 | 16:9 9:16 1:1 | with audio | text, first frame, last frame (image_tail) |

Notes from the docs:
- Wan 3.0: max 30 s at 30 fps; prompt up to 20,000 characters; in reference mode refer to inputs as
  "image 1", "video 1", "audio 1" by order; `reference_*` and `first_frame`/`last_frame` are mutually
  exclusive. Source: https://docs.powertokens.ai/en/zmodelVideo/ali/wan3.0-video-generation
- Seedance 2.5: `generate_audio` makes voice, SFX and music from the prompt; put dialogue in double
  quotes; audio is mono. `return_last_frame` can chain clips (not exposed by these scripts yet).
  `omni_reference_task_type` = auto/reference/edit/extend. Image-to-video crops the image if the
  ratio differs. Source: https://docs.powertokens.ai/en/zmodelVideo/byteplus/dreamina-seedance-2-5-multimodal-reference-to-video
- Seedance 2.0 Fast: 4–15 s, no 1080p. Source: https://docs.powertokens.ai/en/zmodelVideo/byteplus/dreamina-seedance-2-0-fast-text-to-video
- Kling v3: prompt and negative_prompt max 2,500 characters; native multi-shot (`multi_shot`,
  up to 6 shots, 512 chars each, durations must sum to total) exists in the API but is not wired in
  these scripts; image-to-video supports up to 3 reference elements (not wired).
  Sources: https://docs.powertokens.ai/en/zmodelVideo/kling/kling-v3-text2video, https://docs.powertokens.ai/en/zmodelVideo/kling/kling-v3-image2video
- Unknown / unverified here: max reference images per Seedance/Wan request, queue times, per-account
  model availability, prices for non-default inputs. Say "unknown" rather than guessing.

Estimated cost = list USD/s × seconds. Example: Wan 3.0 720p 5 s ≈ $0.50.

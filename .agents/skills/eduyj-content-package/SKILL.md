---
name: eduyj-content-package
description: Use when designing or implementing EduYJ student mission contents, image packages, template stages, gpt-image-2 prompts, teacher approval, or stage-4 realtime practice.
---

# EduYJ Content Package

Canonical docs:

- `docs/01-child-content-experience.md`
- `docs/04-ai-content-template-spec.md`
- `docs/07-realtime-practice-spec.md`
- `docs/09-image-content-package-spec.md`

Non-negotiables:

- Mission content has 4 student-facing stages.
- Stages 1~3 are approved static template JSON.
- Stage 4 is approved realtime practice using `RealtimePracticeSpec`.
- Reflection happens after stage 4 and is not counted as stage 5.
- Each mission has `hero`, `stage_1`, `stage_2`, `stage_3`, `stage_4_realtime` image assets.
- Use `gpt-image-2` for generated images.
- Image text should be minimal; UI text owns questions, choices, and feedback.
- Teacher approval is required before student exposure.

When generating prompts:

```text
visual style
scene
educational focus
composition constraints
accessibility constraints
OCR/text constraints
quality bar
avoid list
```

Reject designs that add video pipelines, free HTML/JS generation, or student-visible AI diagnosis labels.

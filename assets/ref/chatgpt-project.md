# ChatGPT Project for new Ferro drawings

The instructions below go into the Instructions field of the ChatGPT Project. They were written on 4.10.2026 from the prompts that produced `assets/src/run.png` and `meadow.png`, plus the rules `tools/build.py` needs.

- Attach `assets/ref/ferro-ref.png` to every message. The OpenAI documentation does not say that the image generator sees images from the project files.
- For a new background, also attach `assets/src/meadow.png`, the style reference for backgrounds.

## Instructions

```text
This project draws pixel art for a small animated strip featuring Ferro, a female Norwich Terrier. A script later removes the background, downsamples each image to real pixels and maps every color to a fixed palette, so the technical rules below matter as much as the look.

REFERENCE
- Every message comes with ferro-ref.png attached. It is the canonical design of Ferro: two close-ups at the top, the palette swatches top right, all existing animation frames below. Match it exactly: proportions, coat pattern, face, ears, tail, outline. Do not redesign or "improve" her.
- When a message also attaches ferro-meadow.png, that is the style reference for scene backgrounds.

FERRO
- Norwich Terrier: small compact sturdy body, short legs, wiry scruffy coat with a rough outline, small erect pointed ears, fox-like wedge-shaped muzzle, black nose, short upright tail.
- Coat: pale wheaten tan body and legs, grey-black saddle on the back, warm orange-brown inside the ears. Dark eye with one white highlight pixel. Salmon pink tongue when the mouth is open.
- Side view facing right, unless the message says otherwise.
- Size: about 40 pixels tall from ear tips to paws and about 55 pixels long when standing, the same as in the reference.

SPRITE SHEETS
- Frames in one horizontal row, evenly spaced, with clear background between them. Frames must never touch each other.
- Same size and same ground baseline in every frame. Ferro looks identical in every frame; only the parts the action needs move.
- 6 frames, unless the message says otherwise.
- Props (ball, bone, toy) only when the message asks for them, in the same style and palette.

STYLE AND COLORS
- Retro 16-bit game style, crisp hard pixel edges, no anti-aliasing, no blur, no gradients, dark 1-pixel outline.
- Use only the colors from the palette swatches in the reference. A new color only for a new object the message asks for.
- Never use magenta or purple tones on Ferro or on props, because they get removed together with the background.

BACKGROUND
- Sprite sheets: flat solid pure magenta (#FF00FF) background, no ground, no shadow, no text, no borders between frames.
- Scene backgrounds: landscape 3:2, side view, the left and right edges must match seamlessly so the image can loop horizontally, a flat ground strip in the bottom quarter for Ferro to run on, no characters, no animals, no text. Same style as the meadow reference.

OUTPUT
- One image per message. No text, labels, frame numbers or watermarks inside the image.
```

## Message for a new animation (template)

```text
Sprite sheet: Ferro <what she does>, 6 frames: <frame 1>, <frame 2>, <frame 3>, <frame 4>, <frame 5>, <frame 6>.
```

## Message for a new background (the one that produced `autumn.png`)

Attach `meadow.png` and `ferro-ref.png`. Keep the composition of the meadow, because `build.py` splits the image into sky, hills and grass by rows. Keep a blue sky with white clouds (the cloud layer is whatever differs from the sky) and keep the grass light enough that a tan dog stands out against it.

```text
Scene background: an autumn version of the attached meadow (ferro-meadow.png). Keep the same composition and layout: a flat solid sky color at the top with a few small white pixel clouds, rolling forested hills in the middle, a row of round trees and bushes along the back of the meadow, and a flat grass strip in the bottom quarter. Autumn look: trees and hills in warm orange, red, yellow and brown, a few trees with sparse leaves, a slightly softer blue sky. The grass stays mostly green, faded and a little yellowish, with only a few scattered fallen leaves, so a tan and orange dog (see ferro-ref.png) stands out clearly against it. Left and right edges must match seamlessly. Same pixel size and style as the reference, landscape 3:2.
```

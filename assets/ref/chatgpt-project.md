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

## Message for a new animation with props (the one that produced `poop-walk.png`)

ChatGPT drew the dog a little longer and the droppings much bigger than asked; `build.py` evens that out with its own factors (see CLAUDE.md).

```text
Sprite sheet: Ferro walking slowly forward while pooping, 4 frames. She keeps the hunched pooping posture from the poop row of the reference the whole time: back arched, hind legs bent low under the body, tail raised, head forward. Frame 1: front left paw and hind right paw step forward. Frame 2: legs passing under the body. Frame 3: front right paw and hind left paw step forward. Frame 4: legs passing under the body. Small steps; the body stays at the same low height in every frame and only the legs move. Below the row of frames, in a separate row, well apart from each other and from the frames, three small dog droppings of slightly different sizes, each smaller than the pile in the reference, in the same brown and outline style.
```

## Message for sitting and looking at the viewer (the one that produced `sit.png`)

Attached with `ferro-ref.png` and photos of the real Ferro for her face from the front. ChatGPT drew her bigger, with a bigger head, and the bodies in frames 3-6 are close but not identical; `build.py` scales by 9.0 and aligns on the front toes.

```text
Sprite sheet: Ferro stops running, sits down and turns her head to look at the viewer. 6 frames, left to right:
1. Braking out of a run, still facing right: front legs stretched forward and planted, hind legs under the body, body leaning back.
2. Sitting down: hindquarters lowering, hind legs folding, front legs straight.
3. Sitting upright in side view facing right: front legs straight and together, hind legs folded under her, tail resting on the ground behind her, head in profile looking right.
4. The same sitting body as frame 3, head turned three-quarters towards the viewer.
5. The same sitting body, head facing the viewer straight on: both eyes and both erect ears visible, black nose in the centre, mouth closed.
6. The same as frame 5, with the head tilted slightly to one side, the curious dog head tilt.

Rules for this sheet:
- In frames 3 to 6 the body, legs and tail are identical, pixel for pixel, in the same position. Only the head changes.
- Same scale as the frames in the reference: standing, she is about 40 pixels from ear tips to paws. Sitting, she is taller and shorter, but her head is the same size as in the reference.
- All 6 frames stand on the same ground line.
- For her face seen from the front, use the attached photos of the real Ferro: pale wheaten face with a lighter, scruffy muzzle, dark round eyes with one white highlight pixel each, black nose, large erect pointed ears with warm orange-brown inside. Keep the coat pattern from the reference: grey-black saddle on the back, wheaten chest and legs.
- Use only the colours from the palette in the reference.
```

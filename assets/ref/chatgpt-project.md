# ChatGPT Project for new Ferro drawings

The instructions below go into the Instructions field of the ChatGPT Project. They were written on 4.10.2026 from the prompts that produced `assets/src/run.png` and `meadow.png`, plus the rules `tools/build.py` needs. Updated the same day after the new strips: the reference sheet has three close-ups, and ChatGPT drew `poop-walk.png` and `sit.png` bigger than the reference and the droppings far too big, so the size rules are stricter.

- Attach `assets/ref/ferro-ref.png` to every message. The OpenAI documentation does not say that the image generator sees images from the project files.
- For a new background, also attach `assets/src/meadow.png`, the style reference for backgrounds.

## Instructions

```text
This project draws pixel art for a small animated strip featuring Ferro, a female Norwich Terrier. A script later removes the background, downsamples each image to real pixels and maps every color to a fixed palette, so the technical rules below matter as much as the look.

REFERENCE
- Every message comes with ferro-ref.png attached. It is the canonical design of Ferro: three close-ups at the top (standing, running, sitting and facing the viewer), the palette swatches top right, all existing animation frames below. Match it exactly: proportions, coat pattern, face, ears, tail, outline. Do not redesign or "improve" her.
- When a message also attaches ferro-meadow.png, that is the style reference for scene backgrounds.

FERRO
- Norwich Terrier: small compact sturdy body, short legs, wiry scruffy coat with a rough outline, small erect pointed ears, fox-like wedge-shaped muzzle, black nose, short upright tail.
- Coat: pale wheaten tan body and legs, grey-black saddle on the back, warm orange-brown inside the ears. Dark eyes with one white highlight pixel in each visible eye. Salmon pink tongue when the mouth is open.
- Side view facing right, unless the message says otherwise.
- Size: about 40 pixels tall from ear tips to paws and about 55 pixels long when standing, the same as in the reference. Do not draw her bigger, longer or with a bigger head than in the reference, even when the image has room to spare; compare her head with the close-ups.

SPRITE SHEETS
- Frames in one horizontal row, evenly spaced, with clear background between them. Frames must never touch each other.
- Same size and same ground baseline in every frame. Ferro looks identical in every frame; only the parts the action needs move.
- 6 frames, unless the message says otherwise.
- Props (ball, bone, toy) only when the message asks for them, in the same style and palette, and at their real size next to her: a ball or a dropping is smaller than her head.

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

## Message for sniffing (the one that produced `sniff.png`, 6.10.2026)

Attach `ferro-ref.png`; save the result as `assets/src/sniff.png`. The scene plan: she slows out of a run (frame 1), walks slowly with her nose to the grass (frames 2-5, a walk cycle like `poop-walk.png`), stops and sniffs one spot (frame 6), lifts her head (frame 1 played backwards) and runs on. The nose twitch while she sniffs is derived in `build.py` from frame 6, not drawn by ChatGPT: it redraws every frame from scratch, so a subtle movement drawn by it makes the dog tremble.

Frames 1 and 6 are good. The walk (frames 2-5) is not: ChatGPT put the same near front leg forward in frames 2 and 4, so each leg had only two poses, forward and straight under the body, and the walk did not look fluid (Vatra, 6.10.2026). "Front left paw and hind right paw step forward" was not enough to make it alternate the legs; the walk is redrawn with the message below.

```text
Sprite sheet: Ferro sniffing the ground. 6 frames, left to right:
1. Slowing from a run to a walk, mid-step, head lowering towards the ground.
2. Walking slowly forward with her nose close to the ground: head low and stretched forward, the nose just above the ground line, back level, tail up. Front left paw and hind right paw step forward.
3. The same, legs passing under the body.
4. The same, front right paw and hind left paw step forward.
5. The same, legs passing under the body.
6. Standing still on all four paws, sniffing one spot: nose touching the ground line, ears pointing forward, tail up.

Rules for this sheet:
- In frames 2 to 6 the head, back and tail are identical, in the same position and at the same height. Only the legs move (in frame 6 the nose is a little lower, touching the ground).
- Mouth closed in every frame, no tongue.
- Same scale as the frames in the reference: standing, she is about 40 pixels from ear tips to paws and about 55 pixels long, with her head the same size as in the reference. Do not draw her bigger.
- All 6 frames stand on the same ground line. No grass, no ground, no shadow and no object under her nose: the ground is in the scene.
- Use only the colours from the palette in the reference.
```

## Message for the nose-down walk (6.10.2026, result rejected)

Attach `ferro-ref.png` and `assets/src/sniff.png`; save the result as `assets/src/sniff-walk.png`. It replaces frames 2-5 of `sniff.png`. The message names the near and far legs and says outright that frame 4 is frame 1 with the legs swapped, because "front left paw steps forward" alone gave two identical frames.

Result: Vatra liked the first sheet better (the new one had a different head, and the body sat two pixels lower). Shown on one page in motion, three walks were all rejected (6.10.2026): the first sheet as drawn (two poses per leg); the first sheet with near and far leg colours swapped in the second half of the step ("the front leg moves too much"); this sheet ("looks like she cannot move her legs"). The sheet was not kept. Transplanting this sheet's legs onto the first sheet's body was not tried: the bodies differ in height, leg length and hind leg position.

```text
Sprite sheet: Ferro walking slowly forward with her nose to the ground, a 6-frame walk cycle that loops. Keep her pose from the attached sniff sheet (sniff.png), frames 2 to 5: the same head held low with the nose just above the ground line, the same back, tail and size. Only the legs move.

She faces right, so her left legs are the near legs (in front of the body, fully lit) and her right legs are the far legs (behind the body, partly hidden, a little darker). The legs move in diagonal pairs: the near front leg together with the far hind leg, the far front leg together with the near hind leg.

Front legs, left to right (each hind leg does the same as its diagonal partner):
1. Near front leg reaching forward, paw on the ground. Far front leg pushed back behind the shoulder, paw about to lift.
2. Near front leg on the ground, now under the front of the chest. Far front leg lifted, bent, swinging forward.
3. Near front leg on the ground, straight under the shoulder and slanting back. Far front leg passing in front of it, paw still lifted.
4. The mirror of frame 1: far front leg reaching forward, paw on the ground. Near front leg pushed back behind the shoulder, paw about to lift.
5. Far front leg on the ground, under the front of the chest. Near front leg lifted, bent, swinging forward.
6. Far front leg on the ground, straight under the shoulder and slanting back. Near front leg passing in front of it, paw still lifted.

Rules for this sheet:
- Frame 1 and frame 4 must not look the same: in frame 1 the near legs reach forward, in frame 4 the far legs do. Every leg goes through six different positions over the six frames.
- Small slow steps. The head, back and tail are identical in all six frames, at the same height; only the legs change.
- Mouth closed, no tongue.
- Same scale as the frames in the reference and in sniff.png. Do not draw her bigger.
- All 6 frames stand on the same ground line. No grass, no ground and no shadow.
- Use only the colours from the palette in the reference.
```

## Message for drinking (7.10.2026)

Attach only `ferro-ref.png`; save the result as `assets/src/drink.png`. `sniff.png` is left out on purpose (Vatra, 7.10.2026): ChatGPT draws the slowing down and the lowered head from scratch, and if they come out better than in `sniff.png`, they can replace the sniff frames too. The scene plan (Vatra, 7.10.2026): she runs to a bowl and drinks, and drops of water appear beside the bowl so it reads as water. The bowl and the drops are drawn in code like the ball, not by ChatGPT: the bowl has to scroll in with the grass separately from the dog, the drops have to appear and vanish on their own, and a drop of 1-2 pixels is lost in downsampling, as the eye highlight was. The bowl goes in front of her nose and hides the muzzle tip. The lapping head bob is derived from frame 2 in `build.py`, like `sniff-up`. If ChatGPT moves the body between frames 4 and 5, the closed mouth is derived from frame 4 instead. ChatGPT drew the tongue shaded in several pinks, also in frame 2 (lapping). In the saved `drink.png` both tongues are recoloured to the hue of the palette tongue colour `#e7766f`, keeping ChatGPT's shading: each pixel is the palette colour times its brightness relative to the tongue's average (Vatra, 7.10.2026; a flat single colour lost the texture). The rest of the sheet is as ChatGPT drew it.

```text
Sprite sheet: Ferro stops running and drinks water from a bowl that is NOT drawn: a script adds the bowl in front of her nose later. 5 frames, left to right:
1. Slowing from a run to a stop, last step, head lowering towards the ground.
2. Drinking: standing still on all four paws, front legs a little apart, head stretched forward and down so that her nose is just above the ground line. Mouth slightly open, ears relaxed, tail level.
3. The same standing body, head lifted halfway, mouth closed.
4. The same standing body, head raised in normal profile looking right, licking her lips: the tip of the tongue out and curled up over the front of her nose.
5. The same as frame 4 with the mouth closed, no tongue.

Rules for this sheet:
- In frames 2 to 5 the body, legs and tail are identical, pixel for pixel, in the same position. Only the head and neck move.
- No bowl, no water, no drops, no grass, no ground and no shadow.
- Same scale as the frames in the reference: standing, she is about 40 pixels from ear tips to paws and about 55 pixels long, with her head the same size as in the reference. Do not draw her bigger.
- All 5 frames stand on the same ground line.
- The tongue only in frame 4, in the salmon pink from the reference.
- Use only the colours from the palette in the reference.
```

## Message for the water bowl and drops (7.10.2026)

Attach `ferro-ref.png` and `assets/src/drink.png`; save the result as `assets/src/bowl.png`. Vatra rejected the bowl and drops drawn in code (`bowl()` in `build.py`, 7.10.2026: "Užas"). The bowl stays a separate prop, not drawn with the dog, because it scrolls in with the grass; `build.py` splits it into the back of the rim (behind her) and the rest (in front of her), so her muzzle dips under the water. The bowls and drops get factors of their own, like the droppings, because ChatGPT draws props bigger than asked. Three bowls in one sheet, so Vatra can choose.

```text
Sprite sheet: props for Ferro drinking, as in frame 2 of the attached drink.png. No dog in this image.

Row 1: three variants of the same small dog water bowl, side by side and well apart from each other, so I can choose one: 1. red plastic, 2. stainless steel, 3. blue glazed ceramic. Each bowl is seen from the side and a little from above, so the round rim and the water inside are visible: a light blue water surface with one or two white highlight pixels. Low and wide, with a flat bottom standing on the ground line.

Row 2, below the bowls and well apart from them: five single water drops splashed out of a bowl, of different sizes, light blue with a white highlight pixel, each on its own and well apart from the others.

Rules for this sheet:
- Size: Ferro's scale from the reference. A bowl is about as wide as her head is long (about 18 to 20 pixels) and about 7 to 8 pixels tall, wide enough for her muzzle to fit in when she drinks as in frame 2 of drink.png. A drop is 2 to 4 pixels. Do not draw them bigger.
- Same pixel-art style as Ferro: crisp hard pixels, dark 1-pixel outline on the bowls, no anti-aliasing, no gradients.
- No dog, no grass, no ground, no shadow, no text.
- New colours only for the bowls and the water. Never magenta or purple.
```

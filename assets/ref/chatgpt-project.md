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

## Message for lapping water from the bowl (7.10.2026)

Attach `ferro-ref.png`, `assets/src/drink.png` and `assets/src/bowl.png`; save the result as `assets/src/drink-lap.png`. Ferro and the bowl were drawn apart and put together in code, and Vatra did not like it (her muzzle under the water looked like drowning; with the bowl behind her the water hardly showed). Here ChatGPT draws them together, so the tongue meets the water as it should.

```text
Sprite sheet: Ferro lapping water from the red bowl in the attached bowl.png, in the pose of frame 2 of the attached drink.png. 4 frames, left to right:
1. Head lowered over the bowl, muzzle just above the water, tongue out and down, its tip touching the water surface.
2. Tongue curled under, scooping water, two or three small drops splashing out of the bowl beside it.
3. Tongue pulled back up towards the mouth, the drops falling beside the bowl.
4. Mouth closed just above the water, one drop landing on the ground beside the bowl.

Rules for this sheet:
- The muzzle never goes under the water: only the tongue touches it.
- The bowl is identical in every frame and in the same position. Ferro's body, legs and tail are identical in every frame; only the head and the tongue move.
- Same scale as the reference: standing, she is about 40 pixels from ear tips to paws. The bowl is a little wider than her head is long. Do not draw them bigger.
- The tongue in the salmon pink of the reference, with its shading. The drops light blue with a white highlight pixel.
- All 4 frames stand on the same ground line. No grass, no ground, no shadow.
```

## Messages for four new stops (7.10.2026)

Vatra wants more variety: she sat in 42% of all stops. He chose the stops from what the real Ferro does on a walk: she stops and looks around, stops and listens, eats a piece of bread off the ground, and scratches behind her ear. There are three sheets, because looking around and listening share one standing body. ChatGPT redraws the body in every frame, so `build.py` will put each frame's head on one body, as `lap()` does for drinking. Small movements (an ear twitch while she listens, the chewing) are derived in code where they can be. Slowing down with her head lowering before the bread is sniff-0, as for drinking.

### Looking around and listening (save as `assets/src/stand.png`)

Attach `ferro-ref.png` and `assets/src/drink.png`. Looking around plays frames 1, 2, 3, 4, 3, 2; listening plays 1, 2, 5, 6, 5, 2.

```text
Sprite sheet: Ferro stops running and stands still, looking around and listening. 6 frames, left to right:
1. Slowing from a run to a stop, last step, head up and looking ahead.
2. Standing still on all four paws, as in frame 5 of the attached drink.png: head up in profile looking right, ears up, mouth closed, tail up.
3. The same standing body, head turned three-quarters towards the viewer, looking off to the side past the viewer.
4. The same standing body, head turned back over her near shoulder, looking behind her to the left.
5. The same standing body, listening: head raised a little higher than in frame 2, both ears pricked up high and pointing forward, looking far ahead to the right.
6. The same as frame 5 with the head tilted slightly to one side.

Rules for this sheet:
- In frames 2 to 6 the body, legs and tail are identical, pixel for pixel, in the same position. Only the head and neck move.
- Mouth closed in every frame, no tongue.
- Measures: the same scale as the frames in the reference. Standing, she is about 40 pixels from ear tips to paws and about 55 pixels long, about a third of the image height, and her head is the same size as in the reference close-ups. Do not draw her bigger.
- All 6 frames stand on the same ground line, well apart from each other. No grass, no ground, no shadow.
- Use only the colours from the palette in the reference.
```

### Eating a piece of bread (save as `assets/src/bread.png`)

Attach `ferro-ref.png` and `assets/src/drink.png`. The bread on its own (row 2) scrolls in with the grass, as the bowl does; the chewing loops frames 4 and 5, then frame 6.

```text
Sprite sheet: Ferro finds a piece of bread on the ground and eats it. 6 frames, left to right:
1. Standing still as in frame 2 of the attached drink.png, head down, nose just above a small piece of bread lying on the ground in front of her front paws, sniffing it.
2. The same standing body, mouth open, picking the bread up with her front teeth.
3. The same standing body, head lifted halfway, the bread held crosswise in her mouth.
4. The same standing body, head up in profile looking right, chewing: mouth slightly open, a small bit of bread still showing, one crumb falling.
5. The same as frame 4, mouth closed, chewing.
6. The same as frame 5, licking her lips: the tip of the tongue out and curled up over the front of her nose, as in frame 4 of drink.png.

Row 2, below the frames and well apart from them: the same piece of bread on its own, as it lies on the ground in frame 1.

Rules for this sheet:
- In all 6 frames the body, legs and tail are identical, pixel for pixel, in the same position. Only the head and neck move.
- The bread: a small torn piece of white bread with a golden-brown crust. About 8 pixels wide and 4 tall in Ferro's scale: about a seventh of her body length and shorter than her head. Do not draw it bigger.
- Measures for Ferro: the same scale as the frames in the reference. Standing, she is about 40 pixels from ear tips to paws and about 55 pixels long, about a third of the image height, and her head is the same size as in the reference close-ups. Do not draw her bigger.
- The tongue only in frame 6, in the salmon pink of the reference.
- All 6 frames stand on the same ground line, well apart from each other. No grass, no ground, no shadow.
- Use only the colours from the palette in the reference; new colours only for the bread.
```

### Scratching behind the ear (save as `assets/src/scratch.png`)

Not sent: Vatra dropped scratching (7.10.2026, too hard, for ChatGPT too). The message stays as a record.

Attach `ferro-ref.png` and `assets/src/sit.png`. She brakes and sits down with sit-0 and sit-1, as when she sits; the scratching loops frames 2, 3, 4, 3 fast, then frame 5, and she gets up as from sitting.

```text
Sprite sheet: Ferro sits down and scratches behind her ear with a hind leg. 5 frames, left to right:
1. Sitting upright in side view facing right, as in frame 3 of the attached sit.png: front legs straight, hind legs folded under her, tail on the ground behind her, head in profile.
2. The same sitting body, head tilted down towards her near side, her near hind leg lifted forward with its paw behind her near ear, scratching.
3. The same as frame 2 with the paw a little lower, behind her jaw.
4. The same as frame 2 with the paw a little higher, at the base of her ear.
5. The near hind leg back down, folded under her as in frame 1, head in profile, eyes half closed, content.

Rules for this sheet:
- In all 5 frames the front legs, chest, back and tail are identical, pixel for pixel, in the same position. Only the head and the near hind leg move.
- Frames 2, 3 and 4 differ only in where the scratching paw is and in a small tilt of the head.
- Measures: the same scale as frame 3 of sit.png, with her head the same size as in the reference close-ups. Standing she would be about 40 pixels from ear tips to paws; sitting she is a little taller and much shorter. Do not draw her bigger.
- All 5 frames stand on the same ground line, well apart from each other. No grass, no ground, no shadow.
- Mouth closed in every frame, no tongue.
- Use only the colours from the palette in the reference.
```

## Messages for the props she runs past (7.10.2026)

Props stand on the meadow or in the distance and scroll past while Ferro runs; she does not touch them (Vatra, 7.10.2026). They are a library: one line per prop in a registry, so a new one is one drawing and one line (see "Props she runs past" in CLAUDE.md). `tools/props.py` cuts each figure on ChatGPT's own grid, one pixel per ChatGPT pixel, never scaled. Since 8.10.2026 a sheet must come back on the grid and at the sizes its message asks for, or `props.py` rejects it whole and it is drawn again (see "A sheet off its measures is rejected" below). The figures are cut left to right, so the order in the message is the order of the names.

Sizes are in band pixels, the same pixels as Ferro's 40 from ear tips to paws. The band is 82 pixels tall and her paws stand 80 pixels below the top, so a prop on the grass can be up to about 60 pixels tall.

### Ground props (save as `assets/src/props-ground.png`)

Attach `assets/ref/ferro-ref.png` and `assets/src/meadow.png`.

```text
Sprite sheet: props that stand on the meadow in Ferro's strip. No dog in this image. Six separate objects in one row, left to right, well apart from each other, all standing on the same ground line:
1. A grey rock, low and rounded, about 12 pixels wide and 8 tall.
2. A big tuft of tall meadow grass, about 14 pixels wide and 12 tall, in the greens of the grass in the attached meadow.
3. A round leafy green bush, about 32 pixels wide and 26 tall, in the greens of the bushes in the attached meadow.
4. A big inflatable beach ball with red, white, yellow and blue segments, about 20 pixels across, resting on the ground.
5. A medieval knight's steel helmet with a visor slit, lying on its side on the ground, about 14 pixels wide and 11 tall.
6. A medieval sword stuck point-down in the ground, slightly tilted, crossguard and grip above: about 9 pixels wide and 30 tall from the ground to the pommel. Only the part above the ground is drawn.

Rules for this sheet:
- Same scale as Ferro in the reference: she is about 40 pixels from ear tips to paws. Keep each object at the size given above; do not draw them bigger.
- Each object sits on a flat bottom on the same ground line, as it would stand on the grass. No grass under them, no ground, no shadow.
- Same pixel-art style as Ferro and the meadow: crisp hard pixels, dark 1-pixel outline, no anti-aliasing, no gradients, lit from the top left.
- New colours only for these objects. Never magenta or purple.
- Flat solid pure magenta (#FF00FF) background, no text, no labels.
```

### Props in the distance (save as `assets/src/props-far.png`)

Attach `assets/ref/ferro-ref.png` and `assets/src/meadow.png`. In the scene they stand behind the hills and scroll at the hills' speed, so the hills hide their bottom; the bottom only has to be flat.

```text
Sprite sheet: buildings far in the distance behind the hills of the attached meadow. No dog in this image. Two separate objects in one row, left to right, well apart from each other, on the same bottom line:
1. A round stone castle tower with battlements and a small pointed roof with a flag, about 14 pixels wide and 30 tall.
2. A small medieval town on a hill seen from far away: a cluster of houses with red roofs, a town wall and a church steeple, about 60 pixels wide and 22 tall.

Rules for this sheet:
- They are far away: pale, hazy and slightly bluish colours, like the distant hills in the attached meadow, with little detail and no dark outline, so they sit behind the hills and do not stand out more than the hills do.
- Flat straight bottom on the same line; the hills will hide it.
- Keep the sizes given above; do not draw them bigger.
- Crisp hard pixels, no anti-aliasing, no gradients.
- New colours only for these objects. Never magenta or purple.
- Flat solid pure magenta (#FF00FF) background, no text, no labels.
```

### A new prop for the library (template)

Attach `assets/ref/ferro-ref.png` and `assets/src/meadow.png`; save as `assets/src/props-<name>.png`. For a prop in the distance, take the rules of the far sheet instead.

```text
Sprite sheet: a prop that stands on the meadow in Ferro's strip. No dog in this image. <What it is, its colours>, about <W> pixels wide and <H> tall, standing on a flat bottom on the ground line.

Rules for this sheet:
- Same scale as Ferro in the reference: she is about 40 pixels from ear tips to paws. Keep the size given above; do not draw it bigger.
- No grass under it, no ground, no shadow.
- Same pixel-art style as Ferro and the meadow: crisp hard pixels, dark 1-pixel outline, no anti-aliasing, no gradients, lit from the top left.
- New colours only for this object. Never magenta or purple.
- Flat solid pure magenta (#FF00FF) background, no text, no labels.
```

### Far buildings again, smaller (7.10.2026)

All six far buildings came out too tall for their place (`tools/props.py`): tower 67 rows, town 55, Orthanc 68, Barad-dur 72, Minas Tirith 57, the future city 89, against at most 34 behind the hills. Shrinking them loses their detail, so ChatGPT draws them again with bigger pixels. Each message attaches the sheet it redraws, so the look stays, and `ferro-meadow.png`. The bottom of a far building stands behind the hills, so only its top 20-28 rows show: the parts that make it recognisable go in the top two thirds.

Measures are given as a grid over the whole image and as a share of its height, not only as pixel counts (see "Measures in a message" in CLAUDE.md): the first sheets asked for pixel counts and came out 1.4 to 2.5 times bigger.

Tower and town (attach `assets/src/props-far.png` and `ferro-meadow.png`; save as `assets/src/props-far.png`):

```text
Redraw the attached image (the tower and the town) with much bigger pixels, so each building has far fewer pixels. Same two buildings, same pale hazy bluish colours, same composition, on the same flat solid pure magenta (#FF00FF) background.

Measures:
- Draw the whole image as a grid of 128 pixels across and 64 pixels down: every pixel is one solid square block, 1/128 of the image width. No smaller detail than one block.
- The tower: 14 pixels wide and 30 pixels tall, including the little hill under it. That is less than half the height of the image.
- The town: 60 pixels wide and 26 pixels tall, including its hill. Also less than half the height of the image.
- Both stand on the same flat bottom line, near the bottom of the image, well apart from each other.

Rules for this sheet:
- The bottom third of each building will be hidden behind hills, so keep what makes it recognisable (the battlements and the flag, the steeple and the red roofs) in its top two thirds.
- Crisp hard pixels, no anti-aliasing, no gradients, no dark outline.
- No text, no labels.
```

Orthanc, Barad-dur and Minas Tirith (attach `assets/src/props-far-fantasy.png` and `ferro-meadow.png`; save as `assets/src/props-far-fantasy.png`):

```text
Redraw the attached image (the three towers and cities) with much bigger pixels, so each one has far fewer pixels. Same three, left to right, same pale hazy bluish colours, the same glowing orange eye on the middle tower, on the same flat solid pure magenta (#FF00FF) background.

Measures:
- Draw the whole image as a grid of 128 pixels across and 64 pixels down: every pixel is one solid square block, 1/128 of the image width. No smaller detail than one block.
- Left, the black spire: 18 pixels wide and 32 pixels tall, including the hills under it.
- Middle, the dark tower with the eye: 26 pixels wide and 32 pixels tall, including the mountain under it.
- Right, the white city: 36 pixels wide and 28 pixels tall, including the hills under it.
- Each is about half the height of the image or less. All three stand on the same flat bottom line, near the bottom of the image, well apart from each other.

Rules for this sheet:
- The bottom third of each will be hidden behind hills, so keep what makes it recognisable (the four horns of the spire, the eye, the white tiers and the tower of the city) in its top two thirds.
- Crisp hard pixels, no anti-aliasing, no gradients, no dark outline.
- No text, no labels.
```

Vatra dropped the future city after the redraw (7.10.2026); the message stays as a record.

The future city (attach `assets/src/props-far-future.png` and `ferro-meadow.png`; save as `assets/src/props-far-future.png`):

```text
Redraw the attached image (the futuristic city) with much bigger pixels, so it has far fewer pixels. Same city, same pale hazy blue colours with small yellow windows, on the same flat solid pure magenta (#FF00FF) background, without the small flying vehicles.

Measures:
- Draw the whole image as a grid of 128 pixels across and 64 pixels down: every pixel is one solid square block, 1/128 of the image width. No smaller detail than one block.
- The city: 84 pixels wide and 30 pixels tall, from its flat bottom line to the tip of the tallest tower. That is less than half the height of the image. It stands near the bottom of the image.

Rules for this sheet:
- The bottom third will be hidden behind hills, so keep what makes it recognisable (the tallest towers, the saucer-topped tower, the bridges) in its top two thirds.
- Crisp hard pixels, no anti-aliasing, no gradients, no dark outline.
- No text, no labels.
```


The ships needed no new drawing: Vatra wanted them far in the background, then in front of the forest at the edge of the meadow and taller than the trees (7.10.2026), and there the drawings of `props-ships.png` are big enough as they are.

### A sheet off its measures is rejected (8.10.2026)

Vatra saw Orthanc in the band again and it was broken, though ChatGPT's drawing was good: the message asked for a grid of 128 pixels across, ChatGPT drew on one of 175, and `props.py` guessed that grid and cut across the four horns, which were thinner than one of its pixels. Vatra: give the measure from the start, demand the limit, and if a sheet is not right, reject the file and ask for a new one. Nothing is rescaled or repaired to make a sheet fit.

How it works for every new prop sheet:
- The sheet gets its grid in `assets/props.json` (`sheets`: pixels across and down) and each of its props the size asked (`size`: width and height in those pixels).
- `python tools/props.py --template <sheet>` draws `assets/ref/template-<sheet>.png`: the grid on magenta with a checkerboard box per object, at its size, left to right. Attach it to the message: it is the measure, as a picture, because ChatGPT has ignored measures given in numbers.
- After the new sheet is saved in `assets/src/`, `python tools/props.py` checks it: its pixels must be the grid's (within 5%), the image the grid's height, each figure its size (within 10% or 2 pixels) and no taller than its place. If anything is off it prints REJECTED with what is off, its props stay out of the mod, and the message goes to ChatGPT again in a new chat, with only the template attached: a rejected sheet attached for its look anchors ChatGPT to its sizes (see below).
- A sheet that passes is still shown to Vatra side by side with ChatGPT's drawing (`preview/props.html`) before it goes into the mod.

Sheets cut before the rule (`props-ground`, `props-ships`, `props-far`) carry `approved_by_eye`: Vatra saw them in the band, so they are not checked.

### Orthanc, Barad-dur and Minas Tirith on the template (8.10.2026)

`props-far-fantasy.png` was rejected: `props.py` found its pixels 10.1 source pixels for the grid's 13.9 (175 across instead of 128), Orthanc 31 x 36 grid pixels for 18 x 32, Barad-dur 40 x 38 for 26 x 32, Minas Tirith 45 x 30 for 36 x 28. Attach `assets/ref/template-props-far-fantasy.png` and the rejected `assets/src/props-far-fantasy.png` (for the look); save the result as `assets/src/props-far-fantasy.png`.

```text
Redraw the second attached image (the three towers and cities) on the first attached image, the template. Same three, left to right, same pale hazy bluish colours, the same glowing orange eye on the middle tower, on a flat solid pure magenta (#FF00FF) background.

The template is the measure, and it is strict:
- The template is a grid of 128 pixels across and 64 down: one square of its checkerboard is one pixel. Draw on exactly this grid: every pixel one solid square block of that size, lined up with the checkerboard. The image is twice as wide as it is tall, like the template.
- Each grey box is the exact size of one object: the black spire fills the left box (18 pixels wide, 32 tall), the dark tower with the eye the middle box (26 wide, 32 tall), the white city the right box (36 wide, 28 tall). Each fills its box's height, stands on the box's bottom edge and stays inside it.
- No detail smaller than one pixel: every horn, spike, tier and window is at least one whole pixel wide, with at least one pixel of magenta between horns or spikes. With so few pixels, simplify rather than draw thinner.
- Do not draw the checkerboard or the boxes: only the three drawings on magenta.

Rules for this sheet:
- The bottom third of each will be hidden behind hills, so keep what makes it recognisable (the four horns of the spire, the eye, the white tiers and the tower of the city) in its top two thirds.
- Crisp hard pixels, no anti-aliasing, no gradients, no dark outline.
- No text, no labels.
```

Second try (8.10.2026, both images attached as above): rejected again. ChatGPT ignored the template and redrew the attached sheet at the same sizes, with even smaller pixels: 5.6 source pixels for the grid's 13.9 (315 across instead of 128), Orthanc 30 x 35 grid pixels for 18 x 32, Barad-dur 40 x 36 for 26 x 32, Minas Tirith 45 x 28 for 36 x 28. Not saved in the repo.

Third try: attach only `assets/ref/template-props-far-fantasy.png`, the look in words. Save the result as `assets/src/props-far-fantasy.png`.

```text
Draw three buildings far in the distance for a pixel-art game, on the attached image, the template. Keep its flat solid pure magenta (#FF00FF) background and replace each grey checkerboard box with one building:
- Left box: Orthanc, a tall black stone spire with four sharp horns at the top, standing on a small green hill.
- Middle box: Barad-dur, a dark jagged tower on a dark mountain with thin red lava streams, a glowing orange eye between two horns at its top.
- Right box: Minas Tirith, a white city in tiers on a green hill, with a tall white tower at the top.
All three in pale, hazy, bluish colours, as if seen from far away; only the eye and the lava glow.

The template is the measure, and it is strict:
- The template is a grid of 128 pixels across and 64 down: one square of its checkerboard is one pixel. Draw on exactly this grid: every pixel one solid square block of that size, lined up with the checkerboard. The image is twice as wide as it is tall, like the template.
- Each grey box is the exact size of one building: the left box is 18 pixels wide and 32 tall, the middle 26 wide and 32 tall, the right 36 wide and 28 tall. Each building fills its box's height, stands on the box's bottom edge and stays inside it. Do not move, enlarge or add anything.
- No detail smaller than one pixel: every horn, spike, tier and window is at least one whole pixel wide, with at least one pixel of magenta between horns or spikes. With so few pixels, simplify rather than draw thinner.
- Do not draw the checkerboard or the boxes: only the three buildings on magenta.

Rules for this sheet:
- The bottom third of each will be hidden behind hills, so keep what makes it recognisable (the four horns of the spire, the eye, the white tiers and the tower of the city) in its top two thirds.
- Crisp hard pixels, no anti-aliasing, no gradients, no dark outline.
- No text, no labels.
```

Third try (8.10.2026, only the template attached): rejected. The sizes came close (Orthanc 19 x 34 grid pixels for 18 x 32, Minas Tirith 39 x 31 for 36 x 28, Barad-dur 29 x 37 for 26 x 32, the only one off), but ChatGPT drew with pixels of 5.9 source pixels for the grid's 13.9 (299 across instead of 128): about twice the detail asked. Vatra did not like its Minas Tirith. Not saved in the repo.

Fourth try: attach only `assets/ref/template-props-far-fantasy.png`. Minas Tirith looked like a generic castle (Vatra: square white walls on a green hill), so it is described by what makes it Minas Tirith: seven curved tiers against a dark mountain, the rock spur cutting through them like a ship's prow, the tall white tower on top. The pixels are asked as a tiny image enlarged, because the checkerboard did not hold them. Save the result as `assets/src/props-far-fantasy.png`.

```text
Draw three buildings far in the distance for a pixel-art game, on the attached image, the template. Keep its flat solid pure magenta (#FF00FF) background and replace each grey checkerboard box with one building:
- Left box: Orthanc, a tall black stone spire with four sharp horns at the top, standing on a small green hill.
- Middle box: Barad-dur, a dark jagged tower on a dark mountain with thin red lava streams, a glowing orange eye between two horns at its top.
- Right box: Minas Tirith, the white city of seven tiers built against the foot of a dark grey mountain that rises behind it. Each tier is a curved white wall, each higher one smaller and set back, like the steps of a round cake seen from the side. A huge grey rock spur juts forward out of the mountain like the prow of a ship and cuts through the middle of all the tiers up to the top one. On the top tier, at the tip of the spur, one very tall, slender white tower. It must not look like a generic castle with square walls.
All three in pale, hazy, bluish colours, as if seen from far away; only the eye and the lava glow.

The template is the measure, and it is strict:
- The template is a grid of 128 pixels across and 64 down: one square of its checkerboard is one pixel. The result must look like a tiny image of 128 x 64 pixels enlarged 14 times: every pixel one solid square block exactly the size of a checkerboard square, lined up with the checkerboard. The image is twice as wide as it is tall, like the template.
- Each grey box is the exact size of one building: the left box is 18 pixels wide and 32 tall, the middle 26 wide and 32 tall, the right 36 wide and 28 tall. Each building fills its box's height, stands on the box's bottom edge and stays inside it, the eye, the horns and the towers included. Do not move, enlarge or add anything.
- No detail smaller than one pixel: every horn, spike, tier and window is at least one whole pixel wide, with at least one pixel of magenta between horns or spikes. With so few pixels, simplify rather than draw thinner.
- Do not draw the checkerboard or the boxes: only the three buildings on magenta.

Rules for this sheet:
- The bottom third of each will be hidden behind hills, so keep what makes it recognisable (the four horns of the spire, the eye, the white tiers, the rock spur and the tower of the city) in its top two thirds.
- Crisp hard pixels, no anti-aliasing, no gradients, no dark outline.
- No text, no labels.
```

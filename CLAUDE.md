# mod-ferro

Claude Code mod za zabavu: Ferro (Vatrina ženka, Norwich terijer) trči po pixel art livadi u traci iznad prompta dok Claude dulje radi. Nastao 3.-4.10.2026. Vatra ne želi ništa interaktivno ("da ne gubim ako ne vidim"), pa mod samo prikazuje. Provjera poluge iz `personal-os/tasks/someday/claude-code-mods.md` namjerno je preskočena, jer je zabava jedini cilj.

## Kako radi
- `turn.start` pokrene dva timera: nakon 20 s faza `run`, nakon 3 min `sleep`. `turn.complete` glavnog turna (bez `agentId`) ih ugasi i vrati fazu na `null`. Faza je u `$.state` (`mod-ferro.phase`).
- `ui.render` na `AbovePrompt` crta `Svg` samo na Desktopu, dok je `isWorking` i faza nije `null`. Sva animacija je SMIL unutar SVG-a, a mod ga crta jednom.
- Širina: `bodyColumns * 8` CSS px, najviše 1280. Bez zadane `width` okvir ostaje na 300 px. Omjer od 8 px po stupcu izmjeren je 4.10.2026. na TV-u (94 stupca, ~753 px), na monitoru još nije provjeren. Scena ima `preserveAspectRatio="xMidYMid slice"`, pa uža traka reže rubove scene, a pikseli ostaju 2 CSS px.

## Što traka u Desktopu propušta (test 4.10.2026.)
- Prolaze `<path>`, `<rect>`, `<use href>` i `<use xlink:href>`, `<pattern>`, ugniježđeni `<svg>`, `<text>`, SMIL (`animate`, `animateTransform`, `set`).
- **NE prolazi `<image>` s PNG-om kao data URI.** Zato su svi crteži vektorske crte: jedan `<path>` po boji (potez debljine 1 po vodoravnom nizu piksela) u `<defs>`, a scena ih koristi preko `<use>`.
- Limit `Svg` elementa je 131.072 znaka. Trčanje ima ~114 tisuća, spavanje ~80 tisuća. Novi crtež ili scena prvo se mjeri: `python tools/scene.py` ispiše veličine.

## Crteži i alati
- `assets/src/` su izvorni ChatGPT crteži: `run.png`, `poop.png` i `sleep.png` (po 6 frameova na magenta podlozi) te `meadow.png` (livada 3:2, gotovo bez šava). Promptovi su u razgovoru od 4.10.2026. Ključni dijelovi su "Norwich Terrier", "side view facing right", "same ground baseline", "flat solid pure magenta (#FF00FF) background" i za livadu "edges must match seamlessly".
- `tools/build.py` → `assets/px/`: izreže frameove, makne magentu, smanji na pravu mrežu piksela (trčanje faktor 6, ostalo ~5,5 da pas bude iste veličine), svede na zajedničku paletu od 22 boje i poravna frameove po desnom uhu i tlu. Livadu dijeli u tri sloja.
- `tools/scene.py` → `plugin/hooks/scene.ts` (generirano, ne uređivati) i `preview/*.svg`.
- `tools/preview.py` → uvećani PNG svih frameova, za provjeru oka.
- Pregled animacije u pregledniku: u personal-os `preview_start ferro` (`.claude/launch.json` poslužuje `preview/`).

## Naučeno
- **Redoslijed galopa:** ChatGPT je frameove trčanja poslagao bez reda faza i Ferro je izgledala kao da trči unazad. Pravi redoslijed je `[4, 3, 2, 5, 0]` (`RUN_ORDER`): ispružena, doskok prednjima, stražnje naprijed, skupljena, odraz. Frame 1 je višak.
- **Tempo:** 0,13 s po frameu, jer su s 0,085 s noge izgledale kao da se trzaju. Trava ide 80 px/s, iako šapa na tlu ide ~42 px/s. Vatri je brža pozadina draža od savršenog koraka, a vlati preko šapa nisu pomogle.
- **Petlja bez skoka:** drugo trčanje traje toliko da tlo u petlji prijeđe točno 20 širina livade, a brda (0,35 brzine) točno 7.

## Razvoj i instalacija
- Provjera: `claude plugin validate ./plugin`. Testovi: `claude plugin test ./plugin`.
- Instaliran iz ovog foldera: `claude plugin marketplace add`, pa `claude plugin install mod-ferro@mod-ferro --scope user`. Instalacija KOPIRA plugin u cache, pa izmjena u repou ne vrijedi sama: podići `version` u `plugin/.claude-plugin/plugin.json`, pokrenuti `claude plugin update mod-ferro@mod-ferro`, pa `/reload-plugins` ili nova sesija.
- Tekst u sučelju (alt) je na hrvatskom.

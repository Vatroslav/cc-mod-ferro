# mod-ferro

Claude Code mod za zabavu: Ferro (Vatrina ženka, Norwich terijer) trči po pixel art livadi u traci iznad prompta dok Claude dulje radi. Nastao 3.-4.10.2026. Vatra ne želi ništa interaktivno ("da ne gubim ako ne vidim"), pa mod samo prikazuje. Provjera poluge iz `personal-os/tasks/someday/claude-code-mods.md` namjerno je preskočena, jer je zabava jedini cilj.

## Kako radi
- `turn.start` pokrene dva timera: nakon 20 s faza `run`, nakon 3 min `sleep`. `turn.complete` glavnog turna (bez `agentId`) ih ugasi i vrati fazu na `null`. Faza je u `$.state` (`mod-ferro.phase`).
- `ui.render` na `AbovePrompt` crta `Svg` samo na Desktopu, dok je `isWorking` i faza nije `null`. Sva animacija je SMIL unutar SVG-a, a mod ga crta jednom.
- Širina: `bodyColumns * 8` CSS px, najviše 1280. Bez zadane `width` okvir ostaje na 300 px. Omjer od 8 px po stupcu izmjeren je 4.10.2026. na TV-u (94 stupca, ~753 px), na monitoru još nije provjeren. Scena ima `preserveAspectRatio="xMidYMid slice"`, pa uža traka reže rubove scene, a pikseli ostaju 2 CSS px.

## Što traka u Desktopu propušta (test 4.10.2026.)
- Prolaze `<path>`, `<rect>`, `<use href>` i `<use xlink:href>`, `<pattern>`, ugniježđeni `<svg>`, `<text>`, SMIL (`animate`, `animateTransform`, `set`).
- **NE prolazi `<image>` s PNG-om kao data URI.** Zato su svi crteži vektorske crte: jedan `<path>` po boji (potez debljine 1 po vodoravnom nizu piksela) u `<defs>`, a scena ih koristi preko `<use>`.
- Limit `Svg` elementa je 131.072 znaka. Trčanje ima ~110 tisuća, spavanje ~78 tisuća (mjereno 4.10.2026. nakon čišćenja ruba). Novi crtež ili scena prvo se mjeri: `python tools/scene.py` ispiše veličine.

## Crteži i alati
- `assets/src/` su izvorni ChatGPT crteži: `run.png`, `poop.png` i `sleep.png` (po 6 frameova na magenta podlozi) te `meadow.png` (livada 3:2, gotovo bez šava). Promptovi su u razgovoru od 4.10.2026. Ključni dijelovi su "Norwich Terrier", "side view facing right", "same ground baseline", "flat solid pure magenta (#FF00FF) background" i za livadu "edges must match seamlessly".
- `tools/build.py` → `assets/px/`: izreže frameove, makne magentu, smanji na pravu mrežu piksela (trčanje faktor 6, ostalo ~5,5 da pas bude iste veličine), svede na zajedničku paletu, ispegla rub i poravna frameove po desnom uhu i tlu. Livadu dijeli u tri sloja.
- **Paleta psa je zamrznuta** u `assets/palette.json` (4.10.2026.): 22 boje krzna i obruba, jezik i odsjaj u oku. Izvorno ju je izračunao median cut + k-means iz svih slika, a sad `build.py` samo svakom pikselu da najbližu boju iz filea. Zamrzavanje nije promijenilo nijedan piksel. Nova paleta iz slika računa se samo svjesno: `python tools/build.py --nova-paleta`, i tada se pomaknu boje svim animacijama. Boja dodana u `krzno` ne mijenja postojeće boje, ali može preuzeti piksele postojećih crteža kojima je bliža, pa nakon builda `git status assets/px` pokaže koji su se frameovi promijenili. Livada ima svoju paletu (48 boja, samo iz `meadow.png`), pa je novi crtež psa ne dira.
- `tools/scene.py` → `plugin/hooks/scene.ts` (generirano, ne uređivati) i `preview/*.svg`.
- `tools/preview.py` → uvećani PNG svih frameova, za provjeru oka.
- Pregled animacije u pregledniku: u personal-os `preview_start ferro` (`.claude/launch.json` poslužuje `preview/`).

## Naučeno
- **Instalirani mod u običnoj sesiji ne radi bez zastavice** (4.10.2026.). Modovi instaliranih pluginova su iza Anthropicovog rollout prekidača, a za Vatrin račun je ugašen (`"tengu_plugin_hooks_modules": false` u `~/.claude.json`). Desktop 2.1.286 tad ne pokreće hookove instaliranih pluginova. Mod iz `~/.claude/dev-mods` s uključenim hot reloadom ide mimo prekidača, pa je proba u sesiji radila, a instalirana verzija nije. Kad je hot reload u sesiji uključen, radi i instalirana. Trajno rješenje je `"CLAUDE_CODE_ENABLE_FUNCTION_HOOKS": "1"` u `env` bloku `~/.claude/settings.json`. Mod u običnoj sesiji provjeravati tek u novoj sesiji bez hot reloada.
- **Redoslijed galopa:** ChatGPT je frameove trčanja poslagao bez reda faza i Ferro je izgledala kao da trči unazad. Pravi redoslijed je `[4, 3, 2, 5, 0]` (`RUN_ORDER`): ispružena, doskok prednjima, stražnje naprijed, skupljena, odraz. Frame 1 je višak.
- **Tempo:** 0,13 s po frameu, jer su s 0,085 s noge izgledale kao da se trzaju. Trava ide 80 px/s, iako šapa na tlu ide ~42 px/s. Vatri je brža pozadina draža od savršenog koraka, a vlati preko šapa nisu pomogle.
- **Jezik, oči i rub kvario je `build.py`, ne ChatGPT** (4.10.2026.). Izvor ima roza jezik (~170 piksela po psu) i bijeli odsjaj u oku (2-8 piksela), ali smanjivanje je jezik svelo na bordo (premalo piksela za vlastitu boju u median cutu), a odsjaj izgubilo (nikad nije najčešća boja u bloku 6x6). Oko 6.400 piksela magenta ruba uz pozadinu ulazilo je u paletu kao bordo, otud bordo točke po obrubu i bordo uši. Popravak: magenta rub ide u pozadinu, jezik i odsjaj imaju rezervirane boje, svaki odsjaj postane jedan bijeli piksel na tamnom oku, a rub se čisti (zalutali pikseli i bočne izbočine van, krzno uz pozadinu postane obrub). Bez k-means dorade median cut je izgubio neutralnu tamnosivu i sedlo je dobilo smeđe mrlje. Uho za poravnanje mjeri se prije čišćenja ruba, pa su položaji frameova ostali isti. Novi crtež ne treba "ispravljati" u ChatGPT-u za ono što smanjivanje pojede - prvo provjeriti izvor. Vatra je popravak vidio u instaliranoj 0.2.1 (4.10.2026.).
- **Plan proširenja** (Vatra, 4.10.2026.): više animacija i pozadina u dosljednom stilu. Paleta je zamrznuta prije nego što je dizajn Ferro gotov, jer dorada crteža sa zamrznutom paletom i dalje radi. Sljedeće je ChatGPT Project za nove crteže. U Projectu referentni sheet priložiti u svaku poruku - OpenAI dokumentacija ne kaže da generator slika vidi slike iz project fileova.
- **Petlja bez skoka:** drugo trčanje traje toliko da tlo u petlji prijeđe točno 20 širina livade, a brda (0,35 brzine) točno 7.

## Razvoj i instalacija
- Provjera: `claude plugin validate ./plugin`. Testovi: `claude plugin test ./plugin`.
- Instaliran iz ovog foldera: `claude plugin marketplace add`, pa `claude plugin install mod-ferro@mod-ferro --scope user`. Instalacija KOPIRA plugin u cache, pa izmjena u repou ne vrijedi sama: podići `version` u `plugin/.claude-plugin/plugin.json`, pokrenuti `claude plugin update mod-ferro@mod-ferro`, pa `/reload-plugins` ili nova sesija. Sesije koje su već otvorene drže staru verziju dok se u njima ne pokrene reload. Koja verzija je još u upotrebi vidi se u `~/.claude/plugins/cache/mod-ferro/mod-ferro/<verzija>/.in_use/` (jedan file po procesu).
- Tekst u sučelju (alt) je na hrvatskom.

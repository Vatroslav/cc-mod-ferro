# mod-ferro

Claude Code mod koji ne služi ničemu osim zabavi. Kad Claude radi dulje od 20 sekundi, iznad prompta se otvori traka u kojoj Ferro, Norwich terijer, u pixel artu trči po livadi:

- livada ima tri sloja (oblaci, brda s drvećem, trava) koji klize različitim brzinama
- otprilike svakih 40 sekundi Ferro stane i obavi nuždu, a hrpica ostane na livadi i otklizi
- kad Claude radi dulje od 3 minute, Ferro legne i zaspi, a iznad glave joj izlaze z-ovi

Kad Claude završi, traka nestane. Ništa nije interaktivno, pa se ništa ne propušta ako se ne gleda.

Radi samo u Code tabu Claude Desktopa, jer terminal nema `Svg` element. Potreban je Claude Code v2.1.287 ili noviji.

Crteže je napravio ChatGPT (Ferro u tri scene i livada), a `tools/` ih pretvara u prave piksele i slaže u animirani SVG.

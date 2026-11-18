# Wild Skies: next steps

State on 2026-11-12: 0.3.2 worked in game (book, star view, mouse feel, all 24 figures). 0.4.0 (still sky and the
hunt) is built and on the Desktop, not yet seen in game: watch the chart's size on the Tonight page, whether the
hold is too strict with a heavy mouse, and whether 5-6 constellations a night feels right. Rules as always: art is shown as pictures first and nothing goes into the mod until the owner
says yes; no dev client; pixel rules from the `pixel-hud-mods` skill.

## Open items

0. **0.6.0 is on the Desktop** (owner said yes to `previews/square_lens/`, 2026-11-12); not seen in game yet.
   Falling stars are off by default and only come back by config; ask before working on them again.

Done in 0.4.0: still sky per night, bigger constellations, tonight's chart, bearing tag, stricter hold, rim studs.
Sound pass: the owner heard the options (`previews/sounds/`) and keeps today's sounds.

0b. **Archies-style motion for the Star Atlas**: `ATLAS_MOTION_HANDOFF.md` (menu of 8, owner to pick numbers).
1. **Mobs.** Star Hound, Nebula Stalker and the Fallen were in the overview and skipped ("no mobs for now"). Only on
   the owner's word.

## Things to watch in the owner's reports

- **0.5.0 telescope** (GeckoLib): model facing (the tube should point away from where you stood when placing it),
  the tier parts, the lens glint with shaders, the crouch others see, "Someone's already at this telescope.".

Everything below was only checked offline; the owner now says it works, so these are just the places to look first if
something odd turns up:

- FPS in the star view (the sky is worked out per pixel each frame, `GridTextures`); other mods' HUD layers over ours.
- Beams and the falling streak with Photon/ARTShade and Distant Horizons (far beams are pulled in and scaled).
- Atlas screen on small windows (spread is 344 x 236 GUI px; under 236 px tall its top is cut off).
- Biome names in the claims ledger for modded biomes without a translation.

## Ideas not yet asked for (propose, do not build)

- More constellations or planets once the first sets are all found; a "found everything" payoff beyond the four
  section rewards.
- Figures drawn into the sky for hidden constellations while tracing (today they glow only at the moment of a find).
- Config screen entries for the view (muffle strength, figure glow time).

## How to resume

Read `CLAUDE.md`, then this file. Tools and the build/self-test commands are listed in CLAUDE.md under "Tools". Each
delivered version gets a `CHANGELOG.md` entry and a jar on the Desktop.

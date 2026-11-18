# The redo set: notes for the owner and for the Java that comes after a yes

Painted by `python tools/art_redo/paint.py` (deterministic, no `random()`); mockups by `book_mock.py`, comparison
sheets by `compare.py`. `sh tools/use_art.sh redo` / `original` switches sets. Nothing in `src/main/java` was changed.

## Works today with no code change
`gui/sky.png`, `gui/planets.png`, `gui/deep.png`, blocks, items, particles and the beam keep every name, UV and size.
`previews/redo/shots` and `shots_small` are the real `StarViewRenderer` drawing them.

## Needed code (done in 0.2.0 and 0.3.0, see CLAUDE.md; kept as the record of the proposal)
1. **The book.** `gui/atlas.png` is 512x512 with a new region table (`SkySprites.R`, texture 3) and fixed places
   (`SkySprites.AT`). `AtlasRenderer`/`AtlasScreen` get rewritten to it; `StarViewRenderer.TEX_SIZE[3]` becomes
   {512, 512}. Until then the old Atlas screen must not be shown with this set.
   - Layout: spread 344 x 236, `book` at (0,0); `leaves_l_k` / `leaves_r_k` (k = 0..5 by how far in you are);
     `tab_<section>` at `TAB_SLOT` (left slot if the section is behind the open one, right if ahead), y 6;
     `run_<section>` for the open section; `corner_l/r`; `arrow_l/r(_on)`.
   - Charts are 115 x 75 (odd, so a star's centre pixel sits on the chart's centre) on `print_cyan` at +4,+4;
     stars `cy_star_1..3`, lines in 0xFF6E98C8; not found: `pc_*_empty`, `pn_star_1..3`.
   - Plates: `plate_planet` (planet size 3 at +8,+8), `plate_rare` (deep size 2, `rare_comet`, `rare_shower` at +8,+8),
     not found: `sketch_planet`, `sketch_rare`. Corners `pc_tl/tr/bl/br` sit 1 px outside the card's corners.
   - Text colours: writing 0xFF321C12, notes 0xFF583824, faded 0xFF866648, pencil 0xFF84705A, red 0xFF92301C.
   - New strings: "Kept by %s", "The night of", "Night %s of %s, %s", "%s dug up", "Claims", "Night", "Land",
     "From spawn", "Two more nights to go.".
   - Claims ledger: `ledger_head` then `ledger_row` every 12 px; needs a saved list of claims per player.
   - Page turn: `turn_0..3` at their `AT` places over the spread, then the new spread.
2. **Plaque as a paper slip.** The current code writes on the plaque in pale gold and pale blue, so the drop-in
   plaque is a dark saddle-leather tag. A paper slip needs ink text colours in `StarView.plaque(...)`.
3. **Rim ramps** for `StarViewRenderer`: COPPER {0xFF2C140A, 0xFF5C2E1A, 0xFF8E4C2A, 0xFFC47440, 0xFFECA870},
   BRASS {0xFF3A240C, 0xFF6C4A18, 0xFFA07428, 0xFFCEA446, 0xFFF2D88C}.

## Known and open
- The turn frames carry a narrow solid shadow (alpha stays 0/255), which hides the writing under it for those few
  frames. A see-through shadow drawn by code would be the alternative: owner's call.
- Nebulae are centred by their visible box to within 1 px where the box's parity does not match the cell (8 of 15).
- Section 3.6 extras (instrument frames, iris blades, wax-stamp slip, brass slider) were not painted.
- Constellation figures: none drawn; `tools/sky_catalog.py` untouched. Telescope textures and item: untouched.
- Nothing here has been seen in game.

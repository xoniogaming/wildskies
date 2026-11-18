# Wild Skies 1.0

The weather update. Wild Skies 1.0 adds blocks that work with the sky and the weather, a new section of the Star
Atlas that gives back lost recipes, charms that follow the planets, and a new look for stargazing in the rain.

---

## New blocks

### Cloudbuster
Copper pipes aimed at the sky. Within 48 blocks of it, it really stops raining and snowing:
- No rain or snow falls or splashes, and there's no rain sound.
- Nothing gets wet: fires stay lit, cauldrons stay dry and no snow piles up.
- Standing inside, the sky brightens as if the storm had passed. Walking in, it eases from grey to clear.
- A redstone signal turns it off.

**Catching lightning**: during a thunderstorm, lightning that would land in its zone hits the pipes instead and grows
a **Storm Crystal** inside. Right-click to take it out.

**Breaking the storm**: feed a Storm Crystal back to a Cloudbuster and the storm clears over the whole world for 10
minutes. Everyone gets a chat line. After that it needs 3 days to recharge, and the dial on its side shows how far it
has to go.

### Storm Jar
A little storm in a jar. It rains within 6 blocks of it, even on a clear day or in a desert.
- Cauldrons nearby fill up.
- Copper in its rain ages about one step a day, so you can weather copper without waiting for the real weather.
- Drops fall around it and you hear rain while you stand close.

### Orrery
A brass sun with six planets turning on arms, on a wide base with brass feet and an orbit inlay. Each planet has its
own look: Ember is a glowing coal, Old Gold a striped giant with a ring, Verdigris has a little moon, Indigo a dark
belt, Pale Rider is white and Cinder grey and pitted.
- **Right-click** picks the next planet. Its arm stops and points out over the front card, and the Orrery tells you
  whether that planet is up now, rises later tonight, stays below, or isn't out tonight at all. It also tells you
  tomorrow's weather.
- **Sneak + right-click** asks the same thing without changing the planet.
- **Redstone**: it gives a full signal while the chosen planet is up.
- **Comparator**: reads tomorrow's weather: 0 clear, 5 rain, 10 storm, 15 kept off by a Cloudbuster. The plaque on
  its front shows the same thing (sun, rain, storm or cloud).

### Sky Window
Glass that shows tonight's night sky through it, day or night: the stars, the planets and the Milky Way, from deep
blue overhead to a paler band low down, with dark ground below.
- Only the side that faced you when you placed it shows the sky. You can place it facing up or down too, for a
  skylight or a glass floor. The other sides are clear glass with a couple of glints.
- The stars are small sharp points that stay the same size however close you stand, and they sit still against the
  far sky as you walk past, like a real window.
- A wall of windows becomes one clear view: the brass rim only runs round the outer edge, round corners too.

### North Star Lodestone
Right-click it to bind yourself to it. Once a night, hold your spyglass or telescope on the **North Star** for three
seconds and you're brought back to the lodestone. The North Star is due north, low in the sky, the brightest white star
there. It only works under open sky at both ends, with no clouds that way.

---

## Star Atlas

### Forgotten Recipes
A new section after the field notes. Its pages start torn out, with a pencil note saying which find brings each one
back. Make that find and the page comes back as an inked sketch with the brand stamped on it.
- Each restored page lists its parts, one row each: a sketch of the item, its name, and how many you carry out of how
  many it takes (in red while you're short).
- Click **Make it** on the page to make the item straight from the book. The button stays faded until you have
  everything, and the title tells you when it makes more than one.
- These items have no crafting-table recipe; the book is the only way to make them.
- The comet's page also gives you a Storm Crystal recipe.

### Moon phases
Looking through a telescope at night records tonight's moon phase in the Atlas, and its little face on the Tonight
page is inked in. Collect all eight for an advancement and 8 Star Shards.

---

## Planet charms

Six charms, one per planet, made from the book once you've tracked that planet. Each one only works while its planet
is up in the sky, and its bead dims while the planet is down.

| Charm | Effect |
|---|---|
| **Ember** | Strength at night |
| **Indigo** | Regeneration at dusk and dawn |
| **Old Gold** | Pulls drops and experience to you (sneak to stop it) |
| **Verdigris** | Slow falling on long falls |
| **Pale Rider** | Speed |
| **Cinder** | Monsters notice you from half as far, and sculk can't hear you sneak |

With Curios installed they go in the charm slot. Without it, they work anywhere in your hotbar or offhand.

---

## Stargazing

- **Rain in the telescope, redone**: a real cloud deck instead of floating cloud pictures, the moon glowing through
  it, drops (or snow) on the glass that now and then run down, and thunder lighting up the clouds.
- **Stargaze through a storm**: inside a Cloudbuster's zone the clouds part overhead in a ragged hole, and you can
  keep hunting in the clear patch.

---

## Also

- A mod icon in the Mods list: the spyglass's brass lens on stitched leather, with the Lasso drawn in a night sky and a
  crescent moon over the pines.
- The Orrery, Sky Window and North Star Lodestone explain themselves in their tooltips.
- **Upgrading from 0.9.0**: Sky Windows placed in 0.9.0 all face north. Break them and place them again.

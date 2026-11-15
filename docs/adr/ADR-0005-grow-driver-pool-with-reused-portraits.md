# ADR-0005: Grow the driver pool to 1,000 with generated names and reused portraits

**Date:** 2026-11-15
**Status:** accepted
**Deciders:** DevilDogTG (v1.4.0)

## Context
A long-running company hits a hard limit on employees: once about 355 drivers are hired, the
recruitment agencies stop offering anyone, even with many free garage slots. In 1.62 the limit is
plain data, not an engine constant. `locale/en_gb/driver_names.sii` (in `locale.scs`, the only copy
in any locale) defines `driver_names : .driver.names` with `name[0]`..`name[354]`, and each index N
needs a portrait, `/material/ui/driver/N.mat` and `/material/ui/driver/small/N.mat`. SCS's own
comment in the file describes adding drivers this way; SCS itself grew the list in 1.41, 1.44-1.46
and 1.48. Female drivers are the names prefixed with `+` (88 of 355). `def/economy_data.sii` has no
driver-count key.

## Options Considered

### Option A: Use an existing Workshop driver-limit mod
- **Pros:** No work.
- **Cons:** The known ones (e.g. "570 Drivers Limit") date from about 2019, before the 1.41-1.48
  additions; a whole-file copy from then would drop or rename vanilla drivers 341-354 that existing
  saves already employ. Player reports on recent versions are mixed. Not reviewed in detail (the
  Workshop pages could not be read at the time).

Av_Mark's "Additional AI Drivers for ETS2" (ets2.lt, posted 2024-12, "beta", game 1.51-1.53)
was also reviewed from its page: 1,900 drivers in total with new portrait art (30 MB); by its own
notes it works only in English (US), breaks in English (UK), and shows a missing-texture "pink
square" when a new face is the profile photo. Its method and whether it keeps vanilla's drivers
are not described, and it is two game versions out of date.

### Option B: Extend the list with new portrait art
- **Pros:** Every driver has their own face.
- **Cons:** Hundreds of new portraits to make and ship (two sizes each); this repo has no art
  pipeline, and a face adds nothing to the economy.

### Option C: Extend the list with generated names and reused vanilla portraits
`tools/generate_driver_pool.py` copies the vanilla file unchanged and appends names up to the target,
each with two small `.mat` files pointing at a vanilla portrait of the same gender by absolute path.
- **Pros:** No art, no redistributed third-party content; vanilla lines stay byte-identical, so
  every hired driver keeps their name and face; deterministic and re-runnable after a patch.
- **Cons:** Faces repeat. The whole locale file is replaced, so a game patch that adds drivers is
  hidden until the generator is rerun, and any other mod shipping this file conflicts whole.

### Option D: Edit the save
- **Pros:** No mod.
- **Cons:** Saves are encrypted binary by default, and the pool's size still comes from the name
  list, so this means hand edits per profile with no names or portraits for the extra drivers.

## Decision
Option C with a pool of 1,000 (645 new drivers). That is enough for about 200 large garages, nearly
3x vanilla, while each vanilla face is reused at most twice. New names follow vanilla's "First L."
style with first names from every region of the map, interleaved so neighbouring indexes mix
countries; every fourth new driver is female (24.9% overall, vanilla 24.8%); no new name repeats a
vanilla or another new name. Driver economics (hire cost, salary, level cap, revenue coefficients)
stay vanilla: the system removes a cap, it does not change what a driver costs or earns.
The list ships under `en_gb` (vanilla's location, the fallback of every language) and as an
identical `en_us` copy: Av_Mark's language notes suggest the game prefers the current language's
list when one exists, and the maintainer plays in English (US). Because every new portrait points at a vanilla texture, the UI's index-built paths
(`/material/ui/driver/%0.mat`, also the main-menu profile photo) always resolve.

## Consequences
**Easier:** The company can keep growing into free garage slots; nothing about driver pay changes,
so the balance of the other systems holds.
**Harder:** Rerun the generator on every game minor version (as for the 1.62 rebase), or new vanilla
drivers stay hidden. Other driver-count mods must be disabled. A profile that has hired a driver past
`name[354]` depends on this mod: without it those drivers have no name or portrait (what the game
does then is untested), so the pool size can grow later but should never shrink.
**Follow-up:** Confirm in a playtest that an existing save picks up the new names (SCS's own
additions reached existing saves, but it was not verified with a mod), that hiring past 355 works,
and that the reused portraits show in the agency and company screens.

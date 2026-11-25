// Dump the multiverse mod's scene parts as JSON for the profile generator.
// usage: bun export.ts <out.json> <id[:activity]> ...
// The mod is read from $MULTIVERSE (default ~/.claude/skills/multiverse, a clone of Nam0101/claude-multiverse).
import { homedir } from 'node:os'

const mod = process.env.MULTIVERSE ?? `${homedir()}/.claude/skills/multiverse`
const { UNIVERSES } = await import(`${mod}/hooks/universes.ts`)
const { BASE, RIG_STYLE, deskScene } = await import(`${mod}/hooks/scenes/rig.ts`)
const { COMMON } = await import(`${mod}/hooks/scenes/kit.ts`)

const [out, ...specs] = process.argv.slice(2)
const worlds: Record<string, unknown> = {}

for (const [index, spec] of specs.entries()) {
  const [id, act = 'responding'] = spec.split(':')
  const u = UNIVERSES.find((x: any) => x.id === id)
  if (u === undefined) throw new Error(`no universe ${id}`)
  const w: any = u.world()
  const base = (BASE as Record<string, string>)[act]
  worlds[id] = {
    name: u.name,
    role: u.role,
    index: UNIVERSES.indexOf(u) + 1,
    total: UNIVERSES.length,
    classes: `st-${base}${base === act ? '' : ` st-${act}`}`,
    scenery: w.scenery,
    nook: w.nook,
    front: w.front ?? '',
    style: w.style,
    floating: w.rig.floating === true,
    ink: w.rig.ink,
    furniture: w.rig.furniture,
    metal: w.rig.metal,
    paper: w.rig.paper,
    light: w.rig.light,
    claude: deskScene(w.rig, { activity: act, clutter: 0, ultra: false }, `c${index}`),
  }
}

await Bun.write(out, JSON.stringify({ common: COMMON, rig: RIG_STYLE, worlds }))
console.log(Object.keys(worlds).join(' '))

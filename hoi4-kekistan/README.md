# Kekistan — a Hearts of Iron IV mod

Renames Germany to Kekistan, gives it the Kekistan flag and a dark green map
colour, and starts it as a democracy under its own leader instead of fascist
Germany under Hitler.

![flag](tools/kekistan_flag.png)

## What it changes

| Thing | File |
| --- | --- |
| Flag (all sizes + every ideology variant) | `Kekistan/gfx/flags/**/GER*.tga` |
| Map / UI colour → dark green `40 90 40` | `Kekistan/common/countries/Germany.txt` |
| Country name → Kekistan | `Kekistan/localisation/english/kekistan_l_english.yml` |
| Ruling party → democratic, and the country leader | `Kekistan/common/on_actions/kekistan_on_actions.txt` |
| Leader portrait | `Kekistan/gfx/leaders/GER/Portrait_Kekistan_Ben_Shapiro.dds` |

The country is called **Kekistan** — flat, with no formal variant. HOI4 keeps a
short name and a formal name (`_DEF`) per ideology, so it would normally read
"The Republic of …" or similar depending on the ruling party; every one of
those keys is set to plain Kekistan instead, so the name never changes shape.

The adjective (`_ADJ`) stays *Kekistani*, since that is what fills in phrases
like "Kekistani infantry" rather than a name in its own right.

## Politics

Vanilla GER opens 1936 as a fascist state led by Hitler. Kekistan is not a
fascist state, so on startup the country is switched to:

* ruling party **democratic**, elections allowed
* popularity 70 democratic / 15 non-aligned / 10 communist / 5 fascist
* country leader **Ben Shapiro** (`conservatism`), replacing the vanilla
  democratic leader

This is done from `common/on_actions/` rather than by overriding
`history/countries/GER - Germany.txt`, because that history file also carries
the army, navy, air force, national ideas and every general and admiral —
replacing it wholesale to change three lines of politics is how mods
accidentally delete the Wehrmacht.

To change the alignment, edit `ruling_party` and the leader's `ideology` in
`kekistan_on_actions.txt`. The pairs that go together:

| `ruling_party` | leader `ideology` |
| --- | --- |
| `democratic` | `conservatism`, `liberalism`, `socialism` |
| `neutrality` | `despotism`, `oligarchism` |
| `communism` | `marxism`, `leninism`, `stalinism` |
| `fascism` | `fascism`, `nazism` |

## Install

Copy `Kekistan/` **and** `Kekistan.mod` into your HOI4 mod folder:

* Windows — `%USERPROFILE%\Documents\Paradox Interactive\Hearts of Iron IV\mod\`
* Linux — `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/`
* macOS — `~/Documents/Paradox Interactive/Hearts of Iron IV/mod/`

You should end up with `.../mod/Kekistan.mod` and `.../mod/Kekistan/descriptor.mod`.
Launch HOI4, enable **Kekistan** in the launcher's playset, and start a game.

## Notes

* **A democratic Germany plays differently.** Large parts of the German focus
  tree are gated behind being fascist, so those branches will be unavailable,
  and the AI will not open the war the way it usually does. That is a
  consequence of the alignment change, not a bug — flip `ruling_party` back to
  `fascism` if you want vanilla behaviour with the Kekistan skin on top.
* `common/countries/Germany.txt` is a whole-file override, so this conflicts
  with any other mod that changes Germany's colour or graphical culture. It is
  a three-line file — merge by hand if you need to.
* The flags are plain uncompressed 32-bit TGAs at HOI4's three sizes
  (82×52, 41×26, 10×7), one per ideology, cut from the artwork in
  `tools/kekistan_flag.png`.
* The portrait is an uncompressed 32-bit `.dds` at 156×210, the size and format
  vanilla country leader portraits use. `create_country_leader` is given the
  bare filename, which the game resolves under `gfx/leaders/<TAG>/`. If your
  HOI4 build wants the full path instead, the portrait will come up blank —
  change `picture` to `"gfx/leaders/GER/Portrait_Kekistan_Ben_Shapiro.dds"`.
* `supported_version` is set to `1.16.*`.

## Regenerating the art

Both scripts read one source file, so swapping art means replacing that file
and re-running:

```sh
pip install pillow
python3 tools/generate_flags.py      # tools/kekistan_flag.png  -> 15 flag TGAs
python3 tools/generate_portrait.py   # tools/leader_portrait.png -> portrait DDS
```

Each crops to the target aspect before scaling rather than squeezing the art —
85px off the fly for the flag, 158px off the bottom for the portrait. The crop
is computed from the requested aspect, so replacement art of any size works.

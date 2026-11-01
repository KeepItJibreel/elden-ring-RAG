# Elden Ring Build Assistant (Django RAG)

A retrieval-augmented generation (RAG) app that answers Elden Ring build-planning questions. It indexes weapon, shield, armor, talisman, spell and skill data from CSV files, retrieves the entries most relevant to a question, and has an LLM turn them into a build: weapon, talismans and armor, a full stat spread, and an affinity (attunement) pick for non-somber weapons.

> **NOTE!** LLM usage is not provided, users must provide an API key, base url, and model name compatible with OpenAI API endpoint.

## Example

Both responses below were generated with `deepseek-flash`.

### Uchigatana (standard weapon, affinity chosen)

```bash
curl -s --max-time 180 -G "http://127.0.0.1:8000/rag/ask/" \
  --data-urlencode "q=Build me an optimized Uchigatana build at level 150" \
  | python -c "import sys, json; print(json.load(sys.stdin)['answer'])"
```

```text
## Uchigatana — Level 150 Keen/Dexterity bleed build

### 1. Weapon
- **Uchigatana** — Str 11, Dex 15; Slash/Pierce; innate (45) Hemorrhage; standard weapon, upgrades to +25 and can take an Ash of War.
- Ash of War: **Seppuku** (4 FP) — increases attack power and improves blood loss buildup; the self-inflicted bleed also triggers Lord of Blood's Exultation. Default **Unsheathe** (10–15 FP) is the alternative if you prefer active damage.
- Nagakiba (Str 18, Dex 22) is a longer alternative but costs more stat points; Rakshasa's Great Katana is a DLC somber weapon requiring Dex 27 and can't be infused, so it doesn't fit this spread.

### 2. Talismans and armor
- **Lord of Blood's Exultation** — +20% attack for 20s whenever blood loss occurs nearby; Seppuku procs it on yourself immediately, and every enemy bleed refreshes it.
- **Millicent's Prosthesis** — +5 Dex plus a successive-attack attack boost (4/6/11%) that stacks with the next talisman.
- **Rotten Winged Sword Insignia** — successive-attack boost (6/8/13%); katanas build the chain fast.
- **Dragoncrest Greatshield Talisman** — 20% physical damage negation, offsetting Seppuku's HP cost and the armor's downside.
- Armor: **Rakshasa Helm / Armor / Gauntlets / Greaves** (DLC) — +2% all damage per piece (8% total), but they greatly increase damage taken; the Dragoncrest talisman is there to blunt that trade-off. No other armor in the data gives an effect relevant to a Keen katana, so fill any remaining slots for poise/weight.
- If you run Unsheathe instead of Seppuku, swap Rotten Winged Sword Insignia for **Shard of Alexander** (+15% skill damage); **Godfrey Icon** (+15% charged skills) also fits charged Unsheathe.

### 3. Stat spread (Level 150, so 229 total points)
| Attribute | Value | Why |
|---|---|---|
| Vigor | 60 | Main survivability; Seppuku and Rakshasa armor both eat HP. |
| Mind | 18 | Seppuku costs only 4 FP; this covers Unsheathe use comfortably. |
| Endurance | 35 | Stamina for fast katana chains and enough equip load for the Rakshasa set + katana. |
| Strength | 11 | Exactly the Uchigatana requirement; Keen doesn't scale with it. |
| Dexterity | 80 | Keen's Dex A scaling is the entire damage stat. |
| Intelligence | 9 | Dump; not needed for Keen. |
| Faith | 8 | Dump. |
| Arcane | 8 | Dump — Keen has no Arcane scaling. |

Total: 60+18+35+11+80+9+8+8 = **229 = 150 + 79** ✓. Requirements met (Str 11, Dex 15).

### 4. Affinity — **Keen**
- **Keen (+25):** Phy 258, Str E / **Dex A** — with 80 Dex this is the highest realistic output and keeps the (45) Hemorrhage plus Seppuku's buildup boost.
- **Standard (+25):** Phy 281 but only Dex C scaling — the bigger base number loses to Keen once Dex scaling is applied.
- **Heavy (+25):** Phy 258, Str A — same AR as Keen but our Strength is 11, so it's wasted; ruled out.
- **Quality (+25):** Phy 225, Str B / Dex B — worse than Keen when only Dex is invested.
- **Blood (+25):** Phy 236, Dex B / Arc D, **82 bleed** — the strongest alternative. It wins on bleed buildup, but loses ~22 physical AR and the Arc D scaling is weak on a Dex spread; Keen + Seppuku already boosts buildup without the AR loss. Switch to Blood only if you rework the spread toward Arcane.
- **Cold (+25):** 198 Phy + 158 Mag, Dex B / Int C, 105/38 Frostbite — split damage and Int C is wasted at Int 9; ruled out.
- **Sacred / Flame (+25):** 220 Phy + 220 elemental with Faith B — ruled out at Faith 8.
- **Magic / Lightning (+25):** elemental split with Int/Dex-low or Dex C scaling — ruled out (no talisman synergy, weaker scaling than Keen A).
- **Occult / Poison (+25):** Arc B / Dex B + Arc D — need an Arcane spread; ruled out here.

### 5. Notes
- Open each fight with Seppuku: it self-bleeds (triggering Lord of Blood's Exultation), buffs attack and bleed buildup.
- You are deliberately fragile: Rakshasa's 8% damage bonus comes with greatly increased damage taken, and Seppuku drains HP — play around the Dragoncrest negation and don't trade.
- Two-handing gains nothing here (Str 11 already meets the requirement); the **Two-Handed Sword Talisman** (DLC) is only worth it if you two-hand out of preference.
- Base katana hemorrhage is (45); Seppuku is what makes the bleed plan actually pressure bosses.
```

### Moonveil (somber weapon, no affinity)

```bash
curl -s --max-time 180 -G "http://127.0.0.1:8000/rag/ask/" \
  --data-urlencode "q=Build me an optimized Moonveil build at level 150" \
  | python -c "import sys, json; print(json.load(sys.stdin)['answer'])"
```

```text
## 1. Weapon
**Moonveil** — requirements **Str 12, Dex 18, Int 23**. At +10: **Phy 178, Mag 213, Sta 90**, scaling **Str E / Dex B / Int B**, damage type **Slash/Pierce**, passive **Hemorrhage (50)**. Skill: **Transient Moonlight** (FP 15/20). It is **somber**, upgrades to **+10** with Somber Smithing Stones, and **cannot change affinity**.

## 2. Talismans and armor
- **Shard of Alexander** — +15% skill attack power; directly boosts Transient Moonlight.
- **Magic Scorpion Charm** — +12% magic damage; trade-off: +10% physical damage taken.
- **Ritual Sword Talisman** — +10% attack power at max HP; good for ranged skill play, but drops once you take damage.
- **Carian Filigreed Crest** — lowers skill FP cost by 25%, letting you use Transient Moonlight more often. If you reliably proc Moonveil’s Hemorrhage, **Lord of Blood’s Exultation** is a strong swap: +20% attack for 20 seconds when blood loss occurs nearby.
- Armor: **Spellblade’s Pointed Hat**, **Spellblade’s Gloves**, and **Spellblade’s Trousers** each strengthen magic/cold weapon skills by 2%, for about +6% to Transient Moonlight with no listed downside. Chest: no Moonveil-specific chest effect is in the context, so use your best defensive chest.
- Optional: **Lazuli Glintstone Crown** gives +3 Int/+3 Dex but reduces HP by 18%; I would not use it with this spread because it hurts survivability.

## 3. Stat spread — level 150, total 229
Assume level 150 and a class that can reach 10 Faith/10 Arcane; if your class has higher Faith/Arcane, move the excess into Dex or Mind.

- **Vigor 60** — main survivability.
- **Mind 27** — enough FP to use Transient Moonlight regularly.
- **Endurance 20** — stamina and equip load.
- **Strength 12** — exact Moonveil requirement.
- **Dexterity 40** — Moonveil has Dex B scaling and this also meets the Dex 18 requirement.
- **Intelligence 50** — Moonveil has Int B scaling and its +10 magic attack is higher than its physical attack.
- **Faith 10** — no requirement for this build; leftover.
- **Arcane 10** — no requirement for this build; leftover.

Check: **60 + 27 + 20 + 12 + 40 + 50 + 10 + 10 = 229 = 150 + 79**. Requirements met.

## 4. Affinity
**Moonveil is somber**, upgrades to **+10**, and **cannot change affinity**. No affinity choice applies.

## 5. Notes
- **Godfrey Icon** is omitted because Transient Moonlight has **charge: No**, so its charged skill/spell effect does not fit.
- Magic Scorpion and Ritual Sword are damage boosts with conditions/trade-offs; Carian Filigreed is the safer pick if you want more skill uses.
- None of the selected talismans or armor require the DLC.
```

These outputs are LLM-generated and have not been checked line by line against the game.

## How it works

```
CSV files ──► ingest command ──► Chunk rows (text + embedding) in SQLite

question ──► embed ──► quota-based chunk retrieval ──► LLM (OpenAI-compatible API) ──► build
```

### Embedding

Chunks are embedded locally with HF `all-MiniLM-L6-v2` (normalized vectors) and stored as JSON in SQLite. About 5,200 chunks in total.

### Retrieval and Response Generation

The question is embedded with the same model. Because vectors are normalized, cosine similarity is a plain dot product, computed for every chunk at once with NumPy (`matrix @ query_vector`). The chunk matrix is cached to save time on future retrievals.

Retrieval is done by a quota for each item group (weapon, armor, talismans, etc) so that each group is guaranteed to have chunks sent to the LLM. Without this, many queries asking to build around a specific weapon would favor chunks mentioning that weapon.

The retrieved chunks and the question go to the LLM with a system prompt that standardizes the answer structure.

## Tech stack

| Area | Tools |
|---|---|
| Language | Python |
| Web framework | Django (SQLite db) |
| Data processing | pandas, ast |
| Embeddings | HF sentence-transformers, NumPy |
| LLM | Any OpenAI-compatible API via the `openai` SDK, example outputs generated with `deepseek-flash` |

## Project structure

```
elden-ring-RAG/
├── elden_ring_RAG/                     # Django project (settings, root URLs)
├── rag/
│   ├── management/commands/ingest.py   # CSV -> chunks -> embeddings -> database
│   ├── migrations/                     # db schema
│   ├── models.py                       # Chunk model
│   ├── rag.py                          # retrieval, system prompt, LLM call
│   ├── views.py                        # /rag/ask/ endpoint
│   └── urls.py
├── data/                               # CSV files
├── .env.example
├── manage.py
└── requirements.txt
```

## Setup

### 1. Install

```bash
git clone https://github.com/KeepItJibreel/elden-ring-RAG.git
cd elden-ring-RAG
python -m venv .venv

source .venv/Scripts/activate

pip install -r requirements.txt
```

### 2. Configure the LLM

Copy `.env.example` to `.env` and fill it in:

```
LLM_API_KEY=sk-example123
BASE_URL=https://api.deepseek.com
MODEL=deepseek-flash
```

Any OpenAI-compatible provider works.

### 3. Build the database

```bash
python manage.py migrate
python manage.py ingest data
```

### 4. Run and Generate response

```bash
python manage.py runserver
```

In a second terminal:

```bash
curl -s -G "http://127.0.0.1:8000/rag/ask/" \
  --data-urlencode "q=your question"
```

Or open `http://127.0.0.1:8000/rag/ask/?q=your question` in a browser. The response is JSON with `question` and `answer` fields.

## Acknowledgements

- Dataset: [Ultimate Elden Ring with Shadow of the Erdtree DLC](https://www.kaggle.com/datasets/pedroaltobelli/ultimate-elden-ring-with-shadow-of-the-erdtree-dlc) on Kaggle.
- HF [sentence-transformers](https://www.sbert.net/) for the embedding model.
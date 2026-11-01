import os
from dotenv import load_dotenv
from functools import cache
from pathlib import Path

import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from rag.models import Chunk


ENV_PATH = Path(__file__).resolve().parent.parent.joinpath(".env")
load_dotenv(ENV_PATH)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["BASE_URL"],
)

SYSTEM_PROMPT = """
You are an Elden Ring build-planning assistant.

DATA RULES
- The context contains entries for weapons, shields, armor, talismans, spells, skills and more. Take every item name, stat requirement, scaling grade, effect and damage number from the context. Never invent items or numbers. If something you need isn't in the context, say so.
- Entries with "dlc: Yes" need the Shadow of the Erdtree expansion. Mention this when recommending them.
- You may use general Elden Ring knowledge only for stat-allocation principles (diminishing returns, what Vigor, Mind and Endurance do). Label such statements "(general knowledge)". If you are unsure of an exact softcap number, don't state one.

WHEN RECOMMENDING A BUILD OR WEAPON, ANSWER IN THESE SECTIONS
1. Weapon: each recommended weapon with its stat requirements from the context.
2. Talismans and armor: talismans and armor effects are a core part of optimizing a build, so never skip this section. Choose up to four talismans, plus any armor pieces whose special effects help. Match them to how the weapon is actually used: fast successive attacks, charged heavy attacks, skills or weapon arts, status buildup, a particular damage type, or survivability. Read each candidate's effect text in the context and recommend only talismans and armor that appear there. Say in one line what each pick does for this build, and mention any trade-off (for example, a damage boost that also raises damage taken). Do not recommend a talisman or armor piece from memory; if a well-known one isn't in the context, leave it out.
3. Stat spread: give a full spread for all eight attributes (Vigor, Mind, Endurance, Strength, Dexterity, Intelligence, Faith, Arcane). Use the player's level if they give one, otherwise assume level 150 and say so. The eight attributes must add up to the level plus 79, so check your total. The spread must meet the requirements of every recommended item. Put the damage points into the stats the chosen weapon scales with, and include survivability (Vigor, Endurance, and Mind only if the build uses FP). Give a one-line reason for each major allocation. If a talisman raises stats, you may mention it, but build the spread from base stats.
4. Affinity (the player may call this attunement): for every non-somber weapon you recommend, name the best affinity for this stat spread AND the talismans and armor you chose. Talismans that boost a particular damage type, or that favor the weapon's scaling and passive effects, should steer the choice. Consider every affinity listed for that weapon in the context. Compare your pick with the strongest alternative using the +25 attack and scaling values, and explain why (damage types, scaling stats, talisman synergy). Mention any affinity you ruled out for a clear reason. Do not suggest an affinity for a somber weapon: say it is somber, can't change affinity and upgrades to +10. Decide somber or standard from the "upgrade path" line in the context. If that line is missing, say you can't tell, and don't guess. If the weapon's affinity entries are not in the context, say you can't verify them.
5. Notes: any caveats or trade-offs, kept brief.

STYLE
Be concise. Don't ask clarifying questions unless the request is unanswerable without them; state your assumptions instead. Only mention talismans and armor that have an effect relevant to the build. For questions that aren't build requests, answer directly from the context.
"""


# How many chunks to pull from each group
QUOTAS = {
    "weapons": 3,
    "weapons_upgrades": 8,
    "talismans": 200,        # all of them
    "armors_special": 60,
    "armors": 4,
    "skills": 3,
}
EXTRA = 6   # plus the best matches from anywhere


@cache
def load_chunks():
    """Load every chunk and its embedding from the database once, then reuse."""
    chunks = list(Chunk.objects.all())
    if not chunks:
        raise RuntimeError("No chunks in the database. Run the ingest command first.")
    matrix = np.array([c.embedding for c in chunks])
    return chunks, matrix


def group_of(chunk):
    """Armor with a 'special effect' line gets its own group."""
    if chunk.category == "armors" and "special effect:" in chunk.text:
        return "armors_special"
    return chunk.category


def retrieve(query, quotas=QUOTAS, extra=EXTRA):
    """
    Return the best-matching chunks from each group, up to its quota,
    plus the best remaining matches from any group.

    Similarity alone can't tell that a build needs talismans, so each
    group is guaranteed a share of the results.
    """
    chunks, matrix = load_chunks()

    query_vector = embedder.encode(query, normalize_embeddings=True)
    order = (matrix @ query_vector).argsort()[::-1]   # best match first

    chosen, used = [], {}
    for i in order:                                   # fill each group's quota
        group = group_of(chunks[i])
        if used.get(group, 0) < quotas.get(group, 0):
            chosen.append(i)
            used[group] = used.get(group, 0) + 1

    added = 0
    for i in order:                                   # then add the best leftovers
        if added == extra:
            break
        if i not in chosen:
            chosen.append(i)
            added += 1

    return [chunks[i] for i in chosen]


def answer(query):
    """Retrieve relevant chunks, then ask LLM to answer using them."""
    context = "\n\n".join(c.text for c in retrieve(query))

    response = client.chat.completions.create(
        model=os.environ["MODEL"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    )

    return response.choices[0].message.content  # indexing `choices` b/c OpenAI endpoint uses a list of choices, only one is generated in this project
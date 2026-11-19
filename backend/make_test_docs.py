"""Test ke liye 6 documents banata hai (test_docs folder mein). Sirf testing ke liye."""
import os

FOLDER = "test_docs"

ORIGINAL = (
    "Renewable energy is becoming an important part of the global electricity supply. "
    "Solar panels convert sunlight directly into electrical power using photovoltaic cells. "
    "Wind turbines generate electricity by capturing the kinetic energy of moving air. "
    "Many countries have introduced subsidies to encourage households to install solar panels. "
    "The cost of producing solar electricity has fallen sharply over the last decade. "
    "However, the output of solar and wind plants depends heavily on the weather. "
    "Large batteries can store excess electricity and release it when demand is high. "
    "Governments also invest in smart grids to balance supply and demand more efficiently. "
    "Critics argue that the initial cost of installation remains too high for poorer communities. "
    "Despite these challenges, experts expect renewable sources to dominate new power capacity in the coming years."
)

# 5 sentences original se hu-ba-hu, 5 bilkul alag
COPIED = (
    "Renewable energy is becoming an important part of the global electricity supply. "
    "My grandmother grows tomatoes and beans in a small garden behind her house. "
    "Solar panels convert sunlight directly into electrical power using photovoltaic cells. "
    "The village market opens every Saturday morning and sells fresh bread and cheese. "
    "Wind turbines generate electricity by capturing the kinetic energy of moving air. "
    "Our football team trained hard all winter before the final match of the season. "
    "The cost of producing solar electricity has fallen sharply over the last decade. "
    "A good novel can make a long train journey feel surprisingly short. "
    "Large batteries can store excess electricity and release it when demand is high. "
    "Learning a second language takes patience and regular practice every single day."
)

# Har sentence mein 2-3 shabd badle gaye
LIGHT = (
    "Renewable energy is turning into an important part of the worldwide electricity supply. "
    "Solar panels change sunlight directly into electrical power with photovoltaic cells. "
    "Wind turbines produce electricity by capturing the kinetic energy of moving air. "
    "Many countries have started subsidies to encourage households to install solar panels. "
    "The cost of producing solar electricity has dropped sharply during the last decade. "
    "But the output of solar and wind plants depends strongly on the weather. "
    "Large batteries can store extra electricity and release it when demand is high. "
    "Governments also invest in smart grids to balance supply and demand more efficiently. "
    "Critics say that the initial cost of installation stays too high for poorer communities. "
    "Despite these challenges, experts expect renewable sources to dominate new power capacity in the coming years."
)

# Lagbhag har shabd synonym se badla gaya
HEAVY = (
    "Clean power sources are playing a growing role in how the world generates electricity. "
    "Photovoltaic cells inside solar panels turn sunlight straight into usable electric energy. "
    "Turbines driven by the wind produce power by harnessing the motion energy of the air. "
    "Several governments offer financial support so that families will fit solar panels on their roofs. "
    "Over the past ten years, it has become much cheaper to produce electricity from the sun. "
    "Still, how much power solar and wind farms deliver is strongly affected by weather conditions. "
    "Big batteries are able to keep surplus power and supply it at times of high demand. "
    "Authorities are also funding intelligent grids that match supply with demand more effectively. "
    "Opponents claim that the upfront price of installing systems is still unaffordable for poor communities. "
    "Even so, specialists predict that renewables will lead the growth of new generating capacity in the years ahead."
)

UNRELATED = (
    "The Roman Empire expanded across the Mediterranean during several centuries of conquest. "
    "Roman engineers built roads and aqueducts that connected distant provinces to the capital. "
    "A simple pasta sauce needs ripe tomatoes, olive oil, garlic and a handful of fresh basil. "
    "The senate debated new laws while generals led legions along the northern frontier. "
    "Many historians believe that economic troubles and political rivalry weakened the empire from within. "
    "Bakers in the old city rose before dawn to prepare loaves for the morning crowds. "
    "Gladiators trained in large arenas and performed before thousands of cheering spectators. "
    "The emperor Augustus reorganised the army and created a stable system of taxation."
)

# Original ke wahi sentences, ulte kram mein
REORDERED = " ".join(reversed([s.strip() + "." for s in ORIGINAL.split(".") if s.strip()]))

DOCS = {
    "1_original.txt": ORIGINAL,
    "2_copied.txt": COPIED,
    "3_light_rewording.txt": LIGHT,
    "4_heavy_paraphrase.txt": HEAVY,
    "5_unrelated.txt": UNRELATED,
    "6_reordered.txt": REORDERED,
}

os.makedirs(FOLDER, exist_ok=True)
for name, text in DOCS.items():
    with open(os.path.join(FOLDER, name), "w", encoding="utf-8") as f:
        f.write(text)
print(f"{len(DOCS)} files created in '{FOLDER}' folder")
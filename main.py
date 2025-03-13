import os
import subprocess
import json

ENTITIES = [
    "berry",
    "heart",
    "cassette",
    "miniheart",
    "blackgem",
    "memorialtextcontroller",
    "key",
]

EXCLUDE_ENTITIES = ["block", "door", "gate", "fake", "respawn", "berrytoflag"]

if not os.path.exists("maps") or not os.path.exists(".cache"):
    os.makedirs("maps", exist_ok=True)
    os.makedirs(".cache", exist_ok=True)
    subprocess.run(
        [
            "julia",
            "-e",
            'using Pkg; Pkg.add(PackageSpec(url="https://github.com/CelestialCartographers/Maple.git"))',
        ]
    )

maps = list(filter(lambda x: x.endswith(".bin"), os.listdir("maps")))

print(f"Found {len(maps)} map(s)")


def read_map(map: str):
    output = subprocess.run(
        [
            "julia",
            "loadData.jl",
            f"maps/{m}",
        ],
        capture_output=True,
    )
    jsonData = output.stdout.decode("utf-8")

    return json.loads(jsonData)


def count_entities(entities_by_room: list[dict]):
    map_data = {}

    excluded_data = {}
    for room in entities_by_room:
        for entity in room:
            if any(ENTITY in entity["name"].lower() for ENTITY in ENTITIES):
                if any(ENTITY in entity["name"].lower() for ENTITY in EXCLUDE_ENTITIES):
                    if excluded_data.get(entity["name"]):
                        excluded_data[entity["name"]] += 1
                    else:
                        excluded_data[entity["name"]] = 1
                    continue
                # Les cas chiants.... yay
                if (
                    entity["name"] == "blackGem" or "heart" in entity["name"].lower()
                ) and (
                    entity["data"].get("fake") or entity["data"].get("fakeHeartDialog")
                ):
                    if excluded_data.get(entity["name"]):
                        excluded_data[entity["name"]] += 1
                    else:
                        excluded_data[entity["name"]] = 1
                    continue

                if entity["name"] == "strawberry" and entity["data"].get("moon"):
                    name = "MoonBerry"
                elif entity["name"] == "strawberry" and entity["data"].get("winged"):
                    name = "WingedStrawberry"
                elif (
                    entity["name"] == "blackGem"
                    or entity["name"] == "reflectionHeartStatue"
                ):
                    name = "CristalHeart"  # car nous on a un cerveau... PUTAIN
                elif entity["name"] == "memorialTextController":
                    name = "WingedGoldenBerry"
                else:
                    name = entity["name"]

                if map_data.get(name):
                    map_data[name] += 1
                else:
                    map_data[name] = 1
    return map_data, excluded_data


def get_totals(d: dict):
    return sum(d.values())


def end_on_heart(data: dict):
    if data.get("meta"):
        return bool(data["meta"].get("HeartIsEnd"))
    return False


def fuse_database(database: dict):
    new_db = {}
    for mod_db in database["result"].values():
        for k, v in mod_db.items():
            new_db[k] = v
    return new_db


if __name__ == "__main__":
    with open(".cache/entity_database.json") as db:
        database = fuse_database(json.loads(str(db.read())))
    for m in maps:
        print(f"Scanning {m}...")

        parsed = read_map(m)
        print(f"Map read...")
        entities_by_room = list(map(lambda x: x["entities"], parsed["map"]["rooms"]))

        map_data, excluded_data = count_entities(entities_by_room)
        total = get_totals(map_data)
        total_excluded = get_totals(excluded_data)

        print(f"Scanning result:\n")
        print(f"End On Heart: {end_on_heart(parsed["data"])}")

        print(f"Found: {total} entities (excluded: {total_excluded} entities")
        for k, v in map_data.items():
            if database.get(k):
                print(f" - {database[k]}: x{v}")
            else:
                print(f" - {k}: x{v}")

        if total_excluded:
            with open(f".cache/{m.replace(".bin","")}", "w+") as f:
                f.write(str(excluded_data))
        print()

        input("Press enter to scan the next map")

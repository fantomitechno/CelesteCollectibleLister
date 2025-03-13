from requests import get
import yaml
import os
import re
from zipfile import ZipFile
import json
from time import time

LANG_FILE_RE = r"^(?:entities|triggers|style\.effects)\.([^.]+)\.(?:placements\.)?name(?:\.[^=]+)?=(.*)$"

LUA_FILE_NAME_RE = (
    r"^(?:Loenn)\/(?:entities|triggers|style)\/([a-zA-Z\_\/]+)(?:\.lua|\.lua.(?:.+))$"
)
LUA_FILE_ENTITY_ID_RE = (
    r'(?:(?:.+)\.|(?:return|local\s*.+\s*=)\s*\{(?:\n|.)*?)name\s*=\s*"(\S+)"'
)
LUA_FILE_ENTITY_NAME_RE = r'(?:(?:.+)\.|(?:return|local\s*.+\s*=)\s*\{(?:\n|.)*?)placements(?:\.|\s*=\s*{(?:\n|.)*?)name\s*=\s*"(.+)",?'

JULIA_FILE_NAME_RE = (
    r"^(?:Ahorn)\/(?:entities|triggers|style)\/([a-zA-Z\_\/]+)(?:\.jl|\.jl.(?:.+))$"
)
JULIA_FILE_ENTITY_ID_RE = r'(?:@mapdef\s*(?:Entity|Trigger)|@pardef\s*(?:.|\n)+\s*=(?:\s|\n)*(?:Entity|Trigger)\s*\()\s*"(\S+)"\s*'
JULIA_FILE_ENTITY_NAME_RE = r'const\splacements\s*=\s*Ahorn\.PlacementDict\((?:\n|\s)*"(.+)"\s*=>\sAhorn\.EntityPlacement\('
entity_database = dict()


def mod_contain_editor_plugin(id: int):
    raw_list_url = f"https://gamebanana.com/apiv11/File/{id}/RawFileList"
    req = get(raw_list_url)
    return "Loenn" in req.text or "Ahorn" in req.text


def download_mod(id: int, path: str):
    mod_url = f"https://celestemodupdater.0x0a.de/banana-mirror/{id}.zip"
    req = get(mod_url)
    with open(path, "wb") as mod_zip:
        mod_zip.write(req.content)


def bytes_to_str_content(b: bytes) -> str:
    return str(b).replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")


def parse_file(
    file: str,
    file_content: str,
    mod_data: dict,
    error_buffer: str,
    has_lang_file: bool,
    ID_RE: str,
    NAME_RE: str,
):
    match_id = re.findall(ID_RE, file_content, flags=re.MULTILINE)
    if match_id:
        entity_id: str = match_id[0]
        if mod_data.get(entity_id):
            return mod_data, error_buffer
        match_name = re.findall(NAME_RE, file_content, flags=re.MULTILINE)
        if match_name:
            entity_name: str = match_name[0]
            if not mod_data.get(entity_id):
                mod_data[entity_id] = entity_name.split("(")[0].strip("\r")
        elif not has_lang_file:
            print(f"Didn't found an name for the entity of ID {entity_id} in {file}")
            error_buffer += f"ID: {entity_id}, file {file}\n"
    elif not has_lang_file:
        print(f"File {file} doesn't contain any entity ID")
        error_buffer += f"ID: NA, file {file}\n"

    return mod_data, error_buffer


def parse_lua_files(
    file: str, file_content: str, mod_data: dict, error_buffer: str, has_lang_file: bool
):
    return parse_file(
        file,
        file_content,
        mod_data,
        error_buffer,
        has_lang_file,
        LUA_FILE_ENTITY_ID_RE,
        LUA_FILE_ENTITY_NAME_RE,
    )


def parse_julia_files(
    file: str, file_content: str, mod_data: dict, error_buffer: str, has_lang_file: bool
):
    return parse_file(
        file,
        file_content,
        mod_data,
        error_buffer,
        has_lang_file,
        JULIA_FILE_ENTITY_ID_RE,
        JULIA_FILE_ENTITY_NAME_RE,
    )


def get_entities(archive: ZipFile):
    mod_data = {}

    archive_content = list(map(lambda x: x.filename, archive.filelist))
    has_lang_file = any(file.endswith("lang/en_gb.lang") for file in archive_content)
    if has_lang_file:
        file_to_read = (
            "Loenn/lang/en_gb.lang"
            if "Loenn/lang/en_gb.lang" in archive_content
            else "Ahorn/lang/en_gb.lang"
        )

        with archive.open(file_to_read) as lang_file:
            file_content = bytes_to_str_content(lang_file.read())
            matches = re.findall(LANG_FILE_RE, file_content, flags=re.MULTILINE)
            for k, v in matches:
                mod_data[k] = v.split("(")[0].strip("\r")
    else:
        print(f"Lang files not found... relying entirely on improvisation mode, glhf")

    error_buffer = ""
    for file in filter(lambda x: re.match(LUA_FILE_NAME_RE, x), archive_content):
        with archive.open(file) as f:
            file_content = bytes_to_str_content(f.read())
            mod_data, error_buffer = parse_lua_files(
                file, file_content, mod_data, error_buffer, has_lang_file
            )

    for file in filter(lambda x: re.match(JULIA_FILE_NAME_RE, x), archive_content):
        with archive.open(file) as f:
            file_content = bytes_to_str_content(f.read())
            mod_data, error_buffer = parse_julia_files(
                file, file_content, mod_data, error_buffer, has_lang_file
            )

    return mod_data, error_buffer


if __name__ == "__main__":
    if not os.path.exists(".tmp") or not os.path.exists(".cache"):
        os.makedirs(".tmp", exist_ok=True)
        os.makedirs(".cache", exist_ok=True)

    req = get("https://maddie480.ovh/celeste/custom-entity-catalog.json")

    # If only it was this simple...
    modListId: list[int] = list(map(lambda x: x["itemid"], req.json()["modInfo"]))

    req = get("https://everestapi.github.io/modupdater.txt")

    EVEREST_UPDATE_URI = req.text.strip()

    req = get(EVEREST_UPDATE_URI)

    mod_database: dict = yaml.safe_load(req.text)
    error_buffer = ""

    for name, mod in filter(
        lambda x: x[1]["GameBananaId"] in modListId, mod_database.items()
    ):
        if not mod_contain_editor_plugin(mod["GameBananaFileId"]):
            print(f"Bypassing mod {name} ({mod["GameBananaId"]})")
            continue
        print(f"Scanning mod {name} ({mod["GameBananaId"]})")
        download_mod(mod["GameBananaFileId"], ".tmp/mod.zip")

        archive = ZipFile(".tmp/mod.zip", "r")
        md, eb = get_entities(archive)
        error_buffer += eb
        if len(md.keys()) != 0:
            entity_database[name] = md
        else:
            error_buffer += f"Mod {name} has no entity... wait that's wrong\n"

    with open(".cache/entity_database.json", "w+") as database:
        database.write(
            json.dumps({"scanned_timestamp": time(), "result": entity_database})
        )

    with open(".cache/error", "w+") as database:
        database.write(error_buffer)

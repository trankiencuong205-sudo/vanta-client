#!/usr/bin/env python3
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

MC = "1.21.11"
META = "https://meta.fabricmc.net/v2/versions"
MAVEN = "https://maven.fabricmc.net"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "vanta-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def maven_versions(group_path, artifact):
    xml = fetch(f"{MAVEN}/{group_path}/{artifact}/maven-metadata.xml")
    return [v.text for v in ET.fromstring(xml).iter("version")]


def vkey(v):
    return [int(p) if p.isdigit() else 0 for p in re.split(r"[.+\-]", v)]


def main():
    games = json.loads(fetch(f"{META}/game"))
    if not any(g["version"] == MC for g in games):
        sys.exit(f"Fabric does not list Minecraft {MC} yet.")

    loaders = json.loads(fetch(f"{META}/loader"))
    loader = next(l["version"] for l in loaders if l.get("stable"))

    yarns = json.loads(fetch(f"{META}/yarn/{MC}"))
    if not yarns:
        sys.exit(f"No Yarn mappings published for Minecraft {MC}.")
    yarn = yarns[0]["version"]

    api = [v for v in maven_versions("net/fabricmc/fabric-api", "fabric-api") if v.endswith("+" + MC)]
    if not api:
        sys.exit(f"No Fabric API build for Minecraft {MC}.")
    fabric_api = sorted(api, key=vkey)[-1]

    looms = [v for v in maven_versions("net/fabricmc", "fabric-loom") if re.fullmatch(r"\d+\.\d+(\.\d+)?", v)]
    pref = [v for v in looms if v.startswith("1.14")]
    loom = sorted(pref or looms, key=vkey)[-1]

    props = {
        "minecraft_version": MC,
        "yarn_mappings": yarn,
        "loader_version": loader,
        "fabric_version": fabric_api,
        "loom_version": loom,
    }
    print("Resolved versions:")
    for k, v in props.items():
        print(f"  {k} = {v}")

    with open("gradle.properties", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    out = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        out.append(f"{key}={props[key]}" if key in props else line)
    with open("gradle.properties", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()

"""Capture public Muçum forecast rounds and SGB levels for an offline diagnostic.

This is a retrospective snapshot, not proof of what observations were available
at each issue. The public API's archive receipt references are preserved, but
their remote authenticity is not verified here.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://radar.brunozilio.com/api/projection?station=mucum"
TRUTH = "https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv"


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "radar-model-audit/1"}), timeout=30) as response:
        return response.read()


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def main():
    destination = Path(sys.argv[1])
    destination.mkdir(parents=True, exist_ok=False)
    listing = fetch(BASE)
    levels = fetch(TRUTH)
    (destination / "api-listing.json").write_bytes(listing)
    (destination / "sgb-mucum-cota.csv").write_bytes(levels)
    rounds = json.loads(listing)["rounds"]
    if len(rounds) != len(set(rounds)):
        raise ValueError("Duplicate round keys")
    def one(index_round):
        index, reference = index_round
        body = fetch(BASE + "&round=" + quote(reference, safe=""))
        response = json.loads(body)
        projection = response.get("projection")
        if not projection or datetime.fromisoformat(projection["referenceAt"].replace("Z", "+00:00")) != datetime.fromisoformat(reference.replace("Z", "+00:00")):
            raise ValueError(f"Round mismatch: {reference}")
        name = f"round-{index:03}.json"
        (destination / name).write_bytes(body)
        return {"referenceAt": reference, "file": name, "sha256": sha(body),
                "generatedAt": projection["generatedAt"], "modelSha256": projection.get("modelSha256"),
                "archiveReceiptKey": projection.get("archiveReceiptKey")}
    records = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(one, item): item[1] for item in enumerate(rounds)}
        for future in as_completed(futures):
            records.append(future.result())
    records.sort(key=lambda row: row["referenceAt"])
    manifest = {"capturedAt": datetime.now(timezone.utc).isoformat(), "type": "retrospective-public-api-snapshot",
                "api": BASE, "truth": TRUTH, "listingSha256": sha(listing), "truthSha256": sha(levels),
                "rounds": records,
                "limitations": ["Historical source availability and QC cannot be reconstructed from the current SGB CSV.",
                                "API receipt keys were copied but remote receipt existence was not verified."]}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(destination), "rounds": len(records), "capturedAt": manifest["capturedAt"]}))


if __name__ == "__main__":
    main()

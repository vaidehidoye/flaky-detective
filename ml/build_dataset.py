# build_dataset.py
#
# Builds the training data for the model.
#
# IDoFT (International Dataset of Flaky Tests) lists real flaky tests found in
# open-source Python projects. It only has each test's NAME, not its code, so
# we download each test file from GitHub at the exact commit the flaky test
# was found in, and pull out every test in it:
#   - tests IDoFT lists as flaky       -> flaky = 1
#   - the other tests in the same file -> flaky = 0
#
# Taking the non-flaky examples from the same files matters. Otherwise the
# model could learn to spot which PROJECTS have flaky tests, instead of what
# flaky tests look like.
#
# The downloaded code is only read, never run.
#
# Run it with:   .venv/bin/python ml/build_dataset.py
# Output:        ml/data/dataset.csv

import csv
import io
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.features import tests_in_file  # noqa: E402

IDOFT_CSV = "https://raw.githubusercontent.com/TestingResearchIllinois/idoft/main/py-data.csv"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
OUT_CSV = os.path.join(DATA_DIR, "dataset.csv")

# IDoFT's categories, grouped into three causes.
CAUSES = {
    "OD": "order",
    "OD-Vic": "order",          # victim: fails when some other test runs first
    "OD-Brit": "order",         # brittle: passes only when some other test runs first
    "NOD": "nondeterministic",  # randomness, time, threads, network...
    "NIO": "self-polluting",    # passes once, then fails when run again
}


def download(url):
    """Download a URL and return its text, or None if it can't be fetched."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:
        # Missing file, deleted repo, bad URL, timeout... just skip it.
        return None


def fetch_file(project_url, sha, path):
    """Download one file from a GitHub repo at a given commit, with a disk cache."""
    owner_repo = project_url.rstrip("/").removeprefix("https://github.com/")
    cache_path = os.path.join(CACHE_DIR, owner_repo.replace("/", "__"), sha, path)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read()

    text = download(f"https://raw.githubusercontent.com/{owner_repo}/{sha}/{path}")
    if text is not None:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def cause_for(categories):
    """Turn IDoFT's category field (e.g. "OD-Vic" or "OD;NOD") into one cause."""
    causes = {CAUSES[c.strip()] for c in categories.split(";") if c.strip() in CAUSES}
    return causes.pop() if len(causes) == 1 else "unknown"


def read_idoft():
    """Return {(project, sha, path): {test name inside file: cause}} and all flaky names."""
    rows = list(csv.reader(io.StringIO(download(IDOFT_CSV))))[1:]
    files = {}
    all_flaky = set()  # (project, path, name) for every flaky test, at any commit
    for row in rows:
        project, sha, full_name, categories = (field.strip() for field in row[:4])
        # "tests/test_x.py::TestClass::test_y[param]" -> file + name inside it
        path, _, name = full_name.split("[")[0].partition("::")
        files.setdefault((project, sha, path), {})[name] = cause_for(categories)
        all_flaky.add((project, path, name))
    return files, all_flaky


def process_file(item, all_flaky):
    (project, sha, path), flaky_here = item
    source = fetch_file(project, sha, path)
    if source is None:
        return []

    examples = []
    for name, code, context in tests_in_file(source):
        if name in flaky_here:
            flaky, cause = 1, flaky_here[name]
        elif (project, path, name) in all_flaky:
            continue  # flaky at a different commit; not a safe "not flaky" example
        else:
            flaky, cause = 0, ""
        examples.append({"project": project, "test": f"{path}::{name}",
                         "flaky": flaky, "cause": cause,
                         "code": code, "context": context})
    return examples


def main():
    print("Downloading the IDoFT list of flaky tests...")
    files, all_flaky = read_idoft()
    print(f"{len(files)} test files listed. Fetching them from GitHub (cached after the first run)...")

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = pool.map(lambda item: process_file(item, all_flaky), files.items())
        examples = [e for file_examples in results for e in file_examples]

    # The same test can appear at several commits; keep one copy.
    examples = list({(e["project"], e["test"]): e for e in examples}.values())

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["project", "test", "flaky", "cause", "code", "context"])
        writer.writeheader()
        writer.writerows(examples)

    flaky = sum(e["flaky"] for e in examples)
    projects = len({e["project"] for e in examples})
    print(f"Saved {len(examples)} tests from {projects} projects to {OUT_CSV}")
    print(f"  flaky      {flaky}")
    print(f"  not flaky  {len(examples) - flaky}")


if __name__ == "__main__":
    main()

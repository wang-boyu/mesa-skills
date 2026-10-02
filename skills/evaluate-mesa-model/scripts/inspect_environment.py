#!/usr/bin/env python3
"""Report a short set of installed distribution metadata without importing them."""

import argparse
from importlib import metadata
import json
import platform
import sys


CORE_DISTRIBUTIONS = ("Mesa", "NetworkX")
GEO_DISTRIBUTIONS = (
    "Mesa-Geo",
    "NumPy",
    "GeoPandas",
    "Shapely",
    "pyproj",
    "Rasterio",
    "Rtree",
    "libpysal",
    "affine",
    "xyzservices",
)


def _distribution_metadata(name, version_lookup):
    try:
        version = version_lookup(name)
    except metadata.PackageNotFoundError:
        return {"present": False, "state": "absent", "version": None}
    except Exception:
        # A failed read does not establish presence. Never expose its payload.
        return {"present": None, "state": "failed", "version": None}

    if version is not None and not isinstance(version, str):
        try:
            version = str(version)
        except Exception:
            return {"present": True, "state": "unprintable", "version": None}

    # Blankness precedes printability: empty and whitespace-only values are
    # observations, including whitespace that cannot be printed literally.
    if version is None or not str.strip(version):
        return {"present": True, "state": "blank", "version": version}
    if not str.isprintable(version):
        return {"present": True, "state": "unprintable", "version": None}
    return {"present": True, "state": "available", "version": version}


def collect_environment(*, geo=False, version_lookup=None):
    """Collect selected metadata once; resolve the lookup at call time.

    Version text is not parsed or interpreted. A failed distribution read
    leaves its presence unknown and does not prevent the remaining reads.
    """
    if version_lookup is None:
        version_lookup = metadata.version
    python = {
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
    }
    names = CORE_DISTRIBUTIONS + (GEO_DISTRIBUTIONS if geo else ())
    return {
        "python": python,
        "distributions": {
            name: _distribution_metadata(name, version_lookup) for name in names
        },
    }


def render_text(report):
    """Render the collected observations with safely quoted metadata values."""
    python = report["python"]
    lines = [
        "Python: implementation=" + json.dumps(python["implementation"])
        + " version=" + json.dumps(python["version"])
    ]
    for name, entry in report["distributions"].items():
        presence = {True: "true", False: "false", None: "unknown"}[entry["present"]]
        lines.append(
            f"{name}: state={entry['state']} present={presence} "
            + "version=" + json.dumps(entry["version"])
        )
    return "\n".join(lines)


def render_json(report):
    """Render the same collected observations as stable, indented JSON."""
    return json.dumps(report, indent=2, sort_keys=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Report Python and selected installed distribution metadata. "
            "Metadata does not establish importability, binary compatibility "
            "or runtime behavior."
        ),
        allow_abbrev=False,
    )
    parser.add_argument(
        "--geo", action="store_true",
        help="also inspect the documented geographic distributions",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    try:
        report = collect_environment(geo=args.geo)
    except Exception:
        print("error: unable to collect environment metadata.", file=sys.stderr)
        return 2

    try:
        output = render_json(report) if args.json else render_text(report)
        print(output)
    except Exception:
        print("error: unable to render environment metadata.", file=sys.stderr)
        return 2

    if any(entry["state"] == "failed" for entry in report["distributions"].values()):
        print(
            "error: one or more selected metadata reads failed; report is partial.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

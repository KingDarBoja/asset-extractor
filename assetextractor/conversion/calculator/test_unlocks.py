"""Compare params-base.js against params.js to verify dlcUnlocks consistency.

Assets present in params-base.js must have empty dlcUnlocks in params.js.
Assets absent from params-base.js must have non-empty dlcUnlocks in params.js.

Exception: needs are allowed to have empty dlcUnlocks even when absent from params-base.js.
Needs whose NeedProduct is a base-game good inherit no DLC tag intentionally — the
population tier already carries the correct DLC gating for the calculator UI.
"""

import json
import typing as t
from pathlib import Path

CALCULATOR_DIR = Path(__file__).parent.parent.parent.parent.parent / "anno-117-calculator" / "js"
PARAMS_BASE = CALCULATOR_DIR / "params-base.js"
PARAMS = CALCULATOR_DIR / "params.js"
JS_PREFIX = "if(window.params == null)window.params="


def load_params(path: Path) -> dict[str, t.Any]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith(JS_PREFIX):
        raise ValueError(f"{path.name} does not start with expected prefix")
    return t.cast("dict[str, t.Any]", json.loads(content[len(JS_PREFIX) :]))


def collect_guids(data: dict[str, t.Any]) -> dict[str, set[int]]:
    """Return {array_key: set of guids} for all array keys whose items have a guid."""
    result: dict[str, set[int]] = {}
    for key, value in data.items():
        if not isinstance(value, list):
            continue
        guids: set[int] = set()
        item_list: list[t.Any] = t.cast("list[t.Any]", value)
        for item_raw in item_list:
            if isinstance(item_raw, dict) and "guid" in item_raw:
                item_dict: dict[str, t.Any] = t.cast("dict[str, t.Any]", item_raw)
                guids.add(int(item_dict["guid"]))
        if guids:
            result[key] = guids
    return result


def main() -> None:
    try:
        base_data: dict[str, t.Any] = load_params(PARAMS_BASE)
        full_data: dict[str, t.Any] = load_params(PARAMS)
    except FileNotFoundError:
        print("Params files not found, skipping validation")
        return

    base_guids_by_key = collect_guids(base_data)
    full_guids_by_key = collect_guids(full_data)

    array_keys = sorted(set(base_guids_by_key) | set(full_guids_by_key))

    # Keys where missing DLC tags (wrong_empty) are tolerated by design.
    # needs: NeedProducts are often base-game goods; the population tier gates visibility.
    TOLERATE_MISSING: set[str] = {"needs"}  # noqa: N806

    errors: list[str] = []
    stats: dict[str, dict[str, int]] = {}

    for key in array_keys:
        base_guids = base_guids_by_key.get(key, set())
        full_items: dict[int, dict[str, t.Any]] = {}

        full_data_list = full_data.get(key, [])
        if isinstance(full_data_list, list):
            item_list: list[t.Any] = t.cast("list[t.Any]", full_data_list)
            for item_raw in item_list:
                if isinstance(item_raw, dict) and "guid" in item_raw:
                    item_dict: dict[str, t.Any] = t.cast("dict[str, t.Any]", item_raw)
                    guid = int(item_dict["guid"])
                    full_items[guid] = item_dict

        should_be_empty = 0
        should_be_nonempty = 0
        wrong_empty: list[str] = []
        wrong_nonempty: list[str] = []

        for guid, item in full_items.items():
            if "dlcUnlocks" not in item:
                continue
            unlocks = item["dlcUnlocks"]
            in_base = guid in base_guids

            if in_base:
                should_be_empty += 1
                if unlocks:
                    name = str(item.get("name", ""))
                    wrong_nonempty.append(f"    guid={guid} name={name!r} dlcUnlocks={unlocks}")
            else:
                should_be_nonempty += 1
                if not unlocks:
                    name = str(item.get("name", ""))
                    wrong_empty.append(f"    guid={guid} name={name!r}")

        stats[key] = {
            "base": len(base_guids),
            "total": len(full_items),
            "should_be_empty": should_be_empty,
            "should_be_nonempty": should_be_nonempty,
            "wrong_nonempty": len(wrong_nonempty),
            "wrong_empty": len(wrong_empty),
        }

        EXAMPLE_COUNT = 3  # noqa: N806

        if wrong_nonempty:
            example_guids = [int(line.split("guid=")[1].split()[0]) for line in wrong_nonempty[:EXAMPLE_COUNT]]
            suffix = f", e.g. {example_guids}"
            errors.append(
                f"[{key}] {len(wrong_nonempty)} base asset(s) have non-empty dlcUnlocks (should be empty){suffix}"
            )

        if wrong_empty:
            example_guids = [int(line.split("guid=")[1].split()[0]) for line in wrong_empty[:EXAMPLE_COUNT]]
            suffix = f", e.g. {example_guids}"
            msg = f"[{key}] {len(wrong_empty)} DLC asset(s) have empty dlcUnlocks (should be non-empty){suffix}"
            if key in TOLERATE_MISSING:
                msg += " [tolerated]"
                print(msg)
            else:
                errors.append(msg)

    print("=== Stats per array key ===")
    for key, s in stats.items():
        status = "OK" if s["wrong_nonempty"] == 0 and s["wrong_empty"] == 0 else "FAIL"
        print(
            f"  {key}: base={s['base']} total={s['total']} "
            f"dlc_only={s['should_be_nonempty']} "
            f"[{status}]"
            + (f" wrong_nonempty={s['wrong_nonempty']} wrong_empty={s['wrong_empty']}" if status == "FAIL" else "")
        )

    print()
    if errors:
        print(f"FAILED: {len(errors)} check(s) failed")
        print()
        for line in errors:
            print(line)
        raise SystemExit(1)
    else:
        print("PASSED: all dlcUnlocks are consistent between params-base.js and params.js")


if __name__ == "__main__":
    main()

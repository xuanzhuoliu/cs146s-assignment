#!/usr/bin/env python3
"""Reproduce tables using unchanged Factory scores and an explicit crosswalk."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
mapping = json.loads((ROOT / "evidence/criterion-mapping.json").read_text())["criteria"]
result = {}
for repo in ("dayjs", "yt-dlp", "redis"):
    report = json.loads((ROOT / f"evidence/raw/{repo}-report-input.json").read_text())["report"]
    assert set(report) == set(mapping) and len(report) == 84
    assert all(v["denominator"] == 1 and v["numerator"] in (0, 1, None)
               for v in report.values())
    passed = sum(v["numerator"] == 1 for v in report.values())
    failed = sum(v["numerator"] == 0 for v in report.values())
    skipped = sum(v["numerator"] is None for v in report.values())
    item = {"passed": passed, "failed": failed, "skipped": skipped,
            "evaluated": passed + failed, "percent": 100 * passed / (passed + failed)}
    for grouping in ("factory_category", "assignment_pillar"):
        groups = {}
        for key, value in report.items():
            group = groups.setdefault(mapping[key][grouping],
                                      {"passed": [], "failed": [], "skipped": []})
            status = ("skipped" if value["numerator"] is None else
                      "passed" if value["numerator"] == 1 else "failed")
            group[status].append(key)
        for group in groups.values():
            p, f = len(group["passed"]), len(group["failed"])
            group["pass_rate"] = 100 * p / (p + f) if p + f else None
        assert sum(len(g[k]) for g in groups.values()
                   for k in ("passed", "failed", "skipped")) == 84
        item[grouping] = groups
    result[repo] = item
(ROOT / "evidence/comparison.json").write_text(json.dumps(result, indent=2) + "\n")
for repo, item in result.items():
    print(f'{repo}: {item["passed"]}/{item["evaluated"]} passed; '
          f'{item["failed"]} failed; {item["skipped"]} skipped')

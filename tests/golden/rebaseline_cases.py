"""
Recompute the per-case numbers in sample_baseline.json with the CURRENT code.

Run only after the user has approved a numeric change to the calculation:

    python tests/golden/rebaseline_cases.py

Loading/segment entries (point hashes, distance_range_segment) are left as
they are; only `cases[*]` calculation/distribution/report rows are rewritten.
"""

import json
import os

import numpy as np

from pps.core.analysis import run_analysis
from pps.core.filename_parser import parse_filename
from pps.core.ply_loader import load_ply
from pps.report.core.html_pdf_generator import HTMLPDFGenerator

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "sample_baseline.json")
SAMPLE = os.path.join(
    os.path.dirname(os.path.dirname(HERE)),
    "sample", "2_thickness_01#20260203_093652#cloud_compared_07.ply",
)

CALC_FIELDS = (
    "surface_area_m2", "volume_m3", "mean_thickness_mm", "min_thickness_mm",
    "max_thickness_mm", "std_thickness_mm", "num_points", "area_reached_target_m2",
    "out_of_range_count", "max_measurable_mm",
)


def _plain(value):
    return value.item() if isinstance(value, np.generic) else value


def main():
    with open(BASELINE, encoding="utf-8") as f:
        baseline = json.load(f)

    cloud = load_ply(SAMPLE, "distances")
    project_info = parse_filename(SAMPLE)
    gen = HTMLPDFGenerator("unused.pdf")

    for case in baseline["cases"]:
        tmin, tmax = case["target_min"], case["target_max"]
        calc, dist = run_analysis(cloud.points.copy(), cloud.distances.copy(), tmin, tmax)

        case["calculation_result"] = {k: _plain(getattr(calc, k)) for k in CALC_FIELDS}
        case["thickness_distribution"] = {
            "below_target": dist.below_target,
            "within_target": dist.within_target,
            "above_target": dist.above_target,
            "below_target_percent": float(dist.below_target_percent),
            "within_target_percent": float(dist.within_target_percent),
            "above_target_percent": float(dist.above_target_percent),
            "histogram_bins": [float(b) for b in dist.histogram_bins],
            "histogram_counts": [int(c) for c in dist.histogram_counts],
            "target_min": dist.target_min,
            "target_max": dist.target_max,
        }
        case.pop("distances_hash_after_mutation", None)
        case["project_rows"] = gen._project_rows(project_info, calc, tmin, tmax, {})
        case["result_main_rows"] = gen._result_main_rows(calc)
        case["result_stats_rows"] = gen._result_stats_rows(calc)
        case["distribution_rows"] = gen._distribution_rows(dist, tmin, tmax)
        print(tmin, tmax, case["calculation_result"])

    with open(BASELINE, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()

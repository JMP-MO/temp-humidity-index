from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from temp_humidity_index.settings import load_settings


CHART_RE = re.compile(
  r"^ifs_(?P<kind>thi_data|heat_stress|2t_data|2d_data)_(?P<date>\d{8})_(?P<step>\d{3})\.png$"
)


@dataclass(frozen=True)
class ChartStep:
    step_hours: int
    thi_image: str
    heat_risk_image: str
    t2_image: str | None
    d2_image: str | None


def _discover_latest_pairs(charts_root: Path) -> tuple[str, list[ChartStep], Path]:
    grouped: dict[str, dict[int, dict[str, Path]]] = {}
    run_dirs: set[Path] = set()

    for image_path in charts_root.rglob("ifs_*.png"):
        match = CHART_RE.match(image_path.name)
        if not match:
            continue

        date = match.group("date")
        kind = match.group("kind")
        step_hours = int(match.group("step"))

        grouped.setdefault(date, {}).setdefault(step_hours, {})[kind] = image_path
        run_dirs.add(image_path.parent)

    if not grouped:
        raise FileNotFoundError(f"No chart images were found in {charts_root}")

    latest_date = max(grouped)
    latest_steps = grouped[latest_date]

    step_entries: list[ChartStep] = []
    for step_hours in sorted(latest_steps):
        chart_files = latest_steps[step_hours]
        thi_path = chart_files.get("thi_data")
        heat_path = chart_files.get("heat_stress")
        if thi_path is None or heat_path is None:
            continue

        step_entries.append(
            ChartStep(
                step_hours=step_hours,
                thi_image=thi_path.name,
                heat_risk_image=heat_path.name,
            t2_image=chart_files.get("2t_data").name if chart_files.get("2t_data") else None,
            d2_image=chart_files.get("2d_data").name if chart_files.get("2d_data") else None,
            )
        )

    if not step_entries:
        raise FileNotFoundError(
            f"No matched THI / heat-risk chart pairs were found for latest run {latest_date}"
        )

    latest_run_dirs = [path for path in run_dirs if path.name == latest_date]
    latest_run_dir = max(
        latest_run_dirs,
        default=charts_root,
        key=lambda path: path.stat().st_mtime,
    )

    return latest_date, step_entries, latest_run_dir


def _copy_latest_images(latest_run_dir: Path, steps: list[ChartStep], output_dir: Path) -> None:
    images_dir = output_dir / "images"
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    for step in steps:
      for image_name in (
        step.thi_image,
        step.heat_risk_image,
        step.t2_image,
        step.d2_image,
      ):
        if image_name is None:
          continue
        source = latest_run_dir / image_name
        if not source.exists():
            raise FileNotFoundError(f"Missing chart image: {source}")
        shutil.copy2(source, images_dir / image_name)


def _build_manifest(latest_date: str, steps: list[ChartStep]) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latest_date": latest_date,
        "steps": [asdict(step) for step in steps],
    }


def _render_html(manifest: dict) -> str:
    manifest_json = json.dumps(manifest, indent=2)
    latest_date = escape(manifest["latest_date"])

    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Temperature Humidity Index Charts</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4efe7;
      --panel: rgba(255, 255, 255, 0.82);
      --ink: #1f2937;
      --muted: #6b7280;
      --accent: #b45309;
      --border: rgba(31, 41, 55, 0.12);
      --shadow: 0 18px 60px rgba(31, 41, 55, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(245, 158, 11, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 28%),
        linear-gradient(180deg, #fffaf2 0%, var(--bg) 100%);
      min-height: 100vh;
    }
    .page { max-width: 1520px; margin: 0 auto; padding: 28px; }
    header {
      display: flex;
      gap: 16px;
      align-items: end;
      justify-content: space-between;
      margin-bottom: 22px;
      flex-wrap: wrap;
    }
    h1 { margin: 0; font-size: clamp(2rem, 3vw, 3.25rem); letter-spacing: -0.03em; }
    .subtitle { margin-top: 8px; color: var(--muted); max-width: 70ch; }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      color: var(--muted);
      font-size: 0.95rem;
    }
    .controls, .cards {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }
    .controls { padding: 18px 20px; margin-bottom: 18px; }
    .slider-row { display: grid; grid-template-columns: 1fr auto; gap: 14px; align-items: center; }
    .slider-labels { display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; color: var(--muted); font-size: 0.92rem; }
    input[type="range"] { width: 100%; accent-color: var(--accent); }
    .step-title { font-size: 1.25rem; font-weight: 700; }
    .cards { padding: 18px; }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .row-gap { margin-top: 16px; }
    figure { margin: 0; }
    .card {
      border: 1px solid var(--border);
      border-radius: 20px;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.92);
    }
    .card h2 { margin: 0; padding: 16px 18px 0; font-size: 1.05rem; }
    .card p { margin: 8px 18px 0; color: var(--muted); font-size: 0.95rem; }
    .card img { display: block; width: 100%; height: auto; }
    .missing {
      display: grid;
      place-items: center;
      min-height: 260px;
      color: var(--muted);
      font-weight: 600;
      border-top: 1px solid var(--border);
      background: rgba(107, 114, 128, 0.05);
    }
    .missing[hidden] {
      display: none !important;
    }
    .footnote { margin-top: 14px; color: var(--muted); font-size: 0.92rem; }
    @media (max-width: 980px) {
      .grid { grid-template-columns: 1fr; }
      .slider-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="page">
    <header>
      <div>
        <h1>Temperature Humidity Index</h1>
        <div class="subtitle">Latest chart set from model initialisation <strong>__LATEST_DATE__</strong>. Use the slider to move through the available forecast steps.</div>
      </div>
      <div class="badge" id="run-summary"></div>
    </header>

    <section class="controls">
      <div class="slider-row">
        <div>
          <div class="step-title" id="step-title"></div>
          <div class="slider-labels">
            <span id="step-range-start"></span>
            <span id="step-range-end"></span>
          </div>
        </div>
        <div>
          <input id="step-slider" type="range" min="0" max="0" step="1" value="0">
        </div>
      </div>
    </section>

    <section class="cards">
      <div class="grid">
        <figure class="card">
          <h2>THI (Celsius)</h2>
          <p id="thi-caption"></p>
          <img id="thi-image" alt="THI chart">
        </figure>
        <figure class="card">
          <h2>Heat Stress Risk</h2>
          <p id="risk-caption"></p>
          <img id="risk-image" alt="Heat stress risk chart">
        </figure>
      </div>

      <div class="grid row-gap">
        <figure class="card">
          <h2>2m Temperature (Celsius)</h2>
          <p id="t2-caption"></p>
          <img id="t2-image" alt="2m temperature chart">
          <div id="t2-missing" class="missing" hidden>2m temperature chart not available for this run.</div>
        </figure>
        <figure class="card">
          <h2>2m Dew Point Temperature (Celsius)</h2>
          <p id="d2-caption"></p>
          <img id="d2-image" alt="2m dew point temperature chart">
          <div id="d2-missing" class="missing" hidden>2m dew point temperature chart not available for this run.</div>
        </figure>
      </div>
    </section>
  </div>

  <script id="manifest-data" type="application/json">__MANIFEST__</script>
  <script>
    const manifest = JSON.parse(document.getElementById('manifest-data').textContent);
    const steps = manifest.steps;
    const slider = document.getElementById('step-slider');
    const stepTitle = document.getElementById('step-title');
    const stepStart = document.getElementById('step-range-start');
    const stepEnd = document.getElementById('step-range-end');
    const runSummary = document.getElementById('run-summary');
    const thiImage = document.getElementById('thi-image');
    const riskImage = document.getElementById('risk-image');
    const t2Image = document.getElementById('t2-image');
    const d2Image = document.getElementById('d2-image');
    const thiCaption = document.getElementById('thi-caption');
    const riskCaption = document.getElementById('risk-caption');
    const t2Caption = document.getElementById('t2-caption');
    const d2Caption = document.getElementById('d2-caption');
    const t2Missing = document.getElementById('t2-missing');
    const d2Missing = document.getElementById('d2-missing');

    runSummary.textContent = `${steps.length} step${steps.length === 1 ? '' : 's'} loaded`;
    stepStart.textContent = `First step: ${String(steps[0].step_hours).padStart(3, '0')}h`;
    stepEnd.textContent = `Last step: ${String(steps[steps.length - 1].step_hours).padStart(3, '0')}h`;

    if (steps.length > 1) {
      slider.max = String(steps.length - 1);
    } else {
      slider.disabled = true;
    }

    function renderStep(index) {
      const step = steps[index];
      const stepLabel = String(step.step_hours).padStart(3, '0');
      stepTitle.textContent = `Forecast step ${stepLabel}h`;
      thiImage.src = `images/${step.thi_image}`;
      riskImage.src = `images/${step.heat_risk_image}`;
      thiCaption.textContent = `THI for step ${stepLabel}h`;
      riskCaption.textContent = `Heat stress risk for step ${stepLabel}h`;

      if (step.t2_image) {
        t2Image.hidden = false;
        t2Missing.hidden = true;
        t2Image.src = `images/${step.t2_image}`;
        t2Caption.textContent = `2t for step ${stepLabel}h`;
      } else {
        t2Image.hidden = true;
        t2Missing.hidden = false;
        t2Caption.textContent = `2t for step ${stepLabel}h`;
      }

      if (step.d2_image) {
        d2Image.hidden = false;
        d2Missing.hidden = true;
        d2Image.src = `images/${step.d2_image}`;
        d2Caption.textContent = `2d for step ${stepLabel}h`;
      } else {
        d2Image.hidden = true;
        d2Missing.hidden = false;
        d2Caption.textContent = `2d for step ${stepLabel}h`;
      }
    }

    slider.addEventListener('input', (event) => {
      renderStep(Number(event.target.value));
    });

    renderStep(0);
  </script>
</body>
</html>
"""

    return template.replace("__MANIFEST__", manifest_json).replace("__LATEST_DATE__", latest_date)


def build_site(charts_dir: Path, output_dir: Path) -> Path:
    latest_date, steps, latest_run_dir = _discover_latest_pairs(charts_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = _build_manifest(latest_date, steps)
    _copy_latest_images(latest_run_dir, steps, output_dir)

    index_path = output_dir / "index.html"
    manifest_path = output_dir / "manifest.json"

    index_path.write_text(_render_html(manifest), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return index_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build the static THI website.")
    parser.add_argument(
        "--charts-dir",
        type=Path,
        help="Directory that contains generated chart images.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory where the website should be written.",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    charts_dir = args.charts_dir or Path(settings.paths.charts_dir)
    output_dir = args.output_dir or Path(settings.paths.web_dir)

    index_path = build_site(charts_dir, output_dir)
    print(f"Wrote website: {index_path}")


if __name__ == "__main__":
    main()
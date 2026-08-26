"""Reconstruct STT recordings from timeline data and batch-replay all sermons."""
import sys, os, json, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from replay import SttRecordingItem, SermonResult, TimelineEntry
from replay import process_sermon, write_sermon_outputs, build_failure_report
from replay import build_summary, build_failure_report_md, load_config

replay_dir = 'outputs/replay'
config = load_config()
sermon_results: list[SermonResult] = []

for d in sorted(os.listdir(replay_dir), key=lambda x: int(x) if x.isdigit() else 999):
    sdir = os.path.join(replay_dir, d)
    if not os.path.isdir(sdir) or not d.isdigit():
        continue
    tl_path = os.path.join(sdir, 'timeline.json')
    if not os.path.isfile(tl_path):
        print(f"SKIP {d}: no timeline.json")
        continue
    tl = json.load(open(tl_path, 'r', encoding='utf-8'))
    if not tl:
        print(f"SKIP {d}: empty timeline")
        continue
    rlog = logging.getLogger("replay.sermon")
    rlog.handlers.clear()
    recording = []
    for e in tl:
        recording.append(SttRecordingItem(
            timestamp=e.get('timestamp', 0.0),
            raw_text=e.get('raw_transcript', ''),
            corrected_text=e.get('corrected_transcript', ''),
        ))
    rec_path = os.path.join(sdir, 'stt_recording.json')
    json.dump([{'timestamp': r.timestamp, 'raw_text': r.raw_text, 'corrected_text': r.corrected_text}
               for r in recording], open(rec_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print(f"Replaying {d} ({len(recording)} segs)...", end=' ', flush=True)
    try:
        result = process_sermon(rec_path, config, replay_dir, stt_recording=recording)
        result.name = d
        write_sermon_outputs(result, sdir)
        sermon_results.append(result)
        print(f"OK ({result.segments} segs)")
    except Exception as e:
        print(f"FAIL: {e}")

print("\nGenerating reports...")
failure_report = build_failure_report(sermon_results)
with open(os.path.join(replay_dir, "failure_report.json"), "w", encoding="utf-8") as f:
    json.dump(failure_report, f, indent=2, ensure_ascii=False)
print(f"  failure_report.json ({len(failure_report['failures'])} issues)")

summary = build_summary(sermon_results, failure_report)
with open(os.path.join(replay_dir, "summary.md"), "w", encoding="utf-8") as f:
    f.write(summary)
print(f"  summary.md ({len(sermon_results)} sermons)")

failure_md = build_failure_report_md(sermon_results)
with open(os.path.join(replay_dir, "failure_report.md"), "w", encoding="utf-8") as f:
    f.write(failure_md)
print(f"  failure_report.md")

for line in summary.split("\n")[1:6]:
    if line.startswith("-"):
        print(line)

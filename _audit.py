import json

fr = json.load(open('replay/failure_report.json','r',encoding='utf-8'))
for f in fr['failures']:
    if f['type'] == 'unusually_long_processing':
        print(f"  sermon {f['sermon']}: max_seconds={f.get('max_seconds')}, count={f['count']}")

print()
# Check per-sermon timing data
for sid in range(1,14):
    try:
        t = json.load(open(f'replay/{sid}/timings.json','r',encoding='utf-8'))
        if isinstance(t, dict):
            for k,v in t.items():
                if isinstance(v, (int,float)) and v > 5:
                    print(f"  sermon {sid}: {k}={v}")
    except:
        pass

print()
# Check references detected per sermon
print("References per sermon:")
for sid in range(1,14):
    try:
        refs = json.load(open(f'replay/{sid}/detected_references.json','r',encoding='utf-8'))
        if isinstance(refs, list):
            print(f"  sermon {sid}: {len(refs)} refs - {[r.get('reference','') if isinstance(r,dict) else str(r) for r in refs]}")
        elif isinstance(refs, dict):
            ref_list = refs.get('references', [])
            print(f"  sermon {sid}: {len(ref_list)} refs - {ref_list}")
    except:
        pass

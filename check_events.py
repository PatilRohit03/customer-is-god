import json

# Read first 10 and last 10 events
with open('events_store1_bytetrack.jsonl', 'r') as f:
    lines = f.readlines()

print(f"Total event lines: {len(lines)}")
print("\n=== FIRST 5 EVENTS ===")
for i in range(min(5, len(lines))):
    e = json.loads(lines[i].strip())
    print(f"{i+1}. visitor={e.get('visitor_id'):6s} event={e.get('event_type'):18s} camera={e.get('camera_id'):10s}")

print("\n=== LAST 5 EVENTS ===")
for i in range(max(0, len(lines)-5), len(lines)):
    e = json.loads(lines[i].strip())
    idx = i - len(lines) + 1
    print(f"{idx}. visitor={e.get('visitor_id'):6s} event={e.get('event_type'):18s} camera={e.get('camera_id'):10s}")

# Check visitor distribution
visitors = {}
for line in lines:
    e = json.loads(line.strip())
    v = e.get('visitor_id')
    if v:
        visitors[v] = visitors.get(v, 0) + 1

print(f"\n=== VISITOR DISTRIBUTION ===")
print(f"Total unique visitors: {len(visitors)}")
print(f"Top 10 most active visitors:")
for v, count in sorted(visitors.items(), key=lambda x: -x[1])[:10]:
    print(f"  {v}: {count} events")
print(f"\nVisitors with just 1 event: {sum(1 for c in visitors.values() if c == 1)}")

# Check cameras
cameras = {}
for line in lines:
    e = json.loads(line.strip())
    c = e.get('camera_id')
    if c:
        cameras[c] = cameras.get(c, 0) + 1

print(f"\n=== EVENTS BY CAMERA ===")
for c, count in sorted(cameras.items(), key=lambda x: -x[1]):
    print(f"  {c}: {count} events")

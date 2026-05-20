from engine import AgriSignalEngine

e = AgriSignalEngine()
zones = e.compute_risk_zones()
print(f"Total zones processed: {len(zones)}")
print()
for z in zones[:15]:
    print(f"{z['urgency']:8} score={z['priority_score']:5} | {z['district']:20} | {z['crop']:10} | stage={z['growth_stage']:15} | RH={z['weather']['humidity']}%")

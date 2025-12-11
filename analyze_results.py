import json

with open('muraena_results_20251211_232231.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total records: {len(data)}")
print(f"Non-empty records: {len([r for r in data if r['companyName']['text']])}\n")

# Show first 3 non-empty samples
samples = [r for r in data if r['companyName']['text']][:3]

for r in samples:
    print(f"\n{'='*80}")
    print(f"Record {r['rowNumber']}:")
    print(f"\nAllText:\n  {r['allText']}")
    print(f"\nParsed Data:")
    print(f"  Name: {r['companyName']['text']}")
    print(f"  Website: '{r['website']['text']}'")
    print(f"  Industry: {r['industry']['text']}")
    print(f"  Location: {r['location']['text']}")
    print(f"  Headcount: {r['headcount']['text']}")

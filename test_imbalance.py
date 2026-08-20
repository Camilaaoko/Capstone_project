from analytics_module.models.imbalance import detect_imbalances, find_matching_pairs, optimize_allocation, generate_allocation_plan
import time

start = time.time()
imbalances = detect_imbalances(threshold_dofs=7)
print('Detection:', time.time()-start)

start = time.time()
matches = find_matching_pairs(imbalances['overstocked'], imbalances['understocked'], None, max_distance_km=400)
print('Matching:', time.time()-start, 'matches:', len(matches))

if len(matches) > 0:
    print('Top 5 matches:')
    for _, r in matches.head(5).iterrows():
        print('  {} -> {} ({}): {:.0f} units, {:.0f}km, ROI={:.2f}, Priority={:.1f}'.format(
            r["source_facility_id"], r["dest_facility_id"], r["commodity_id"],
            r["transferable_units"], r["distance_km"], r["roi"], r["priority_score"]
        ))

start = time.time()
allocation = optimize_allocation(matches, budget_kes=5000000, max_distance_km=300)
print('Optimization:', time.time()-start, 'recommendations:', len(allocation))
print('Total cost:', allocation['estimated_transport_cost'].sum())
print('Total units:', allocation['transferable_units'].sum())

plan = generate_allocation_plan(allocation)
rec = plan[plan['recommendation'] == 'RECOMMEND']
print('Final plan:', len(rec), 'recommendations')
print('Total units:', rec['transferable_units'].sum())
print('Total value:', rec['transfer_value'].sum())
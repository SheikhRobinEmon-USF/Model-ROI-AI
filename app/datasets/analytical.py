"""Original synthetic problems with checkable intermediate and final answers."""
from app.datasets.validate import EvalCase

PROBLEMS = {
    "Math": [
        ("A service handles 400 tickets. It resolves 70% automatically. Each remaining ticket takes 6 minutes. Give manual_tickets and staff_hours as numbers.", {"manual_tickets":120,"staff_hours":12}),
        ("A shipment has 80 units costing $12 each. Ten are damaged. Sell every good unit for $18. Give revenue and profit in dollars.", {"revenue":1260,"profit":300}),
    ],
    "Coding": [
        ("Trace this Python function: def f(xs): return [x for i,x in enumerate(xs) if x not in xs[:i]]. Give result for [3,1,3,2,1] and worst_case_time as one of O(n), O(n^2).", {"result":[3,1,2],"worst_case_time":"O(n^2)"}),
        ("A binary search on sorted values sets lo = mid when a[mid] < target, using floor midpoint and a while lo <= hi loop. It stalls. Give replacement_lo as a compact expression without spaces and smallest_stalling_length for a nonempty array when target exceeds every value.", {"replacement_lo":"mid+1","smallest_stalling_length":1}),
    ],
    "Case study": [
        ("A team has 10 hours. Projects A, B, C take 6, 5, 4 hours and save 90, 80, 65 dollars. Choose whole projects once to maximize savings. Give projects in alphabetical order and savings.", {"projects":["A","C"],"savings":155}),
        ("A clinic needs 72 follow-ups in one shift. Three staff each process 18. Each temporary worker can process 12. Find the minimum temporary workers and unused capacity after meeting demand. Give temps and unused_slots.", {"temps":2,"unused_slots":6}),
    ],
}

def analytical_cases():
    return [EvalCase(case_id=f"{group.split()[0].lower()}-{i}",task_type=group.lower().replace(" ","_"),
                     input=question+" Return only one JSON object with the requested keys.",
                     expected=answer,grader="json_exact",dataset_version="analytical-v1",
                     source_license="original_synthetic",split="dev",review_status="pending_human_review")
            for group, problems in PROBLEMS.items() for i,(question,answer) in enumerate(problems,1)]

import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import json
import os

def build_rect_strip_packing_model(instance_id: str):
    """
    instance_id: e.g. "4_1"  (will load strip_packing_rectangle_4_1.json)
    """
    # Get the absolute path of the current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the JSON file, Modify the path number for different scheduling data
    filename = f"strip_packing_rectangle_{instance_id}.json"
    json_file_path = os.path.abspath(
        os.path.join(script_dir, "..", "packing_data", filename)
    )

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    strip_width = data["strip_width"]
    rec_ids     = [rec["index"] for rec in data["rectangles"]]
    widths      = {rec["index"]: rec["width"]  for rec in data["rectangles"]}
    lengths     = {rec["index"]: rec["length"] for rec in data["rectangles"]}

    # Create a concrete model
    m = pyo.ConcreteModel(name="Rectangles strip packing")

    # sets & parameters
    m.rectangles   = pyo.Set(initialize=rec_ids, ordered=True) # Set of rectangles
    m.rect_width   = pyo.Param(m.rectangles, initialize=widths) # Width of each rectangle
    m.rect_length  = pyo.Param(m.rectangles, initialize=lengths) # Length of each rectangle
    m.strip_width  = pyo.Param(initialize=strip_width) # Available width of the strip
    
    # upperbound on length (default is sum of lengths of rectangles)
    m.max_length = pyo.Param(
        initialize=sum(lengths.values()),
        doc="Loose upper bound on total strip length",
    )

    # x (length) and y (width) coordinates of each of the rectangles
    m.x = pyo.Var(
        m.rectangles,
        bounds=(0, m.max_length),
        doc="rectangle corner x-position (position down length)",
    )
    
    def w_bounds(m, i):
        return (0, m.strip_width - m.rect_width[i])

    m.y = pyo.Var(
        m.rectangles,
        bounds=w_bounds,
        doc="rectangle corner y-position (position across width)",
    )

    m.strip_length = pyo.Var(within=pyo.NonNegativeReals, doc="Length of strip required.")

    def rec_pairs_filter(m, i, j):
        return i < j
    
    m.overlap_pairs = pyo.Set(
        initialize=m.rectangles * m.rectangles,
        dimen=2,
        filter=rec_pairs_filter,
        doc="set of possible rectangle conflicts",
    )

    # Constraints
    @m.Constraint(m.rectangles)
    def strip_ends_after_last_rec(m, i):
        return m.strip_length >= m.x[i] + m.rect_length[i]

    # Objective
    m.total_length = pyo.Objective(expr=m.strip_length, doc="Minimize length")

    # Disjunctions
    @m.Disjunction(
        m.overlap_pairs,
        doc="Make sure that none of the rectangles on the strip overlap in "
        "either the x or y dimensions.",
    )
    def no_overlap(m, i, j):
        return [
            m.x[i] + m.rect_length[i] <= m.x[j],  # i before j
            m.x[j] + m.rect_length[j] <= m.x[i],  # j before i
            m.y[i] + m.rect_width[i] <= m.y[j],   # i above j
            m.y[j] + m.rect_width[j] <= m.y[i],   # j above i
        ]
    return m

if __name__ == "__main__":
    model = build_rect_strip_packing_model("5_1")
    # Transform the model to a mixed-integer programming (MIP) model
    pyo.TransformationFactory('gdp.hull').apply_to(model)

    # Solve the model
    solver = pyo.SolverFactory("gurobi")
    results = solver.solve(model, tee=True)

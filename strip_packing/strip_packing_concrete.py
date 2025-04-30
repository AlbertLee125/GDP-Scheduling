import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import json
import os

def build_rect_strip_packing_model():
    """Build the strip packing model."""
    model = pyo.ConcreteModel(name="Rectangles strip packing")
    model.rectangles = pyo.Set(ordered=True, initialize=[0, 1, 2, 3])

    # Width and Length of each rectangle
    model.rect_width = pyo.Param(model.rectangles, initialize={0: 6, 1: 3, 2: 4, 3: 2})
    model.rect_length = pyo.Param(model.rectangles, initialize={0: 6, 1: 8, 2: 5, 3: 3})

    model.strip_width = pyo.Param(initialize=10, doc="Available width of the strip")

    # upperbound on length (default is sum of lengths of rectangles)
    model.max_length = pyo.Param(
        initialize=sum(model.rect_length[i] for i in model.rectangles),
        doc="maximum length of the strip (if all rectangles were arranged "
        "lengthwise)",
    )

    # x (length) and y (width) coordinates of each of the rectangles
    model.x = pyo.Var(
        model.rectangles,
        bounds=(0, model.max_length),
        doc="rectangle corner x-position (position down length)",
    )

    def w_bounds(m, i):
        return (0, m.strip_width - m.rect_width[i])

    model.y = pyo.Var(
        model.rectangles,
        bounds=w_bounds,
        doc="rectangle corner y-position (position across width)",
    )

    model.strip_length = pyo.Var(within=pyo.NonNegativeReals, doc="Length of strip required.")

    def rec_pairs_filter(model, i, j):
        return i < j

    model.overlap_pairs = pyo.Set(
        initialize=model.rectangles * model.rectangles,
        dimen=2,
        filter=rec_pairs_filter,
        doc="set of possible rectangle conflicts",
    )

    @model.Constraint(model.rectangles)
    def strip_ends_after_last_rec(model, i):
        return model.strip_length >= model.x[i] + model.rect_length[i]

    model.total_length = pyo.Objective(expr=model.strip_length, doc="Minimize length")

    @model.Disjunction(
        model.overlap_pairs,
        doc="Make sure that none of the rectangles on the strip overlap in "
        "either the x or y dimensions.",
    )
    def no_overlap(m, i, j):
        return [
            m.x[i] + m.rect_length[i] <= m.x[j],  # i left of j
            m.x[j] + m.rect_length[j] <= m.x[i],  # i right of j
            m.y[i] + m.rect_width[i] <= m.y[j],  # i below j
            m.y[j] + m.rect_width[j] <= m.y[i],  # i above j
        ]

    return model

if __name__ == "__main__":
    model = build_rect_strip_packing_model()
    # Solve the model
    pyo.TransformationFactory('gdp.bigm').apply_to(model)
    opt = pyo.SolverFactory('gurobi')
    results = opt.solve(model, tee=True)
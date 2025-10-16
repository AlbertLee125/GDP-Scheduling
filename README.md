# GLDP Reaggregated Hull Reformulation

This repository contains implementations and benchmarks for Generalized Disjunctive Programming (GDP) formulations with a focus on the reaggregated hull reformulation strategy. The code demonstrates two application domains: **single-unit scheduling** and **strip packing** problems.

## Overview

Generalized Disjunctive Programming (GDP) is a powerful modeling paradigm for optimization problems with logical disjunctions. This repository compares different GDP reformulation approaches:

- **BigM reformulation** (`gdp.bigm`)
- **Hull reformulation** (`gdp.hull`)
- **Reaggregated Hull reformulation** (manually reformulated MINLP)

The reaggregated hull reformulation is a tighter convex relaxation that can improve solver performance for certain problem classes.

## Repository Structure

```
.
├── model/                          # Scheduling model implementations
│   ├── single_unit_sequencing_gp.py          # General Precedence GDP
│   ├── single_unit_sequencing_gp_reagg.py    # General Precedence with Reaggregated Hull
│   ├── single_unit_sequencing_ip.py          # Immediate Precedence formulations
│   └── single_unit_sequencing_ts.py          # Time Slots formulations
├── strip_packing/                  # Strip packing model implementations
│   ├── strip_packing.py                      # Traditional GDP formulation
│   ├── strip_packing_altered.py              # Alternative formulations
│   └── strip_packing_trespacolis.py          # Trespalacios formulations
├── scheduling_data/                # Test instances for scheduling problems
│   └── scheduling_data_*.json               # JSON files with job data
├── packing_data/                   # Test instances for strip packing problems
├── results/                        # Benchmark results (JSON and text)
├── figures/                        # Generated performance plots
├── main_benchmark.py               # Main benchmarking script for scheduling
├── strip_benchmarking.py           # Benchmarking script for strip packing
├── performance_profile_scheduling.py  # Generate performance profiles
└── plot*.py                        # Various plotting utilities
```

## Installation

### Requirements

- Python 3.7+
- Pyomo
- A MINLP solver (Gurobi, SCIP, or HiGHS)
- NumPy
- Matplotlib (for visualization)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/SECQUOIA/GLDP-reaggregated-hull.git
cd GLDP-reaggregated-hull
```

2. Install dependencies:
```bash
pip install pyomo numpy matplotlib
```

3. Install a solver (e.g., Gurobi with a valid license):
```bash
pip install gurobipy
```

## Usage

### Running Scheduling Benchmarks

The `main_benchmark.py` script benchmarks multiple scheduling formulations:

```bash
python main_benchmark.py
```

This will:
- Test scheduling instances 1-10
- Run 4 MILP formulations and 2 GDP formulations (with BigM and Hull transformations)
- Apply a 900-second time limit per solve
- Save results to `results/benchmark_results_overall_1to10_900.json`

### Running Strip Packing Benchmarks

```bash
python strip_benchmarking.py
```

### Generating Performance Profiles

```bash
python performance_profile_scheduling.py
python performance_profile_gdp.py
```

## Problem Formulations

### 1. Single-Unit Sequencing (Scheduling)

Given a set of jobs with:
- Processing times (`p_i`)
- Release times (`r_i`)
- Due dates (`d_i`)

**Objective**: Minimize makespan while respecting temporal constraints.

#### Formulation Types:

**General Precedence (GP)**
- Uses precedence variables to determine job ordering
- GDP version (`single_unit_sequencing_gp.py`)
- Reaggregated Hull MINLP (`single_unit_sequencing_gp_reagg.py`)

**Immediate Precedence (IP)**
- Each job immediately follows the previous
- BigM version (`build_single_unit_sequencing_Immediate_Precedence_BigM`)
- Hull Reformulation version (`build_single_unit_sequencing_Immediate_Precedence_HR`)

**Time Slots (TS)**
- Discretizes time into slots
- GDP version with BigM and Hull transformations

### 2. Strip Packing

**Problem**: Pack rectangles into a strip of fixed width, minimizing the strip length.

Given:
- Strip width (fixed)
- Set of rectangles with dimensions

**Objective**: Minimize strip length while ensuring no rectangles overlap.

Multiple formulations are implemented with different tightness properties.

## Benchmark Results

Benchmark results are stored in the `results/` directory with:
- Solve times
- Objective values
- Termination conditions
- Model statistics

Example metrics compared:
- **GP_RHR**: General Precedence with Reaggregated Hull Reformulation
- **GP_BM**: General Precedence with BigM
- **GP_HR**: General Precedence with Hull Reformulation
- **IP_BM**: Immediate Precedence with BigM
- **IP_HR**: Immediate Precedence with Hull Reformulation
- **TS_BM**: Time Slots with BigM
- **TS_HR**: Time Slots with Hull Reformulation

Performance profiles visualize solver efficiency across multiple instances.

## Key Files

- **`main_benchmark.py`**: Primary entry point for scheduling benchmarks
- **`model/single_unit_sequencing_gp_reagg.py`**: Implements the reaggregated hull reformulation
- **`performance_profile_scheduling.py`**: Generates performance comparison plots
- **`scheduling_data/`**: Contains 10 test instances for scheduling problems

## Results Interpretation

The repository includes pre-generated results comparing:
- Different reformulation strategies
- Multiple solvers (Gurobi, SCIP, HiGHS)
- Various time limits (900s, 1800s)

Check the `results/` directory and generated PDFs for detailed performance comparisons.

## Contributing

This is a research repository. For questions or collaboration, please open an issue.

## License

Please check with the repository maintainers for licensing information.

## References

The reaggregated hull reformulation is based on research in GDP and disjunctive programming. For theoretical background, refer to relevant publications on GDP reformulations and convex hull representations.
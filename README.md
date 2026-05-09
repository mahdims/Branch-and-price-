# Branch-and-Price for the Equitable Relief Routing Problem

A Branch-and-Price algorithm for solving the **Equitable Vehicle Routing Problem** in humanitarian relief distribution. The solver optimizes two competing objectives:

1. **Efficiency** — Minimize total unmet demand across affected nodes
2. **Equity** — Minimize the Gini index to ensure fair distribution of relief supplies

## Problem Description

After a disaster, limited relief supplies must be distributed across affected areas using a fleet of capacitated vehicles. This solver finds vehicle routes and delivery plans that balance minimizing unmet demand with ensuring equitable service across all nodes.

The multi-objective function combines:
- **Unmet demand** — total shortage across all nodes
- **Gini index** — measure of inequality in demand satisfaction (weighted by `Lambda`)
- **Travel distance** — total route distance penalty (weighted by `Gamma`)

## Project Structure

```
├── Source/
│   ├── Run_BnP.py                 # Main entry point — runs Branch-and-Price
│   ├── Pareto_finder.py           # Bi-objective Pareto frontier computation
│   ├── read_results.py            # Query and display results
│   ├── BnP/                       # Branch-and-Bound tree search
│   │   ├── BnP.py                 #   Core B&B algorithm
│   │   ├── Node.py                #   B&B tree node
│   │   ├── Master_int.py          #   Integer master problem
│   │   └── Cuts.py                #   Valid inequalities / cuts
│   ├── Column_Gen/                # Column Generation
│   │   ├── ColumnGeneration.py    #   CG main loop
│   │   ├── Master.py              #   Restricted master problem (LP)
│   │   └── Sub_model.py           #   Subproblem model
│   ├── Pricing/                   # Pricing subproblem solvers
│   │   ├── Pricing_GRASP.py       #   GRASP heuristic pricing
│   │   └── Path.py                #   Route/path representation
│   ├── Initial_Alg/               # Initial feasible solution heuristics
│   │   ├── Alg.py                 #   Sweep, greedy, CW heuristics
│   │   ├── Builder.py             #   Greedy and Clarke-Wright builders
│   │   ├── Solution.py            #   Solution data structure
│   │   ├── TSP_Solver.py          #   TSP improvement procedures
│   │   └── TSP_model.py           #   TSP MIP formulation
│   ├── labeling_Alg/              # Label-setting algorithm (via cspy)
│   │   └── labeling.py            #   Elementary shortest path pricing
│   ├── Mathematical_Models/       # Direct MIP formulations (benchmarks)
│   │   ├── Model1.py              #   Arc-based formulation
│   │   ├── Model1_V2.py           #   Improved arc-based formulation
│   │   ├── Model2.py              #   Alternative formulation
│   │   ├── Runner.py              #   Run models on instances
│   │   ├── Runner_Capacity.py     #   Capacity sensitivity analysis
│   │   ├── Runner_equity.py       #   Equity-focused runs
│   │   └── Runner_pareto.py       #   Pareto frontier via models
│   └── utils/                     # Utilities
│       ├── utils.py               #   Data loading, objective calculation
│       ├── Route_delivery.py      #   Route-delivery data structure
│       ├── Seq.py                 #   Sequence operations
│       ├── Obj_Calc.py            #   Objective function helpers
│       └── plots.py               #   Visualization utilities
├── Data/
│   ├── Van/                       # Van (Turkey) test instances
│   ├── Kartal/                    # Kartal, Istanbul test instances
│   └── Tehran/                    # Tehran test instances
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.7+
- [Gurobi Optimizer](https://www.gurobi.com/) with a valid license

### Installation

```bash
git clone https://github.com/mahdims/Branch-and-price-.git
cd Branch-and-price-
pip install -r requirements.txt
```

### Usage

#### Run Branch-and-Price

Edit `Source/Run_BnP.py` to select the case, instance size, and instance index, then run:

```bash
cd Source
python Run_BnP.py
```

Configuration parameters in `Run_BnP.py`:
- `Case_name` — `"Van"` or `"Kartal"`
- `NN` — Number of nodes (e.g., 13, 15, 30, 60)
- `inst` — Instance index
- `MaxTime` — Time limit in seconds (default: 7200)

The number of vehicles `M` is determined by the node count: `{15: 3, 30: 5, 60: 9, 13: 3}`.

Results are appended to `Data/Results/LOG.txt`.

#### Run Pareto Frontier Analysis

```bash
cd Source
python Pareto_finder.py
```

Computes the Pareto frontier by varying the distance epsilon constraint to explore equity vs. efficiency tradeoffs.

#### Run Direct MIP Models (Benchmarks)

```bash
cd Source/Mathematical_Models
python Runner.py
```

### Test Instances

Instances follow the naming convention `{Case}_{Nodes}_{Vehicles}_{Index}`:

| Case   | Nodes | Vehicles | Instance Types                        |
|--------|-------|----------|---------------------------------------|
| Van    | 15    | 3        | T (1-5), VT (6-10), VTL (11-15)      |
| Van    | 30    | 5        | T (1-5), VT (6-10), VTL (11-15)      |
| Van    | 60    | 9        | T (1-5), VT (6-10), VTL (11-15)      |
| Kartal | 13    | 3        | T (1-10), VT (11-20), VTL (21-30)    |

Instance types represent different demand/supply tightness levels: **T** (tight), **VT** (very tight), **VTL** (very tight large).

## Algorithm Overview

The Branch-and-Price algorithm combines:

1. **Column Generation** — Solves a linear relaxation of the master problem by dynamically generating promising vehicle routes (columns). The pricing subproblem identifies routes with negative reduced cost.

2. **Branch-and-Bound** — Searches the solution space by branching on fractional edge variables to enforce integrality, using strong branching for variable selection.

3. **Pricing Strategies**:
   - **Gurobi MIP** — Exact pricing via integer programming
   - **GRASP Heuristic** — Fast approximate pricing
   - **Label-Setting** — Elementary shortest path algorithm (via `cspy`)

4. **Initial Solutions** — Feasible starting solutions from Sweep, Clarke-Wright savings, and greedy construction heuristics, improved with TSP local search.

## Author

**Mahdi Mostajabdaveh**
- Email: Mahdi.ms86@gmail.com
- GitHub: [github.com/mahdims](https://github.com/mahdims)

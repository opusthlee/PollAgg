# Implementation Plan: V2 Advanced Modular Engine

This plan outlines the integration of four advanced statistical methodologies into the `Stats-Optimizer` engine. To ensure maximum flexibility, these features will be implemented as toggleable modules, allowing the user to turn them on or off depending on the specific issue, data availability, or desired complexity.

## User Review Required

> [!IMPORTANT]
> Adding correlated errors requires a covariance matrix, and smoothing requires a time-series approach. These are mathematically heavier. Are you comfortable with us implementing simplified versions of these (e.g., Moving Average for smoothing, simple correlation factors for errors) as a starting point?

## Proposed Changes

### 1. Fundamentals Prior (구조적 펀더멘털 사전 확률)
We will expand the existing Bayesian strategy to accept multi-dimensional priors (e.g., economic growth, incumbency).
#### [MODIFY] [engine/strategies.py](file:///Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer/engine/strategies.py)
- Enhance `BayesianAdjustmentStrategy` to accept a `fundamentals_score` alongside polling priors.

### 2. Time-Series Smoothing (시계열 곡선 스무딩)
Instead of just returning point-in-time averages, we will add a module that processes the raw data into a continuous, smoothed trend line.
#### [NEW] [engine/processors.py](file:///Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer/engine/processors.py)
- Create `TimeSeriesSmoother` class.
- Implement a configurable Moving Average (MA) or Exponential Smoothing algorithm.

### 3. Correlated Polling Errors (상관된 여론조사 오차)
We will upgrade the Monte Carlo simulation to inject correlated systemic errors, increasing the realism of the "fat tails" in our predictions.
#### [MODIFY] [engine/election.py](file:///Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer/engine/election.py)
- Update `simulate_win_probability` to accept a `correlation_factor`. If toggled on, the simulation will shift both candidates' distributions simultaneously to simulate a "polling miss" across the board.

### 4. Sensitivity Analysis & Forward Checking (민감도 스트레스 테스트)
A new evaluation module to test model fragility.
#### [NEW] [engine/evaluators.py](file:///Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer/engine/evaluators.py)
- Create `StressTester` class.
- Add `run_shock_scenario(shock_value)` to simulate a sudden 10% swing in tomorrow's polls and measure the model's reaction.

### 5. Configurable Orchestrator (Toggling System)
Update the main entry point to allow easy toggling of these features.
#### [MODIFY] [main.py](file:///Users/up_main/Desktop/T_Antigravity/dev/stats-optimizer/main.py)
- Update `StatsOptimizer` initialization to accept a `config` dictionary:
  `{"use_smoothing": True, "use_correlated_errors": True, "run_stress_test": False}`

---

## Verification Plan
1. **Toggle Test**: Run the pipeline with all features OFF, then all features ON, ensuring the outputs differ logically without crashing.
2. **Stress Test Output**: Verify that `evaluators.py` outputs a clear report showing how much the win probability changed under a hypothetical shock.

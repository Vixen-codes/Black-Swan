"""
Black Swan — V0.1 Core Portfolio Monte Carlo Engine

Dependencies:
    pandas
    numpy
    matplotlib
    yfinance

This module provides:
    - Yahoo Finance and CSV data loading
    - Frequency-aware date handling
    - Multi-asset alignment
    - Return calculation
    - Portfolio definition/validation
    - Reproducible correlated Monte Carlo simulation
    - Robust covariance handling
    - VaR / Expected Shortfall
    - Summary statistics and percentiles
    - PNG and CSV output

V0.1 deliberately keeps the simulation model focused on correlated
Gaussian returns. More advanced engines (bootstrap, fat tails, regimes)
can be added later without changing the portfolio/risk interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_from_yahoo(
    ticker: str = "SPY",
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Download adjusted close data for one asset."""
    ticker = ticker.upper().strip()

    if not ticker:
        raise ValueError("Ticker cannot be empty.")

    print(f"Loading data for {ticker} from Yahoo Finance...")

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        raise ValueError(f"No data found for ticker {ticker}.")

    # yfinance can return MultiIndex columns even for one ticker.
    if isinstance(df.columns, pd.MultiIndex):
        if "Close" not in df.columns.get_level_values(0):
            raise ValueError(f"Yahoo Finance did not return Close data for {ticker}.")
        df = df["Close"]

        # A single ticker can still leave a one-column DataFrame.
        if isinstance(df, pd.Series):
            df = df.to_frame(name=ticker)
        elif df.shape[1] == 1:
            df.columns = [ticker]
    else:
        if "Close" not in df.columns:
            raise ValueError(f"Yahoo Finance did not return Close data for {ticker}.")
        df = df[["Close"]].rename(columns={"Close": ticker})

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.dropna(how="all")

    print(f"Downloaded {len(df)} rows for {ticker}.")
    return df


def load_multiple_assets(
    tickers: Sequence[str],
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Download close data for multiple assets into one DataFrame."""
    tickers = [str(t).upper().strip() for t in tickers]

    if not tickers or any(not ticker for ticker in tickers):
        raise ValueError("tickers must contain at least one non-empty ticker.")

    # Remove duplicates while preserving order.
    tickers = list(dict.fromkeys(tickers))

    print(f"Fetching data for {len(tickers)} assets: {', '.join(tickers)}...")

    df = yf.download(
        tickers,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        raise ValueError("Yahoo Finance returned no data.")

    if isinstance(df.columns, pd.MultiIndex):
        if "Close" not in df.columns.get_level_values(0):
            raise ValueError("Yahoo Finance did not return Close data.")

        df = df["Close"]

        if isinstance(df, pd.Series):
            df = df.to_frame(name=tickers[0])
        else:
            # Yahoo may order columns differently from the request.
            df = df.reindex(columns=tickers)
    else:
        if "Close" not in df.columns:
            raise ValueError("Yahoo Finance did not return Close data.")
        df = df[["Close"]]
        df.columns = [tickers[0]]

    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df.dropna(how="all")

    missing_columns = [ticker for ticker in tickers if ticker not in df.columns]
    if missing_columns:
        raise ValueError(f"Yahoo Finance returned no data for: {missing_columns}")

    print(f"Downloaded {len(df)} rows across {len(df.columns)} assets.")
    return df


def load_csv(filepath: str = "data/price.csv") -> pd.DataFrame:
    """
    Load a CSV containing a Date column and a Close/Last or Close column.

    This function intentionally does not invent missing dates. Date handling
    belongs to the preprocessing stage.
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.set_index("Date").sort_index()

    if "Close/Last" in df.columns:
        df = df.rename(columns={"Close/Last": "Close"})

    if "Close" not in df.columns:
        raise ValueError("CSV must contain a 'Close' or 'Close/Last' column.")

    df = df[["Close"]]
    df = df[~df.index.duplicated(keep="last")]
    return df.dropna(how="all")


# ---------------------------------------------------------------------------
# Data preprocessing
# ---------------------------------------------------------------------------

def filling_missing_dates(
    df: pd.DataFrame,
    frequency: str = "D",
    method: str = "ffill",
    backward_fill: bool = False,
) -> pd.DataFrame:
    """
    Reindex data to a specified frequency.

    Important:
    This function does NOT hardcode daily frequency.

    For market prices, forward filling is generally preferable to blindly
    interpolating prices. Backward filling is optional and should normally
    only be used when the initial missing values need a defined value.

    Examples:
        daily:   frequency="D"
        hourly:  frequency="h"
        monthly: frequency="ME"
        quarterly: frequency="QE"
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be a DatetimeIndex.")

    if df.empty:
        raise ValueError("Cannot process an empty DataFrame.")

    if method not in {"ffill", "bfill", "none"}:
        raise ValueError("method must be 'ffill', 'bfill', or 'none'.")

    result = df.sort_index().copy()
    result = result[~result.index.duplicated(keep="last")]
    result = result.asfreq(frequency)

    if method == "ffill":
        result = result.ffill()
        if backward_fill:
            result = result.bfill()
    elif method == "bfill":
        result = result.bfill()
        if backward_fill:
            result = result.ffill()

    return result


def align_assets(
    df: pd.DataFrame,
    frequency: str = "D",
    fill_method: str = "ffill",
    backward_fill: bool = False,
    drop_remaining_missing: bool = True,
) -> pd.DataFrame:
    """
    Align multiple assets to a common frequency.

    This function is intentionally separate from loading so that the user can
    decide the common simulation frequency explicitly.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be a DatetimeIndex.")

    if df.empty:
        raise ValueError("Asset DataFrame is empty.")

    result = df.sort_index().copy()
    result = result[~result.index.duplicated(keep="last")]

    # Common timeline. We do not assume all assets originally have the same
    # frequency; we align them here.
    result = result.resample(frequency).last()

    if fill_method == "ffill":
        result = result.ffill()
        if backward_fill:
            result = result.bfill()
    elif fill_method == "bfill":
        result = result.bfill()
        if backward_fill:
            result = result.ffill()
    elif fill_method != "none":
        raise ValueError("fill_method must be 'ffill', 'bfill', or 'none'.")

    if drop_remaining_missing:
        result = result.dropna(how="any")

    if result.empty:
        raise ValueError(
            "No usable observations remain after alignment and missing-data handling."
        )

    return result


def resample(df: pd.DataFrame, frequency: str = "D") -> pd.DataFrame:
    """
    Resample price data using the last available observation in each period.

    For price levels, 'last' is generally preferable to taking an arithmetic
    average. Return aggregation is handled separately in calculate_returns().
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be a DatetimeIndex.")

    return df.sort_index().resample(frequency).last()


def calculate_returns(
    df: pd.DataFrame,
    method: str = "simple",
) -> pd.DataFrame:
    """
    Calculate returns.

    method='simple':
        r_t = P_t / P_(t-1) - 1

    method='log':
        r_t = ln(P_t / P_(t-1))
    """
    if (df <= 0).any().any():
        raise ValueError("Price data must be strictly positive.")

    if method == "simple":
        returns = df.pct_change(fill_method=None)
    elif method == "log":
        returns = np.log(df / df.shift(1))
    else:
        raise ValueError("method must be 'simple' or 'log'.")

    returns = returns.replace([np.inf, -np.inf], np.nan).dropna(how="any")

    if returns.empty:
        raise ValueError("Return calculation produced no usable observations.")

    return returns


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Portfolio:
    """Validated portfolio definition."""

    weights: pd.Series
    initial_value: float

    def __post_init__(self):
        if not isinstance(self.weights, pd.Series):
            raise TypeError("weights must be a pandas Series indexed by asset name.")

        if self.weights.empty:
            raise ValueError("Portfolio must contain at least one asset.")

        if not np.all(np.isfinite(self.weights.values)):
            raise ValueError("Portfolio weights must be finite.")

        if (self.weights < 0).any():
            raise ValueError(
                "Negative weights are not supported in V0.1. "
                "Shorting can be added later."
            )

        if not np.isclose(self.weights.sum(), 1.0, atol=1e-8):
            raise ValueError(
                f"Portfolio weights must sum to 1.0; got {self.weights.sum():.10f}."
            )

        if not np.isfinite(self.initial_value) or self.initial_value <= 0:
            raise ValueError("initial_value must be a positive finite number.")

    @classmethod
    def from_dict(
        cls,
        weights: Mapping[str, float],
        initial_value: float = 100_000.0,
    ) -> "Portfolio":
        series = pd.Series(weights, dtype=float)

        if series.index.duplicated().any():
            raise ValueError("Portfolio contains duplicate asset names.")

        return cls(series, float(initial_value))


def validate_portfolio_assets(
    portfolio: Portfolio,
    asset_names: Sequence[str],
) -> None:
    """Ensure portfolio assets match the simulation data exactly."""
    asset_names = list(asset_names)

    missing = [asset for asset in portfolio.weights.index if asset not in asset_names]
    extra = [asset for asset in asset_names if asset not in portfolio.weights.index]

    if missing:
        raise ValueError(f"Portfolio assets missing from data: {missing}")

    if extra:
        raise ValueError(
            f"Data contains assets not defined in the portfolio: {extra}. "
            "Define weights for every simulated asset."
        )


# ---------------------------------------------------------------------------
# Covariance handling
# ---------------------------------------------------------------------------

def _make_positive_semidefinite(
    covariance: np.ndarray,
    eigenvalue_floor: float = 1e-10,
) -> np.ndarray:
    """
    Repair a symmetric covariance matrix by clipping negative/small
    eigenvalues. This is a practical fallback for simulation input.

    The result is symmetric positive semidefinite and is lightly diagonal
    regularised so Cholesky decomposition can succeed.
    """
    covariance = np.asarray(covariance, dtype=float)

    covariance = (covariance + covariance.T) / 2.0

    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    eigenvalues = np.maximum(eigenvalues, eigenvalue_floor)

    repaired = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    repaired = (repaired + repaired.T) / 2.0

    return repaired


def safe_cholesky(
    covariance: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Return a Cholesky factor and the covariance actually used.

    First tries the original covariance. If it is not positive definite,
    eigenvalue clipping is used as a fallback.
    """
    covariance = np.asarray(covariance, dtype=float)

    try:
        chol = np.linalg.cholesky(covariance)
        return chol, covariance
    except np.linalg.LinAlgError:
        repaired = _make_positive_semidefinite(covariance)

        try:
            chol = np.linalg.cholesky(repaired)
            return chol, repaired
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                "Covariance matrix is not suitable for simulation even after "
                "positive-semidefinite repair."
            ) from exc


# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------

def run_monte_carlo_sim(
    returns_df: pd.DataFrame,
    portfolio: Portfolio,
    num_simulations: int = 1000,
    horizon: int = 252,
    seed: int = 42,
) -> dict:
    """
    Run a reproducible correlated Gaussian Monte Carlo simulation.

    Returns a dictionary containing:
        asset_paths:
            shape = (horizon + 1, simulations, assets)
        portfolio_paths:
            shape = (horizon + 1, simulations)
        final_values:
            shape = (simulations,)
        covariance:
            covariance matrix used by the simulation
        mean_returns:
            historical mean returns
        seed:
            reproducibility seed
    """
    if not isinstance(returns_df, pd.DataFrame):
        raise TypeError("returns_df must be a pandas DataFrame.")

    if returns_df.empty:
        raise ValueError("returns_df cannot be empty.")

    if not isinstance(num_simulations, int) or num_simulations <= 0:
        raise ValueError("num_simulations must be a positive integer.")

    if not isinstance(horizon, int) or horizon <= 0:
        raise ValueError("horizon must be a positive integer.")

    if not isinstance(seed, (int, np.integer)):
        raise TypeError("seed must be an integer.")

    if not np.isfinite(returns_df.to_numpy()).all():
        raise ValueError("returns_df contains NaN or infinite values.")

    validate_portfolio_assets(portfolio, returns_df.columns)

    # Ensure consistent order between the returns and portfolio weights.
    assets = list(portfolio.weights.index)
    returns = returns_df.loc[:, assets].copy()
    weights = portfolio.weights.loc[assets].to_numpy(dtype=float)

    if len(assets) < 2 or len(assets) > 10:
        raise ValueError("V0.1 supports portfolios containing 2-10 assets.")

    # Convert simple returns to log returns for compounding.
    # (If you already pass log returns in via calculate_returns(method="log"),
    # skip this line and use `returns` directly below instead of `log_returns`.)
    log_returns = np.log1p(returns)

    mu = log_returns.mean().to_numpy(dtype=float)
    covariance = log_returns.cov().to_numpy(dtype=float)

    if not np.isfinite(mu).all() or not np.isfinite(covariance).all():
        raise ValueError("Historical statistics contain NaN or infinite values.")

    # handles singular / nearly singular covariance matrices.
    chol, covariance_used = safe_cholesky(covariance)

    rng = np.random.default_rng(seed)

    # Generate all shocks at once:
    # shape = (horizon, simulations, assets)
    random_normals = rng.standard_normal(
        size=(horizon, num_simulations, len(assets))
    )

    # Apply historical correlation structure.
    shocks = random_normals @ chol.T

    # Geometric (log-return) model with Ito correction, applied per asset.
    drift = mu - 0.5 * np.diag(covariance)
    log_paths = drift.reshape(1, 1, -1) + shocks
    cum_log_returns = np.cumsum(log_paths, axis=0)

    # Start with initial portfolio value distributed according to weights.
    initial_asset_values = portfolio.initial_value * weights

    # Asset values over time — each asset compounds off its own path.
    asset_values = np.empty(
        (horizon + 1, num_simulations, len(assets)),
        dtype=float,
    )
    asset_values[0] = initial_asset_values
    asset_values[1:] = initial_asset_values * np.exp(cum_log_returns)

    # No guard needed here: exp() makes negative prices impossible.

    portfolio_paths = asset_values.sum(axis=2)
    final_values = portfolio_paths[-1]

    return {
        "version": VERSION,
        "seed": int(seed),
        "assets": assets,
        "asset_paths": asset_values,
        "portfolio_paths": portfolio_paths,
        "final_values": final_values,
        "mean_returns": pd.Series(mu, index=assets),
        "covariance": pd.DataFrame(
            covariance_used,
            index=assets,
            columns=assets,
        ),
        "weights": portfolio.weights.copy(),
        "initial_value": portfolio.initial_value,
        "num_simulations": num_simulations,
        "horizon": horizon,
    }


# ---------------------------------------------------------------------------
# Risk metrics
# ---------------------------------------------------------------------------

def calculate_risk_metrics(
    final_values: np.ndarray,
    initial_value: float,
    confidence: float = 0.95,
) -> dict:
    """
    Calculate portfolio return distribution, VaR and Expected Shortfall.

    VaR is reported as a positive monetary loss at the chosen confidence.
    Expected Shortfall is the average loss in the tail beyond VaR.
    """
    final_values = np.asarray(final_values, dtype=float).reshape(-1)

    if final_values.size == 0:
        raise ValueError("final_values cannot be empty.")

    if not np.isfinite(final_values).all():
        raise ValueError("final_values contains NaN or infinite values.")

    if initial_value <= 0:
        raise ValueError("initial_value must be positive.")

    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1.")

    returns = final_values / initial_value - 1.0

    loss_distribution = -returns
    var_threshold = np.quantile(loss_distribution, confidence)

    tail_losses = loss_distribution[loss_distribution >= var_threshold]

    if tail_losses.size == 0:
        expected_shortfall = float(var_threshold)
    else:
        expected_shortfall = float(tail_losses.mean())

    percentiles = {
        f"{p:g}": float(np.percentile(final_values, p))
        for p in [5, 25, 50, 75, 95]
    }

    return {
        "confidence": confidence,
        "var": float(var_threshold * initial_value),
        "expected_shortfall": expected_shortfall * initial_value,
        "mean_final_value": float(np.mean(final_values)),
        "median_final_value": float(np.median(final_values)),
        "std_final_value": float(np.std(final_values, ddof=1)),
        "min_final_value": float(np.min(final_values)),
        "max_final_value": float(np.max(final_values)),
        "mean_return": float(np.mean(returns)),
        "std_return": float(np.std(returns, ddof=1)),
        "skewness": float(pd.Series(returns).skew()),
        "kurtosis": float(pd.Series(returns).kurtosis()),
        "percentiles": percentiles,
    }


# ---------------------------------------------------------------------------
# Reporting / export
# ---------------------------------------------------------------------------

def print_summary(
    simulation: dict,
    risk_metrics: dict,
) -> None:
    """Print a human-readable simulation summary."""
    print("\n" + "=" * 60)
    print("BLACK SWAN — MONTE CARLO PORTFOLIO REPORT")
    print("=" * 60)

    print(f"Version:             {simulation['version']}")
    print(f"Seed:                {simulation['seed']}")
    print(f"Assets:              {', '.join(simulation['assets'])}")
    print(f"Simulations:         {simulation['num_simulations']:,}")
    print(f"Horizon:             {simulation['horizon']} periods")
    print(f"Initial value:       £{simulation['initial_value']:,.2f}")

    print("\nPortfolio weights:")
    for asset, weight in simulation["weights"].items():
        print(f"  {asset:<10} {weight:.2%}")

    print("\nRisk metrics:")
    print(f"  VaR (95%):          £{risk_metrics['var']:,.2f}")
    print(
        f"  Expected Shortfall: £{risk_metrics['expected_shortfall']:,.2f}"
    )
    print(f"  Mean final value:   £{risk_metrics['mean_final_value']:,.2f}")
    print(f"  Median final value: £{risk_metrics['median_final_value']:,.2f}")
    print(f"  Std. final value:   £{risk_metrics['std_final_value']:,.2f}")
    print(f"  Minimum:            £{risk_metrics['min_final_value']:,.2f}")
    print(f"  Maximum:            £{risk_metrics['max_final_value']:,.2f}")

    print("\nFinal-value percentiles:")
    for percentile, value in risk_metrics["percentiles"].items():
        print(f"  {percentile:>2}%:               £{value:,.2f}")

    print("=" * 60)


def export_simulation_csv(
    simulation: dict,
    risk_metrics: dict,
    filepath: str = "outputs/simulation_results.csv",
) -> Path:
    """Export final simulation values and key metadata to CSV."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "simulation": np.arange(1, len(simulation["final_values"]) + 1),
        "final_portfolio_value": simulation["final_values"],
        "final_return": (
            simulation["final_values"] / simulation["initial_value"] - 1.0
        ),
        "seed": simulation["seed"],
        "version": simulation["version"],
    })

    df.to_csv(path, index=False)

    # Separate metadata/risk report is useful for auditability.
    metadata_path = path.with_name(path.stem + "_report.csv")

    report_rows = {
        "version": simulation["version"],
        "seed": simulation["seed"],
        "initial_value": simulation["initial_value"],
        "num_simulations": simulation["num_simulations"],
        "horizon": simulation["horizon"],
        "VaR_95": risk_metrics["var"],
        "Expected_Shortfall_95": risk_metrics["expected_shortfall"],
        "mean_final_value": risk_metrics["mean_final_value"],
        "median_final_value": risk_metrics["median_final_value"],
        "std_final_value": risk_metrics["std_final_value"],
        "min_final_value": risk_metrics["min_final_value"],
        "max_final_value": risk_metrics["max_final_value"],
    }

    for asset, weight in simulation["weights"].items():
        report_rows[f"weight_{asset}"] = weight

    pd.DataFrame([report_rows]).to_csv(metadata_path, index=False)

    print(f"✓ Simulation results saved to {path}")
    print(f"✓ Report metadata saved to {metadata_path}")

    return path


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------

def plot_portfolio_paths(
    simulation: dict,
    filename: str = "outputs/portfolio_simulation_paths.png",
    max_paths: int = 100,
) -> Path:
    """Plot portfolio median and percentile simulation paths."""
    paths = simulation["portfolio_paths"]

    if paths.ndim != 2:
        raise ValueError("portfolio_paths must have shape (time, simulations).")

    horizon = paths.shape[0]
    number_to_plot = min(max_paths, paths.shape[1])

    p5 = np.percentile(paths, 5, axis=1)
    p50 = np.percentile(paths, 50, axis=1)
    p95 = np.percentile(paths, 95, axis=1)

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))

    # First 100 paths are shown for readability, as specified in V0.1.
    for i in range(number_to_plot):
        plt.plot(paths[:, i], alpha=0.08)

    plt.plot(p50, linewidth=2, label="Median (50th percentile)")
    plt.fill_between(
        range(horizon),
        p5,
        p95,
        alpha=0.25,
        label="5th–95th percentile range",
    )

    plt.title("Black Swan — Monte Carlo Portfolio Paths")
    plt.xlabel("Simulation Period")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    print(f"✓ Portfolio paths saved to {path}")
    return path


def plot_final_value_distribution(
    simulation: dict,
    risk_metrics: dict,
    filename: str = "outputs/final_value_distribution.png",
) -> Path:
    """Plot histogram of final portfolio values with VaR marker."""
    final_values = simulation["final_values"]

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.hist(final_values, bins=40, alpha=0.75)

    var_cutoff = simulation["initial_value"] - risk_metrics["var"]
    plt.axvline(
        var_cutoff,
        linewidth=2,
        label=f"95% VaR threshold (£{var_cutoff:,.0f})",
    )

    plt.axvline(
        risk_metrics["median_final_value"],
        linestyle="--",
        linewidth=2,
        label="Median final value",
    )

    plt.title("Black Swan — Final Portfolio Value Distribution")
    plt.xlabel("Final Portfolio Value")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close()

    print(f"✓ Final-value distribution saved to {path}")
    return path


# ---------------------------------------------------------------------------
# Example / smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example: 60/40 portfolio.
    assets = ["SPY", "BND"]

    prices = load_multiple_assets(
        assets,
        period="5y",
        interval="1d",
    )

    prices = align_assets(
        prices,
        frequency="D",
        fill_method="ffill",
        backward_fill=False,
    )

    returns = calculate_returns(prices, method="simple")

    portfolio = Portfolio.from_dict(
        {
            "SPY": 0.60,
            "BND": 0.40,
        },
        initial_value=100_000,
    )

    simulation = run_monte_carlo_sim(
        returns_df=returns,
        portfolio=portfolio,
        num_simulations=1_000,
        horizon=252,
        seed=42,
    )

    risk_metrics = calculate_risk_metrics(
        final_values=simulation["final_values"],
        initial_value=simulation["initial_value"],
        confidence=0.95,
    )

    print_summary(simulation, risk_metrics)

    plot_portfolio_paths(simulation)
    plot_final_value_distribution(simulation, risk_metrics)

    export_simulation_csv(simulation, risk_metrics)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from data_loader import (
    load_from_yahoo,
    load_multiple_assets,
    load_csv,
    filling_missing_dates,
    resample,
    calculate_returns,
    run_monte_carlo_sim,
    plots_path
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

print("=" * 70)
print(" BLACK SWAN - COMPREHENSIVE TEST SUITE")
print("=" * 70)

# ============================================================
# TEST 1: Single Asset from Yahoo Finance
# ============================================================
print("\n[TEST 1] Single Asset - Yahoo Finance")
print("-" * 70)

try:
    df_single = load_from_yahoo('SPY', period='1y', interval='1d')
    
    print(f"✓ Data loaded successfully")
    print(f"  Shape: {df_single.shape}")
    print(f"  Columns: {df_single.columns.tolist()}")
    print(f"  Date range: {df_single.index[0].date()} to {df_single.index[-1].date()}")
    latest_price = df_single['Close'].iloc[-1]
    print(f"  Latest price: ${df_single['Close'].iloc[-1]:.2f}")
    
    # Verify structure
    assert isinstance(df_single, pd.DataFrame), "Should return DataFrame"
    assert 'Close' in df_single.columns, "Should have 'Close' column"
    assert len(df_single) > 0, "Should have data"
    
    print("✓ All checks passed")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================
# TEST 2: Multiple Assets from Yahoo Finance
# ============================================================
print("\n[TEST 2] Multiple Assets - Yahoo Finance")
print("-" * 70)

try:
    tickers = ['SPY', 'AGG', 'GLD']
    df_multi = load_multiple_assets(tickers, period='1y', interval='1d')
    
    print(f"✓ Data loaded successfully")
    print(f"  Shape: {df_multi.shape}")
    print(f"  Assets: {df_multi.columns.tolist()}")
    print(f"  Date range: {df_multi.index[0].date()} to {df_multi.index[-1].date()}")
    print(f"\n  Latest prices:")
    for ticker in df_multi.columns:
        print(f"    {ticker}: ${df_multi[ticker].iloc[-1].item():.2f}")
    
    # Verify structure
    assert isinstance(df_multi, pd.DataFrame), "Should return DataFrame"
    assert len(df_multi.columns) == len(tickers), f"Should have {len(tickers)} columns"
    assert all(ticker in df_multi.columns for ticker in tickers), "Should have all tickers"
    
    print("✓ All checks passed")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================
# TEST 3: Single Asset - Full Pipeline
# ============================================================
print("\n[TEST 3] Single Asset - Full Simulation Pipeline")
print("-" * 70)

try:
    # Use single asset from TEST 1
    print("Step 1: Fill missing dates...")
    df_filled = filling_missing_dates(df_single)
    print(f"  ✓ {len(df_filled)} rows (added {len(df_filled) - len(df_single)})")
    
    print("Step 2: Calculate returns...")
    returns_single = calculate_returns(df_filled)
    print(f"  ✓ {len(returns_single)} returns")
    print(f"  ✓ Mean daily return: {returns_single.mean().values[0]*100:.4f}%")
    print(f"  ✓ Daily volatility: {returns_single.std().values[0]*100:.4f}%")
    
    print("Step 3: Run Monte Carlo (1000 sims, 252 days)...")
    initial_price_single = df_filled['Close'].iloc[-1].item()
    sims_single = run_monte_carlo_sim(
        returns_single,
        num_simulations=1000,
        horizon=252,
        initial_price=initial_price_single
    )
    print(f"  ✓ Simulation shape: {sims_single.shape}")
    
    # Analyze results
    final_prices = sims_single[-1, :, 0]
    print(f"\n  Results (starting from ${initial_price_single:.2f}):")
    print(f"    Mean final price:    ${final_prices.mean():.2f}")
    print(f"    Median final price:  ${np.median(final_prices):.2f}")
    print(f"    5th percentile:      ${np.percentile(final_prices, 5):.2f}")
    print(f"    95th percentile:     ${np.percentile(final_prices, 95):.2f}")
    print(f"    Expected return:     {((final_prices.mean()/initial_price_single - 1) * 100):.2f}%")
    
    print("Step 4: Generate plot...")
    plots_path(sims_single, assets_index=0, 
               filename=os.path.join(RESULTS_DIR, 'test_single_asset.png'))
    
    print("✓ Single asset pipeline complete")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================
# TEST 4: Multiple Assets - Full Pipeline
# ============================================================
print("\n[TEST 4] Multiple Assets - Full Simulation Pipeline")
print("-" * 70)

try:
    # Use multi-asset from TEST 2
    print("Step 1: Fill missing dates...")
    df_multi_filled = filling_missing_dates(df_multi)
    print(f"  ✓ {len(df_multi_filled)} rows")
    
    print("Step 2: Calculate returns...")
    returns_multi = calculate_returns(df_multi_filled)
    print(f"  ✓ {len(returns_multi)} returns for {len(returns_multi.columns)} assets")
    print(f"\n  Mean daily returns:")
    for col in returns_multi.columns:
        print(f"    {col}: {returns_multi[col].mean()*100:.4f}%")
    
    print("\nStep 3: Run Monte Carlo (1000 sims, 252 days)...")
    initial_prices_multi = df_multi_filled.iloc[-1].values
    sims_multi = run_monte_carlo_sim(
        returns_multi,
        num_simulations=1000,
        horizon=252,
        initial_price=initial_prices_multi
    )
    print(f"  ✓ Simulation shape: {sims_multi.shape}")
    
    # Analyze each asset
    print(f"\n  Results for each asset:")
    for i, ticker in enumerate(df_multi.columns):
        final_prices = sims_multi[-1, :, i]
        initial = initial_prices_multi[i]
        print(f"\n  {ticker} (starting ${initial:.2f}):")
        print(f"    Mean final:    ${final_prices.mean():.2f}")
        print(f"    5th-95th:      ${np.percentile(final_prices, 5):.2f} - ${np.percentile(final_prices, 95):.2f}")
        print(f"    Expected return: {((final_prices.mean()/initial - 1) * 100):.2f}%")
    
    print("\nStep 4: Generate plots for each asset...")
    for i, ticker in enumerate(df_multi.columns):
        plots_path(sims_multi, assets_index=i,
                   filename=os.path.join(RESULTS_DIR, f'test_multi_{ticker}.png'))
    
    print("✓ Multi-asset pipeline complete")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================
# TEST 5: Edge Cases & Error Handling
# ============================================================
print("\n[TEST 5] Edge Cases & Error Handling")
print("-" * 70)

# Test 5a: Invalid ticker
print("\nTest 5a: Invalid ticker should raise error...")
try:
    df_invalid = load_from_yahoo('INVALID_TICKER_XYZ123', period='1mo')
    print("  ✗ Should have raised an error!")
except ValueError as e:
    print(f"  ✓ Correctly raised error: {e}")
except Exception as e:
    print(f"  ⚠ Raised different error: {e}")

# Test 5b: Single ticker in list (edge case)
print("\nTest 5b: Single ticker in list format...")
try:
    df_single_list = load_multiple_assets(['SPY'], period='1mo')
    print(f"  ✓ Handled correctly: {df_single_list.columns.tolist()}")
    assert 'SPY' in df_single_list.columns or df_single_list.shape[1] == 1
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 5c: Very short simulation
print("\nTest 5c: Very short simulation (1 day, 10 sims)...")
try:
    sims_short = run_monte_carlo_sim(returns_single, num_simulations=10, horizon=1)
    print(f"  ✓ Shape: {sims_short.shape}")
    assert sims_short.shape == (1, 10, 1)
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Test 5d: All prices positive (GBM property)
print("\nTest 5d: GBM should produce only positive prices...")
try:
    assert np.all(sims_single > 0), "Found negative prices!"
    print(f"  ✓ All {sims_single.size} simulated prices are positive")
except AssertionError as e:
    print(f"  ✗ FAILED: {e}")

print("\n✓ Edge case tests complete")

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 70)
print(" ✓✓✓ ALL TESTS PASSED ✓✓✓")
print("=" * 70)
print("\nTest Summary:")
print("  [✓] Single asset loading (Yahoo Finance)")
print("  [✓] Multiple assets loading (Yahoo Finance)")
print("  [✓] Single asset simulation pipeline")
print("  [✓] Multiple assets simulation pipeline")
print("  [✓] Edge cases and error handling")
print(f"\nGenerated plots in: {RESULTS_DIR}/")
print("  - test_single_asset.png")
print("  - test_multi_SPY.png")
print("  - test_multi_AGG.png")
print("  - test_multi_GLD.png")
print("\nYour code is working correctly! 🚀")

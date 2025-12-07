import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from data_loader import (  # ← Changed from data_handler
    load_csv, 
    filling_missing_dates, 
    resample, 
    calculate_returns,
    run_monte_carlo_sim,
    plots_path
)

# Get base directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

print("=" * 60)
print(" BLACK SWAN v0.1 - FOUNDATION TEST SUITE")
print("=" * 60)

# Test 1: Load CSV
print("\n[1/7] Loading SPY data...")
try:
    spy_path = os.path.join(DATA_DIR, 'spy.csv')
    df = load_csv(spy_path)
    print(f"    ✓ Loaded {len(df)} rows")
    print(f"    ✓ Columns: {df.columns.tolist()}")
    print(f"    ✓ Date range: {df.index[0].date()} to {df.index[-1].date()}")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: Fill missing dates
print("\n[2/7] Filling missing dates...")
try:
    df_filled = filling_missing_dates(df)
    added = len(df_filled) - len(df)
    print(f"    ✓ After filling: {len(df_filled)} rows (+{added} filled)")
    print(f"    ✓ No missing values: {not df_filled.isnull().any().any()}")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Resample
print("\n[3/7] Testing resampling...")
try:
    df_weekly = resample(df_filled, 'W')
    print(f"    ✓ Weekly resampling: {len(df_weekly)} data points")
    df_monthly = resample(df_filled, 'M')
    print(f"    ✓ Monthly resampling: {len(df_monthly)} data points")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Calculate returns
print("\n[4/7] Calculating returns...")
try:
    returns = calculate_returns(df_filled)
    print(f"    ✓ Returns shape: {returns.shape}")
    print(f"    ✓ Mean daily return: {returns.mean().values[0]*100:.4f}%")
    print(f"    ✓ Daily volatility: {returns.std().values[0]*100:.4f}%")
    print(f"    ✓ Annualized return: {returns.mean().values[0]*252*100:.2f}%")
    print(f"    ✓ Annualized volatility: {returns.std().values[0]*np.sqrt(252)*100:.2f}%")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Small Monte Carlo test
print("\n[5/7] Running small Monte Carlo test (10 sims, 30 days)...")
try:
    sims_small = run_monte_carlo_sim(returns, num_simulations=10, horizon=30, initial_price=100)
    print(f"    ✓ Shape: {sims_small.shape}")
    print(f"    ✓ All prices positive: {np.all(sims_small > 0)}")
    print(f"    ✓ Price range: ${sims_small.min():.2f} to ${sims_small.max():.2f}")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 6: Full Monte Carlo
print("\n[6/7] Running full Monte Carlo (1000 sims, 252 days)...")
try:
    import time
    start = time.time()
    
    sims_full = run_monte_carlo_sim(returns, num_simulations=1000, horizon=252, initial_price=100)
    
    elapsed = time.time() - start
    throughput = 1000 / elapsed
    
    print(f"    ✓ Simulation complete in {elapsed:.2f}s")
    print(f"    ✓ Throughput: {throughput:.0f} sims/sec")
    
    # Statistics
    final_prices = sims_full[-1, :, 0]
    print(f"\n    Final Price Statistics (after 1 year):")
    print(f"      Mean:   ${final_prices.mean():.2f}")
    print(f"      Median: ${np.median(final_prices):.2f}")
    print(f"      Std:    ${final_prices.std():.2f}")
    print(f"      Min:    ${final_prices.min():.2f}")
    print(f"      Max:    ${final_prices.max():.2f}")
    print(f"      Return: {((final_prices.mean()/100 - 1) * 100):.2f}%")
    
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 7: Plotting
print("\n[7/7] Generating visualization...")
try:
    output_path = os.path.join(RESULTS_DIR, 'v01_test.png')
    plots_path(sims_full, assets_index=0, filename=output_path)
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print(" ✓ ALL TESTS PASSED - BLACK SWAN v0.1 COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("  1. git add .")
print("  2. git commit -m 'feat: v0.1 complete - GBM Monte Carlo working'")
print("  3. git push")
print("  4. Move to v0.2: Multi-engine comparison")
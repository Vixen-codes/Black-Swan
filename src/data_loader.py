import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def load_csv(filepath = 'data/price.csv'):
    #loads a csv with a date column and returns with the dataframe.
    df = pd.read_csv(filepath, parse_dates=['date'])
    df = df.set_index('date').sort_index()
    return df

def filling_missing_dates(df):
    #for filling missing dates in the csv
    df = df.asfreq('D')
    df = df.ffill().bfill()
    return df
def resample(df, frequency ='D'):
    ## for resampling weekly, monthly, daily
    return df.resample(frequency).last()

def calculate_returns(df):
    ##for daily returns
    return df.pct_change().dropna()

def run_monte_carlo_sim(returns_df, num_simulations=1000, horizon=252, initial_price=None):
    #for stats extraction
    num_assets = len(returns_df.columns)
    mu = returns_df.mean().values## mean of the data is returned as a numpy array
    cov_daily = returns_df.cov().values  ## covariance would be returned as a numpy array aswell
    ##implemented brown intial piian motion for a geometric brownian motion since it is better for stock prices
    #default initail price
    if initial_price is None:
        initial_price = np.ones(num_assets) * 100  ## default initial price of 100 for each asset
        #to make sure the prce is an array
    elif isinstance(initial_price, (int, float)):
        initial_price = np.ones(num_assets) * initial_price
  #didnt wanna do the calculation of covarience manully so i implemneted the built in
    chol = np.linalg.cholesky(cov_daily) ## cholesky decomposition
    sims = np.zeros((horizon, num_simulations, num_assets))
    for sim in range (num_simulations):
        #generation of random shocks
        rand = np.random.normal(size = (horizon, num_assets))
        #correlation structure application
        shock = rand @ chol.T
        #gbm components daily
        dt = 1
        drift =(mu - 0.5 * np.diag(cov_daily)) * dt
        diffusion = shock * np.sqrt(dt)
        log_return = drift + diffusion
        price_paths = initial_price * np.exp(np.cumsum(log_return, axis =0))
        sims[:, sim, :] = price_paths
    return sims
 
def plots_path(sims, assets_index = 0, filename = "simulations_paths.png"):
    horizon= sims.shape[0]
    num_simulations = sims.shape[1]
    num_assets = sims.shape[2]
    ## so i was thinking ot import percentiles cus i feel like any outliers would skew the data a lot
    #so i am selecting the 5th and 95th percentiles to plot
    p5 = np.percentile(sims[:, :, assets_index], 5, axis=1)
    p95 = np.percentile(sims[:, :, assets_index], 95, axis=1)
    p50 = np.percentile(sims[:, :, assets_index], 50, axis=1)
    plt.figure(figsize=(10,6))
    plt.plot(p50, color ='black', label = 'Median (50th Percentile)')
    ##the confidence band of this
    plt.fill_between(range(horizon), p5, p95, color='gray', alpha=0.3, label='5th-95th Percentile Range')
    plt.title(f'Monte Carlo Simulation of Asset Price paths {assets_index}')
    plt.xlabel('Days')
    plt.ylabel('Simulated Price')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename, dpi=300)
    plt.close()
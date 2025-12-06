import pandas as pd
import numpy as pd
def load_csv(filepath = 'data/price.csv'):
    """loads a csv with a date colume and retnres with the dataframe.
    """
    df = pd.read_csv(filepath, parse_dates=['date'])
    df = df.set_index('date')
    df = df.sort_values('date')
    return df
def filling_missing_dates(df):
    #for filling missing dates in the csv
   df = df.asfreq('D')
   df = df.ffill().bfill()
   return df
def resample(df, frequency ='D'):
    ## for resampling weekly, monthly, daily
    return df.resample(frequency).last()

def calculate_returns():
    ##for daily returns
    return df.pct.change().dropna()

def run_monte_carlo_sim(returns_df, n_sims=1000, horizon=252):
  mu = returns_df.mean().values ## mean of the data is returned as a numpy array
  cov = retunes_df.cov().values ## covariance would be returned as a numpy array aswell
  #didnt wanna do the calculation of covarience manully so i implemneted the built in
  chol = np.linalg.cholesky(cov) ## cholesky decomposition
for sim in range (num_simulations):
    rand = np.random.normal(size = (horizon, num_assets))
    shock = rand @ chol
     #to convert the shocks to returns
    simulation_return = mu + shock 
    sims[:, sim, sim :] = np.cumprod(1 + simulation_return, axis =0)
    return simulation_return
 
def plots_path(sims, assets_index = 0, filename = "simulations_paths.png"):
    horizon= sims.shape
    num_simulations = sims.shape
    num_assets = sims.shape
    ## so i was thinking ot import percentiles cus i feel like any outliers would skew the data a lot
    #so i am selecting the 5th and 95th percentiles to plot
    p5 = np.percentile(sims[:, :, assets_index], 5, axis=1)
    p95 = np.percentile(sims[:, :, assets_index], 95, axis=1)
    p50 = np.percentile(sims[:, :, assets_index], 50, axis=1)
    plt.figure(figsize=(10,6))
    plt.plot(p50, colour ='black', label = 'Median (50th Percentile)')
    ##the confidence band of this
    plot.fill_between(range(horizon), p5, p95, color='gray', alpha=0.3, label='5th-95th Percentile Range')
    plt.title('Monte Carlo Simulation of Asset Price paths {assets_index}')
    plt.xlabel('Days')
    plt.ylabel('Simulated Price')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename, dpi=300)
    plt.close()
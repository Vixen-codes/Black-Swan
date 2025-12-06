Black Swan

Monte Carlo simulator and portfolio manager (Project)

I am quite a finance enthusiast. Checking stocks and changes based on news is like a habit to me, , thought  I would talk to an unnamed stakeholder who works and is very into the field itself and thought I would bring some gaping problems to surface to address, would be researching on them

Multi asset support with mixed time horizons.
	They had been facing a problem with this. The software they used was not auto handling missing dates, mismatch frequencies, or resampling so I had to include it as my first requirement.
1.	These include: -
•	Daily stocks
•	Hourly crypto
•	Monthly bonds
•	Quarterly real estate index data
2.	And it must also auto handle.
•	Missing dates
•	Mismatched frequencies
•	Resampling
•	Weighted averaging
•	Forward filling and backward filling logic
Regime detection
	Most tools think that markets behave the same in time of crashes or calm. They really don’t from what I understood after having a talk with him, black swan events, changes in presidency of a major superpower or diplomatic relations changing in a bink of an eye,, to address this  I would make the Monte Carlo simulations to simulate different per regime, but since there are thousands of regime to make, I would be considering only a few that are applying in the real world right now, though in further updates I would make sure to add more regimes to the database so that it could detect it with ease
	Requirements: -
•	The systems must detect. 
1.	Bullish expansion
2.	Volatile sideways
3.	Crisis drawdown
4.	High-rate vs low-rate macro regimes
•	The system should be able to simulate differently per regime.
•	Transition probabilities should be calculated and stored from historical data.
Multi-simulation engine
	from what I have gathered after talking to them, the majority of simulations do only one simulation: which is monte Carlo, so I thought why not include more features to make it provide more features to the user.
o	so, thinking that I came to a settle down with four of the engines I know the best about. So, it is possible to make their simulations in the best way and so that they do not fail much.
	historical resampling bootstraps
	parametric monte Carlo (normal distribution)
	fat tailed
	regime based as I have said in the last requirement.
one more thing that I took into consideration while thinking about it was that output comparison was a necessity so that would be also taken into account while building this.
Dynamic portfolio rebalancing logic
	another problem they were facing was most tools assume that the money you put into buying the stock. And then you forget it which leads to an uneven distribution in portfolio, especially when you are investing huge sums so the portfolio section of the calculator would be doing the follows:
•	should rebalance itself at set intervals, the user could select the intervals or else it is set at weekly.
•	the rebalancing should not fall outside the domain of simulation, i.e. they should be taken into consideration when rebalanced or check in fresh.
•	should be able to model slippage and transaction costs as well now that I think of it.
•	should be realistically able to execute rules like proportional costs. Minimum size and liquidity constraints, 
•	the one problem I am just thinking of at this point is that rebalancing would happen inside of nested loop of the simulation itself, which I feel I am not competent enough to do, but I could ways have a look to decide if I want it in my final iteration of requirement, if it is feasible enough
Non normal risk modelling
-	so, since there is always threat of instability in the markets because they are not normal. What I myself saw was that the existing tools were thinking that it is normal ad just based of Gaussian models, now I am not saying I know more than a real quant out there and that I have access to such tools, I don’t even have access to the Bloomberg terminal, so those software that are used by such companies would function at a higher capacity and would be taking a lot of models into account, way more than I even know of but for the civilians out there who aren’t fighting in the world of finance and quants, the things we have access to are pretty limited and I don’t plan letting it stay the same the first update shall  take these requirements into account
	skewness
	kurtosis
	heavy tail modelling
	 and should be able to compute VaR. expected short fall and tail risk metrics and also it should be able to offer both historical and parametric VaR.
Stress testing
-	Yeah, after talking abut non risk and regime changes for half of the document till now, letting it go without stress testing the limits of it would just be too unsatisfying to put it through, so by granting the powers of Mannat the supreme leader of this document. I grant it to be stress tested (sorry this is 2 am caffeinated Mannat, with 1g of caffeine in her blood stream, heart is a muscle we shall train it to failure)
	From what my little brain gathered about the metrics that the test should be evaluated against
•	+200 bps interest rate
•	-30% equity crash
•	Oil prices
•	2008 replay (because that thing is not a black swan even anymore)
•	Covid shall be tested too
•	What do I wish is that the portfolio should be able to bounce back or at least not have a huge flaw in its code, but we do not get what we want always to do we? But yeah, I will try incorporating that into it as well.
•	And for fun if it passes majority of the tests, we could combine the tests and gauge how it bounces back or if at all.

Real world constraints (not sure)
Should be optimising my fine shyts constraints.
•	Max position
•	Min diversification constraints
•	No short or limited short rules.
•	Risk budgeting constraints.
Auditable
•	See dear reader I am not trying get caught for money laundering or anything. So that means this is auditable. Because the last thing I want is for police to pick me up for something that I missed turned out to be a gaping hole
-	Report generated would be with for each simulation that it would contain. Version. Seed. Parameters. Assumption and all results should be reproducible, so it does not give us God knows whose numbers.

Development:- (backend)

Version 0.1
•	Version 0.1 would mainly concern itself with working on the core concepts, which would be dealing with monte carlo simulation, basics
	Requirements
	Data Management
•	Load CSV files with price/return data
•	Handle multiple asset types (stocks, bonds, crypto)
•	Auto-detect and handle missing dates
•	Forward fill and backward fill logic
•	Align multiple assets to common date range
•	Resample data to common frequency (daily/weekly/monthly)
•	Calculate returns from price data
	Monte Carlo Engine - Parametric
•	Implement basic parametric Monte Carlo (Gaussian assumptions)
•	Calculate mean returns and covariance matrix from historical data
•	Generate N simulation paths (default: 1000)
•	Support configurable time horizon (days/weeks/months)
•	Output: Distribution of final portfolio values
	Portfolio Definition
•	Define portfolio with asset names and weights
•	Validate weights sum to 1.0
•	Set initial portfolio value
•	Support 2-10 assets in a portfolio
	Basic Risk Metrics
•	Calculate Value at Risk (VaR) at 95% confidence
•	Calculate Expected Shortfall (CVaR)
•	Summary statistics: mean, median, std dev, min, max
•	Return distribution percentiles (5th, 25th, 50th, 75th, 95th)
	Visualization
•	Plot simulation paths (first 100 paths for readability)
•	Show median path and confidence bands (5th/95th percentile)
•	Histogram of final portfolio values
•	Display risk metrics on plots
	Output
•	Console output with summary statistics
•	Matplotlib plots saved as PNG files
•	Basic CSV export of simulation results
Success Criteria: Can run 1000 simulations on a 60/40 stock/bond portfolio and visualize results in under 10 seconds.


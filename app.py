from flask import Flask, request, jsonify
from flask_cors import CORS

from src.main import (
    load_multiple_assets,
    align_assets,
    calculate_returns,
    Portfolio,
    run_monte_carlo_sim,
    calculate_risk_metrics,
)

app = Flask(__name__)

# Allow requests from GitHub Pages and local development.
CORS(app)


@app.get("/")
def health_check():
    """Simple endpoint to confirm that the API is running."""
    return jsonify({
        "status": "ok",
        "service": "Black Swan Monte Carlo Risk Engine",
        "version": "0.1.0",
    })


@app.get("/health")
def health():
    """Health check endpoint for deployment platforms such as Render."""
    return jsonify({
        "status": "healthy"
    })


@app.post("/simulate")
def simulate():
    """
    Run a Monte Carlo portfolio simulation.

    Expected JSON:

    {
        "assets": [
            {"ticker": "SPY", "weight": 0.6},
            {"ticker": "BND", "weight": 0.4}
        ],
        "initial_value": 100000,
        "num_simulations": 10000,
        "horizon": 252,
        "seed": 42,
        "period": "5y",
        "confidence": 0.95
    }
    """

    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "Request body must contain valid JSON."
            }), 400

        # ---------------------------------------------------------------
        # Read and validate request parameters
        # ---------------------------------------------------------------

        assets = data.get("assets")

        if not isinstance(assets, list) or len(assets) < 2:
            return jsonify({
                "error": "At least 2 assets are required."
            }), 400

        if len(assets) > 10:
            return jsonify({
                "error": "A maximum of 10 assets is supported."
            }), 400

        initial_value = float(data.get("initial_value", 100000))
        num_simulations = int(data.get("num_simulations", 10000))
        horizon = int(data.get("horizon", 252))
        seed = int(data.get("seed", 42))
        period = str(data.get("period", "5y"))
        confidence = float(data.get("confidence", 0.95))

        if initial_value <= 0:
            raise ValueError("Initial value must be greater than zero.")

        if num_simulations <= 0:
            raise ValueError("Number of simulations must be positive.")

        if horizon <= 0:
            raise ValueError("Horizon must be positive.")

        if not 0 < confidence < 1:
            raise ValueError("Confidence must be between 0 and 1.")

        # ---------------------------------------------------------------
        # Build ticker / weight dictionaries
        # ---------------------------------------------------------------

        weights = {}

        for asset in assets:

            if not isinstance(asset, dict):
                raise ValueError(
                    "Each asset must contain a ticker and weight."
                )

            ticker = str(asset.get("ticker", "")).strip().upper()

            if not ticker:
                raise ValueError("Every asset needs a ticker.")

            weight = float(asset.get("weight", 0))

            if weight < 0:
                raise ValueError(
                    f"Weight for {ticker} cannot be negative."
                )

            if ticker in weights:
                raise ValueError(
                    f"Duplicate ticker: {ticker}"
                )

            weights[ticker] = weight

        # Frontend sends weights as decimals:
        # SPY = 0.6, BND = 0.4
        weight_total = sum(weights.values())

        if not abs(weight_total - 1.0) < 1e-8:
            return jsonify({
                "error": (
                    f"Portfolio weights must sum to 100%. "
                    f"Current total: {weight_total * 100:.2f}%."
                )
            }), 400

        # ---------------------------------------------------------------
        # Load historical market data
        # ---------------------------------------------------------------

        tickers = list(weights.keys())

        prices = load_multiple_assets(
            tickers=tickers,
            period=period,
            interval="1d",
        )

        # ---------------------------------------------------------------
        # Align assets and calculate historical returns
        # ---------------------------------------------------------------

        prices = align_assets(
            prices,
            frequency="D",
            fill_method="ffill",
            backward_fill=False,
        )

        returns = calculate_returns(
            prices,
            method="simple",
        )

        # ---------------------------------------------------------------
        # Create portfolio
        # ---------------------------------------------------------------

        portfolio = Portfolio.from_dict(
            weights,
            initial_value=initial_value,
        )

        # ---------------------------------------------------------------
        # Run Monte Carlo simulation
        # ---------------------------------------------------------------

        simulation = run_monte_carlo_sim(
            returns_df=returns,
            portfolio=portfolio,
            num_simulations=num_simulations,
            horizon=horizon,
            seed=seed,
        )

        # ---------------------------------------------------------------
        # Calculate risk metrics
        # ---------------------------------------------------------------

        risk_metrics = calculate_risk_metrics(
            final_values=simulation["final_values"],
            initial_value=simulation["initial_value"],
            confidence=confidence,
        )

        # ---------------------------------------------------------------
        # Convert NumPy / pandas objects into JSON-safe values
        # ---------------------------------------------------------------

        final_values = simulation["final_values"].tolist()

        response = {
            "version": simulation["version"],
            "seed": simulation["seed"],
            "assets": simulation["assets"],
            "num_simulations": simulation["num_simulations"],
            "horizon": simulation["horizon"],
            "initial_value": simulation["initial_value"],
            "weights": {
                asset: float(weight)
                for asset, weight in simulation["weights"].items()
            },
            "risk_metrics": {
                "confidence": float(risk_metrics["confidence"]),
                "var": float(risk_metrics["var"]),
                "expected_shortfall": float(
                    risk_metrics["expected_shortfall"]
                ),
                "mean_final_value": float(
                    risk_metrics["mean_final_value"]
                ),
                "median_final_value": float(
                    risk_metrics["median_final_value"]
                ),
                "std_final_value": float(
                    risk_metrics["std_final_value"]
                ),
                "min_final_value": float(
                    risk_metrics["min_final_value"]
                ),
                "max_final_value": float(
                    risk_metrics["max_final_value"]
                ),
                "mean_return": float(
                    risk_metrics["mean_return"]
                ),
                "std_return": float(
                    risk_metrics["std_return"]
                ),
                "skewness": float(
                    risk_metrics["skewness"]
                ),
                "kurtosis": float(
                    risk_metrics["kurtosis"]
                ),
                "percentiles": {
                    key: float(value)
                    for key, value in risk_metrics["percentiles"].items()
                },
            },
            "final_values": final_values,
        }

        return jsonify(response)

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        # Avoid exposing internal implementation details in production.
        app.logger.exception("Simulation failed")

        return jsonify({
            "error": f"Simulation failed: {str(exc)}"
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
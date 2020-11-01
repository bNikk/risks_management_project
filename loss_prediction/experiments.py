import sys
from typing import Iterable, NoReturn

import pandas as pd
from matplotlib import pyplot as plt
from pylab import rcParams
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.svm import SVR


sys.path.append(".")
from loss_prediction.target import create_next_day_price
from utils.dataset import create_arma_table


def print_scores(y_true: Iterable, y_predict: Iterable, prefix: str = "") -> None:
    mae = mean_absolute_error(y_true, y_predict)
    mse = mean_squared_error(y_true, y_predict)
    r2 = r2_score(y_true, y_predict)
    print(f"{prefix} MAE: {mae:4f} MSE: {mse:.4f}, R2-score: {r2:.4f}")


def main() -> NoReturn:
    table = pd.read_csv("./data/tesla_stock.csv", index_col=0)
    table.index = pd.to_datetime(table.index)
    variable = table["Close"]

    x = create_arma_table(variable=variable, p=50, q=10, ma_window=10)
    x["next_day_price"] = create_next_day_price(variable=variable)
    x = x.dropna()
    x = x.loc["2019":]

    x_train, x_test = x.loc[:"2019-12"], x.loc["2020-01"]
    x_train, y_train = x_train.iloc[:, :-1], x_train.iloc[:, -1]
    x_test, y_test = x_test.iloc[:, :-1], x_test.iloc[:, -1]

    models = [
        LinearRegression(fit_intercept=False, n_jobs=-1),
        Ridge(fit_intercept=False),
        Lasso(fit_intercept=False, alpha=2),
        # SVR(),
        # RandomForestRegressor(),
    ]

    true_day_losses = y_test - x_test["ar(1)"]
    true_month_losses = y_test - y_train.loc["2019-12"].mean()

    fig, axs = plt.subplots(2, 1, figsize=(16, 16))

    for model in models:
        model.fit(x_train, y_train)
        y_predict = model.predict(x_test)

        predict_day_losses = y_predict - x_test["ar(1)"]
        predict_month_losses = y_predict - y_train.loc["2019-12"].mean()

        class_name = model.__class__.__name__
        print_scores(true_day_losses, predict_day_losses, f"{class_name} day losses")
        print_scores(true_month_losses, predict_month_losses, f"{class_name} month losses")
        print("")

        axs[0].plot(y_test.index, predict_day_losses, label=class_name)
        axs[1].plot(y_test.index, predict_month_losses, label=class_name)

    axs[0].plot(true_day_losses, label="True")
    axs[0].legend()
    axs[0].set_title("Losses relative to previous day price")

    axs[1].plot(true_month_losses, label="True")
    axs[1].legend()
    axs[1].set_title("Losses relative to previous month average price")
    plt.show()


if __name__ == "__main__":
    main()
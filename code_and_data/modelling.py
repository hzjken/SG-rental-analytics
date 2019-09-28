import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


def get_x_y():
    data = pd.read_csv('model_data.csv')
    psf = data['psf']
    price = data['price']
    data = data.drop(['psf', 'price', 'lat', 'lon'], axis=1)
    y = list(zip(psf, price))

    return data, y


def split_x_y(x, y):
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.5, random_state=1)
    psf_train, price_train = zip(*y_train)
    psf_test, price_test = zip(*y_test)

    return x_train, x_test, psf_train, price_train, psf_test, price_test


def build_rf(x_train, x_test, psf_train, price_train, psf_test, price_test):

    price_rf = RandomForestRegressor(n_estimators=200)
    price_rf.fit(x_train, price_train)
    rf_price_diff = mean_absolute_error(price_test, price_rf.predict(x_test))

    psf_rf = RandomForestRegressor(n_estimators=200)
    psf_rf.fit(x_train, psf_train)
    rf_psf_diff = mean_absolute_error(psf_test, psf_rf.predict(x_test))

    return price_rf, psf_rf, rf_price_diff, rf_psf_diff


def lasso_coef(x_train, x_test, price_train, price_test):

    lasso = Lasso(alpha=10)
    lasso.fit(x_train, price_train)
    lasso_price_diff = mean_absolute_error(price_test, lasso.predict(x_test))

    lasso_coef = list(zip(x_train.columns, lasso.coef_))
    lasso_coef = pd.DataFrame(lasso_coef, columns = ['feature', 'coef'])

    return lasso_coef, lasso_price_diff


if __name__ == '__main__':
    x, y = get_x_y()
    x_train, x_test, psf_train, price_train, psf_test, price_test = split_x_y(x, y)
    price_rf, psf_rf, rf_price_diff, rf_psf_diff = build_rf(
        x_train=x_train,
        x_test=x_test,
        psf_train=psf_train,
        price_train=price_train,
        psf_test=psf_test,
        price_test=price_test
    )
    lasso_coef, lasso_price_diff = lasso_coef(
        x_train=x_train,
        x_test=x_test,
        price_train=price_train,
        price_test=price_test
    )

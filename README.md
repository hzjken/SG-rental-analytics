# SG-rental-analytics
Explore the rental market and find out where to rent a house in Singapore using data and analytics!

<img width="857" alt="dashboard" src="https://user-images.githubusercontent.com/30411828/65695980-105bec80-e0ab-11e9-9873-4cf94a914472.png">

## Project Background
An analytics that I do for myself to find out where I should rent a flat in Singapore and learn about the price drivers of the rental market.

## Process
### Data Scraping
In order not to increase server burden to the rental website or get myself into trouble, the scraping script as well as the original scraped data are excluded from this repo.
### Data Cleaning & Engineering
Script: [**data_cleaning_and_engineering.py**](https://github.com/hzjken/SG-rental-analytics/blob/master/code_and_data/data_cleaning_and_engineering.py)<br><br>
Data quality check, data cleaning, supplementary info joining and feature engineering are done within this script. Two datasets are generated from this scirpt: <br>
* [**engineered_data.csv**](https://github.com/hzjken/SG-rental-analytics/blob/master/code_and_data/engineered_data.csv), used for later dashboard building and visualization purpose.<br>
* [**model_data.csv**](https://github.com/hzjken/SG-rental-analytics/blob/master/code_and_data/model_data.csv), used for machine learning model building, all the features have been transformed into numerical or dummy-categorical values.
### Modelling
Script: [**modelling.py**](https://github.com/hzjken/SG-rental-analytics/blob/master/code_and_data/modelling.py)<br><br>
To validate whether the features that we have and generate really make sense, I built machine learning models to check:
* <b>Prediction (explaining) Ability</b>: Random forest model is built, out-of-sample MAE is roughly 3% of the average price, which means the model is able to give a very accurate estimate of a house rental price given the data.
* <b>Important Features</b>: Feature importance from random forest model is leveraged to find out what are some of the most important features that will affect rental price in Singapore. 

* <b>Quantified Effects</b>: Lasso regression is built to check each feature's dollar effect on the rental price. For example, 1 unit increase in the housing area (sqft) will lead to 2.26 SGD increase on the monthly rental price.

Detail results can be found in [**SG_rental_analytics_2019_AUG.pptx**](https://github.com/hzjken/SG-rental-analytics/blob/master/slides_dashboard/SG_rental_analytics_2019_AUG.pptx).

## Dashboard
Visualization is implemented to explore more logical insights into the market.<br>
Check details in [**SG_rental_dashboard_2019_AUG.pbix**](https://github.com/hzjken/SG-rental-analytics/blob/master/slides_dashboard/SG_rental_dashboard_2019_AUG.pbix).
### Screenshots

<img width="857" alt="dashboard2" src="https://user-images.githubusercontent.com/30411828/65696252-7b0d2800-e0ab-11e9-9d62-ea32b0cae539.png">

<br>

<img width="857" alt="dashboard3" src="https://user-images.githubusercontent.com/30411828/65813249-54630480-e205-11e9-906b-ce5f8ad3fce6.png">

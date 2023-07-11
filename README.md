# YNAB-Plotly-Dash-Analysis
A simple (mostly ChatGPT-generated) Plotly Dash app for analyzing data exported from YNAB.

## Installation
1. Have Docker
2. Run `docker build -t finance-dash .`
3. Run `docker run -p 8080:80 finance-dash`
4. Go to `localhost:8080`
5. Go to [YNAB](https://app.ynab.com/)
6. Click `Export Budget` in the top-left menu
7. Upload `My Budget as of ... - Register.csv` to the dashboard
8. Enjoy :)

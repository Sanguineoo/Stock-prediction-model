from flask import Flask, render_template,request
import yfinance as yf
import matplotlib.pyplot as plt
from livereload import Server
import pickle
import pandas as pd
from datetime import date
companies = {'MSFT':'Microsoft', 'AAPL':'Apple', 'AMZN':'Amazon', 'GOOGL':'Google', 'PG':'Procter & Gamble', 'TSLA':'Tesla', 'JPM':'JPMorgan', 'JNJ':'Johnson and Johnson'}
markets = ['NASDAQ']
metrics = ['Days', 'Weeks']
today = date.today()
current_date = today.strftime("%Y-%m-%d")

app = Flask(__name__)
@app.route('/', methods = ['GET'])
def index_html():
    return render_template('stock app.html', default_text = "the results of the forcast would appear here")



@app.route('/generate', methods = ['POST'])
def give_output():
    selected_company = request.form["Company name"]
    market = request.form["Stock_exchange_market"]
    forecast_metric = request.form["Forecast metric"]
    date_number = request.form.get("Date number")

    if forecast_metric == "Weeks":
        date_number = int(date_number)*7
    try:
        company_name = companies[selected_company]
        ticker = yf.Ticker(selected_company)

        
        df = ticker.history(start="2016-01-01", end=current_date)
        df = df[['Close']]
        df.reset_index(inplace=True)
        df.columns = ['ds','y']
    
    except:
        pass    
    def remove_tz(x):
        new_time = pd.Timestamp(str(x.date()))
        return new_time
    df['ds'] = df['ds'].apply(remove_tz)

    if (selected_company in companies.keys()) and (market in markets) and (forecast_metric in metrics):
        current_price = ticker.info['regularMarketOpen']
        market_high = ticker.info['regularMarketDayHigh']
        market_low = ticker.info['regularMarketDayLow']

        with open(f'pickle_files\{selected_company}.pkl', 'rb') as f:
            model = pickle.load(f)

        future = model.make_future_dataframe(periods =int(date_number))
        forecast = model.predict(future)
        forecast = forecast[-int(date_number):]
        forecast = forecast[['ds','yhat', 'yhat_lower', 'yhat_upper']]
        forecast.reset_index(drop=True, inplace=True)

        highest_stock = forecast['yhat'].max()
        highest_day_index = forecast['yhat'].argmax()
        highest_day = str(forecast['ds'][highest_day_index])

        lowest_stock = forecast['yhat'].min()
        lowest_day_index = forecast['yhat'].argmin()
        lowest_day = str(forecast['ds'][lowest_day_index])

        sorted_forecast = forecast[['ds','yhat']].sort_values(by= 'yhat', ascending = False)
        sorted_forecast = sorted_forecast[:3].sort_values(by= 'ds', ignore_index = True)
        first_index = str(sorted_forecast['ds'][0])
        last_index = str(sorted_forecast['ds'][len(sorted_forecast)-1])
        spiral_down = []
        spiral_up = []
        for price in forecast['yhat']:
            perc = ((price - current_price)/current_price) * 100
            if perc < 0:
                spiral_down.append(perc)
            elif perc > 0:
                spiral_up.append(perc)
        if sum(spiral_down) *-1 > sum(spiral_up):
            if int(date_number) >2:
                return(render_template('stock app.html', negative_pred = f"""The current price of {company_name} is {current_price} is likely to go up by a total of {int(sum(spiral_up))}%🔼 and have a decrease of about {int(sum(spiral_down))*-1}%🔻.
                Overall we see the best time for {company_name}'s stock to be around {first_index} to {last_index}, however after this is followed by a decrease and we would not recommend this stock at this period."""))
            else:
                return(render_template('stock app.html', negative_pred = f"""The current price of {company_name} is {current_price} is likely to go up by a total of {int(sum(spiral_up))}%🔼 and have a decrease of about {int(sum(spiral_down))*-1}%🔻.
                The ending of the period is characterized by a decrease and we would not recommend this stock at this period."""))
        else:
            if int(date_number) > 2:
                return(render_template('stock app.html', positive_pred = f"""{company_name}'s current stock price which is {current_price} is likely to have a {int(sum(spiral_up))}%🔼 increase and a total decrease of {int(sum(spiral_down))*-1}%🔻.{company_name}'s stock price looks to be constantly increasing at the moment with the best time being around {first_index} to {last_index} and is recommended by us as a good stock to invest in."""))
            else:
                return(render_template('stock app.html', positive_pred = f"""{company_name}'s current stock price which is {current_price} is likely to have a {int(sum(spiral_up))}%🔼 increase and a total decrease of {int(sum(spiral_down))*-1}%🔻.{company_name}'s stock price looks to be constantly increasing at the moment and is recommended by us as a good stock to invest in."""))

    else:
        return(render_template('stock app.html', error_message = "An error was detected in your selection process, please go over your options."))

if __name__ == '__main__':
    app.debug = True
    app.run()
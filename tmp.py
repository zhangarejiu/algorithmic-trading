from market_maker.settings import settings
import stockstats
import pandas as pd
from market_maker.exchange_interface import ExchangeInterface

pd.options.display.width = 300 # for pandas


# df = pd.read_csv('../test.csv')
# print(df)
# a = pandas.DataFrame(np.random.rand(4,5), columns = list('abcde'))
# print(a)
# a_asndarray = a.values
# print(a_asndarray)

# stockstats expects a column named 'close'

exchange = ExchangeInterface(settings.DRY_RUN)
quote = exchange.get_quoteBucketed(symbol=settings.SYMBOL, count=30)
df = pd.DataFrame.from_dict(quote) # convert to pandas
df.set_index('timestamp', inplace=True) # set the df index
df.index = pd.to_datetime(df.index) # convert index to datetime obj
# df = df.dropna(axis='index', how='any') # remove nans
df = df.fillna(method='backfill')
print(df)
# one should choose if the df is built using askPrice or bidPrice
df['close'] = df['askPrice']
df = df[['close']]
print(df) # this is what stockstats is expecting

stock = stockstats.StockDataFrame.retype(df, index_column='timestamp')
print(stock['macd'])

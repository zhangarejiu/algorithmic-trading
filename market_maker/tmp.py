
import stockstats
import pandas as pd
from market_maker.exchange_interface import ExchangeInterface

pd.options.display.width = 300 # for pandas

print('something')

# df = pd.read_csv('../test.csv')
# print(df)
# stock = stockstats.StockDataFrame.retype(df, index_column='timestamp')
# print(stock)
# a = pandas.DataFrame(np.random.rand(4,5), columns = list('abcde'))
# print(a)
# a_asndarray = a.values
# print(a_asndarray)

print('sssss')
quote = self.exchange.get_quoteBucketed(symbol=settings.SYMBOL)
print(quote)
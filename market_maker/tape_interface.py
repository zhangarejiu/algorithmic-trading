import pandas as pd
from market_maker.settings import settings
import matplotlib.pyplot as plt
import os
# import matplotlib.dates as mdates
# from matplotlib.finance import candlestick2_ochl
import matplotlib.dates as dates
import matplotlib.ticker as mticker

import numpy as np
# import urllib
# import datetime as dt

# widen the pd printing size
pd.options.display.width = 180 # for pandas

class Tape:
    """
    Tape class stores a live stream of all the quotes, strategies and others bucketed data.
    These records can can be quereid and combined with helper method of the tape class.
    """

    def __init__(self, dry_run=False):
        
        self.dry_run = dry_run
        # initialize and create tape data frame
        self.tape_df = pd.DataFrame()

        # quote = self.exchange.get_quoteBucketed() # returns a list of dictionary quotes
        # df = pd.DataFrame.from_dict(quote) # convert to pandas
        # df.set_index('timestamp', inplace=True) # set the df index
        # df.index = pd.to_datetime(df.index) # convert index to datetime obj
        
        # TODO: fix as for now is only working with 1m timeframe... add other timeframes
        # resample_time = {'1m':'1Min'}
        
        # candle_df = df[column].resample(resample_time[settings.TIMEFRAME]).ohlc() # group again and sorts 1Min candles (just to make sure!)
        # candle_df = candle_df.dropna(axis=0, how='all') # remove nans
        # return candle_df

        # pass

        """
        "timestamp": "2014-11-28T12:00:00.000Z",
        "symbol": "XBTH15",
        "bidSize": null,
        "bidPrice": null,
        "askPrice": null,
        "askSize": null
        """

    def get_df(self):
        return self.tape_df

    def put_df(self, df):
        self.tape_df = df
        return self.tape_df

    def append_record(self, df):
        """
        Append a record (df indexed on timestamp) as new row to the tape_df
        A record should be a row indexed with 'datetime'
        """
        if df is not None:
            tmp = pd.concat([self.tape_df,df])
            self.tape_df = tmp[~tmp.index.duplicated(keep='last')] # this is way faster than remove duplicates
            # see https://stackoverflow.com/questions/13035764/remove-rows-with-duplicate-indices-pandas-dataframe-and-timeseries
            self.tape_df = self.tape_df.sort_index(ascending=False, kind='quicksort') # sorts the df after the concat
            return self.tape_df



    def add_strategy_record(self, record):
        """
        Adds a new strategy record from dict to the global DF
        A record contains a dictionary with datetime object in a 'timestamp' colume, then any other amount/colum.
        """
        if record is not None:
            tmp_df = pd.DataFrame.from_dict([record]) # convert to pandas
            tmp_df.set_index('timestamp', inplace=True) # set the df index
            tmp_df.index = pd.to_datetime(tmp_df.index) # convert index to datetime obj
            tmp_df = tmp_df.dropna(axis=0, how='all') # remove nans

            """ DF created:
                                              order_price order_size
            timestamp
            2018-02-24 18:15:00+00:00           0          0
            ------------------------------------------------------------------------      
            """

            tmp_df = pd.concat([self.strategy_df,tmp_df])
            self.strategy_df = tmp_df[~tmp_df.index.duplicated(keep='last')] # this is way faster than remove duplicates
            self.strategy_df = self.strategy_df.sort_index(ascending=False, kind='quicksort') # sorts the df after the concat
            return self.strategy_df

    def add_balance_record(self, record):
        """
        Adds a new balance record from dict to the global DF
        A record should return a dictionary with datetime object in a 'timestamp' colume, then any other amount/colum
        """
        tmp_df = pd.DataFrame.from_dict([record]) # convert to pandas
        tmp_df.set_index('timestamp', inplace=True) # set the df index
        tmp_df.index = pd.to_datetime(tmp_df.index) # convert index to datetime obj
        tmp_df = tmp_df.dropna(axis=0, how='all') # remove nans
        # print(tmp_df)

        """ DF created:
                                    balance
        timestamp
        2018-02-24 18:23:00+00:00  0.89123742
        """
        tmp_df = pd.concat([self.balances_df,tmp_df])
        self.balances_df = tmp_df[~tmp_df.index.duplicated(keep='last')] # this is way faster than remove duplicates
        self.balances_df = self.balances_df.sort_index(ascending=False, kind='quicksort') # sorts the df after the concat
        return self.balances_df

    def add_trade_record(self):
        """
        Not sure if this method is necessary.... verify
        """
        # add new record
        return self.trades_df

    """
    def add_unrealisedPnlPcnt(self, current_time, pnl):
        record = {'timestamp':current_time, 'unrealisedPnlPcnt':str(pnl)}
        tmp_df = pd.DataFrame.from_dict([record]) # convert to pandas
        tmp_df.set_index('timestamp', inplace=True) # set the df index
        tmp_df.index = pd.to_datetime(tmp_df.index) # convert index to datetime obj
        tmp_df = tmp_df.dropna(axis=0, how='all') # remove nans
        return tmp_df
        """

    """
    def append_colum_df(self, new_df):
        Returns the combined colums of all df. df need to be indexed with datetime
        # print(self.quotes_df,self.strategy_df,self.balances_df)
        # self.tape_df
        # self.tape_df.append(new_df)
        self.tape_df = pd.concat([self.tape_df,new_df], axis=1, join_axes=[self.tape_df.index])
        # print(result)
        return self.tape_df
        """

    """
    def save_csv(self, df, filename='log.txt'):
        takes a PD dataframe with index on date and reorders is to be compatible for candlestics
        # np_time = []
        # df_asarray = pd_quotes.values
        # convert pandas to np
        # timestamps = pd_quotes.index
        # for t in pd_quotes:
            # np_time.append(dates.date2num(t))
        # print(np_time)
        # for x in np_time:
            # print(dates.num2date(x))
        # return df_asarray

        # timestamp 
        # df_candles['timestamp'] = df_candles.index

        # print(df_asarray)
        # matplotlib.mlab.rec2csv(r, fname, delimiter=', ', formatd=None, missing='', missingd=None, withheader=True)¶
        """

    def append_to_csv(self, df, csvFilePath, sep=","):
        """
        convert datetime index into a colum to be able to store it within the file
        """
        if csvFilePath is not None:
            if not os.path.isfile(csvFilePath):
                df.to_csv(csvFilePath, mode='a', index=True, sep=sep)
            elif (len(df.columns)+1) != len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns):
                raise Exception("Columns do not match!! Dataframe has " + str(len(df.columns)) + " columns. CSV file has " + str(len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns)) + " columns.")
            else:
                df.to_csv(csvFilePath, mode='a', index=True, sep=sep, header=False)

    def reset_csv(self, csvFilePath):
        """
        reset csv file. ensure that a new csv file is created upon start
        """
        if os.path.exists(csvFilePath):
            os.remove(csvFilePath)             
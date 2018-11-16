#import matplotlib.pyplot as plt
import pandas as pd
from market_maker.strategies import funding_rates
import argparse


# widen the pd printing size
pd.options.display.width = 300 # for pandas


class Plotter:

    def __init__(self, dry_run=False):
        parser = argparse.ArgumentParser()
        parser.add_argument("filepath", help="CSV log file")
        args = parser.parse_args()
        self.filepath = args.filepath

    def read_csv(self, filename):
        """
        Read csv file and set datetime as index
        """
        df = pd.read_csv(filename)
        df.set_index('timestamp', inplace=True) # set the df index
        df.index = pd.to_datetime(df.index) # convert index to datetime obj
        return df

    def draw_mom(self, df):
        # fig = plt.figure()
        # ax1 = plt.subplot2grid((1,1), (0,0))

        # fig, (ax1, ax2) = plt.subplots(1, 2)
        # my_plotter(ax1, data1, data2, {'marker':'x'})
        # my_plotter(ax2, data3, data4, {'marker':'o'})


        # df['balance'].plot()

        # plt.show()

        # Data for plotting
        timestamp = df.index
        balance = df['balance']
        askPrice = df['askPrice']
        order_size = df['order_size']
        unrealisedPnlPcnt = df['unrealisedPnlPcnt']

        # Post-process data
        # df['new'] = df['position'] 
        long_timestamps = []
        long_positions = []
        short_timestamps = []
        short_positions = []
        previous_position = 0
        for x in range(0,len(df['position'])):
            position = df['position'][x]
            if position != previous_position:
                if (position > 0):
                    long_timestamps.append(df.index[x])
                    long_positions.append(df['askPrice'][x])
                elif (position < 0):
                    short_timestamps.append(df.index[x])
                    short_positions.append(df['askPrice'][x])
                previous_position = position

        # print(timestamps)                
        # print(positions)
        print(df)

        # Create two subplots sharing y axis
        fig, (ax1, ax2, ax3) = plt.subplots(3, sharey=False)

        ax1.plot(timestamp, balance, 'k-')
        ax1.set(title='Mom-bot v0.1', ylabel='Balance')

        # plot the price
        ax2.plot(timestamp, askPrice, 'b-')
        # plot the entries
        # set the marker size according to the number of entries
        markersize =  100000 / df.size
        markersize = max(1, min(markersize, 10))

        ax2.plot(long_timestamps,long_positions,'go', markersize=markersize)
        ax2.plot(short_timestamps,short_positions,'ro', markersize=markersize)
        # ax2.plot(timestamp[1], askPrice[1], 'go')
        ax2.set(ylabel='price')

        ax3.plot(timestamp, unrealisedPnlPcnt, 'g-')
        ax3.set(ylabel='unrealisedPnlPcnt')


        plt.show()


    
        """
        stock_price_url = 'https://pythonprogramming.net/yahoo_finance_replacement'
        source_code = urllib.request.urlopen(stock_price_url).read().decode()
        stock_data = []
        split_source = source_code.split('\n')
        for line in split_source[1:]:
            split_line = line.split(',')
            if len(split_line) == 7:
                if 'values' not in line and 'labels' not in line:
                    stock_data.append(line)

        
        date, closep, highp, lowp, openp, adj_closep, volume = np.loadtxt(stock_data,
                                                              delimiter=',',
                                                              unpack=True,
                                                              converters={0: bytespdate2num('%Y-%m-%d')})

        x = 0
        y = len(date)
        ohlc = []

        while x < y:
            append_me = date[x], openp[x], highp[x], lowp[x], closep[x], volume[x]
            ohlc.append(append_me)
            x+=1
            """

            # opens = df['open'].tolist()
            # closes = df['close'].tolist()
            # highs = df['high'].tolist()
            # lows = df['low'].tolist()

            # opens = [1,2,3,4]
            # closes = [1.2,2.2,3.2,4.2]
            # highs = [2,3,4,5]
            # lows = [0,1,2,3]

            # print(opens, closes, highs, lows)



            # candlestick_ohlc(ax1, df_asarray, width=0.4, colorup='#77d879', colordown='#db3f3f')
            # candlestick2_ochl(ax1, opens, closes, highs, lows, width=0.4, colorup='#77d879', colordown='#db3f3f', alpha=0.75)


            # for label in ax1.xaxis.get_ticklabels():
            #     label.set_rotation(45)

            # ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            # ax1.xaxis.set_major_locator(mticker.MaxNLocator(4))
            # ax1.grid(True)
            

            # plt.xlabel('Date')
            # plt.ylabel('Price')
            # plt.title(stock)
            # plt.legend()
            # plt.subplots_adjust(left=0.09, bottom=0.20, right=0.94, top=0.90, wspace=0.2, hspace=0)
            # plt.show()

    def draw_trailstop_strategy(self, df):
        # fig = plt.figure()
        # ax1 = plt.subplot2grid((1,1), (0,0))

        # fig, (ax1, ax2) = plt.subplots(1, 2)
        # my_plotter(ax1, data1, data2, {'marker':'x'})
        # my_plotter(ax2, data3, data4, {'marker':'o'})


        # df['balance'].plot()

        # plt.show()

        # Data for plotting
        timestamp = df.index
        balance = df['walletBalance']
        askPrice = df['askPrice']
        bidPrice = df['bidPrice']

        # Post-process data
        # df['new'] = df['position'] 
        long_timestamps = []
        long_positions = []
        short_timestamps = []
        short_positions = []
        previous_position = 0
        print(df)
        
        for x in range(0,len(df['action'])):
            action = df['action'][x]
            if action:
                price = df['execution_price'][x]
                if action == 'Buy':
                    long_timestamps.append(df.index[x])
                    long_positions.append(price)
                else:
                    short_timestamps.append(df.index[x])
                    short_positions.append(price)

        """
        for x in range(0,len(df['action'])):
            position = df['position'][x]
            if position != previous_position:
                if (position > 0):
                    long_timestamps.append(df.index[x])
                    long_positions.append(df['askPrice'][x])
                elif (position < 0):
                    short_timestamps.append(df.index[x])
                    short_positions.append(df['askPrice'][x])
                previous_position = position

        # print(timestamps)                
        # print(positions)
        print(df)
        """

        # Create two subplots sharing y axis
        fig, (ax1, ax2) = plt.subplots(2, sharey=False)

        ax1.plot(timestamp, balance, 'k-')
        ax1.set(title='Trailstop Strategy v0.1', ylabel='Balance')

        # plot the price
        ax2.plot(timestamp, askPrice, 'r-')
        ax2.plot(timestamp, bidPrice, 'g-')
        # plot the entries
        # set the marker size according to the number of entries
        markersize =  100000 / df.size
        markersize = max(1, min(markersize, 3))

        ax2.plot(long_timestamps,long_positions,'go', markersize=markersize)
        ax2.plot(short_timestamps,short_positions,'ro', markersize=markersize)
        # ax2.plot(timestamp[1], askPrice[1], 'go')
        ax2.set(ylabel='price')

        # ax3.plot(timestamp, unrealisedPnlPcnt, 'g-')
        # ax3.set(ylabel='unrealisedPnlPcnt')


        plt.show()

def run():

    plotter = Plotter()
    
    try:
        df = plotter.read_csv(plotter.filepath)
        fr = funding_rates.Plotter()
        fr.draw(df)

    except (KeyboardInterrupt, SystemExit):
        sys.exit()



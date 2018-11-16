"""
A strategy should always receive the tape to be modified and return the last line so can be feeded to the tape back in the main market_maker class
"""

from market_maker.utils import log
import pandas as pd
from market_maker.settings import settings
from time import sleep
import matplotlib.pyplot as plt


logger = log.setup_custom_logger(__name__)
pd.options.display.width = 300 # for pandas

class Strategy:

    def __init__(self, exchange):
        self.exchange = exchange

    def check_contingent_limit(self):
        """
        Check API limits. If a limit is reached no trades should be submitted. 
        @return: True if the limit is reached, false otherwise
        """

        #max_contingents = 10
        max_contingents = 2
        # max_stops = 10

        # check for API limits
        open_position = self.exchange.get_position()['simpleCost']
        # open_orders = self.exchange.get_num_open_orders()
        contingent_orders = self.exchange.get_num_contingent_orders()
        
        # check contingent orders limit to avoid being kicked our form the API
        # if (contingent_orders >= max_contingents) and (open_position != 0): # DEBUG: prevents any additional orders being added when there is an open position
        if (contingent_orders >= max_contingents):
            logger.info("Max contingent orders reached: {} ... System sleeping for {}s".format(contingent_orders, settings.LOOP_INTERVAL))
            return True
        #elif open_position != 0:
        #    logger.info("Open position detected of {} contracts. ... System sleeping for {}s".format(open_position, settings.LOOP_INTERVAL))
        #    return 'position'
        elif (contingent_orders < max_contingents) and open_position == 0:
            return False

    def check_open_position(self):
        position = self.exchange.get_position()
        if position['isOpen']:
            open_position = position['simpleCost']
            return open_position
        else:
            return False

    def run_strategy(self):

        # Get latest quote (raw df line)
        """
        INPUT : latest quote contains : 
                                       askPrice  askSize  bidPrice  bidSize  symbol walletBalance marginBalance fundingRate          fundingTimestamp  indicativeFundingRate
        timestamp
        2018-04-02 03:12:00+00:00       6938.0     4258    6937.5    70688  XBTUSD    3.13026403    3.13026403   -0.001697  2018-04-02 04:00:00+00:00               0.000967
        --------------------------------------------------------------------------------------------------------------                
        """

        # set defaults
        trade_side = False
        executed = False
        latest_quote = self.exchange.get_latest_quote_with_funding()
        current_time = latest_quote.index.tolist()[0] # extrapolate latest time

        logger.info('....executing run_strategy()')
        
        # check limites
        if not self.check_contingent_limit():

            open_position = self.check_open_position()
            latest_quote_time = pd.to_datetime(latest_quote.index)
            funding_time = pd.to_datetime(latest_quote['fundingTimestamp']).tolist()[0]
            time_delta = funding_time - latest_quote_time
            time_delta = time_delta.seconds.tolist()[0]
            
            if not open_position:

                if time_delta < settings.THRESHOLD_TIME_BEFORE:
                        
                        logger.info('Funding rates in LESS than {} seconds [{}s]'.format(settings.THRESHOLD_TIME_BEFORE, time_delta))
                        indicative_funding_rate = latest_quote['indicativeFundingRate'].tolist()[0]
                        
                        # set action to perform: if funding_rate > 0 sell
                        if indicative_funding_rate > 0: 
                        # if indicative_funding_rate < 0: # this is the revers of the funding strategy !!! You will pay when funding takes place 
                            trade_side = 'Sell'
                            new_order = self.exchange.send_smart_order(side=trade_side, orderQty=settings.ORDER_QUANTITY)
                            logger.info('New SELL order : {}'.format(new_order))
                        elif indicative_funding_rate < 0:
                        # elif indicative_funding_rate > 0: # see above. invrse strategy
                            trade_side = 'Buy'
                            new_order = self.exchange.send_smart_order(side=trade_side, orderQty=settings.ORDER_QUANTITY)
                            logger.info('New BUY order : {}'.format(new_order))
                        
                        # Append strategy details to df if order was successfull
                        if new_order: #check if order was created
                            order_status = new_order[0]['ordStatus']
                            if order_status == 'Filled':
                                executed = new_order[0]['orderID']
                        else:
                            executed = False
                else:
                    logger.info('Time delta {} [sec] is > funding rates BEFORE theshold time of {} [sec]. Skipping ...'.format(time_delta, settings.THRESHOLD_TIME_BEFORE))
        
            elif open_position: # there is an open position
                
                if time_delta > settings.THRESHOLD_TIME_AFTER: # passed finding rates -> close position

                        if open_position > 0: # is a buy order
                            trade_side = 'Sell'
                        else:
                            trade_side = 'Buy'
                        
                        new_order = self.exchange.send_smart_order(side=trade_side, orderQty=open_position)
                        # logger.info('New order : {}'.format(new_order))

                        # Append strategy details to df if order was successfull
                        if new_order:
                            order_status = new_order[0]['ordStatus']
                            if order_status == 'Filled':
                                executed = new_order[0]['orderID']
                        else:
                            executed = False
                else:
                    logger.info('Time delta {} [sec] > funding rates AFTER threshold {} [sec]. Skipping ...'.format(time_delta, settings.THRESHOLD_TIME_BEFORE))

        else: # contingent order do nothing but allow the record to be written
            # new_dict = {'timestamp':current_time, 'action':trade_side, 'executed': executed}
            sleep(settings.LOOP_INTERVAL)
            
        new_dict = {'timestamp':current_time, 'action':trade_side, 'executed': executed}
        new_df = pd.DataFrame.from_records([new_dict], index='timestamp') # convert to pandas

        # Concat latest quote with new_df
        latest_record = self.append_colums_df(latest_quote, new_df)
        return latest_record 


    def append_colums_df(self, df, new_df):
        """
        Returns the combined colums of all df. df need to be indexed with datetime
        """
        df = pd.concat([df,new_df], axis=1, join_axes=[df.index])
        return df

class Plotter:
    def draw(self, df):
        
        """
                                   askPrice askSize  bidPrice bidSize  symbol walletBalance marginBalance fundingRate          fundingTimestamp  indicativeFundingRate  action  executed
        timestamp
        2018-04-03 22:42:00+00:00    7384.0    5232    7381.5    1114  XBTUSD    2.97556539    2.97556539   -0.000673 2018-04-04 04:00:00+00:00               0.000218   False     False
        """

        # fig = plt.figure()
        # ax1 = plt.subplot2grid((1,1), (0,0))

        # fig, (ax1, ax2) = plt.subplots(1, 2)
        # my_plotter(ax1, data1, data2, {'marker':'x'})
        # my_plotter(ax2, data3, data4, {'marker':'o'})


        # df['balance'].plot()

        # plt.show()

        # Data for plotting
        timestamp = df.index
        askPrice = df['askPrice']
        bidPrice = df['bidPrice']
        balance = df['walletBalance']
        indicative_funding_rate =  df['indicativeFundingRate']
        actual_funding_rate = df['fundingRate']

        """
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
        fig, (ax1, ax2, ax3) = plt.subplots(3, sharey=False)

        # balance
        ax1.plot(timestamp, balance, 'k-')
        ax1.set(title='Funding Rates Continuous Inverse Strategy v0.3', ylabel='Balance')

        # plot the price
        ax2.plot(timestamp, askPrice, 'r-')
        ax2.plot(timestamp, bidPrice, 'g-')
        # plot the entries
        # set the marker size according to the number of entries
        markersize =  100000 / df.size
        markersize = max(1, min(markersize, 3))

        ax3.plot(timestamp,indicative_funding_rate,'k-')
        ax3.plot(timestamp,actual_funding_rate,'r-')
        #ax2.plot(short_timestamps,short_positions,'ro', markersize=markersize)
        # ax2.plot(timestamp[1], askPrice[1], 'go')
        #ax2.set(ylabel='price')

        # ax3.plot(timestamp, unrealisedPnlPcnt, 'g-')
        # ax3.set(ylabel='unrealisedPnlPcnt')
        plt.show()
import bitmex, json, sys
from datetime import datetime, timezone, date
from datetime import timedelta
from time import sleep
import pandas as pd
import decimal # this module is used to round up the tickSize
from market_maker.utils import log, errors, constants
from market_maker.settings import settings
from market_maker.utils.math import toNearest
from future.utils import iteritems
import atexit
import signal
from market_maker.exchange_interface import ExchangeInterface
from market_maker.tape_interface import Tape
import pytz
import random
import uuid # to generate unique id for linked orders
import stockstats
import math
from market_maker.strategies import funding_rates


logger = log.setup_custom_logger(__name__)
VERSION = 'v0.2'
pd.options.display.width = 300 # for pandas

class OrderManager:

    def __init__(self):
        self.exchange = ExchangeInterface(settings.DRY_RUN)
        # Once exchange is created, register exit handler that will always cancel orders on any error.
        atexit.register(self.exit)
        signal.signal(signal.SIGTERM, self.exit)
        logger.info("Using symbol %s." % self.exchange.symbol)
        # self.start_time = datetime.utcnow()
        self.instrument = self.exchange.get_instrument()
        self.starting_qty = self.exchange.get_currentQty()
        self.running_qty = self.starting_qty
        self.reset()

    def reset(self):
        self.exchange.cancel_all_orders()
        self.exchange.close_position()
        self.sanity_check()
        #self.print_status()
        if settings.DRY_RUN:
            sys.exit()             

    def exit(self):
        """
        Function to execute when exit handle is called
        """
        logger.info("Shutting down. All open orders will be cancelled.")
        try:
            self.exchange.cancel_all_orders()
            self.exchange.close_position()
        except errors.AuthenticationError as e:
            logger.info("Was not authenticated; could not close orders.")
        except Exception as e:
            logger.info("Unable to terminate correctly: %s" % e)
        sys.exit()  

    def print_status(self):
        logger.info("PRINT STATUS IS DEPRECATED. REPLACED BY TAPE LOGGING")
        """Print the current status"""
        margin = self.exchange.get_margin()
        position = self.exchange.get_simpleCost()
        if position and margin:
            logger.info("XBT Balance : %.6f" % margin)
            logger.info("Open Position: {}".format(position))

    def sanity_check(self):
        # Check if OB is empty - if so, can't quote.
        # self.exchange.check_if_orderbook_empty()
        # Ensure market is still open.
        self.exchange.check_market_open()
     
    def momentum(self, seria, periods, array_length):
        # for x in range 0 to array_length, mom becomes a list ... 
        # @periods defines how many candles back to use for the momentum calculation
        mom = [] 
        for x in range(array_length):
            mom.append(seria[x]-seria[periods+x])
        return mom

    def mom_strategy(self, quotes_df):
        """
        If you are selling a stock, you are going to get the BID price, if you are buying a stock you are going to get the ASK price.
        """
        current_time = quotes_df.index.tolist()[0] # extrapolate latest time
        # print(current_time)
        # rather than grabbing the quote from the last minute, use the current ticker
        open_position = self.exchange.get_simpleCost()

        # for logging purposes
        # full_position = self.exchange.get_position()
        # position = 0
        # print(full_position)
        # if (full_position['isOpen']):
            # position = full_position['simpleCost']

        unrealisedPnlPcnt = self.exchange.get_unrealisedPnlPcnt()

        # quote_bid = quotes_df['bidPrice'].tolist()[::-1] # reverse the list
        quote_bid = quotes_df['bidPrice'].tolist()
        quote_ask = quotes_df['askPrice'].tolist()
        action = 'Pass' # default action is 'Pass'
        position_size = 0 # default position size is zero
        price = 0 # default price is zero
        order_size = 0
        # calculate MOMentum
        mom0_ask = self.momentum(quote_ask,12,2) ## index starts form 0, 
        mom1_ask = self.momentum(mom0_ask, 1, 1)
        mom0_bid = self.momentum(quote_bid,12,2) ## index starts form 0, 
        mom1_bid = self.momentum(mom0_bid, 1, 1)
        logger.info('Calculated momentum ASKs: mom0: {}\tmom1: {}'.format(mom0_ask[0],mom1_ask[0]))
        logger.info('Calculated momentum BIDs: mom0: {}\tmom1: {}'.format(mom0_bid[0],mom1_bid[0]))

        # check if momentum is up and if we have open sell positions to be closed
        #if(mom0_ask[0]>0 and mom1_ask[0]>0 and open_position <= 0 and unrealisedPnlPcnt >= 0):
        # if(mom0_ask[0]<0 and mom1_ask[0]<0 and open_position <= 0 and unrealisedPnlPcnt >= 0):
        if(mom0_ask[0]<0 and mom1_ask[0]<0 and open_position <= 0):
        #if(mom0_ask[0]<0 and mom1_ask[0]<0):
            # amount of open shorts to close + default order position
            action = 'Buy'
            position_size = -1*open_position + settings.ORDER_QUANTITY
            self.exchange.cancel_all_orders() # cancels previous orders which might still be pendind
            buy_order = self.exchange.send_smart_order(side=action, orderQty=position_size)
            if buy_order is not None:
                order_size = buy_order[0]['orderQty']
                price = buy_order[0]['price']
                logger.info("NEW BUY Order: {} contract @ {}".format(order_size,price))
            else:
                logger.info("Attention! BUY ORDER IS NONE")
        else:
            pass
        #if(mom0_bid[0]<0 and mom1_bid[0]<0 and open_position >= 0 and unrealisedPnlPcnt >= 0):
        # if(mom0_bid[0]>0 and mom1_bid[0]>0 and open_position >= 0 and unrealisedPnlPcnt >= 0):
        if(mom0_bid[0]>0 and mom1_bid[0]>0 and open_position >= 0):
        #if(mom0_bid[0]>0 and mom1_bid[0]>0):
            # amount of open longs to close - default order position
            action = 'Sell'
            position_size = -1*open_position - settings.ORDER_QUANTITY
            logger.info('Momentum is down, SELLING new position of {} contracts'.format(position_size))
            self.exchange.cancel_all_orders()
            sell_order = self.exchange.send_smart_order(side=action, orderQty=position_size)
            if sell_order is not None:
                order_size = sell_order[0]['orderQty']
                price = sell_order[0]['price']
                order_size = -1*order_size
                logger.info("NEW SELL Order: {} contract @ {}".format(order_size,price))
            else:
                loggel.info("Attention! SELL ORDER IS NONE")
        else:
            pass

        # a strategy should return the action performed, buy/sell or nothing and the amount of the position and the price at which was performed
        # return {'action:'buy|sell|pass', 'amount':int, 'price':float}
        # return {'timestamp':current_time,'action':action, 'amount':position_size, 'price':price}
        return {'timestamp':current_time, 'ASK-mom0':str(mom0_ask[0]), 'ASK-mom1':str(mom1_ask[0]), 'BID-mom0':str(mom0_bid[0]), 'BID-mom1':str(mom1_bid[0]), 'order_size':str(order_size), 'order_price':str(price), 'position':str(open_position), 'unrealisedPnlPcnt':str(unrealisedPnlPcnt)}

    def paul_strategy(self, quotes_df):
        """awesome strategy"""
        pass

    def pnl_strategy(self, quotes_df):
        """
        This strategy takes in consideration unrealised PNL. If the profit is 3% or more closes the trade to take profit. 
        Once the trade is successfully closed send another buy order in the same direction as winning bet. To determine the previous position we store it into the df

        NOTE: If you are selling a stock, you are going to get the BID price, if you are buying a stock you are going to get the ASK price.
        """
        current_time = quotes_df.index.tolist()[0] # extrapolate latest time
        

        full_position = self.exchange.get_position()
        # position = 0
        #print(full_position)
        # if (full_position['isOpen']):
            # position = full_position['simpleCost']

        unrealisedPnlPcnt = self.exchange.get_unrealisedPnlPcnt()

        # quote_bid = quotes_df['bidPrice'].tolist()[::-1] # reverse the list
        quote_bid = quotes_df['bidPrice'].tolist()
        quote_ask = quotes_df['askPrice'].tolist()
        action = 'Pass' # default action is 'Pass'
        position_size = 0 # default position size is zero
        price = 0 # default price is zero
        order_size = 0
        # calculate MOMentum
        #mom0_ask = self.momentum(quote_ask,12,2) ## index starts form 0, 
        #mom1_ask = self.momentum(mom0_ask, 1, 1)
        #mom0_bid = self.momentum(quote_bid,12,2) ## index starts form 0, 
        #mom1_bid = self.momentum(mom0_bid, 1, 1)
        #logger.info('Calculated momentum ASKs: mom0: {}\tmom1: {}'.format(mom0_ask[0],mom1_ask[0]))
        #logger.info('Calculated momentum BIDs: mom0: {}\tmom1: {}'.format(mom0_bid[0],mom1_bid[0]))

        # check if momentum is up and if we have open sell positions to be closed
        #if(mom0_ask[0]>0 and mom1_ask[0]>0 and open_position <= 0 and unrealisedPnlPcnt >= 0):
        # if(mom0_ask[0]<0 and mom1_ask[0]<0 and open_position <= 0 and unrealisedPnlPcnt >= 0):
        action_list = ['Buy', 'Sell']
        random_action = random.choice(action_list)

        # determine if is a long or a short
        open_position = self.exchange.get_simpleCost()
        if open_position < 0:
            action = 'Sell' 
            opposite_action = 'Buy' # set opposite position so we can close it with inverse action
        elif open_position > 0:
            action = 'Buy'
            opposite_action = 'Sell'
        else:
            action = random_action # this is temporary, because I need to store previous winning trade.
            # this action is executed when there are no open positions, therefore at the beginning of 
            # of the bot or after closing a winning/loosing trade
        
        # if PNL is above threshold take profit then open a new order in the same direction
        if(unrealisedPnlPcnt >= 0.03):

            position_size = open_position
            
            self.exchange.cancel_all_orders() # cancels previous orders which might still be pendind
            
            if action is not 'None':
                order = self.exchange.send_smart_order(side=opposite_action, orderQty=position_size)
            
            # if order is not None:
            #     order_size = order[0]['orderQty']
            #     price = order[0]['price']
            #     logger.info("NEW Order: {} contract @ {}".format(order_size,price))
            # else:
            #     logger.info("Attention! ORDER IS NONE")

        
        elif(unrealisedPnlPcnt > -0.003 and unrealisedPnlPcnt < 0.03):
            
            # let the position run
            logger.info("PNL within range: {}".format(unrealisedPnlPcnt))
            
            if (open_position == 0):
                # open a new position
                order = self.exchange.send_smart_order(side=random_action, orderQty=settings.ORDER_QUANTITY)

                # if order is not None:
                #     order_size = order[0]['orderQty']
                #     price = order[0]['price']
                #     logger.info("NEW Order: {} contract @ {}".format(order_size,price))
                # else:
                #     logger.info("Attention! ORDER IS NONE")

        elif(unrealisedPnlPcnt <= -0.003):
            
            # loss stop close position then open in opposite way
            position_size = open_position

            self.exchange.cancel_all_orders() # cancels previous orders which might still be pendind
            
            if action is not 'None':
                order = self.exchange.send_smart_order(side=opposite_action, orderQty=position_size)
            
            # if order is not None:
            #     order_size = order[0]['orderQty']
            #     price = order[0]['price']
            #     logger.info("NEW Order: {} contract @ {}".format(order_size,price))
            # else:
            #     logger.info("Attention! ORDER IS NONE")

        return {'timestamp':current_time, 'order_size':str(order_size), 'order_price':str(price), 'position':str(open_position), 'unrealisedPnlPcnt':str(unrealisedPnlPcnt)}

    def trailstop_strategy(self, new_quote_df, tape):


        """
        LEGACY: this method should not be called and should be removed soon
        """

        logger.info("THIS METHOD SHOULD NOT BE CALLED. IS OUTDATED...")

        """
        @TOD: tape object is not being used, refactor and remove
        """
        """
        Span random orders then set trailing stop with ratio loss/profit.

        Procedure pseudo code:

        1) pick a random entry (buy or sell)
        2) send the random limit-order just above/below the price
        2) wait order to be filled. If order is not filled in time, swap the order around and retry in the other direction
        3) .. wait for confirmation of order is filled
        4) set a trailing stop to execute the opposite trade (set order_quantity and trail value)
        5) if either trailing stop or take profit is executed, cancel all pending orders


        NOTE: If you are selling a stock, you are going to get the BID price, if you are buying a stock you are going to get the ASK price.
        """

        ############################
        # random.seed(0) # remove when done debugging. <------------------------------------
        ############################
        
        random_int = random.randint(0,1)
        action_list = ['Buy','Sell']
        random_action = action_list[random_int]
        logger.info("Random action: {}".format(random_action))
        clOrdLinkID = str(uuid.uuid4()) # generate unique ID


        # Send a new order
        current_time = new_quote_df.index.tolist()[0] # extrapolate latest time
        new_order = self.exchange.send_smart_order(side=random_action, orderQty=settings.ORDER_QUANTITY)
        # logger.info('New order : {}'.format(new_order))

        if new_order: 
            
            logger.info("Order successfully filled. Setting up trailing stop and take profit orders...")
            # logger.info("new_order is {}".format(new_order))

            # Compute ATR for stop limits
            quotes = self.exchange.get_latest_quote(count=200) # count should be same as in ATR smoothing settings
            resample_time = {'1m':'1Min'}
            candles = quotes['askPrice'].resample(resample_time[settings.TIMEFRAME]).ohlc() # group again and sorts 1Min candles (just to make sure!)
            stock_df = stockstats.StockDataFrame.retype(candles)
            atr_df = stock_df['atr_200']
            # logger.info("\n {}".format(atr_df))
            atr = max(1,int(round(atr_df[-1:].tolist()[0])) * settings.OFFSET_MULTIPLIER)
            logger.info("atr: {}\ttrailstop_offset_value: {}".format(atr_df[-1:].tolist()[0], atr))
             
            trailstop_offset_value = atr
            takeprofit_offset_value = atr * settings.OFFSET_RATIO
            logger.info("trailstop_offset_value\t{}".format(trailstop_offset_value))
            logger.info("takeprofit_offset_value\t{}".format(takeprofit_offset_value))

            # Append order details to df (time, action buy, price bought at ?)
            price = new_order[0]['price']
            orderID = new_order[0]['orderID']
            order_quantity = new_order[0]['cumQty'] # use cumQty which return the quantity even on partial orders
            new_dict = {'timestamp':current_time, 'action':random_action, 'execution_price':price, 'orderID':orderID, 'atr':atr}
            new_df = pd.DataFrame.from_records([new_dict], index='timestamp') # convert to pandas

            # Generate two linked orders with OCO (one cancels the other)
            """
            IDEA: a position could be closed if A) a stop loss is triggered, or B) if a timer runs out. The thought behind this is that a stop loss can end in a loss.
            A timed close would only be sensible if timed against the payout times (3 times per day)
            """

            # Trailstop order
            """
            IDEA: for a custom trailstop which get paid green fees: use a stoplimit order, same as a takeprofit order, then on each loop iteraction move it closer to the price if 
            the new_price - old price is in the same direction as the trade, and leave it unchanged if the price has gone against the bid 
            """
            trailstop_order = self.exchange.send_trailing_order(clOrdLinkID=clOrdLinkID, original_side=random_action, pegOffsetValue=trailstop_offset_value, orderQty=settings.ORDER_QUANTITY)
            # this is a temporary limit order not a trailstop
            # trailstop_order = self.exchange.send_stoploss_order(clOrdLinkID=clOrdLinkID, original_side=random_action, takeprofitOffset=trailstop_offset_value, orderQty=settings.ORDER_QUANTITY)
            trailstop_order_id = trailstop_order[0]['orderID']
            trailstop_order_status = trailstop_order[0]['ordStatus']
            
            # Takeprofit order
            takeprofit_order = self.exchange.send_takeprofit_order(clOrdLinkID=clOrdLinkID, original_side=random_action, takeprofitOffset=takeprofit_offset_value, orderQty=settings.ORDER_QUANTITY)
            takeprofit_order_id = takeprofit_order[0]['orderID']
            takeprofit_order_status = takeprofit_order[0]['ordStatus']

        else: # no new order was executed
            new_dict = {'timestamp':current_time, 'action':float('nan'), 'execution_price':float('nan'), 'orderID':float('nan'), 'atr':float('nan')}
            new_df = pd.DataFrame.from_records([new_dict], index='timestamp') # convert to pandas

        # now check if any trade was closed

        # concat latest quote with new_df
        latest_record = self.append_colums_df(new_quote_df, new_df)
        #logger.info("latest_record\n{}".format(latest_record))

        return latest_record 

    def append_colums_df(self, df, new_df):
        """
        Returns the combined colums of all df. df need to be indexed with datetime
        """
        df = pd.concat([df,new_df], axis=1, join_axes=[df.index])
        return df

    def get_balance(self, quotes_df):
        """
        Return a df containing datetime object (index) and balance at the time of latest quote (as string). Use this method to feed the tape object
        """ 
        logger.info("GET_BALANCE IS DEPRECATED. DON'T USE THIS FUNCTION")
        current_time = quotes_df.index.tolist()[0] # extrapolate latest time
        balance_record = {'timestamp':current_time, 'balance':str(self.exchange.get_margin())}
        return balance_record

    def run_loop(self):
        
        """
        Method to run strategy in loop. Execution frequency is defined in the setting file as LOOP_INTERVAL.
        LOOP_INTERVAL should be smaller than the timeframe used for the strategy calculation,
        for example executing trades on a 1m scale should have a LOOP_INTERVAL of ~30 seconds or less.
        
        NOTE: Starting December 11th, 2017 at 12:00 UTC, the following limits will be applied:

        (1) Maximum 200 open orders per contract per account;
        (2) Maximum 10 stop orders per contract per account;
        (3) Maximum 10 contingent orders per contract per account.

        When placing a new order that causes these caps to be exceeded, it will be rejected with the message “Too many [open|stop|contingent] orders”.
        """
        
        previous_quote_time = datetime(2000, 1, 1, 0, 0, 0, 0, pytz.UTC)
        
        max_open_orders = 199
        max_stops = 9
        max_contingents = 2 # 2 to avoid having multiple orders open

        # initialize empty tape
        tape = Tape(dry_run=settings.DRY_RUN)

        # initialize csv
        start_time = datetime.utcnow()
        csv_file = './log_{:%d-%m-%Y_%H.%M.%S}.csv'.format(start_time)
        tape.reset_csv(csv_file) # rest csv

        while True:
            
            sys.stdout.write("-----\n")
            sys.stdout.flush()

            self.sanity_check()

            """
            Check if is time to request a new quote...
            NOTE: the latest BitMex quote is already 1 minutes ahead of the current clock (this I am not sure why, should ask BitMex why such ofset)
            """
            now = datetime.now(timezone.utc)
            # logger.info('Now {}'.format(now))

            # previous quote time is looking to the next minute (!), so 'now' is smaller than previous_quote_time until the last second (59) of each minute
            if (now > previous_quote_time):
                
                logger.info("New cycle ...")
                                        
                ###########################################################################################
                # run a strategy. each strategy must returns a df line with the quote and columns to store
                #new_record = self.trailstop_strategy(latest_quote, tape)
                funding_rates_strategy = funding_rates.Strategy(self.exchange)
                new_record = funding_rates_strategy.run_strategy()
                # append record to tape object
                tape.append_record(new_record)  
                # append latest record to disk
                tape.append_to_csv(new_record, csv_file)
                logger.info("Tape DF after strategy is appended ...\n{}".format(tape.get_df()))
                ###########################################################################################

                # OPTIMIZATION: if the order was not filled try submitting again skipping the sleep
                # DON'T USE OPTIMIZATION IF USING FUNDING STRATEGY (because should not retry if the order is not open)
                """
                executed = new_record.executed.astype(str)[0]
                logger.info("Executed {}".format(executed))
                if executed == 'False':
                    logger.info('No orders detected for this timeframe. Bot will retry skipping the sleep')
                    continue
                else:
                    logger.info("Detected order: {}".format(executed,settings.LOOP_INTERVAL))
                    latest_quote_time = new_record.index.tolist()[0] # extrapolate latest time
                    previous_quote_time = latest_quote_time # update quote time
                """
                logger.info("... sleeping for {} [sec]".format(settings.LOOP_INTERVAL))
                sleep(settings.LOOP_INTERVAL)
            else:
                if (now < previous_quote_time):
                    logger.info("Waiting for new candlestick. Bot will sleep for {}s".format(executed,settings.LOOP_INTERVAL))
                    sleep(settings.LOOP_INTERVAL)

    def collect_fundingRates(self):
            tape = Tape(dry_run=settings.DRY_RUN)
            # rest csv
            csv_file = './test.csv'
            tape.reset_csv(csv_file)

            while True:
                sys.stdout.write("-----\n")
                sys.stdout.flush()
            
                new_record = self.exchange.get_latest_quote_with_funding()
                # append record to the tape object
                tape.append_record(new_record)                    
                
                # append latest record to disk
                tape.append_to_csv(new_record, csv_file)
                logger.info("\nTape DF after strategy is appended ...\n{}".format(tape.get_df()))
                logger.info("Waiting for new quote ... System is sleeping for {}s".format(settings.LOOP_INTERVAL))
                sleep(settings.LOOP_INTERVAL)

    def tmp(self):
        # print(self.get_balance(quotes_df))
        # random.seed(3) # remove when done debugging. <------------------------------------
        # current_time = quotes_df.index.tolist()[0] # extrapolate latest time
        # random_int = random.randint(0,1)
        # action_list = ['Buy','Sell']
        # random_action = action_list[random_int]
        # logger.info("Random action: {}".format(random_action))
        # clOrdLinkID = str(uuid.uuid4()) # generate unique ID
        logger.info("%%%%%%%%%")

        # # set main order
        # order = self.exchange.send_smart_order(side=random_action, orderQty=settings.ORDER_QUANTITY)
        self.bitmex = bitmex.bitmex(test=settings.USE_TESTNET, api_key=settings.API_KEY_TEST, api_secret=settings.API_SECRET_TEST)
        logger.info("Connected to TESTNET")
        # order = self.bitmex.Order.Order_new(symbol=settings.SYMBOL, side='Buy', orderQty=100, ordType='Market').result()
        order = self.bitmex.Order.Order_new(symbol=settings.SYMBOL, side='Buy', orderQty=100, ordType='Limit', execInst='ParticipateDoNotInitiate', price='8700').result()

        order_id = order[0]['orderID']
        
        # logger.info(order)
        
        # logger.info('%%%$$$$$')
        logger.info(self.exchange.cancel_order_by_id(order_id))

def run():
    logger.info('BitMEX Market Maker Version: %s' % VERSION)

    om = OrderManager()
    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        # om.tmp()
        om.run_loop()

        # tmp hack to collect fundingRates
        # om.collect_fundingRates()

    except (KeyboardInterrupt, SystemExit):
        sys.exit()

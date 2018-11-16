import bitmex, json, sys
from datetime import datetime
from time import sleep
import pandas as pd
import decimal # this module is used to round up the tickSize
from market_maker.utils import log, errors, constants
# import mombot.settings as settings
from market_maker.settings import settings
from market_maker.utils.math import toNearest
from future.utils import iteritems
import atexit
import signal
from urllib.error import HTTPError
import time
import keyboard


logger = log.setup_custom_logger(__name__)

class ExchangeInterface:

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        
        if len(sys.argv) > 1:
            self.symbol = sys.argv[1]
        else:
            self.symbol = settings.SYMBOL
        
        if self.dry_run:
            logger.info("Initializing dry run. Orders printed below represent what would be posted to BitMEX.")
        else:
            if (settings.USE_TESTNET):
                logger.info("Connecting to TESTNET")
                try:
                    self.bitmex = bitmex.bitmex(test=settings.USE_TESTNET, api_key=settings.API_KEY_TEST, api_secret=settings.API_SECRET_TEST)
                    logger.info("Connected to TESTNET")

                except:
                    logger.error("Can't connect to Bitmex. Please check your connection")
            else:
                logger.info("Connecting to REAL")
                try:
                    self.bitmex = bitmex.bitmex(test=settings.USE_TESTNET, api_key=settings.API_KEY_REAL, api_secret=settings.API_SECRET_REAL)
                    logger.info("Connected to REALNET")
                except:
                    logger.error("Can't connect to Bitmex. Please check your connection")
            # append order prefix to identify bot id
            self.orderIDPrefix=settings.ORDERID_PREFIX

    def get_instrument(self, symbol=None):
        """
        Instrument is the currency pair we are trading. In this case XBTUSD.
        We filter out only the one in use XBTUSD
        """
        if symbol is None:
            symbol = self.symbol
        try:
            instrument = None
            while not instrument:
                instrument = self.bitmex.Instrument.Instrument_get(filter=json.dumps({'symbol':symbol})).result()
            instrument = instrument[0][0]
            instrument['tickLog'] = decimal.Decimal(str(instrument['tickSize'])).as_tuple().exponent * -1 # tickLog represent the number of decimal points on the right of the comma 0.1234...
            # if instrument is None:
                # raise errors.MarketEmptyError("Instrument is empty")
            # logger.info("Instrument correctly imported")
        except:
            logger.info("Connection error. Couldn't retrive 'instrument'. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            instrument =  self.get_instrument()
        return instrument

    def get_currentQty(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        return self.get_position(symbol)['currentQty']

    def get_simpleCost(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        try:
            position = self.get_position(symbol)
            if position is None: 
                raise errors.MarketEmptyError("Couldn't get simplecost")
            simpleCost = position['simpleCost'] 
            return simpleCost
        except:
            logger.info("Connection error. Couldn't retrive 'simple_cost'. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            self.get_simpleCost()

    def get_unrealisedPnlPcnt(self, symbol=None):
        """
        return the unrealised profit and loss as percentage
        """
        if symbol is None:
            symbol = self.symbol
        position = self.get_position(symbol)
        pnl = position['unrealisedPnlPcnt'] 
        return pnl
        # print("########")
        # print(pnl)
        # timestamp = position['timestamp']
        # record = {'timestamp':timestamp, 'unrealisedPnlPcnt':str(pnl)}
        # tmp_df = pd.DataFrame.from_dict([record]) # convert to pandas
        # tmp_df.set_index('timestamp', inplace=True) # set the df index
        # tmp_df.index = pd.to_datetime(tmp_df.index) # convert index to datetime obj
        # tmp_df = tmp_df.dropna(axis=0, how='all') # remove nans
        # return tmp_df

    def get_position(self, symbol=None):
        """
        simpleCost is expressed in USD
        currentQty is expressed in XBT

        "account": 25306,
        "commission": 0.00075,
        "initMarginReq": 0.3333333333333333,
        "maintMarginReq": 0.005,
        "riskLimit": 20000000000,
        "leverage": 3,
        "crossMargin": false,
        "deleveragePercentile": 1,
        "rebalancedPnl": 23624,
        "prevRealisedPnl": -272,
        "prevUnrealisedPnl": 0,
        "prevClosePrice": 10631.26,
        "openingTimestamp": "2018-03-08T00:00:00.000Z",
        "openingQty": 0,
        "openingCost": 30870,
        "openingComm": -11599,
        "openOrderBuyQty": 0,
        "openOrderBuyCost": 0,
        "openOrderBuyPremium": 0,
        "openOrderSellQty": 0,
        "openOrderSellCost": 0,
        "openOrderSellPremium": 0,
        "execBuyQty": 180,
        "execBuyCost": 1793670,
        "execSellQty": 150,
        "execSellCost": 1499190,
        "execQty": 30,
        "execCost": -294480,
        "execComm": -221,
        "currentTimestamp": "2018-03-08T01:34:51.019Z",
        "currentQty": 30,
        "currentCost": -263610,
        "currentComm": -11820,
        "realisedCost": 35370,
        "unrealisedCost": -298980,
        "grossOpenCost": 0,
        "grossOpenPremium": 0,
        "grossExecCost": 298945,
        "isOpen": true,
        "markPrice": 9976.27,
        "markValue": -300720,
        "riskValue": 300720,
        "homeNotional": 0.0030072,
        "foreignNotional": -30,
        "posState": "",
        "posCost": -298980,
        "posCost2": -298980,
        "posCross": 0,
        "posInit": 99660,
        "posComm": 299,
        "posLoss": 0,
        "posMargin": 99959,
        "posMaint": 2916,
        "posAllowance": 0,
        "taxableMargin": 0,
        "initMargin": 0,
        "maintMargin": 98219,
        "sessionMargin": 0,
        "targetExcessMargin": 0,
        "varMargin": 0,
        "realisedGrossPnl": -35370,
        "realisedTax": 0,
        "realisedPnl": -23550,
        "unrealisedGrossPnl": -1740,
        "longBankrupt": 0,
        "shortBankrupt": 0,
        "taxBase": 0,
        "indicativeTaxRate": 0,
        "indicativeTax": 0,
        "unrealisedTax": 0,
        "unrealisedPnl": -1740,
        "unrealisedPnlPcnt": -0.0058,
        "unrealisedRoePcnt": -0.0175,
        "simpleQty": 0.003,
        "simpleCost": 30,
        "simpleValue": 30,
        "simplePnl": 0,
        "simplePnlPcnt": 0,
        "avgCostPrice": 10034,
        "avgEntryPrice": 10034,
        "breakEvenPrice": 10032.5,
        "marginCallPrice": 7576,
        "liquidationPrice": 7576,
        "bankruptPrice": 7526,
        "timestamp": "2018-03-08T01:34:51.019Z",
        "lastPrice": 9976.27,
        "lastValue": -300720
        
"""
        if symbol is None:
            symbol = self.symbol
        try:
            position = self.bitmex.Position.Position_get(filter=json.dumps({'symbol':symbol})).result()[0][0]
            if position is None:
                raise errors.MarketEmptyError("Position is empty")
            # logger.info("Position correctly imported")
            # print(position)
            return position
        except:
            logger.info("Connection error. Couldn't retrive 'position'. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            self.get_position()

    def get_quoteBucketed(self, symbol=None, count=settings.BUFFER):

        """
        OUTDATED ---> REMOVE THIS METHOD
        """
        logger.info("get_quoteBucketed is outdated, should not be used")
        """
        """
        if symbol is None:
            symbol = self.symbol
        try:
            # quote = self.bitmex.Quote.Quote_getBucketed(symbol=symbol, reverse=False, binSize=settings.TIMEFRAME, count=settings.BUFFER, partial=False).result()[0]
            quote = self.bitmex.Quote.Quote_getBucketed(symbol=symbol, reverse=True, binSize=settings.TIMEFRAME, count=count, partial=False).result()[0]
            if quote is None:
                raise errors.MarketEmptyError("Quote is empty")
            # logger.info("QuoteBucketed correctly imported")
            return quote
        except:
            logger.info("Connection error. Couldn't retrive 'quoteBucketed'. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            self.get_quoteBucketed()

    def get_latest_quote(self, symbol="XBTUSD", binSize=settings.TIMEFRAME, partial=False, count=1):
        
        """
        @returns data-frame containing quotes for the past x minutes
        
        DF created:
                                    askPrice  askSize  bidPrice  bidSize  symbol available_margin available_margin
        timestamp
        2018-03-14 17:45:00+00:00    8363.5      700    8352.0    21266  XBTUSD       3.13691847       3.13691847
        --------------------------------------------------------------------------------------------------------------                
        """
        
        # Return a list of dictionaries containing quotes sorted in reverse order
        quote = self.bitmex.Quote.Quote_getBucketed(symbol=symbol, reverse=True, binSize=settings.TIMEFRAME, count=count, partial=partial).result()[0]
        df = pd.DataFrame.from_dict(quote) # convert to pandas
        
        """
        # df = df.dropna(axis=0, how='all') # remove nans
        # logger.info('\n {}'.format(df))
        The following part is redundant and here because of legacy: it is not necessary if you get bucketed quotes per minutes and display data for the 1m timefarme.
        The candles would all be the same hloc values.

        # resample_time = {'1m':'1Min'}
        # candle_df = df[column].resample(resample_time[settings.TIMEFRAME]).ohlc() # group again and sorts 1Min candles (just to make sure!)
        # print(candle_df)
        """

        # add datetime, margin and balance to the DF
        df.set_index('timestamp', inplace=True) # set the df index
        df.index = pd.to_datetime(df.index) # convert index to datetime obj
        current_time = df.index.tolist()[0] # extrapolate latest time
        
        # margin balance df
        margin_balance = self.bitmex.User.User_getMargin(currency='XBt').result()[0]['marginBalance']
        margin_in_XBT = self.XBt_to_XBT(margin_balance)
        available_margin_record = {'timestamp':current_time, 'marginBalance':str(margin_in_XBT)}
        margin_df = pd.DataFrame.from_records([available_margin_record], index='timestamp') # convert to pandas
        
        # wallet balance df
        wallet_balance = self.bitmex.User.User_getMargin(currency='XBt').result()[0]['walletBalance']
        wallet_in_XBT = self.XBt_to_XBT(wallet_balance)
        available_wallet_record = {'timestamp':current_time, 'walletBalance':str(margin_in_XBT)}
        wallet_df = pd.DataFrame.from_records([available_wallet_record], index='timestamp') # convert to pandas

        # merge DFs
        combined_df = pd.concat([df, wallet_df, margin_df], axis=1) # join axes is not needed as there is only one row
        
        return combined_df

    def get_latest_quote_with_funding(self, symbol="XBTUSD", binSize=settings.TIMEFRAME, partial=False, count=1):
        
        """
        @returns data-frame containing quotes for the past x minutes
        
        DF created:
                                   askPrice  askSize  bidPrice  bidSize  symbol walletBalance marginBalance fundingRate  indicativeFundingRate
        timestamp
        2018-04-02 03:05:00+00:00    6949.5   500924    6939.0     1010  XBTUSD    3.13026403    3.13026403   -0.001697               0.001086
        --------------------------------------------------------------------------------------------------------------                
        """
        
        # Return a list of dictionaries containing quotes sorted in reverse order
        quote = self.bitmex.Quote.Quote_getBucketed(symbol=symbol, reverse=True, binSize=settings.TIMEFRAME, count=count, partial=partial).result()[0]
        df = pd.DataFrame.from_dict(quote) # convert to pandas
        
        """
        # df = df.dropna(axis=0, how='all') # remove nans
        # logger.info('\n {}'.format(df))
        The following part is redundant and here because of legacy: it is not necessary if you get bucketed quotes per minutes and display data for the 1m timefarme.
        The candles would all be the same hloc values.

        # resample_time = {'1m':'1Min'}
        # candle_df = df[column].resample(resample_time[settings.TIMEFRAME]).ohlc() # group again and sorts 1Min candles (just to make sure!)
        # print(candle_df)
        """

        # add datetime, margin and balance to the DF
        df.set_index('timestamp', inplace=True) # set the df index
        df.index = pd.to_datetime(df.index) # convert index to datetime obj
        current_time = df.index.tolist()[0] # extrapolate latest time
        
        # margin balance df
        margin_balance = self.bitmex.User.User_getMargin(currency='XBt').result()[0]['marginBalance']
        margin_in_XBT = self.XBt_to_XBT(margin_balance)
        available_margin_record = {'timestamp':current_time, 'marginBalance':str(margin_in_XBT)}
        margin_df = pd.DataFrame.from_records([available_margin_record], index='timestamp') # convert to pandas
        
        # wallet balance df
        wallet_balance = self.bitmex.User.User_getMargin(currency='XBt').result()[0]['walletBalance']
        wallet_in_XBT = self.XBt_to_XBT(wallet_balance)
        available_wallet_record = {'timestamp':current_time, 'walletBalance':str(margin_in_XBT)}
        wallet_df = pd.DataFrame.from_records([available_wallet_record], index='timestamp') # convert to pandas

        # funding rate data
        funding_time = self.get_instrument()['fundingTimestamp']
        funding_rate = self.get_instrument()['fundingRate']
        indicative_funding_rate = self.get_instrument()['indicativeFundingRate']
        funding_record = {'timestamp':current_time, 'fundingTimestamp':funding_time, 'fundingRate':str(funding_rate), 'indicativeFundingRate':indicative_funding_rate}
        funding_df = pd.DataFrame.from_records([funding_record], index='timestamp') # convert to pandas

        # merge DFs
        combined_df = pd.concat([df, wallet_df, margin_df, funding_df], axis=1) # join axes is not needed as there is only one row
        
        return combined_df

    def cancel_order_by_id(self, id):
        if self.dry_run:
            return
        try:
            logger.info("Cancelling order id {}".format(id))
            tickLog = self.get_instrument()['tickLog'] # tickLog represent the number of decimal points on the right of the comma 0.1234...        
            cancelled_order = self.bitmex.Order.Order_cancel(orderID=id, text='Time too long').result()[0][0]
            # logger
            # if cancelled_order:
                # logger.info("Cancelled: %s %d @ %.*f" % (cancelled_order['side'], cancelled_order['orderQty'], tickLog, cancelled_order['price']))
            # if cancelled_order is None:
                # raise errors.MarketEmptyError("Orderbook is empty, cannot quote")
            return cancelled_order
        # else:
        #     logger.info("No order was cancel")
        #     return
        except:
            logger.info("Unexprected error", sys.exc_info()[0])
            logger.info("Connection error. Couldn't cancel all orders. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            return self.cancel_order_by_id(id)

    def cancel_all_orders(self):
        if self.dry_run:
            return
        logger.info("Resetting current orders. Cancelling pending orders.")
        tickLog = self.get_instrument()['tickLog'] # tickLog represent the number of decimal points on the right of the comma 0.1234...
        orders = self.bitmex.Order.Order_cancelAll().result()[0]

        if len(orders):
            for order in orders:
                logger.info("Cancelling order: {}".format(order['orderID']))
            return orders
        else:
            logger.info("No orders to cancel")
            return

    def close_position(self):
        if self.dry_run:
            return
        logger.info("Resetting current position. Cancelling all open positions.")
        # check how much we have open
        # logger.info(self.get_position()['simpleCost'])
        open_position = self.get_position()['simpleCost']
        # then close the position
        if (open_position != 0):
            # if there was an open position print out the id, symbol and amount to close
            position_to_close = self.bitmex.Order.Order_closePosition(symbol=self.symbol).result()[0]
            logger.info("Closing position: {}".format(position_to_close['orderID']))
        else:
            logger.info("No position to close.")

###################
    def get_order_with_id(self, id):
        if self.dry_run:
            return []
        try:
            order = self.bitmex.Order.Order_getOrders(filter=json.dumps({'orderID':str(id)})).result()[0]
            return order
        except:
            logger.info("Connection error. Couldn't get order with id. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            return self.get_order_with_id()
####################

    def get_num_open_orders(self):
        if self.dry_run:
            return []
        try:
            orders = self.bitmex.Order.Order_getOrders(filter=json.dumps({'ordStatus':'New'})).result()[0]
            order_num = len(orders)
            logger.info("Total open orders: {}".format(order_num))
            return order_num
        except:
            logger.info("Connection error. Couldn't get num open orders. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            return self.get_num_open_orders()
####################

    def get_num_contingent_orders(self):
        if self.dry_run:
            return []
        try:
            counter = 0
            orders = self.bitmex.Order.Order_getOrders(filter=json.dumps({'ordStatus':'New'})).result()[0]
            if orders:
                for order in orders:
                    if order['clOrdLinkID']:
                        counter = counter + 1
                logger.info("Total contingent orders: {}".format(counter))
            return counter
        except:
            logger.info("Connection error. Couldn't get num contingent orders. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            return self.get_num_contingent_orders()
####################

    def get_orders(self):
        if self.dry_run:
            return []
        try:
            # orders = self.bitmex.Order.Order_getOrders(filter=json.dumps({'ordStatus.isTerminated':False})).result()[0]
            # orders = self.bitmex.Order.Order_getOrders(filter=json.dumps({'ordStatus':'New'})).result()[0]
            orders = self.bitmex.Order.Order_getOrders().result()[0]
            # Only return orders that start with our clOrdID prefix.
            if orders:
                # logger.info("Orders correctly imported")
                return [o for o in orders if str(o['clOrdID']).startswith(self.orderIDPrefix)]
            else:
                logger.error("Couldn't get orders")
        except:
            logger.info("Connection error. Couldn't get orders. Sleeping...")
            sleep(settings.LOOP_INTERVAL)
            return self.get_orders()
####################            

    def check_market_open(self):
        instrument = self.get_instrument()
        if not instrument:
        # if instrument["state"] != "Open":
            raise errors.MarketClosedError("The instrument %s is not open. State: %s" %(self.symbol, instrument["state"]))
            # send email ? 
        
    def get_ticker(self, instrument, symbol=None):
        '''
        Return a ticker dictionary with last, buy, sell and mid. Generated from instrument. NOTE: Values are rounded up with tick size
        I.E. {'last': 10563.5, 'buy': 10563.5, 'sell': 10564.0, 'mid': 10564.0}
        '''
        if symbol is None:
            symbol = self.symbol

        # instrument = self.get_instrument(symbol)

        # If this is an index, we have to get the data from the last trade.
        if instrument['symbol'][0] == '.':
            ticker = {}
            ticker['mid'] = ticker['buy'] = ticker['sell'] = ticker['last'] = instrument['markPrice']
        # Normal instrument
        else:
            bid = instrument['bidPrice'] or instrument['lastPrice']
            ask = instrument['askPrice'] or instrument['lastPrice']
            ticker = {
                "last": instrument['lastPrice'],
                "buy": bid,
                "sell": ask,
                "mid": (bid + ask) / 2
            }

        # The instrument has a tickSize. Use it to round values.
        #print({k: toNearest(float(v or 0), instrument['tickSize']) for k, v in iteritems(ticker)})
        return {k: toNearest(float(v or 0), instrument['tickSize']) for k, v in iteritems(ticker)}

    def get_margin(self):
        """
        Margin is the amount of equity expressed in XBT
        """
        logger.info("DEPRECATED FUNCTION USE GET_LATEST_QUOTE TO RETURN A DF !!!!")
        if self.dry_run:
            return {'marginBalance': float(settings.DRY_BTC), 'availableFunds': float(settings.DRY_BTC)}
        try:
            margin_balance = self.bitmex.User.User_getMargin(currency='XBt').result()[0]['marginBalance']
            if margin_balance:
                margin_in_XBT = self.XBt_to_XBT(margin_balance)
                # logger.info("Imported margin")
                return margin_in_XBT
            else:
                raise errors.MarketEmptyError("Margin is empty")
        except:
            sleep(settings.LOOP_INTERVAL)
            self.get_margin()

    def XBt_to_XBT(self, XBt):
        return float(XBt) / constants.XBt_TO_XBT        

    def send_trailing_order(self, clOrdLinkID, original_side, pegOffsetValue=settings.TRAILSTOP_OFFSET, orderQty=settings.ORDER_QUANTITY, symbol=None):
        if symbol is None:
            symbol = self.symbol
        # try:           
            # Define variables
        if original_side == 'Buy': # if we have a buy we need to sell and to set an offset to price - offsett
            opposite_side = 'Sell'
            pegOffsetValue = pegOffsetValue * -1
        if original_side == 'Sell':
            opposite_side = 'Buy'
        orderQty = settings.ORDER_QUANTITY # should be equal to the bidding quantity
        pegPriceType = 'TrailingStopPeg' # follows the price movement in one direction
        # execInst = 'LastPrice, ParticipateDoNotInitiate'  # this could be assigned to the mark price, but for now uses the last-price
        execInst = 'LastPrice'  # this could be assigned to the mark price, but for now uses the last-price
        contingencyType = 'OneCancelsTheOther' # to allow the stoploss and takeprofit to be linked
        # ordType ='LimitIfTouched'
        # ordType ='Stop'

        # SET SMART ORDERS
        order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, clOrdLinkID=clOrdLinkID, pegOffsetValue=pegOffsetValue, pegPriceType=pegPriceType, execInst=execInst, contingencyType=contingencyType).result()

        # LOGGING
        if order is not None:
            order_size = order[0]['orderQty']
            price = order[0]['price']
            logger.info("NEW Trailing Order: {} contract @ {}".format(order_size,price))
        else:
            logger.info("Attention! ORDER IS NONE")

        return order
        # except :
            # logger.info("Couldn't place the order")
            # sleep(settings.LOOP_INTERVAL)
            # self.send_smart_order(opposite_side, orderQty, symbol)

    def send_stoploss_order(self, clOrdLinkID, original_side, takeprofitOffset=settings.TAKEPROFIT_OFFSET, orderQty=settings.ORDER_QUANTITY, symbol=None):
        if symbol is None:
            symbol = self.symbol
        try:
            # Define variables
            orderQty = settings.ORDER_QUANTITY
            # ordType ='StopLimit'
            ordType ='Stop'
            # execInst = 'LastPrice, ParticipateDoNotInitiate'
            execInst = 'MarkPrice' # mark price uses the sma of the price to avoid spikes
            # execInst='ParticipateDoNotInitiate' # might want to use this to get green fees (to test)
            contingencyType = 'OneCancelsTheOther'
            instrument = self.get_instrument(symbol)
            ticker = self.get_ticker(instrument)            
            # Set up our buy & sell positions as the smallest possible unit above and below the current spread
            if original_side == 'Buy':
                stopPx = ticker["sell"] - takeprofitOffset
                position_limit = ticker["sell"] - takeprofitOffset - instrument['tickSize']
                opposite_side = 'Sell'
            else:
                stopPx = ticker["buy"] + takeprofitOffset
                position_limit = ticker["buy"] + takeprofitOffset + instrument['tickSize'] 
                opposite_side = 'Buy'

            # SET SMART ORDERS
            # order = self.bitmex.Order.Order_new(symbol=symbol, orderQty=orderQty, original_side=opposite_side, price=position_limit, stopPx=stopPx, ordType=ordType, execInst=execInst).result()
            # order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, price=position_limit, stopPx=stopPx, clOrdLinkID=clOrdLinkID, ordType=ordType, execInst=execInst, contingencyType=contingencyType).result()
            # order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, stopPx=stopPx, clOrdLinkID=clOrdLinkID, ordType=ordType, execInst=execInst, contingencyType=contingencyType).result()
            # order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, price=position_limit, stopPx=stopPx, clOrdLinkID=clOrdLinkID, ordType=ordType, execInst=execInst, contingencyType=contingencyType).result()
            # order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, stopPx=stopPx, clOrdLinkID=clOrdLinkID, ordType=ordType, execInst=execInst, contingencyType=contingencyType).result()
            order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, stopPx=stopPx, clOrdLinkID=clOrdLinkID, ordType=ordType, execInst=execInst, contingencyType=contingencyType).result()
            # logger.info(order)

            # LOGGING
            if order is not None:
                order_size = order[0]['orderQty']
                price = order[0]['price']
                logger.info("NEW Takeprofit Order: {} contract @ {}".format(order_size,price))
            else:
                logger.info("Attention! ORDER IS NONE")

            return order
        except:
            # logger.info("Unexpected error", sys.exc_info()[0])
            logger.info("Couldn't place the order")
            return
            # sleep(settings.LOOP_INTERVAL)
            # self.send_smart_order(side, orderQty, symbol)  

    def send_takeprofit_order(self, clOrdLinkID, original_side, takeprofitOffset=settings.TAKEPROFIT_OFFSET, orderQty=settings.ORDER_QUANTITY, symbol=None):
        if symbol is None:
            symbol = self.symbol

        # Define variables
        orderQty = settings.ORDER_QUANTITY
        
        # green fees
        # ordType ='LimitIfTouched'
        # execInst = 'LastPrice, ParticipateDoNotInitiate, ReduceOnly'
        
        # for limit
        ordType ='Limit'
        execInst = 'ReduceOnly'
        
        contingencyType = 'OneCancelsTheOther'
        instrument = self.get_instrument(symbol)
        ticker = self.get_ticker(instrument)            
        # Set up our buy & sell positions as the smallest possible unit above and below the current spread
        if original_side == 'Buy':
            stopPx = ticker["sell"] + takeprofitOffset
            position_limit = ticker["sell"] + takeprofitOffset + instrument['tickSize']
            opposite_side = 'Sell'
        else:
            stopPx = ticker["buy"] - takeprofitOffset
            position_limit = ticker["buy"] - takeprofitOffset - instrument['tickSize'] 
            opposite_side = 'Buy'

        # SET SMART ORDERS

        # regular limit order
        order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, price=position_limit, clOrdLinkID=clOrdLinkID, ordType=ordType, execInst=execInst, contingencyType=contingencyType).result()

        # green fees
        # order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, price=position_limit, stopPx=stopPx, clOrdLinkID=clOrdLinkID, ordType=ordType, execInst=execInst, contingencyType=contingencyType).result()
        
        # LOGGING
        if order is not None:
            order_size = order[0]['orderQty']
            price = order[0]['price']
            logger.info("NEW Takeprofit Order: {} contract @ {}".format(order_size,price))
        else:
            logger.info("Attention! ORDER IS NONE")
        return order
          
    def send_smart_order(self, side, orderQty=settings.ORDER_QUANTITY, symbol=None):
        """
        send_smart_order is automatically setting BUY/SELL price to ensure we get paid market-maker fees
        @return a list of orders
        @return null if cannot cancel the orders
        """
        if symbol is None:
            symbol = self.symbol
        
        # try:
        instrument = self.get_instrument(symbol)
        ticker = self.get_ticker(instrument)
        # Set up our buy & sell positions as the smallest possible unit above and below the current spread
        # and we'll work out from there. That way we always have the best price but we don't kill wide
        # and potentially profitable spreads.

        
        # SET ORDERS
        # buy_order = self.exchange.Order.Order_new(symbol='XBTUSD', side='Buy', orderQty=10, ordType='Market').result() # this should be optimized avoiding a market order
        # TODO: check if there is enough balance
        # order = self.bitmex.Order.Order_new(symbol=symbol, side=side, orderQty=orderQty, ordType='Market').result() # this should be optimized avoiding a market order
        if (side=='Buy'):
            opposite_side = 'Sell'
            position_limit = ticker["buy"] - (instrument['tickSize'])
        else:
            opposite_side = 'Buy'
            position_limit = ticker["sell"] + (instrument['tickSize'])
        
        order = self.bitmex.Order.Order_new(symbol=symbol, side=side, orderQty=orderQty, ordType='Limit', execInst='ParticipateDoNotInitiate', price=position_limit).result()

        if order:
            
            order_status = order[0]['ordStatus']
            
            if order_status == 'New':
                order_size = order[0]['orderQty']
                price = order[0]['price']
                order_id = order[0]['orderID']
                order_side = order[0]['side']
                order_time = time.perf_counter() # start a timer
                logger.info("NEW {} Order: {} contract @ {}".format(order_side, order_size, price))
            else:
                # logger.info(order_status)
                return
                        
            while order_status == 'New':

                sleep(max(3,settings.SMART_ORDER_TIMEOUT/100)) # wait at least x sec
            
                # check if the time elapsed since order is above threshold, then clear out the order
                current_time = time.perf_counter()
                elapsed_time = current_time - order_time
                
                logger.info("Waiting for order {} to fill.\tElapsed time: {:3.1f}s ...".format(order_id, elapsed_time))

                # get order updated details
                order = self.get_order_with_id(order_id)
                order_status = order[0]['ordStatus']

                if elapsed_time > settings.SMART_ORDER_TIMEOUT and order_status == 'New': # if time passed is greather than threshold and order is still new ... 
                    logger.info("Elapsed time waiting to fill order is too long {}s.".format(settings.SMART_ORDER_TIMEOUT))
                    # cancel order
                    canceled_order = self.cancel_order_by_id(order_id)
                    """
                    the assumption here is that if the order is not filled is because the price trend is moving in the same direction as our bet, 
                    which in other words means we are on the winning side of the trade => send the order with same direction at market price
                    """
                    # order = self.bitmex.Order.Order_new(symbol=symbol, side=side, orderQty=orderQty, ordType='Market').result() 
                    """
                    # alternative idea: if the order doesn't fill in time send an order with opposite side
                    order = self.bitmex.Order.Order_new(symbol=symbol, side=opposite_side, orderQty=orderQty, ordType='Limit', execInst='ParticipateDoNotInitiate', price=position_buy_limit).result() 
                    """
                    return
                    # break
            
            # refresh the order status
            order = self.get_order_with_id(order_id)
            order_status = order[0]['ordStatus']
            logger.info("OrderID {} status: {}".format(order_id, order_status))
            
            if order_status == 'New': # this should not happene
                logger.info("Order Status is still New, this should not happen")
                pass
            elif order_status == 'Filled':
                return order
            elif order_status == 'Canceled':
                return # empty order
            elif order_status == 'PartiallyFilled':
                # cancel remaining order
                order_id = order[0]['orderID']
                canceled_order = self.cancel_order_by_id(order_id)
                return order
            else: 
                logger.error("ATTENTION: Order status is not recognised : {}".format(order_status))
                raise systemExit # quit
        else:
            logger.error("COULDN'T SEND ORDER TO BITMEX. ORDER IS NONE!")
from os.path import join
import logging

########################################################################################################################
# Connection/Auth
########################################################################################################################

# API URL.
BASE_URL = "https://testnet.bitmex.com/api/v1/"
# BASE_URL = "https://www.bitmex.com/api/v1/" # Once you're ready, uncomment this.

# The BitMEX API requires permanent API keys. Go to https://testnet.bitmex.com/api/apiKeys to fill these out.
USE_TESTNET = True

API_KEY_TEST = "bq7g_XTdbMVnChs4eGW7hzO-"
API_SECRET_TEST = "sOK-EDk-tPGxhLpSeScspx5niAvVg02mok9RmoUuZrXKQWYJ"

API_KEY_REAL = "xxxxxxxxxxx"
API_SECRET_REAL = "xxxxxxxxxxxxxxxxxx"

########################################################################################################################
# Target
########################################################################################################################

# Instrument to market make on BitMEX.
SYMBOL = "XBTUSD"

########################################################################################################################
# Order Size & Spread
########################################################################################################################

# How many pairs of buy/sell orders to keep open
ORDER_PAIRS = 6

# ORDER_START_SIZE will be the number of contracts submitted on level 1
# Number of contracts from level 1 to ORDER_PAIRS - 1 will follow the function
# [ORDER_START_SIZE + ORDER_STEP_SIZE (Level -1)]
# ORDER_START_SIZE = 100
# ORDER_STEP_SIZE = 100

# Distance between successive orders, as a percentage (example: 0.005 for 0.5%)
# INTERVAL = 0.005

# Minimum spread to maintain, in percent, between asks & bids
# MIN_SPREAD = 0.01

# If True, market-maker will place orders just inside the existing spread and work the interval % outwards,
# rather than starting in the middle and killing potentially profitable spreads.
# MAINTAIN_SPREADS = True

# This number defines far much the price of an existing order can be from a desired order before it is amended.
# This is useful for avoiding unnecessary calls and maintaining your ratelimits.
#
# Further information:
# Each order is designed to be (INTERVAL*n)% away from the spread.
# If the spread changes and the order has moved outside its bound defined as
# abs((desired_order['price'] / order['price']) - 1) > settings.RELIST_INTERVAL)
# it will be resubmitted.
#
# 0.01 == 1%
# RELIST_INTERVAL = 0.01


########################################################################################################################
# Trading Behavior
########################################################################################################################

# How often to re-check and replace orders. This should be adjusted based on the TIMEFRAME parameter
"""
Starting December 11th, 2017 at 12:00 UTC, the following limits will be applied:

(1) Maximum 200 open orders per contract per account;
(2) Maximum 10 stop orders per contract per account;
(3) Maximum 10 contingent orders per contract per account.

When placing a new order that causes these caps to be exceeded, it will be rejected with the message “Too many [open|stop|contingent] orders”.
"""
BUFFER = 16

# Position limits - set to True to activate. Values are in contracts.
# If you exceed a position limit, the bot will log and stop quoting that side.
CHECK_POSITION_LIMITS = False
MIN_POSITION = -10000
MAX_POSITION = 10000

# If True, will only send orders that rest in the book (ExecInst: ParticipateDoNotInitiate).
# Use to guarantee a maker rebate.
# However -- orders that would have matched immediately will instead cancel, and you may end up with
# unexpected delta. Be careful.
POST_ONLY = False

########################################################################################################################
# Misc Behavior, Technicals
########################################################################################################################



# Wait times between orders / errors
API_REST_INTERVAL = 1
API_ERROR_INTERVAL = 10
TIMEOUT = 7

# If we're doing a dry run, use these numbers for BTC balances
DRY_BTC = 50

# Available levels: logging.(DEBUG|INFO|WARN|ERROR)
LOG_LEVEL = logging.INFO

# To uniquely identify orders placed by this bot, the bot sends a ClOrdID (Client order ID) that is attached
# to each order so its source can be identified. This keeps the market maker from cancelling orders that are
# manually placed, or orders placed by another bot.
#
# If you are running multiple bots on the same symbol, give them unique ORDERID_PREFIXes - otherwise they will
# cancel each others' orders.
# Max length is 13 characters.
ORDERID_PREFIX = "mm_bitmex_"

# If any of these files (and this file) changes, reload the bot.
WATCHED_FILES = [join('market_maker', 'market_maker.py'), join('market_maker', 'bitmex.py'), 'settings.py']


########################################################################################################################
# BitMEX Portfolio
########################################################################################################################

# Specify the contracts that you hold. These will be used in portfolio calculations.
CONTRACTS = ['XBTUSD']

########################################################################################################################
# Tape Settings
########################################################################################################################

########################################################################################################################
# GLOBAL settings
########################################################################################################################
# If true, don't set up any orders, just say what we would do
DRY_RUN = False
TIMEFRAME = '1m' 

########################################################################################################################
# Trailstop and takeprofit algo settings
########################################################################################################################
# How big each order (in contracts) 
#ORDER_QUANTITY = 30 
# TRAILSTOP_OFFSET = 35 # (IN CONTRACTS - USD)
# TAKEPROFIT_OFFSET = 70
OFFSET_RATIO = 2 # ratio between take profit and stop loss
OFFSET_MULTIPLIER = 10 # ATR multiplier for the offset between entry price and stop-loss
# Keep the system idle while waiting for smart_order to be filled. To make sure the quotes are queried each minute the idle time should be < 60s

########################################################################################################################
# Funding rates strategy
########################################################################################################################
SMART_ORDER_TIMEOUT = 30  
LOOP_INTERVAL = 15
THRESHOLD_TIME_BEFORE = 240
THRESHOLD_TIME_AFTER = 10
ORDER_QUANTITY = 100000
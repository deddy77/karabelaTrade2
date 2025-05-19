//+------------------------------------------------------------------+
//|                                              KarabelaTrade.mq5     |
//|                                      Copyright 2025, Your Name Here |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025"
#property link      ""
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
CTrade trade;  // Trade operations object

// Input Parameters - Trading Strategy Configuration
input string   InpSymbol = "EURUSD";         // Trading Symbol
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M5;  // Base Timeframe

// AMA Settings
input int     InpMaMedium = 50;              // AMA Medium Period (AMA50)
input int     InpMaLong = 200;               // AMA Long Period (AMA200)
input double  InpMinAmaGap = 0.05;           // Minimum AMA Gap Percent
input int     InpAmaFastEma = 2;             // AMA Fast EMA Period
input int     InpAmaSlowEma = 30;            // AMA Slow EMA Period

// ADX Settings
input bool    InpUseAdx = true;              // Use ADX Filter
input int     InpAdxPeriod = 14;             // ADX Period
input int     InpAdxThreshold = 20;          // ADX Threshold
input int     InpAdxExtreme = 40;            // ADX Extreme Level

// MACD Settings
input bool    InpUseMacd = true;             // Use MACD Filter
input int     InpMacdFast = 12;              // MACD Fast EMA
input int     InpMacdSlow = 26;              // MACD Slow EMA
input int     InpMacdSignal = 9;             // MACD Signal Period
input double  InpMacdGrowingFactor = 1.05;   // MACD Growing Factor
input int     InpMacdConsecutiveBars = 3;    // MACD Consecutive Bars
input bool    InpMacdZeroCross = true;       // MACD Zero Cross Confirmation

// RSI Settings
input bool    InpUseRsi = true;              // Use RSI Filter
input int     InpRsiPeriod = 14;             // RSI Period
input int     InpRsiOverbought = 70;         // RSI Overbought Level
input int     InpRsiOversold = 30;           // RSI Oversold Level

// Risk Management
input double  InpRiskPercent = 1.0;          // Risk Per Trade (%)
input double  InpMinLot = 0.01;              // Minimum Lot Size
input double  InpMaxLot = 10.0;              // Maximum Lot Size
input int     InpMaxSpread = 15;             // Maximum Spread (points)
input int     InpSlippage = 100;             // Maximum Slippage (points)

// Trading Hours (EST)
input int     InpMarketOpenHour = 17;        // Market Open Hour (EST)
input int     InpMarketCloseHour = 16;       // Market Close Hour (EST)

// Global Variables
double g_ama_medium[];          // AMA50 buffer
double g_ama_long[];           // AMA200 buffer
double g_macd_main[];          // MACD main line
double g_macd_signal[];        // MACD signal line
double g_macd_hist[];          // MACD histogram
double g_adx[];               // ADX
double g_rsi[];               // RSI
int g_handle_ama_medium;      // AMA50 handle
int g_handle_ama_long;        // AMA200 handle
int g_handle_macd;            // MACD handle
int g_handle_adx;             // ADX handle
int g_handle_rsi;             // RSI handle

//+------------------------------------------------------------------+
//| Custom functions forward declarations                              |
//+------------------------------------------------------------------+
double CalculateAMA(const double &price[], int period, int ama_fast, int ama_slow);
bool ValidateInputs();
bool InitializeIndicators();
void CleanupIndicators();
double CalculateLotSize(bool is_buy, double sl_points);
bool CheckTradingTime();
bool CheckMarketConditions();
void CloseAllPositions();
bool HasOpenPosition();
int Digits();

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
    // Validate inputs
    if(!ValidateInputs())
        return INIT_PARAMETERS_INCORRECT;
        
    // Initialize indicators
    if(!InitializeIndicators())
        return INIT_FAILED;
        
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    CleanupIndicators();
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // Skip if outside trading hours
    if(!CheckTradingTime())
        return;
        
    // Check market conditions (spread, etc.)
    if(!CheckMarketConditions())
        return;
        
    // Update indicator values
    if(!UpdateIndicators())
        return;
        
    // Get signal
    int signal = GetTradingSignal();
    
    // Check existing positions
    if(HasOpenPosition())
    {
        // Close position if signal is opposite to current position
        if((signal < 0 && PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ||
           (signal > 0 && PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL))
        {
            CloseAllPositions();
            Sleep(100);  // Small delay before opening new position
        }
        else
            return;  // No action if signal matches current position
    }
    
    // Process signal if no position exists or old position was just closed
    if(signal != 0)
        ProcessSignal(signal);
}

//+------------------------------------------------------------------+
//| Validate all input parameters                                      |
//+------------------------------------------------------------------+
bool ValidateInputs()
{
    if(InpMaMedium <= 0 || InpMaLong <= 0 || InpMinAmaGap <= 0)
    {
        Print("Invalid MA parameters");
        return false;
    }
    
    if(InpRiskPercent <= 0 || InpRiskPercent > 5)
    {
        Print("Risk percent must be between 0 and 5");
        return false;
    }
    
    if(InpMinLot < 0.01 || InpMaxLot > 10.0)
    {
        Print("Invalid lot size limits");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Initialize all indicators                                          |
//+------------------------------------------------------------------+
bool InitializeIndicators()
{
    // Initialize buffers
    ArraySetAsSeries(g_ama_medium, true);
    ArraySetAsSeries(g_ama_long, true);
    ArraySetAsSeries(g_macd_main, true);
    ArraySetAsSeries(g_macd_signal, true);
    ArraySetAsSeries(g_macd_hist, true);
    ArraySetAsSeries(g_adx, true);
    ArraySetAsSeries(g_rsi, true);
    
    // Create indicator handles
    g_handle_macd = iMACD(Symbol(), Period(), InpMacdFast, InpMacdSlow, InpMacdSignal, PRICE_CLOSE);
    g_handle_adx = iADX(Symbol(), Period(), InpAdxPeriod);
    g_handle_rsi = iRSI(Symbol(), Period(), InpRsiPeriod, PRICE_CLOSE);
    
    // Check if indicators were created successfully
    if(g_handle_macd == INVALID_HANDLE || g_handle_adx == INVALID_HANDLE || g_handle_rsi == INVALID_HANDLE)
    {
        Print("Error creating indicator handles");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Cleanup indicator handles                                          |
//+------------------------------------------------------------------+
void CleanupIndicators()
{
    IndicatorRelease(g_handle_macd);
    IndicatorRelease(g_handle_adx);
    IndicatorRelease(g_handle_rsi);
}

//+------------------------------------------------------------------+
//| Calculate Adaptive Moving Average                                  |
//+------------------------------------------------------------------+
double CalculateAMA(const double &price[], int period, int ama_fast, int ama_slow)
{
    if(ArraySize(price) < period + 1)
        return 0.0;
        
    static double ama = 0.0;
    static bool initialized = false;
    
    if(!initialized)
    {
        ama = price[ArraySize(price)-1];
        initialized = true;
        return ama;
    }
    
    double direction = MathAbs(price[0] - price[period]);
    double volatility = 0.0;
    
    for(int i = 0; i < period; i++)
        volatility += MathAbs(price[i] - price[i+1]);
        
    double er = (volatility == 0.0) ? 0.0 : direction / volatility;
    
    double fast_sc = 2.0 / (ama_fast + 1.0);
    double slow_sc = 2.0 / (ama_slow + 1.0);
    double sc = MathPow(er * (fast_sc - slow_sc) + slow_sc, 2);
    
    ama = ama + sc * (price[0] - ama);
    return ama;
}

//+------------------------------------------------------------------+
//| Update all indicator values                                        |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
    // Copy indicator values
    if(CopyBuffer(g_handle_macd, 0, 0, InpMacdConsecutiveBars+1, g_macd_main) <= 0) return false;
    if(CopyBuffer(g_handle_macd, 1, 0, InpMacdConsecutiveBars+1, g_macd_signal) <= 0) return false;
    if(CopyBuffer(g_handle_macd, 2, 0, InpMacdConsecutiveBars+1, g_macd_hist) <= 0) return false;
    if(CopyBuffer(g_handle_adx, 0, 0, 2, g_adx) <= 0) return false;
    if(CopyBuffer(g_handle_rsi, 0, 0, 2, g_rsi) <= 0) return false;
    
    // Calculate AMA values
    double close[];
    ArraySetAsSeries(close, true);
    if(CopyClose(Symbol(), Period(), 0, InpMaLong+1, close) <= 0) return false;
    
    ArrayResize(g_ama_medium, ArraySize(close));
    ArrayResize(g_ama_long, ArraySize(close));
    
    for(int i = ArraySize(close)-1; i >= 0; i--)
    {
        g_ama_medium[i] = CalculateAMA(close, InpMaMedium, InpAmaFastEma, InpAmaSlowEma);
        g_ama_long[i] = CalculateAMA(close, InpMaLong, InpAmaFastEma, InpAmaSlowEma);
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Get trading signal (-1:Sell, 0:None, 1:Buy)                       |
//+------------------------------------------------------------------+
int GetTradingSignal()
{
    // Price data
    double current_price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
    double ama50 = g_ama_medium[0];
    double ama200 = g_ama_long[0];
    
    // Calculate AMA gap percentage
    double ama_gap_percent = MathAbs(ama50 - ama200) / ama200 * 100;
    bool sufficient_gap = ama_gap_percent >= InpMinAmaGap;
    
    if(!sufficient_gap)
    {
        Print("Insufficient AMA gap: ", ama_gap_percent, "% < ", InpMinAmaGap, "%");
        return 0;
    }
    
    // Check primary AMA signals
    bool bullish_setup = ama50 > ama200 && current_price > ama50;
    bool bearish_setup = ama50 < ama200 && current_price < ama50;
    
    // Count confirming filters
    int filter_count = 0;
    int required_filters = 2;  // Need 2 out of 3 filters to confirm
    
    // Check ADX
    if(InpUseAdx)
    {
        bool adx_confirms = g_adx[0] >= InpAdxThreshold;
        if(adx_confirms) filter_count++;
    }
    
    // Check MACD
    if(InpUseMacd)
    {
        bool macd_confirms = false;
        // Check for consecutive growing bars
        if(bullish_setup)
        {
            bool growing = true;
            for(int i = 0; i < InpMacdConsecutiveBars-1; i++)
            {
                if(g_macd_hist[i] <= g_macd_hist[i+1] * InpMacdGrowingFactor)
                {
                    growing = false;
                    break;
                }
            }
            macd_confirms = growing;
        }
        else if(bearish_setup)
        {
            bool growing = true;
            for(int i = 0; i < InpMacdConsecutiveBars-1; i++)
            {
                if(MathAbs(g_macd_hist[i]) <= MathAbs(g_macd_hist[i+1]) * InpMacdGrowingFactor)
                {
                    growing = false;
                    break;
                }
            }
            macd_confirms = growing;
        }
        if(macd_confirms) filter_count++;
    }
    
    // Check RSI
    if(InpUseRsi)
    {
        if(bullish_setup && g_rsi[0] < InpRsiOversold) filter_count++;
        if(bearish_setup && g_rsi[0] > InpRsiOverbought) filter_count++;
    }
    
    // Return signal if enough filters confirm
    if(filter_count >= required_filters)
    {
        if(bullish_setup) return 1;   // Buy signal
        if(bearish_setup) return -1;  // Sell signal
    }
    
    return 0;  // No signal
}

//+------------------------------------------------------------------+
//| Process trading signal                                            |
//+------------------------------------------------------------------+
void ProcessSignal(int signal)
{
    // Define stop loss points (can be adjusted based on ATR or fixed value)
    double sl_points = 200;  // 20 pips default
    
    if(signal > 0)  // Buy Signal
    {
        // Calculate lot size
        double lot_size = CalculateLotSize(true, sl_points);
        
        // Calculate stop loss and take profit prices
        // Place buy order at market price
        trade.SetDeviationInPoints(InpSlippage);
        trade.SetTypeFilling(ORDER_FILLING_IOC);
        if(!trade.Buy(lot_size, Symbol(), 0.0, 
           NormalizeDouble(SymbolInfoDouble(Symbol(), SYMBOL_ASK) - (sl_points * SymbolInfoDouble(Symbol(), SYMBOL_POINT)), Digits()),
           NormalizeDouble(SymbolInfoDouble(Symbol(), SYMBOL_ASK) + (sl_points * 2 * SymbolInfoDouble(Symbol(), SYMBOL_POINT)), Digits()),
           "KarabelaTrade"))
        {
            Print("Buy order failed with error: ", GetLastError());
            return;
        }
    }
    else if(signal < 0)  // Sell Signal
    {
        // Calculate lot size
        double lot_size = CalculateLotSize(false, sl_points);
        
        // Calculate stop loss and take profit prices
        // Place sell order at market price
        trade.SetDeviationInPoints(InpSlippage);
        trade.SetTypeFilling(ORDER_FILLING_IOC);
        if(!trade.Sell(lot_size, Symbol(), 0.0,
           NormalizeDouble(SymbolInfoDouble(Symbol(), SYMBOL_BID) + (sl_points * SymbolInfoDouble(Symbol(), SYMBOL_POINT)), Digits()),
           NormalizeDouble(SymbolInfoDouble(Symbol(), SYMBOL_BID) - (sl_points * 2 * SymbolInfoDouble(Symbol(), SYMBOL_POINT)), Digits()),
           "KarabelaTrade"))
        {
            Print("Sell order failed with error: ", GetLastError());
            return;
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk management                       |
//+------------------------------------------------------------------+
double CalculateLotSize(bool is_buy, double sl_points)
{
    double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double risk_amount = account_balance * InpRiskPercent / 100.0;
    
    // Get tick value in account currency
    double tick_value = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
    double point = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
    
    // Calculate lot size based on risk
    double lot_size = risk_amount / (sl_points * tick_value / point);
    
    // Round to broker's lot step
    double lot_step = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
    lot_size = MathFloor(lot_size / lot_step) * lot_step;
    
    // Apply lot size limits
    lot_size = MathMax(InpMinLot, MathMin(InpMaxLot, lot_size));
    
    return lot_size;
}

//+------------------------------------------------------------------+
//| Check if current time is within trading hours                     |
//+------------------------------------------------------------------+
bool CheckTradingTime()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    // Convert current hour to EST (GMT-4)
    int est_hour = (dt.hour - 4 + 24) % 24;
    
    // Trading allowed from Sunday 5 PM to Friday 5 PM EST
    if(dt.day_of_week == 0 && est_hour < InpMarketOpenHour)  // Sunday before 5 PM
        return false;
    if(dt.day_of_week == 5 && est_hour >= InpMarketCloseHour)  // Friday after 5 PM
        return false;
    if(dt.day_of_week == 6)  // Saturday
        return false;
        
    return true;
}

//+------------------------------------------------------------------+
//| Check market conditions (spread, etc.)                            |
//+------------------------------------------------------------------+
bool CheckMarketConditions()
{
    // Check spread
    long spread = SymbolInfoInteger(Symbol(), SYMBOL_SPREAD);
    if(spread > InpMaxSpread)
    {
        Print("Spread too high: ", spread, " > ", InpMaxSpread);
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Digits function returns number of decimal places for current symbol|
//+------------------------------------------------------------------+
int Digits()
{
    return (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS);
}

//+------------------------------------------------------------------+
//| Check if there's an open position for the current symbol          |
//+------------------------------------------------------------------+
bool HasOpenPosition()
{
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionGetSymbol(i) == Symbol())
        {
            if(!PositionSelectByTicket(PositionGetTicket(i)))
                continue;
                
            return true;
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| Close all positions for the current symbol                        |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);
        if(ticket <= 0)
            continue;
            
        if(!PositionSelectByTicket(ticket))
            continue;
            
        if(PositionGetString(POSITION_SYMBOL) != Symbol())
            continue;
            
        trade.PositionClose(ticket);
        Sleep(100);  // Small delay between closing positions
    }
}

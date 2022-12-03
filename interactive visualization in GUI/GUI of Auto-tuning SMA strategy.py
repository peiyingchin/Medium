#!/usr/bin/env python
# coding: utf-8

# In[8]:


import pip

def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])    
list_packages = ['PySimpleGUI','numpy','matplotlib','pandas_datareader','datetime','pandas_ta','pandas','statistics' ]
for i in list_packages:
    import_or_install(i)


# In[1]:


import PySimpleGUI as sg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas_datareader as pdr
import datetime 
import pandas_ta as ta
import pandas as pd
from statistics import mean


# In[2]:


# data = dataframe in pandas format to calculate sma
# sma_value = is an array to calcuate the lenth of sma 
# variable = variable used to calculate sma, it can be a "Close", or "Adj Close" in string format
def sma(data,sma_value,variable):
     # auto assign a variable name based on length of sma 
    variable_name = 'SMA'+ str(sma_value)
    # calculate sma 
    data[variable_name] =ta.sma(data[variable], length=sma_value)
    # return sma variable calculated 
    return data[variable_name]
# sym =  string format, ticker name
# ema value = is an array to calcuate the lenth of ema 
# sma_value = is an array to calcuate the lenth of sma 
# close = variable use for calcuate sma and ema, either "Close"or "Adj Close" in string format
def getdata(sym,sma_value,close):
    today = datetime.datetime.now()
    df = pdr.get_data_yahoo(sym, start=datetime.datetime(today.year-10,today.month, 1),
                                    end=datetime.datetime(today.year, today.month, today.day)).reset_index()
    df['ticker'] =sym
        
    for i in sma_value:
        variable_name = 'SMA'+ str(i)
        df[variable_name] = sma(df,i,close)
    return df
# variable_lower = lower perios SMA 
# variable_upper = higher period SMA
def Generate_signal(data, variable_lower, variable_upper):    
    #table start
    df_init =  data.copy()
    
    '''To make sure row arrange in an ascending order'''
    df.sort_values(by = 'Date',inplace=True)
    
    '''Process data by remove Null value in moving average varaible that your want to used for triggered''' 
    df_init.dropna(subset=[variable_lower],inplace=True)
    df_init.dropna(subset=[variable_upper],inplace=True)
    '''generate as 1 if Adj close is higher than variable you want to test, generate as -1 if Adj close is less than the
    variable you want to test in a signal variable  
    '''
    # create a signal variable
    df_init['signal'] = np.nan 
    # trigger a buy only if it is a up trend 
    df_init.loc[(df['Adj Close']>=df[variable_lower])&(df[variable_lower]>=df[variable_upper]) ,'signal'] = 1
    
    # just triggered sell as close is less than variable triggered
    df_init.loc[(df['Adj Close']<df[variable_lower]) |(df[variable_lower]<df[variable_upper]),'signal'] = -1
    
    ''' move the signal of today to tmr, thus, we need to define a shift(1), as the signal buy is based on yesterday'''
    df_init['signal'] = df_init['signal'].shift(1)
    
    '''after we have a buy and sell signal, lets create a hold signal which is equal to 2 after a buy signal and
    a do nothing signal which is equal to 0 after a sell signal'''
    
    # In order to make a decision on a hold or do nothing signal based on yesterday signal we need to create a for loop 
    # a calendar date should be created to used for a a for loop 
    date_list = df_init.Date.unique()
    
    # declare a first day, the first date is a null in signal as there is no yesterday data for first data
    first_date = date_list[0]
    
    # declare a previous day 
    prev = first_date 
    
    for i in date_list:
        if i == first_date:
            df_init.loc[df_init.Date == i,'signal'] = 0 
        else:
            # if you have a sell signal yesterday, you should have a do nothing signal today
            if (df_init.loc[df_init.Date == prev,'signal'].values[0]==-1):
                df_init.loc[df_init.Date == i,'signal']=0 
            # if you have a buy signal yesterday, you should have a hold signal today
            elif (df_init.loc[df_init.Date == prev,'signal'].values[0]==1):
                df_init.loc[df_init.Date == i,'signal'] = 2
              
            # if you have a hold signal yesterday and you do not have a sell signal today, you should have a hold signal today
            elif ((df_init.loc[df_init.Date == prev,'signal'].values[0]==2)&(df_init.loc[df_init.Date == i,'signal'].values[0]!=-1) ):
                df_init.loc[df_init.Date == i,'signal'] = 2
                
            # if you have a do nothing signal yesterday and today is a sell signal, you should equal to have a do nothing signal
            elif ((df_init.loc[df_init.Date == prev,'signal'].values[0]==0)&(df_init.loc[df_init.Date == i,'signal'].values[0]==-1) ):
                df_init.loc[df_init.Date == i,'signal'] = 0
                
        # redeclare your previous date before to next day in for loop
        prev = i
    
    return df_init

# data = dataframe with signal
# capital = ur starting capital
def backtest_strategy(data,capital):   
    
    #table start
    df_init =  data.copy()
    df_init.set_index('Date',inplace=True) 
    
    #assign dummy row - day before the trade
    start_date = pd.DataFrame(columns=data.columns,index=[df_init.index.min()- datetime.timedelta(days=1)])
    df_init = df_init.append(start_date)
    
    #initiat 2 variable: cash and units which represent each status of cash and units of apple holding for each day
    df_init = df_init.assign(cash=np.nan,units = 0)
    
    #assign capital for first dummy day assigned to be capital defined in function
    df_init.loc[pd.Series(df_init.index.min()), 'cash'] = capital
    
    # obtain list of calendar 
    calendar = pd.Series(df_init.index.sort_values().unique()).iloc[1:]
    
    ''' assign a variable which is trade, earn trade and lost trade to calculate total number of trade, total earn trade 
    and total lost trade'''
    trade = 0
    earn_trade = 0
    loss_trade = 0
    
    ''' create an array to keep all earn value and lost value for each trade'''
    earn_value =[]
    lost_value =[]

    for date in calendar:
        
        #get yesterday data
        prev_date = df_init.index[df_init.index<date].unique().sort_values()[-1]
        
        # calculate total stock value of yesterday 
        stock_holding = df_init.loc[(df_init.index==prev_date), 'units'].values[0]*df_init.loc[(df_init.index==date),'Price'].values[0]
        
        # total portfolio value by add cash and stock value of yesterday 
        port_value = stock_holding + df_init.loc[prev_date, 'cash'].sum()

        # if signal is do nothing, mean our cash = portfolio value and units=0
        if df_init.loc[(df_init.index==date), 'signal'].values[0] == 0:          
            df_init.loc[(df_init.index==date), 'units'] = 0
            df_init.loc[(df_init.index==date), 'cash'] =port_value        
        #if we have a buy signal 
        #start to calculate the trade
        #we start to calculate start_cap which represent the starting capital for each trade
        #unit_buy is total unit buy based on port_value available
        elif df_init.loc[(df_init.index==date), 'signal'].values[0] == 1:
            trade+=1
            start_cap = port_value 
            unit_buy = port_value/df_init.loc[(df_init.index==date), 'Price'].values[0]
            df_init.loc[(df_init.index==date), 'units'] = unit_buy
            df_init.loc[(df_init.index==date), 'cash'] = port_value - unit_buy*df_init.loc[(df_init.index==date), 'Price'].values[0]        
        
        #if we have a hold signal or do nothing signal,
        #mean today units hold and cash are same as yesterday units hold and yesterday cash
        elif ((df_init.loc[(df_init.index==date), 'signal'].values[0] == 2) | (df_init.loc[(df_init.index==date), 'signal'].values[0] == 0)): 
            df_init.loc[(df_init.index==date), 'units'] = df_init.loc[(df_init.index==prev_date), 'units'].values[0]
            df_init.loc[(df_init.index==date), 'cash'] =df_init.loc[(df_init.index==prev_date), 'cash'].values[0]
        
        #if we have a sell signal,
        #1. we sell all the units at the today open price and thus units =0 and cash = port_value
        #2. we calculate the total earn/lost of this trade by using port_value - start cap of the trade and store as v variable
        #3. if v> 0, we store as earn_value array
        #4. if v<0, we store as lost trade
        elif (df_init.loc[(df_init.index==date), 'signal'].values[0] == -1):
            df_init.loc[(df_init.index==date), 'units'] = 0
            df_init.loc[(df_init.index==date), 'cash'] =port_value 
            if (start_cap is None):
                0
            else:
                v = port_value  - start_cap 
                if v> 0: 
                    earn_value.append(v)
                    earn_trade +=1
                elif v<0: 
                    lost_value.append(v)
                    loss_trade+=1

    # calculate current value of the strategy, the formula = unit holding * Price + cash available
    df_init['Total_value_todate'] = df_init['units']*df_init['Price'] + df_init['cash'] 
    
    # append 0 to earn value array to prevent later calculation fail if there is no any earn trade
    earn_value.append(0)
    #remove dummy rows
    df_init.drop(df_init[df_init.index == df_init.index.min()].index,axis=0,inplace=True)
  
    # get summarize of total portfolio value, return by date, benchmark_index
    total_port_value = pd.DataFrame(df_init.groupby([df_init.index])['Total_value_todate'].sum())
    total_port_value['Return_without_trailing'] = total_port_value['Total_value_todate']/total_port_value['Total_value_todate'].iloc[0] *100
    total_port_value['Return_trailing_12m'] = total_port_value['Total_value_todate']/total_port_value['Total_value_todate'].shift(252)*100

    return total_port_value, df_init
# annualized return 
# df =data with return 
# variable = variable name of return
def annualized(df,variable):
    days_held =df.shape[0]
    Return = (df.iloc[-1][variable] - df.iloc[0][variable])/df.iloc[0][variable]
    ar = ((1+Return) ** (365/days_held))-1
    # get annualized in %
    return ar*100
# maximum drawdown 
# df =data with return 
# variable = variable name of return
def MDD(df,variable):
    window = 252
    Roll_Max = df[variable].rolling(window, min_periods=1).max()
    Drawdown = df[variable]/Roll_Max - 1.0
    mdd = Drawdown.min()
    # get drawdown in %
    return mdd*100


# In[4]:


# VARS CONSTS, window for whole gui variable, fig_agg and pltFig for our plot
_VARS = {'window': False,
         'fig_agg': False,
         'pltFig': False}

# to draw canvas figure 
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# \\  -------- PYSIMPLEGUI -------- //
# Theme for GUI and font using
AppFont = 'Any 16'
sg.theme('SandyBeach')  
# Theme for pyplot
plt.style.use('Solarize_Light2')

# output of text
text_stock = ""
text_win = ""
text_annualized_sma = ""
text_mdd_sma = ""
text_annualized_hs = ""
text_mdd_hs = ""
text_best_strategy =""
# Note the new colors for the canvas and window to match pyplots theme:
# prepared layout
layout = [[sg.Text('Please enter information needed for tunning SMA cross-over strategy')],
           [sg.Text('Ticker', size =(18, 1)), sg.InputText()],
           [sg.Text('SMA example:10,20,30', size =(18, 1), key ='sma'), sg.InputText(default_text='5,10,15,20,25,30,40,50,60')],
         [sg.Submit( font=AppFont),sg.Cancel( font=AppFont)],
    [sg.Canvas(key='figCanvas', background_color='#FDF6E3')],
         [sg.Text(text_stock,key ='-text_stock-')],
            [sg.Text(text_best_strategy, key='-text_best_strategy-' )],
            [sg.Text(text_win, key='-text_win-') ],
            [sg.Text(text_annualized_sma , key='-text_annualized_sma-')],
            [sg.Text(text_mdd_sma, key='-text_mdd_sma-' )],
            [sg.Text(text_annualized_hs, key='-text_annualized_hs-' )],
            [sg.Text(text_mdd_hs, key='-text_mdd_hs-')]]
_VARS['window'] = sg.Window('Auto-tune SMA strategy',
                            layout,
                            finalize=True,
                            resizable=True)
# \\  -------- PYSIMPLEGUI -------- //


# \\  -------- PYPLOT -------- //

# Starting plot. Blank plot without input
def drawChart():
    _VARS['pltFig'] = plt.figure()
    plt.plot()
    plt.legend()
    _VARS['fig_agg'] = draw_figure(
        _VARS['window']['figCanvas'].TKCanvas, _VARS['pltFig'])

# update plot based on user change
def updateChart():
    _VARS['fig_agg'].get_tk_widget().forget()
    # plt.cla()
    plt.clf()
    # plot to be shown
    plt.plot(result.Return_without_trailing, '.k', label='Return without trailing of best strategy',color='blue')
    plt.plot(result['hold_without_sell_return (%)'], '.k', label='Return without trailing of hold without sell',color='green')
    plt.legend()
    _VARS['fig_agg'] = draw_figure(
        _VARS['window']['figCanvas'].TKCanvas, _VARS['pltFig'])

# \\  -------- PYPLOT -------- //
# run starting plot function
drawChart()
# MAIN LOOP
while True:
    # Read your event and input 
    event, values = _VARS['window'].read()
    # if GUI is close or cancle, quit
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
        
  # \\  -------- EVENT = SUBMIT -------- //  
    elif (event == 'Submit'):
        # \\  -------- Run Auto-tuning -------- //  
        SMA=[]
        for i in values[1].split(','):
            SMA.append(int(i))
        #get daily data and sma_value needed. 
        df = getdata(values[0],sma_value = SMA,close = "Adj Close")
        # Define your a win represent a return trailing 12 months
        win=0
        # define your best strategy
        best_strategy ='NA'
        # shorter sma of best strategy
        best_lower = 'NA'
        # longer sma of best strategy
        best_higher = 'NA'
        # loop sma to get best strategy which has the best aveage return trailing 12 months
        for i in SMA:
            for j in SMA:
                if i<j:
                    lower = 'SMA'+str(i)
                    higher = 'SMA'+str(j)
                    # Get signal
                    df_signal = Generate_signal(df, lower,higher)

                    # back test your strategy using Open price as price action to buy sell on particular day
                    df_signal['Price']=df_signal['Open']
                    df_backtest = df_signal[['Date','Price','signal','Open']].copy()
                    result, hold_detail = backtest_strategy(df_backtest,1000)
                    if result.dropna().Return_trailing_12m.mean()>win:
                        win = result.dropna().Return_trailing_12m.mean()
                        best_strategy = lower+' and '+higher
                        best_higher = higher
                        best_lower = lower
        # Get signal
        df_signal = Generate_signal(df, best_lower,best_higher)
        # back test your strategy using Open price as price action to buy sell on particular day
        df_signal['Price']=df_signal['Open']
        df_backtest = df_signal[['Date','Price','signal','Open']].copy()
        result, hold_detail = backtest_strategy(df_backtest,1000)
        # calculate the return without trailing of hold without sell 
        df_signal['hold_without_sell_return (%)'] = df_signal['Close']/df_signal['Close'].iloc[0]*100
        result['hold_without_sell_return (%)'] = df_signal.set_index('Date')['hold_without_sell_return (%)']
        # \\  -------- Auto-tuning finish run-------- //  

        # reassigned our text output
        text_annualized_sma = 'Annualized_return of best strategy: '+ str(annualized (result,'Return_without_trailing'))
        text_mdd_sma = 'MDD of best strategy: '+ str(MDD(result,'Return_without_trailing'))

        text_annualized_hs ='Annualized_return of hold without sell:'+ str(annualized (result,'hold_without_sell_return (%)'))
        text_mdd_hs ='MDD of hold without sell: '+ str(MDD(result,'hold_without_sell_return (%)'))
        text_best_strategy = "Your best strategy: " + best_strategy
        text_win = "Average return trailing 12 months for best strategy: "+ str(win)
        text_stock = "Stock: " + values[0]
        
        # reupdate our chart after the tuning finish write
        updateChart()
        
        # reupdate the text
        _VARS['window']['-text_annualized_sma-'].update(text_annualized_sma)
        _VARS['window']['-text_mdd_sma-'].update(text_mdd_sma)
        _VARS['window']['-text_annualized_hs-'].update(text_annualized_hs)
        _VARS['window']['-text_best_strategy-'].update(text_best_strategy)
        _VARS['window']['-text_win-'].update(text_win)
        _VARS['window']['-text_stock-'].update(text_stock)
        _VARS['window']['-text_mdd_hs-'].update(text_mdd_hs)

        
_VARS['window'].close()




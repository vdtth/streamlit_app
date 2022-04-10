from typing import Optional

import json

import pandas as pd
import os

import math
import pickle
import csv 


pd.options.display.float_format = '{:,.3f}'.format

TP_threshold = 0.3/100





def calculatte_contract(data,last_trade,max_SO=3,SO_i=0,p=1.1):
    max_SO += 1
    coin = data["coin"]
    coin = coin.replace("PERP", "")
    precision = get_precision(data)
#     total_money = last_trade["Remain_Money"] + last_trade['Avg_price']*last_trade['Price']
    total_money = last_trade["Equity"]
    money = abs(total_money/(1- p**max_SO)*(1-p)*p**SO_i)
    if money > last_trade["Remain_Money"]:
        money = last_trade["Remain_Money"]
    quantity = round(math.trunc(money/precision/data["Price"])*precision, int(math.log10(1/precision)))
    return quantity
def get_precision(data):
    coin = data["coin"]
    coin = coin.replace("PERP", "")
    if data["type"] == "spot":
        list_001 = ["BTCUSDT", "ETHUSDT","BNBUSDT"] 
        list_01 = ["DOTDOWNUSDT","LINKDOWNUSDT","LINKUPUSDT","ATOMUSDT"]
        list_1 = ["ALICEUSDT", "XRPUSDT", "DYDXUSDT","CRVUSDT","ANCUSDT"]
    elif data["type"] == "future-usd":
        list_001 = ["BTCUSDT", "ETHUSDT"] 
        list_01 = ["BNBUSDT", "ATOMUSDT"]
        list_1 = ["ALICEUSDT", "XRPUSDT", "DYDXUSDT","CRVUSDT","ANCUSDT"]
    elif data["type"] == "margin":
        list_001 = ["BTCUSDT", "ETHUSDT","BNBUSDT"] 
        list_01 = ["DOTDOWNUSDT","LINKDOWNUSDT","LINKUPUSDT","ATOMUSDT"]
        list_1 = ["ALICEUSDT", "XRPUSDT", "DYDXUSDT","CRVUSDT","ANCUSDT"]
    
    if coin in list_001:
        precision = 0.001
    elif coin in list_01:
        precision = 0.01
    elif coin in list_1:
        precision = 0.1
    else:
        precision = 1
    return precision
    



def decision_buy_sell_combine(data,last_trade):
    # init
    write_log = True
    total_vol = 0
    average_price = 0
    output = {}
    coin = data["coin"]
    coin = coin.replace("PERP", "")
    data['time'] = pd.to_datetime(data['time'],unit='ms')
    precision = get_precision(data)
    type = data["type"]
    name = data["Name"].lower()
    price = data["Price"]
    max_SO = data["max_SO"]
    SO_price_list = [data["SO_1_price"],data["SO_2_price"],data["SO_3_price"],data["SO_4_price"],0.03,0.0375]
#     #COMMISSION =  data["commission"]/100
    COMMISSION = 0.04/100

    #skip already recorded trades
    if data['time']<=pd.to_datetime(last_trade['Date'],unit='ms'): 
    # print(data['time'],'\n',pd.to_datetime(last_trade['Date'],unit='ms'),'\n',data['time']<=pd.to_datetime(last_trade['Date'],unit='ms'))
    # print("===================")
    # if int(data['time'])<=last_trade['Date']: 

        write_log = False
        return output,write_log


    if int(data["Timeframe"]) < 16:
        TP_threshold = -10/100
    else:
        TP_threshold = -10/100
    # decision 
    if name.lower() == "long":
        # flat => buy all; quantity:total vol last time  final_vol: hien thi last dang la bn
        if last_trade["Last_vol"] == 0:
            current_SO = 0
            #try fix?
            quantity = calculatte_contract(data,last_trade,max_SO=max_SO, SO_i=current_SO)
            profit_per = 0
            total_profit = 0
            final_vol = quantity
    #        print(last_trade["Remain_Money"] ,quantity,price,COMMISSION)
            remain_money = last_trade["Remain_Money"] - quantity*price - COMMISSION*quantity*price
            
            avg_price = price
#             if data["Demo"] != "demo":
#                 order(data,quantity)
            output["Equity"] = last_trade["Equity"]  - COMMISSION*quantity*price
 
        else:
            current_SO = last_trade['SO']
            avg_price = last_trade["Avg_price"]

            if current_SO >= 0 and current_SO <= max_SO  and price < avg_price*(1-SO_price_list[current_SO]):
                current_SO += 1 
                quantity = calculatte_contract(data,last_trade,max_SO=max_SO, SO_i=current_SO)
                profit_per = 0
                total_profit = 0
                final_vol = quantity +abs(last_trade["Last_vol"]) 
#                print(last_trade["Remain_Money"] ,quantity,price,COMMISSION)
                remain_money = last_trade["Remain_Money"] - quantity*price - COMMISSION*quantity*price
#                 avg_price = (price*quantity + last_trade['Price']*last_trade['Last_vol'])/(quantity+last_trade['Last_vol'])
                avg_price = (price*quantity + last_trade['Price']*abs(last_trade['Last_vol']))/(quantity+abs(last_trade['Last_vol']))
#                 if data["Demo"] != "demo":
#                     order(data,quantity)
                output["Equity"] = last_trade["Equity"]  - COMMISSION*quantity*price
            else:
                print(f"Skip Long SO{current_SO+1} long because at {(last_trade['Avg_price']-price)/last_trade['Avg_price']*100:.2} < {SO_price_list[current_SO]*100}")
                write_log = False
    elif name.lower() == "short":
        if last_trade["Last_vol"] == 0:
            current_SO = 0
            #try fix?
            quantity = calculatte_contract(data,last_trade,max_SO=max_SO, SO_i=current_SO)
            profit_per = 0
            total_profit = 0
            final_vol = -quantity
 #           print(last_trade["Remain_Money"] ,quantity,price,COMMISSION)
            remain_money = last_trade["Remain_Money"] - quantity*price - COMMISSION*quantity*price
            avg_price = price
#             if data["Demo"] != "demo":
#                 order(data,quantity) 
            output["Equity"] = last_trade["Equity"]  - COMMISSION*quantity*price
        else:

            current_SO = last_trade['SO']
            avg_price = last_trade["Avg_price"]

                
            if current_SO >= 0 and current_SO <= max_SO and price > avg_price*(1+SO_price_list[current_SO]):
                current_SO += 1 
                quantity = calculatte_contract(data,last_trade,max_SO=max_SO, SO_i=current_SO)
                profit_per = 0
                total_profit = 0
                final_vol = -(quantity+abs(last_trade["Last_vol"]) )
#                print(last_trade["Remain_Money"] ,quantity,price,COMMISSION)
                remain_money = last_trade["Remain_Money"] - abs(quantity*price) - abs(COMMISSION*quantity*price)
                avg_price = (price*quantity + last_trade['Price']*abs(last_trade['Last_vol']))/(quantity+abs(last_trade['Last_vol']))
#                 if data["Demo"] != "demo":
#                     order(data,quantity)
                output["Equity"] = last_trade["Equity"]  - COMMISSION*quantity*price
            else:
               #print(f"Skip {current_SO+1} long because at {-(last_trade['Avg_price']-price)/price:.2%} < {SO_price_list[current_SO-1]}"
                print(f"Skip short SO{current_SO+1} long because at {(-last_trade['Avg_price']+price)/last_trade['Avg_price']*100:.2} < {SO_price_list[current_SO]*100}")
#                print(f"Skip short because already sell")
                write_log = False
    elif name.lower() == "tp_long" or name.lower() == "sl_long" :
        if last_trade["Last_vol"] > 0:
            if (name.lower() == "tp_long" and (price>last_trade['Price']*(1+TP_threshold))) or name.lower() == "sl_long":
                current_SO = -1
                quantity = abs(last_trade["Last_vol"])
                final_vol = 0
                profit_per = (price - last_trade['Avg_price'])/last_trade['Avg_price']*100
                total_profit = profit_per* quantity*last_trade['Avg_price']/(quantity*last_trade['Avg_price']+last_trade["Remain_Money"])
                remain_money = last_trade["Remain_Money"] + quantity*last_trade['Avg_price']*(1+profit_per/100) - COMMISSION*quantity*price
                avg_price = 0
#                 if data["Demo"] != "demo":
#                     order(data,quantity)
                output["Equity"] = last_trade["Equity"]*(1+total_profit/100)
            else:
                profit_per = (price - last_trade['Avg_price'])/last_trade['Avg_price']*100
                print(f"{profit_per:.2f} Smaller than TP long threshold")
                write_log = False
        else:
            print(f"Nothing to tp/sell long")
            write_log = False
    elif name.lower() == "tp_short" or name.lower() == "sl_short" :
        if last_trade["Last_vol"] < 0:
            if (name.lower() == "tp_short" and (price<last_trade['Price']*(1-TP_threshold))) or name.lower() == "sl_short":
                current_SO = -1
                quantity = abs(last_trade["Last_vol"])
                profit_per = -(price - last_trade['Avg_price'])/last_trade['Avg_price']*100
                total_profit = profit_per* quantity*last_trade['Avg_price']/(quantity*last_trade['Avg_price']+last_trade["Remain_Money"])
                final_vol = 0
                remain_money = last_trade["Remain_Money"] + quantity*last_trade['Avg_price']*(1+profit_per/100)  - COMMISSION*quantity*price
                avg_price = 0
                print(f"TP short {coin} price:{price}")
#                 if data["Demo"] != "demo":
#                     order(data,quantity)
                output["Equity"] = last_trade["Equity"]*(1+total_profit/100) #output["remain_money"] + avg_price*abs(output["final_vol"]) #avg_price
            else:
                profit_per = -(price - last_trade['Avg_price'])/last_trade['Avg_price']*100
                print(f"{profit_per:.2f} Smaller than TP short threshold")
                write_log = False
                
        else:
        
            print(f"Nothing to tp/sell short")
            write_log = False

    if write_log:
#         if remain_money < -10
        output["vol"] = quantity
        output["remain_money"] = math.floor(remain_money*100)/100
        output["final_vol"] = final_vol
        output["profit"] = f'{profit_per:.3f}' +"%"
        output["G_profit"] = total_profit
        output["SO"] = current_SO
        output["Avg_price"] = avg_price
        
    return output,write_log


def wh(data):
    # get json data/
    try:
        data = json.loads(data)
        if data['type'] == 'future-coin':
            return

    except:
        return # not alert
#     data = data.dict()
    try:
        date = data['time']
    except:
        return
    print(data)
    data["max_SO"] = 4
    # print(data['time'])
    # data['time'] = str(pd.to_datetime(data['time']))
    
    # date = str(pd.to_datetime(data['time']))
    coin = data["coin"]
    trade_mode  = data["Demo"]
    timeframe = data["Timeframe"]
    INIT_MONEY = data["initial_money"]
    price = data["Price"]
    type = data["type"] # ["spot","margin", "future-usd", "future-coin"]
    base_path_demo = f'./history/demo/{coin}/{type}'
    base_path_real = f'./history/real/{coin}/{type}'
    
    if not os.path.exists(base_path_demo):
        os.makedirs(base_path_demo)
    if not os.path.exists(base_path_real):
        os.makedirs(base_path_real)
        
    if trade_mode =="demo":
        log_file = os.path.join(base_path_demo,f"{timeframe}.csv")
    elif trade_mode =="real":
        log_file = os.path.join(base_path_real,f"{timeframe}.csv")
    elif trade_mode =="both":
        log_file_d = os.path.join(base_path_demo,f"{timeframe}.csv")
        log_file_r = os.path.join(base_path_real,f"{timeframe}.csv")
    price = data["Price"]
    name = data["Name"].lower()
    write_log = False
    coin = coin.replace("PERP", "")
    # message = json.dumps(data)
    
    #initial file log
#     date = f"{datetime.datetime.now():%y-%m-%d,%H:%M}"  
    
    if trade_mode =="both":
        if not os.path.exists(log_file_r):
            df_temp = pd.DataFrame({"Date":[date],"Name":["flat"],"SO":[-1],
                           "Volume":[0],"Price":[0],"Last_vol":[0],"Avg_price":[0],"Equity":[INIT_MONEY],
                           "Profit":["0%"],"G_profit":["0"],"Remain_Money":[INIT_MONEY]})
            df_temp.to_csv(log_file_r,index=False)
            df =  df_temp
            
        if not os.path.exists(log_file_d):
            df_temp = pd.DataFrame({"Date":[date],"Name":["flat"],"SO":[-1],
                           "Volume":[0],"Price":[0],"Last_vol":[0],"Avg_price":[0],"Equity":[INIT_MONEY],
                           "Profit":["0%"],"G_profit":["0"],"Remain_Money":[INIT_MONEY]})
            df_temp.to_csv(log_file_d,index=False)
            df =  df_temp
    else:
        if not os.path.exists(log_file):
            df_temp = pd.DataFrame({"Date":[date],"Name":["flat"],"SO":[-1],
                           "Volume":[0],"Price":[0],"Last_vol":[0],"Avg_price":[0],"Equity":[INIT_MONEY],
                           "Profit":["0%"],"G_profit":["0"],"Remain_Money":[INIT_MONEY]})
            df_temp.to_csv(log_file,index=False)
            df =  df_temp
        
    
    #initial trade
    precision = get_precision(data)
    
    #trade
    if trade_mode =="both":
        if os.path.exists(log_file_r):
            df_r = pd.read_csv(log_file_r)
            last_trade_r = json.loads(df_r.iloc[[-1]].to_json(orient="records"))[0]
            print(data,last_trade_r)
            data["Demo"] = "real"
            output_r,write_log_r = decision_buy_sell_combine(data,last_trade_r)
            
        if os.path.exists(log_file_d):
            df_d = pd.read_csv(log_file_d)
            last_trade_d = json.loads(df_d.iloc[[-1]].to_json(orient="records"))[0]
            data["Demo"] = "demo"
#             print(data,last_trade_d)
            output_d,write_log_d = decision_buy_sell_combine(data,last_trade_d)
    else:
        if os.path.exists(log_file):
            df = pd.read_csv(log_file)
            last_trade = json.loads(df.iloc[[-1]].to_json(orient="records"))[0]
            print(data,last_trade)
            data["Demo"] = "demo"
            output,write_log = decision_buy_sell_combine(data,last_trade)

    


    # telegram + log
    if trade_mode =="both":
        if write_log_r:
            # Write each symbols
            result_dict_r = {"Date":[date],"Name":[name],"SO":[output_r["SO"]],
                               "Volume":[output_r["vol"]],"Price":[price],"Last_vol":[output_r["final_vol"]],"Avg_price":[output_r["Avg_price"]],
                               "Profit":[output_r["profit"]],'G_profit':[output_r["G_profit"]],"Remain_Money":[output_r["remain_money"]], "Equity":[output_r["Equity"]]}    
            df_temp_r = pd.DataFrame(result_dict_r)
            df_r = df_r.append(df_temp_r, ignore_index = True)
            df_r.to_csv(log_file_r,index=False)
            
            
            result_dict_r['coin'] = [coin]
            result_dict_r['timeframe'] = [timeframe]
            result_dict_r['Demo/Real'] = ['real']
            print("Real\n",df_r.tail())
            
            # Write log all symbols longform
            if os.path.exists('log_r.csv'):
                df_log = pd.read_csv('./log_r.csv')
                df_temp = pd.DataFrame(result_dict_r)    
                df_log = df_log.append(df_temp, ignore_index = True)
                df_log.to_csv('./log_r.csv',index=False)
                
                
            else:
                result_dict_r = {"Date":[date],"Name":[name],"SO":[output_r["SO"]],
                               "Volume":[output_r["vol"]],"Price":[price],"Last_vol":[output_r["final_vol"]],"Avg_price":[output_r["Avg_price"]],
                               "Profit":[output_r["profit"]],'G_profit':[output_r["G_profit"]],"Remain_Money":[output_r["remain_money"]], "Equity":[output_r["Equity"]]}    
                df_temp_r = pd.DataFrame(result_dict_r)
                df_temp_r.to_csv('log_r.csv',index=False)
                
        if write_log_d:
            
            # Write
            result_dict_d = {"Date":[date],"Name":[name],"SO":[output_d["SO"]],
                           "Volume":[output_d["vol"]],"Price":[price],"Last_vol":[output_d["final_vol"]],"Avg_price":[output_d["Avg_price"]],
                           "Profit":[output_d["profit"]],'G_profit':[output_d["G_profit"]],"Remain_Money":[output_d["remain_money"]], "Equity":[output_d["Equity"]]}

            df_temp_d = pd.DataFrame(result_dict_d)
            df_d = df_d.append(df_temp_d, ignore_index = True)
            df_d.to_csv(log_file_d,index=False)
            print("Demo",df_d.tail())
            result_dict_d['coin'] = [coin]
            result_dict_d['timeframe'] = [timeframe]
            result_dict_d['Demo/Real'] = ['demo']
        
        
            if os.path.exists('./log.csv'):
                df_log = pd.read_csv('./log.csv')
                df_temp = pd.DataFrame(result_dict_d)    
                df_log = df_log.append(df_temp, ignore_index = True)
                df_log.to_csv('./log.csv',index=False)
            else:
                with open('./log.csv', 'w') as csv_file:  
                    df_temp = pd.DataFrame(result_dict_d)
                    df_temp.to_csv('./log.csv',index=False)

        print(coin,timeframe)
            
    else:
        if write_log:
            # Write 
            result_dict = {"Date":[date],"Name":[name],"SO":[output["SO"]],
                           "Volume":[output["vol"]],"Price":[price],"Last_vol":[output["final_vol"]],"Avg_price":[output["Avg_price"]],
                           "Profit":[output["profit"]],'G_profit':[output["G_profit"]],"Remain_Money":[output["remain_money"]], "Equity":[output["Equity"]]}    
            df_temp = pd.DataFrame(result_dict)    
            df = df.append(df_temp, ignore_index = True)
            df.to_csv(log_file,index=False)
            print(df.tail())
            
    #             global_dict = {"Date":date,"Name":name,"SO":output["SO"],
    #                            "Volume":output["vol"],"Price":price,"Last_vol":output["final_vol"],"Avg_price":output["Avg_price"],
    #                            "Profit":output["profit"],'G_profit':output["G_profit"],"Remain_Money":output["remain_money"], "Equity":output["Equity"]}
            result_dict['coin'] = [coin]
            result_dict['timeframe'] = [timeframe]
            result_dict['Demo/Real'] = [trade_mode]
            
            
            if os.path.exists('./log.csv'):
                df_log = pd.read_csv('./log.csv')
                df_temp = pd.DataFrame(result_dict)    
                df_log = df_log.append(df_temp, ignore_index = True)
                df_log.to_csv('./log.csv',index=False)
            else:
                with open('./log.csv', 'w') as csv_file:  
                    df_temp = pd.DataFrame(result_dict)
                    df_temp.to_csv('./log.csv',index=False)

            print(coin,timeframe)
    return data


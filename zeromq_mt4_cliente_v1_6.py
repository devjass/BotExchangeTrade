# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 10:59:55 2018

@author: personal
"""

# Importando  Libreria ZMQ
import zmq

msg_pull=''  
"""
# Sample Commands for ZeroMQ MT4 EA
TRADE|ACTION|TYPE|SYMBOL|VOLUMEN|PRICE|SL|TP|COMMENT
eurusd_buy_order = "TRADE|OPEN|0|EURUSD|0.1|0|50|50|Python-to-MT4"
eurusd_sell_order = "TRADE|OPEN|1|EURUSD|0|50|50|Python-to-MT4"
eurusd_closebuy_order = "TRADE|CLOSE|0|EURUSD|0|50|50|Python-to-MT4"
eurusd_data= "DATA|EURUSD|VOLUMEN|0|0|15"
get_rates = "RATES|GBPUSD"
get_rates = "RATES|GBPAUD"
# query=""     # Variable usada para hacer las solicitudes desde el módulo mind_control


Estructura de DATA: "DATA|SYMBOL|TIPO|TIMEFRAME|START_INDICE|NUMERO DE PERIODOS ATRAS"
El TIPO puede tener los siguientes valores: CLOSE, OPEN, LOW, HIGH, VOLUMEN, TIME
Ejemplo para el timesteps:
"DATA|EURUSD|CLOSE|0|0|15"    //Datos desde la barra actual hasta 15 periodos atrás.
Ejemplo para obtener datos históricos de 2-4 meses:
"DATA|EURUSD|TIME|2018.04.01 00:00|2018.01.01 00:00"    //Datos desde Enero 1 del 2018 hasta Marzo 31 del 2018.
Formato del START_TIME y END_TIME: 2015.01.01 00:00

Estructura TIME = "TIME|EURUSD|TIMEFRAME|INDICE_INICIO|NUMERO DE PERIODOS ATRAS"
Ejemplo:
"TIME|EURUSD|0|0|0"  // Para obtener la fecha y hora actual de acuerdo al timeframe
"""

# Función cliente para solicitar los datos al Servidor MT4
def zeromq_mt4_ea_client(query=""):
    global msg_pull
    
    if(query==""):
        print("Argumento no válido")
        return None
    # Create ZMQ Context
    context = zmq.Context()
    
    # Create REQ Socket
    reqSocket = context.socket(zmq.REQ)
    reqSocket.connect("tcp://127.0.0.1:5566")
    
    # Create PULL Socket
    pullSocket = context.socket(zmq.PULL)
    pullSocket.connect("tcp://127.0.0.1:5567")
    
    # Send RATES command to ZeroMQ MT4 EA
    #remote_send(reqSocket, get_rates)
    
    # Send DATA command to ZeroMQ MT4 EA
    remote_send(reqSocket, query)
        
    # Send BUY EURUSD command to ZeroMQ MT4 EA
    # remote_send(reqSocket, eurusd_buy_order)
    
    # Send CLOSE EURUSD command to ZeroMQ MT4 EA. You'll need to append the 
    # trade's ORDER ID to the end, as below for example:
    # remote_send(reqSocket, eurusd_closebuy_order + "|" + "12345678")
    
    # PULL from pullSocket
    remote_pull(pullSocket)
    
    try:
        msg = msg_pull.decode("utf-8")     #.decode loo convierte a string con codificacion utf-8
    except AttributeError:
        msg = msg_pull
        
    return msg
    
# Function to send commands to ZeroMQ MT4 EA
def remote_send(socket, data):
        
    try:
        socket.send_string(data)
        msg = socket.recv_string()
        #print(msg)
        
    except zmq.Again as e:
        pass
        #print("Waiting for PUSH from MetaTrader 4..")
    
# Function to retrieve data from ZeroMQ MT4 EA
def remote_pull(socket):
    global msg_pull
    try:
        msg_pull = socket.recv(flags=zmq.NOBLOCK)
        #print(msg_pull)
        
    except zmq.Again as e:
        pass
        #print("Waiting for PUSH from MetaTrader 4..")
    
# Run Tests
#zeromq_mt4_ea_client()
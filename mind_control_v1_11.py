# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 09:21:09 2018

@author: personal

Este módulo es el cerebro del Robot de Trading, es el que consultara
a los demás módulos, y tomara las decisiones de acuerdo al análisis de 
los datos.

Se usa la estrategia Longshot, con los siguientes indicadores:
RSI
EMA
CANAL DE DONCHIAN

ROBOT ENFOCADO PARA EL PAR: AUD/CHF u otros pares de divisas con la misma proporcion
a nivel precio, es decir que el precio no supere el valor de 2.0

Cálculo de los indicadores con respecto a número de ticks o velas del pasado:

RSI: 1 vela hacia atrás
EMA_M30: 2 vela hacia atrás
 
Parámetros:
stoploss max = 60
cont = 100 ms


Los Módulos son los siguientes:
    
* zeromq_mt4_cliente_v_5_1: Es el módulo que llevara acabo la comunicación con
el MT4 Server para obtener los datos históricos del mercado.


* data_Parser_v_5_1: Es el módulo que arma y organiza los datos historicos de la 
información obtenida del MT4. Organiza dos tipos de datos; uno son los datos
del timesteps(180) para que la RNN pueda predecir la operación, el otro dato
es más histórico, puede ser una recopilación de 2 meses de datos
historicos de un activo o un instrumento del mercado.
"""
import time
import datetime
import os
import pytz
import locale
from math import pow,degrees,atan2
from zeromq_mt4_cliente_v1_11 import zeromq_mt4_ea_client
from data_parser_v1_11 import parser,parser_data,parser_donchian
'''
while True:
    digits = trading("GET",2,simbolo,1,0)
    pip = (10*pow(10,-digits))/10
    data = trading("GET",3,simbolo,1,0)
    precio = round(((float(data[0])+float(data[1]))/2)-1*pip,digits)    
    print("Precio: ",precio)
    time.sleep(0.14)
'''
# Funciones

#regressor = ini_modelo_rnn()
#time.sleep(5)

# Sincronización de la hora y los temporizadores
# Funcion del tiempo
def tiempo():
    global simbolo
    hora_server_s=[]
    hora_server = zeromq_mt4_ea_client("TIME|{}|0|0|0".format(simbolo))        # Se obtiene la hora del servidor del mt4
    print(hora_server)
    try:
        hora_server_s = hora_server.split(':')
        
    except:
        hora_server_s = ["Error"]
        return hora_server_s
    else:
        if(hora_server_s[0] == "HORA ACTUAL SERVER"):
            return hora_server_s
        hora_server_s = ["Error"]
        return hora_server_s
    finally:
        pass
    

def hora_server():
    t = 0
    hora_server1 = [0]
    #time_local = datetime.datetime.now(pytz.timezone('America/Bogota'))
    #hora_local = time_local.strftime("%S")
    while (len(hora_server1) != 4):
        time.sleep(0.00003)
        hora_server1 = tiempo()
        time.sleep(0.00006)
        
    while(hora_server1 == "Error"):
        time.sleep(0.00003)
        hora_server1 = tiempo()
        time.sleep(0.00006)    
    t = (int(hora_server1[2])%5)*60 + int(hora_server1[3])
    #t = datetime.timedelta(days=0,hours=0,minutes=0,seconds=dif_seg)    # Diferencia en formato datetime   
    return t
# Función que obtiene los datos de las 5 entradas a la RNN y para luego poder hacer la predicción
def get_data(simbolo='EURAUD'):       
    close1 =zeromq_mt4_ea_client("DATA|{}|CLOSE|0|0|20".format(simbolo))
    open1 =zeromq_mt4_ea_client("DATA|{}|OPEN|0|0|20".format(simbolo))
    high1 =zeromq_mt4_ea_client("DATA|{}|HIGH|0|0|20".format(simbolo))
    low1 =zeromq_mt4_ea_client("DATA|{}|LOW|0|0|20".format(simbolo))
    volumen1 = zeromq_mt4_ea_client("DATA|{}|VOLUMEN|0|0|20".format(simbolo))
    return parser(open1,high1,low1,close1,volumen1)
# Función para obtener los valores del Donchian Channel
def get_donchian(simbolo,digits):
    high1 =zeromq_mt4_ea_client("DATA|{}|HIGH|0|0|21".format(simbolo))    
    lista_sup = parser_donchian(high1)
    while(len(lista_sup) < 20):
        high1 =zeromq_mt4_ea_client("DATA|{}|HIGH|0|0|21".format(simbolo))
        lista_sup = parser_donchian(high1)
    low1 =zeromq_mt4_ea_client("DATA|{}|LOW|0|0|21".format(simbolo))
    lista_inf = parser_donchian(low1)
    while(len(lista_inf) < 20):
        low1 =zeromq_mt4_ea_client("DATA|{}|LOW|0|0|21".format(simbolo))
        lista_inf = parser_donchian(low1)
    banda_sup = round(max(lista_sup),digits)
    banda_inf = round(min(lista_inf),digits)
    lista = [banda_sup,banda_inf]
    return lista
# Función para hacer opereaciones y modificaciones en las ordenes
def trading(accion,tipo,simbolo,stoploss,precio):
    global ticket
    global paperturareal
    global lote
    data = []
    #digits = 0
    res = True
    #TRADE|ACTION|TYPE|SYMBOL|VOLUMEN|PRICE|SL|TP|COMMENT
    #"TRADE|{}|{}|EURUSD|0.1|0|50|50|Python-to-MT4"
    if(accion=="OPEN"):
        ticket =zeromq_mt4_ea_client("TRADE|OPEN|{}|{}|{}|0|{}|50|Robot-Python-v9.3".format(tipo,simbolo,lote,stoploss))
        return ticket
    if(accion=="MODIFICAR"):
        res = parser_data(zeromq_mt4_ea_client("TRADE|MODIFICAR|{}|{}|{}".format(ticket,paperturareal,stoploss)))
        try:
            while(len(res) > 1):
                res = parser_data(zeromq_mt4_ea_client("TRADE|MODIFICAR|{}|{}|{}".format(ticket,paperturareal,stoploss)))
                time.sleep(0.2)
            res = int(res[0])
        except:
            
            res = 2 
            return res
        else:
            return res
        finally:
            pass
    if(accion=="GET" and tipo == 1):
        # PRECIO_APERTURA|STOPLOSS|PIP|DIGITS|BID|ASK
        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|{}|1".format(ticket)))
        while( len(data) < 6):
            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|{}|1".format(ticket)))
            try:
                while(float(data[4]) > 2):
                    data = parser_data(zeromq_mt4_ea_client("TRADE|GET|{}|1".format(ticket)))
            except:
                data = parser_data(zeromq_mt4_ea_client("TRADE|GET|{}|1".format(ticket)))
            else:
                pass
            finally:
                pass
            try:
                if(float(data[4]) < 2):
                    break
            except:
                pass
            finally:
                pass
        return data
    if(accion=="GET" and tipo == 2):
        # DIGITS
        digits = zeromq_mt4_ea_client("TRADE|GET|123445|2")
        while("|" in digits):
            digits = zeromq_mt4_ea_client("TRADE|GET|123445|2")
        digits = int(digits)
        return digits
    if(accion=="GET" and tipo == 3):
        # BID|ASK
        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
        while(len(data) < 2):
            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
            try:
                while(float(data[0]) > 2):
                    data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
            except:
                data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
            else:
                pass
            finally:
                pass
            try:
                if(float(data[0]) < 2):
                    break
            except:
                pass
            finally:
                pass
        return data    
    if(accion=="CLOSE"):
        res = zeromq_mt4_ea_client("TRADE|CLOSE|{}|{}|0.1".format(ticket,tipo))
        return res
    
def inicializacion():
    #lista = get_data(simbolo)
    predicted_stock_price_anterior = 1
    hora_local = hora_server()
    time.sleep(300.001-hora_local)
    return predicted_stock_price_anterior
# Función para obtener carácteristicas de las velas
def get_vela(posicion=-2):
    global lista
    global simbolo
    vela =[]
    lista = get_data(simbolo)
    while(len(lista) < 20):
        lista = get_data(simbolo)
    #print(type(lista[-1][0]))
    #print("Última Lista: ",lista[-1])
    #print("Penultima Lista:", lista[-2])
    if(lista[posicion][0] < lista[posicion][-2]):
        color_vela = "VERDE"
        cola = abs(lista[posicion][0] - lista[posicion][-3])
        mecha = abs(lista[posicion][1] - lista[posicion][-2])
    elif(lista[posicion][0] > lista[posicion][-2]):
        color_vela = "ROJO"
        cola = abs(lista[posicion][-2] - lista[posicion][-3])
        mecha = abs(lista[posicion][1] - lista[posicion][0])
    else:
        color_vela = "GRIS"
        cola = abs(lista[posicion][-2] - lista[posicion][-3])
        mecha = abs(lista[posicion][1] - lista[posicion][0])
    cuerpo = abs(lista[posicion][0] - lista[posicion][-2])
    volumen = lista[posicion][-1]
    vela = [color_vela, cola,mecha,cuerpo,volumen]
    return vela
def get_indicador(tipo="TODOS",periodos=14):
    '''  "INDICADOR|SIMBOLO|TIMEFRAME|NÚMERO_DE_PERIODOS|TIPO"         
         e.g. INDICADOR|EURAUD|0|14|MA
         Los tipos son los siguientes: TODOS,RSI,MA,DONCHIAN
    '''         
    global simbolo    
    if(tipo == "TODOS"):
        # Datos recibidos:"RSI_PASADO|RSI_ACTUAL|EMA_LENTA_M5|EMA_RAPIDA_M5|EMA_LENTA_M30_PASADO|EMA_LENTA_M30_ACTUAL|DONCHIAN_SUP|DONCHIAN_INF"
        indicadores = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        while(len(indicadores) < 10 or indicadores[0] == simbolo):
            indicadores = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
            try:
                for i in indicadores:
                    float(i)
            except:
                indicadores = []
        return indicadores
    if(tipo == "RSI"):
        # Datos recibidos:"RSI_PASADO|RSI_ACTUAL"
        rsi = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        return rsi
        
    if(tipo == "MA"):
        # Datos recibidos:"EMA_LENTA_M5|EMA_RAPIDA_M5|EMA_LENTA_M30_PASADO|EMA_LENTA_M30_ACTUAL"
        ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        try:
            for i in ma:
                float(i)
        except:
            ma = []
        while(len(ma) < 4):
            ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
            try:
                for i in ma:
                    float(i)
            except:
                ma = []
        return ma
    if(tipo == "MA_TRAILINGSTOP"):
        # Datos recibidos:"EMA_TRAILINGSTOP"        
        try:
            for i in range(10):
                ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        except:
            ma = [1,2]
        ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        while(len(ma) > 1):            
            try:
                for i in range(10):                    
                    ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
                for i in ma:
                    float(i)
            except:
                ma = [1,2]
        return ma         
    if(tipo == "DONCHIAN"):
        # Datos recibidos:"DONCHIAN_SUPERIOR|DONCHIAN_INFERIOR"
        donchian = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        return donchian
def get_simbolo():
    simbolo = zeromq_mt4_ea_client("SIMBOLO")
    return simbolo
simbolo = get_simbolo()            
#predicted_stock_price_anterior = inicializacion()
cont = 0
lista = []
lista_dis_emalenta = []
lista_angulo_emarapida = []
vela = []
#--------------------------------------------+
# Variables usadas en las Ordenes de Trading +
#--------------------------------------------+
stoploss = 0.0
ticket = ""
paperturareal = 0.0
paperturaflot = 0.0
# Variable para la distancia entre el Precio de Apertura y el StopLoss
DAStop = 0.0
# Variable de la Distania del TrailStop
Dtrailstop = 0.0
predicionpips = 0.0
bid = 0.0
ask = 0.0
cont_tempo_10ms = 0
cont_tempo_100ms = 0
cont_tempo_seg = 0
res = 0
lote = 0.0
#--------------------------------------------+
# Loop que permite operar sincronizadamente  +
#--------------------------------------------+
locale.setlocale(locale.LC_ALL,'es-CO')
dtn = datetime.datetime.now(pytz.timezone('America/New_York'))
minutos = 60 - dtn.minute 
hora = dtn.hour + 1
if(hora < 25 and hora >= 16):
    x = 24-hora+4
if(hora > 0 and hora <= 4):
    x = 4-hora
if(hora < 16 and hora > 4):
    x = 0
    minutos = 0
print("Hora New York: {}:{}".format(dtn.hour,dtn.minute))    
print("{} horas con {} minutos en espera.".format(x,minutos))
time.sleep(x*3600 + minutos*60)
print("Termino el temporizador, ahora iniciara el loop de la aplicación.")
dtn = datetime.datetime.now(pytz.timezone('America/New_York'))
print("Hora New York: {}:{}".format(dtn.hour,dtn.minute))
dtc = datetime.datetime.now(pytz.timezone('America/Bogota'))
print("Hora Colombia-Bogotá:{}:{}".format(dtc.hour,dtc.minute))
print("Simbolo: ",simbolo)
while True:
    cont = 0.0    
    cont_tempo_10ms = 0
    cont_tempo_100ms = 0
    cont_tempo_seg = 0
    flag_donchian = 2
    flag_trailstop = 0
    flag_condiciones = 0
    lista_dis_emalenta = []
    lista_angulo_emarapida = []
    lote = 0.0
    #os.system('cls')
    # Datos recibidos:"RSI_PASADO|RSI_ACTUAL|EMA_LENTA_M5|EMA_RAPIDA_M5|EMA_LENTA_M30_PASADO|EMA_LENTA_M30_ACTUAL|DONCHIAN_SUP|DONCHIAN_INF"
    ma = get_indicador("MA")
    emalenta_m5 = float(ma[0])
    emarapida_m5 = float(ma[1])
    data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
    while(len(data) > 2):
        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
    digits = trading("GET",2,simbolo,stoploss,0)
    donchian = get_donchian(simbolo,digits)
    donchian_sup = donchian[0] 
    donchian_inf = donchian[1]    
    pip = (10*pow(10,-digits))/10
    precio = round(float(data[0]),digits)
    while((donchian_sup <= precio) or (donchian_inf >= precio)):
        print("1. El Precio Toco la banda de Donchian.")
        print("Precio:",precio)
        print("Canal Donchian:",donchian)
        print("MA:",ma)         
        if(donchian_inf >= precio):    # Indica que va haber una tendencia Alcista
            print("2. El Precio toco la Banda Inferior: hacia una Tendencia Alcista")
            flag_donchian = 1
            while(emarapida_m5 < emalenta_m5+1*pip):  # Temporizador hasta llegar al cruce de medias móviles
                ma = get_indicador("MA")
                emalenta_m5 = float(ma[0])
                emarapida_m5 = float(ma[1])
                time.sleep(0.2)
            print("3. Cruce de Medias Móviles: MARapida cruza  MA lenta de abajo hacia arriba")
            indicadores = get_indicador()
            rsi_pasado = float(indicadores[0])
            rsi_actual = float(indicadores[1])
            emalenta_m5_actual = float(indicadores[2])
            emalenta_m5_pasado = float(indicadores[8])
            emarapida_m5 = float(indicadores[3])
            emalenta_m30_pasado = float(indicadores[4])
            emalenta_m30_actual = float(indicadores[5])
            cont_tempo_seg = 300.01- hora_server()
            while(cont < cont_tempo_seg):
                indicadores = get_indicador()
                rsi_pasado = float(indicadores[0])
                rsi_actual = float(indicadores[1])
                emalenta_m5_actual = float(indicadores[2])
                emalenta_m5_pasado = float(indicadores[8])
                emarapida_m5 = float(indicadores[3])
                emarapida_m5_pasado = float(indicadores[9])
                emalenta_m30_pasado = float(indicadores[4])
                emalenta_m30_actual = float(indicadores[5])
                #lista_dis_emalenta.append(round(abs(emalenta_m5_actual-emalenta_m5_pasado),digits))
                #lista_angulo_emarapida.append(round(degrees(atan2(abs(emarapida_m5-emarapida_m5_pasado)*pow(10,digits),15)),2))
                if(emarapida_m5 >= emalenta_m5_actual and rsi_actual > rsi_pasado and rsi_actual > 50 
                   and emalenta_m30_actual > emalenta_m30_pasado and emalenta_m5_actual > emalenta_m5_pasado 
                   and abs(emalenta_m5_actual-emalenta_m5_pasado) >= 2*pip
                   and round(degrees(atan2(abs(emarapida_m5-emarapida_m5_pasado)*pow(10,digits),15)),2) > 39):
                    flag_condiciones = 1
                    break
                cont += 0.2
                time.sleep(0.2)
            #print("Lista de Angulos EMA Rapida: ",lista_angulo_emarapida)
            #print("Lista de Distancias EMA Lenta: ",lista_dis_emalenta)
            if(flag_condiciones == 1):      # Condición de cruce de medias móviles y rsi
                print("4. Se cumple la condición de cruce de medias móviles, rsi mayor a 50 y con pendiente alcista, y pendiente alcista de las MA de 30 min. ")
                if(cont < cont_tempo_seg):
                    time.sleep(300.01- hora_server())      # Temporizador para esperar la siguiente vela
                lista = get_data(simbolo)
                #vela = [color_vela, cola,mecha,cuerpo,volumen]
                vela = get_vela(-2)
                pip = (10*pow(10,-digits))/10
                if(vela[0] == "ROJO"):
                    time.sleep(300.01)
                    vela = get_vela(-2)
                if(vela[0] == "VERDE"):      # Señal de Confirmación de entrada
                    print("5. Vela Verde: Buy (UP)")
                    # Falta configurar el stoploss para que no supere el valor minimo de pérdidas por operación
                    stoploss = round(min([lista[-3][2],lista[-4][2],lista[-5][2]]),digits)
                    data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                    while(len(data) > 2):
                        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                    precio = round(float(data[0]),digits)
                    if(abs(precio - stoploss) < 70*pip):
                        if(abs(precio - stoploss) < 40*pip):
                            stoploss += 30*pip
                        lote = 0.30
                    elif(abs(precio - stoploss) >= 70*pip and abs(precio - stoploss) <= 90*pip):
                        lote = 0.21
                    elif(abs(precio - stoploss) > 90*pip and abs(precio - stoploss) <= 120*pip):
                        lote = 0.12
                    else:
                        print("No cumplio las condiciones para BUY, Stoploss superior a 120 pips")
                        break
                    print("Distancia Stoploss: ",abs(precio - stoploss))
                    ticket = trading("OPEN",0,simbolo,stoploss,0)
                    #cont = 1
                    print("Ticket: ",ticket)
                    if(int(ticket) > 0):
                        data = trading("GET",1,simbolo,stoploss,0)
                    else:
                        print("Falló al abrir el ticket")
                        break
                    if(int(ticket) > 0 and len(data) > 1):
                        #print(data)
                        digits = int(data[3])
                        paperturareal = float(data[0])
                        paperturaflot = float(data[0])
                        stoploss = float(data[1])
                        pip = float(data[2])
                        DAStop = abs(paperturareal - stoploss)
                        Dtrailstop = round(DAStop/2,digits)
                        while True:
                            res = trading("MODIFICAR",0,simbolo,stoploss,0)
                            if(res==0):
                                # Actualización de precio y bandas de donchian antes de quebrar o salir del while
                                indicadores = get_indicador()
                                donchian_sup = float(indicadores[6])
                                donchian_inf = float(indicadores[7])                                
                                data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                while(len(data) > 2):
                                    data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                precio = round(float(data[0]),digits)                                                                
                                break
                            data = trading("GET",1,simbolo,stoploss,0)
                            if(len(data) > 1):
                                bid = float(data[4])
                                stoploss = float(data[1])
                                if(bid >= (paperturaflot + Dtrailstop) ):
                                    stoploss += Dtrailstop
                                    if(flag_trailstop !=3):
                                        res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                        if(res == 1):                                
                                            paperturaflot += Dtrailstop
                                            flag_trailstop += 1
                                        elif(res == 0):
                                            flag_donchian = 2
                                            break
                                        else:
                                            stoploss -= Dtrailstop
                                    else:       # Condición para entrar en trailstop flag_trailstop=3
                                        print("6. Etapa de Trailstop")
                                        time.sleep(0.14)
                                        ma = get_indicador("MA_TRAILINGSTOP")
                                        emalenta_m5 = float(ma[0])
                                        while True:                                            
                                            ma = get_indicador("MA_TRAILINGSTOP")
                                            time.sleep(0.14)
                                            emalenta_m5 = float(ma[0])                                            
                                            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                            while(len(data) != 2):
                                                data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                            precio = round(float(data[0]),digits)
                                            if(emalenta_m5 >= precio or precio <= paperturareal+15*pip):
                                                print("7. Se cumplieron las condiciones para el cierre de la operacion: ",)
                                                print("EMA Lenta: ", emalenta_m5)
                                                print("Precio Apertura + 15 Pips: ", paperturareal+15*pip)
                                                print("Precio: ", precio)
                                                try:
                                                    res = int(trading("CLOSE",1,simbolo,stoploss,0))
                                                except:
                                                    res = 1
                                                else:
                                                    pass
                                                finally:
                                                    pass
                                                if(res==1):
                                                    break
                                            else:
                                                stoploss = emalenta_m5
                                                res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                                time.sleep(0.2)
                                        # Actualización de precio y bandas de donchian antes de quebrar o salir del while
                                        indicadores = get_indicador()
                                        donchian_sup = float(indicadores[6])
                                        donchian_inf = float(indicadores[7])
                                        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        while(len(data) > 2):
                                            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        precio = round(float(data[0]),digits)                                                
                                        break
                            else:
                                flag_donchian = 2
                                pass
                            time.sleep(0.2)
 
            else:
                flag_donchian = 2
                print("No cumplio las condiciones para BUY")
                break   # No se cumple las condiciones de entrada y se sale del loop   
        elif(donchian_sup <= precio):       # Indica que va haber una tendencia Bajista    
            print("2. El Precio toco la Banda Superior: hacia una Tendencia Bajista")
            flag_donchian = 0
            while(emarapida_m5 > emalenta_m5-1*pip):  # Temporizador hasta llegar al cruce de medias móviles
                ma = get_indicador("MA")
                emalenta_m5 = float(ma[0])
                emarapida_m5 = float(ma[1])
                time.sleep(0.2)
            print("3. Cruce de Medias Móviles: MARapida cruza  MA lenta de arriba hacia abajo")
            indicadores = get_indicador()
            rsi_pasado = float(indicadores[0])
            rsi_actual = float(indicadores[1])
            emalenta_m5_actual = float(indicadores[2])
            emalenta_m5_pasado = float(indicadores[8])
            emarapida_m5 = float(indicadores[3])
            emalenta_m30_pasado = float(indicadores[4])
            emalenta_m30_actual = float(indicadores[5])
            cont_tempo_seg = 300.01- hora_server()
            while(cont < cont_tempo_seg):                
                indicadores = get_indicador()
                rsi_pasado = float(indicadores[0])
                rsi_actual = float(indicadores[1])
                emalenta_m5_actual = float(indicadores[2])
                emalenta_m5_pasado = float(indicadores[8])
                emarapida_m5 = float(indicadores[3])
                emarapida_m5_pasado = float(indicadores[9])
                emalenta_m30_pasado = float(indicadores[4])
                emalenta_m30_actual = float(indicadores[5])
                #lista_dis_emalenta.append(round(abs(emalenta_m5_actual-emalenta_m5_pasado),digits))
                #lista_angulo_emarapida.append(round(degrees(atan2(abs(emarapida_m5-emarapida_m5_pasado)*pow(10,digits),15)),2))
                if(emarapida_m5 <= emalenta_m5_actual and rsi_actual < rsi_pasado and rsi_actual < 50 
                   and emalenta_m30_actual < emalenta_m30_pasado and emalenta_m5_actual < emalenta_m5_pasado 
                   and abs(emalenta_m5_actual-emalenta_m5_pasado) >= 2*pip
                   and round(degrees(atan2(abs(emarapida_m5-emarapida_m5_pasado)*pow(10,digits),15)),2) > 39):
                    flag_condiciones = 1
                    break
                cont += 0.2
                time.sleep(0.2)
            #print("Lista de Angulos EMA Rapida: ",lista_angulo_emarapida)
            #print("Lista de Distancias EMA Lenta: ",lista_dis_emalenta)
            if(flag_condiciones == 1):      # Condición de cruce de velas y rsi
                print("4. Se cumple la condición de cruce de medias móviles, rsi menor a 50 y con pendiente bajista, y pendiente bajista de las MA de 30 min. ")
                if(cont < cont_tempo_seg):
                    time.sleep(300.01- hora_server())      # Temporizador para esperar la siguiente vela
                lista = get_data(simbolo)
                #vela = [color_vela, cola,mecha,cuerpo,volumen]
                vela = get_vela(-2)
                pip = (10*pow(10,-digits))/10
                if(vela[0] == "VERDE"):
                    time.sleep(300.01)
                    vela = get_vela(-2)
                if(vela[0] == "ROJO"):      # Señal de Confirmación de entrada
                    print("5. Vela Roja: Sell (DOWN)")
                    # Falta configurar el stoploss para que no supere el valor minimo de pérdidas por operación
                    stoploss = round(max([lista[-3][1],lista[-4][1],lista[-5][1]]),digits)
                    data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                    while(len(data) > 2):
                        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                    precio = round(float(data[0]),digits)
                    if(abs(precio - stoploss) < 70*pip):
                        if(abs(precio - stoploss) < 40*pip):
                            stoploss += 30*pip
                        lote = 0.30
                    elif(abs(precio - stoploss) >= 70*pip and abs(precio - stoploss) <= 90*pip):
                        lote = 0.21
                    elif(abs(precio - stoploss) > 90*pip and abs(precio - stoploss) <= 120*pip):
                        lote = 0.12
                    else:
                        print("No cumplio las condiciones para SELL, Stoploss superior a 120 pips")
                        break
                    print("Distancia Stoploss: ",abs(precio - stoploss))
                    ticket = trading("OPEN",1,simbolo,stoploss,0)
                    cont = 1
                    print("Ticket: ",ticket)
                    if(int(ticket) > 0):
                        data = trading("GET",1,simbolo,stoploss,0)
                    else:
                        print("Falló al abrir el Ticket")
                        break
                    if(int(ticket) > 0 and len(data) > 1):
                        #print(data)
                        digits = int(data[3])
                        paperturareal = float(data[0])
                        paperturaflot = float(data[0])
                        stoploss = float(data[1])
                        pip = float(data[2])
                        DAStop = abs(paperturareal - stoploss)
                        Dtrailstop = round(DAStop/2,digits)
                        while True:
                            res = trading("MODIFICAR",0,simbolo,stoploss,0)
                            if(res==0):
                                # Actualización de precio y bandas de donchian antes de quebrar o salir del while
                                indicadores = get_indicador()
                                donchian_sup = float(indicadores[6])
                                donchian_inf = float(indicadores[7])                                
                                data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                while(len(data) > 2):
                                    data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                precio = round(float(data[0]),digits)                                                                
                                break
                            data = trading("GET",1,simbolo,stoploss,0)
                            if(len(data) > 1):
                                ask = float(data[5])
                                stoploss = float(data[1])
                                if(ask <= (paperturaflot - Dtrailstop) ):
                                    stoploss -= Dtrailstop
                                    if(flag_trailstop !=3):
                                        res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                        if(res == 1):                                
                                            paperturaflot -= Dtrailstop
                                            flag_trailstop += 1
                                        elif(res == 0):
                                            flag_donchian = 2
                                            break
                                        else:
                                            stoploss += Dtrailstop
                                    else:       # Condición para entrar en trailstop flag_trailstop=3
                                        print("6. Etapa de Trailstop")
                                        time.sleep(0.14)
                                        ma = get_indicador("MA_TRAILINGSTOP")
                                        emalenta_m5 = float(ma[0])
                                        while True:                                            
                                            ma = get_indicador("MA_TRAILINGSTOP")
                                            time.sleep(0.14)
                                            emalenta_m5 = float(ma[0])                                            
                                            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                            while(len(data) != 2):
                                                data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                            precio = round(float(data[0]),digits)
                                            if(emalenta_m5 <= precio or precio >= paperturareal-15*pip):
                                                print("7. Se cumplieron las condiciones para el cierre de la operacion: ",)
                                                print("EMA Lenta: ", emalenta_m5)
                                                print("Precio Apertura - 15 Pips: ", paperturareal-15*pip)
                                                print("Precio: ", precio)
                                                try:
                                                    res = int(trading("CLOSE",0,simbolo,stoploss,0))
                                                except:
                                                    res = 1
                                                else:
                                                    pass
                                                finally:
                                                    pass
                                                if(res==1):
                                                    break
                                            else:
                                                stoploss = emalenta_m5
                                                res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                                time.sleep(0.2)
                                        # Actualización de precio y bandas de donchian antes de quebrar o salir del while
                                        indicadores = get_indicador()
                                        donchian_sup = float(indicadores[6])
                                        donchian_inf = float(indicadores[7])
                                        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        while(len(data) > 2):
                                            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        precio = round(float(data[0]),digits)                                                
                                        break
                            else:
                                flag_donchian = 2
                                pass
                            time.sleep(0.2)

            else:
                flag_donchian = 2
                print("No cumplio las condiciones para SELL")
                break   # No se cumple las condiciones de entrada y se sale del loop   
        else:
            break
        break
    time.sleep(0.5)

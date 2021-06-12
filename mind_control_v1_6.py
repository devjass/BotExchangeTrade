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

ROBOT ENFOCADO PARA EL PAR: EUR/USD u otros pares de divisas con la misma proporcion
a nivel precio, es decir que el precio no supere el valor de 2.0

Cálculo de los indicadores con respecto a número de ticks o velas del pasado:

RSI: 1 vela hacia atrás
EMA_M30: 2 vela hacia atrás
 
Parámetros:
stoploss max = 50
cont = 500 ms


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
import copy
import os
import pytz
import locale
import openpyxl
from math import pow,degrees,atan2
from zeromq_mt4_cliente_v1_6 import zeromq_mt4_ea_client
from data_parser_v1_1 import parser,parser_data,parser_donchian

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
    t = (int(hora_server1[2])%2)*60 + int(hora_server1[3])      
    #t = datetime.timedelta(days=0,hours=0,minutes=0,seconds=dif_seg)    # Diferencia en formato datetime   
    return t
# Función que obtiene los datos de las 5 entradas a la RNN y para luego poder hacer la predicción
def get_data(simbolo='EURAUD',numero=20): 

 
    high1 =zeromq_mt4_ea_client("DATA|{}|HIGH|0|1|{}".format(simbolo,numero))    
    lista_high = parser_donchian(high1)
    while(len(lista_high) < numero):
        high1 =zeromq_mt4_ea_client("DATA|{}|HIGH|0|1|{}".format(simbolo,numero))
        lista_high = parser_donchian(high1)
    
    low1 =zeromq_mt4_ea_client("DATA|{}|LOW|0|1|{}".format(simbolo,numero))
    lista_low = parser_donchian(low1)
    while(len(lista_low) < numero):
        low1 =zeromq_mt4_ea_client("DATA|{}|LOW|0|1|{}".format(simbolo,numero))
        lista_low = parser_donchian(low1)
    
    open1 =zeromq_mt4_ea_client("DATA|{}|OPEN|0|1|{}".format(simbolo,numero))
    lista_open = parser_donchian(open1)
    while(len(lista_open) < numero):
        open1 =zeromq_mt4_ea_client("DATA|{}|OPEN|0|1|{}".format(simbolo,numero))
        lista_open = parser_donchian(open1)
    
    close1 =zeromq_mt4_ea_client("DATA|{}|CLOSE|0|1|{}".format(simbolo,numero))
    lista_close = parser_donchian(close1)
    while(len(lista_close) < numero):
        close1 =zeromq_mt4_ea_client("DATA|{}|CLOSE|0|1|{}".format(simbolo,numero))
        lista_close = parser_donchian(close1)
    lista = [lista_open,lista_high,lista_low,lista_close]
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
        ticket =zeromq_mt4_ea_client("TRADE|OPEN|{}|{}|{}|0|{}|50|Robot-Python-v9.1".format(tipo,simbolo,lote,stoploss))
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
        data1 = copy.copy(data)
        if(data[0] == "Orden Cerrada"):
            data = [1,2,3,4,5,6,7]
            
        while( len(data) < 6):
            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|{}|1".format(ticket)))
            if(data[0] == "Orden Cerrada"):
                data1 = copy.copy(data)
                break                
            try:
                if(float(data[0]) > 0 and len(data) == 6):
                    data1 = copy.copy(data)                
            except:
                data = [1,2,3,4,5]
            else:
               pass
            finally:
                pass
            data1 = copy.copy(data)
        data = data1
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
        try:
            float(data[0])                
        except:
            data = [1,2,3]
        else:
            pass
        finally:
            pass        
        while(len(data) != 2):
            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
            try:
                float(data[0])                
            except:
                data = [1,2,3]
            else:
                pass
            finally:
                pass
        return data              
    if(accion=="CLOSE"):
        res = zeromq_mt4_ea_client("TRADE|CLOSE|{}|{}|0.1".format(ticket,tipo))
        return res
    

# Función para obtener carácteristicas de las velas
def get_vela(numero =20):
    global lista
    global simbolo
    global digits
    vela =[]
    lista = get_data(simbolo,numero)
    promedio = get_promedio(lista,'CUERPO')
    while(promedio == 0):               # Loop para verificar y asegurarse que el promedio de las velas sea diferente de cero        
        lista = get_data(simbolo,numero)
        promedio = get_promedio(lista,'CUERPO')
        print("Promedio = ",promedio)
    for posicion in range(numero):
        if(lista[0][posicion] < lista[-1][posicion]):
            color_vela = "VERDE"
            cola = round(abs(lista[0][posicion] - lista[-2][posicion]),digits)
            mecha = round(abs(lista[1][posicion] - lista[-1][posicion]),digits)
        elif(lista[0][posicion] > lista[-1][posicion]):
            color_vela = "ROJO"
            cola = round(abs(lista[-1][posicion] - lista[-2][posicion]),digits)
            mecha = round(abs(lista[1][posicion] - lista[0][posicion]),digits)
        else:
            color_vela = "GRIS"
            cola = round(abs(lista[-1][posicion] - lista[-2][posicion]),digits)
            mecha = round(abs(lista[1][posicion] - lista[0][posicion]),digits)
        cuerpo = round(abs(lista[0][posicion] - lista[-1][posicion]),digits)
        maximo = lista[1][posicion]
        minimo = lista[-2][posicion]
        open1 = lista[0][posicion]
        #volumen = lista[posicion][-1]        
        vela.append([color_vela, cola,mecha,cuerpo,maximo,minimo,open1])
    #print("Close:",lista[-1])
    #print("Open:",lista[0])
    #print("High:", lista[1])
    #print("Low:", lista[2])
    #print(vela)
    return vela
# Funcion que saca el promedio de los cuerpos de una lista de velas
def get_promedio( velas=[],tipo ='VELAS'):
    global digits
    suma = 0
    cantidad = 0
    if(tipo == 'VELAS'):
        for i in range(len(velas)):
            if(i == len(velas)-1):
                pass
            else:                
                suma = suma + velas[i][3]
            #print(velas[i][3])
            cantidad = cantidad + 1
    else:
        for posicion in range(len(velas[0])):  
            try:
                cuerpo = round(abs(velas[0][posicion] - velas[-1][posicion]),digits)
                suma = suma + cuerpo
                cantidad = cantidad + 1
            except:
                suma = 0
                cantidad = 1
            else:
                pass
            finally:
                pass
  
    promedio = round(suma/cantidad,digits)
    print("CuerpoVp20:",promedio)
    return promedio       
        
def get_indicador(tipo="TODOS",periodos=14):
    '''  "INDICADOR|SIMBOLO|TIMEFRAME|NÚMERO_DE_PERIODOS|TIPO"         
         e.g. INDICADOR|EURAUD|0|14|MA
         Los tipos son los siguientes: TODOS,RSI,MA,DONCHIAN
    '''   
    global simbolo    
    if(tipo == "TODOS"):
        # Datos recibidos:"SMA8|SMA20_ACTUAL|SMA20_PASADO|SMA200|EMA5_ACTUAL|EMA5_PASADO|EMATRAILINGSTOP"
        indicadores = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        while(len(indicadores) < 7 or indicadores[0] == simbolo):
            indicadores = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
            try:
                for i in indicadores:
                    float(i)
            except:
                indicadores = []
        return indicadores

    if(tipo == "MA"):
        # Datos recibidos:"SMA20_ACTUAL|SMA20_PASADO|SMA200"
        ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
        try:
            for i in ma:
                float(i)
        except:
            ma = []
        while(len(ma) != 3):
            #time.sleep(0.01)
            ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
            try:
                for i in ma:
                    float(i)
            except:
                ma = []
            else:
                pass
            finally:
                pass
        return ma
 
    if(tipo == "MA_TRAILINGSTOP"):
        # Datos recibidos:"EMA_TRAILINGSTOP"
        #ma = parser_data(zeromq_mt4_ea_client("INDICADOR|{}|0|{}|{}".format(simbolo,periodos,tipo)))
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
            else:
                pass
            finally:
                pass                
        return ma    
def get_stoploss(tipo , stop, precio):
    if(tipo == "ELEFANTE"):
        pass

# Función para obtener la ubicación del evento       
def get_ubicacion():
    global digits
    global pip
    global stoploss
    global simbolo
    """Posibles ubicaciones de los eventos:
        1. SMA-20 en contacto con la vela
        2. El Precio un poco por encima de la SMA-20
        3. El Precio un poco por debajo de la SMA-20
        4. El Precio muy por debajo de la SMA-20
        5. El Precio muy por encima de la SMA-20
    """
    sma_20 = get_indicador("MA")
    data = trading("GET",3,simbolo,stoploss,0)
    precio = round(float(data[0]),digits)
    velas = get_vela(21)
    cuerpo_vp20 = get_promedio(velas)
    ubicacion = 5
        
    if(precio > 1.5*cuerpo_vp20 + float(sma_20[0])):        # Verificación 5ta ubicación
        print("No cumplio para operar: 5ta ubicación")
        ubicacion = 5        
    elif(precio >= 0.2*cuerpo_vp20 + float(sma_20[0]) and precio <= 1.5*cuerpo_vp20 + float(sma_20[0])):      # Verificación 2da ubicción
        print("Zona: 2da ubicación")
        ubicacion = 2
    elif(precio <= float(sma_20[0]) - 0.2*cuerpo_vp20  and precio >= float(sma_20[0]) - 1.5*cuerpo_vp20):   # Verificación 3ra ubicación
        print("Zona: 3ra ubicación")
        ubicacion = 3
    elif(precio < float(sma_20[0]) - 3*cuerpo_vp20):     # Verificación 4ta ubicación
        print("Zona: 4ta ubicación")
        ubicacion = 4
    elif((float(sma_20[0]) <= precio and float(sma_20[0]) >= velas[-1][-1]) or (float(sma_20[0]) >= precio and float(sma_20[0]) <= velas[-1][-1])):     # Verificación 1era ubicación 
        print("Zona: 1era ubicación")
        ubicacion = 1        
    # Validación de Lotes y Stoploss máximo por operación
    if(abs(precio - stoploss)<= 40*pip):
        tipo_lote = "TODO"
        lote = get_lote(tipo_lote,ubicacion)
    elif(abs(precio - stoploss) > 40*pip and abs(precio - stoploss) <= 60*pip):
        tipo_lote = "LIGERO"
        lote = get_lote(tipo_lote,ubicacion)
    else:
        print("Distancia Stoploss: ",abs(precio - stoploss))
        print("Pip:",pip)
        print("No cumplio requisito minimo de stoploss, stoploss mayor a 60 pips")
        tipo_lote = "NO OPERAR"
        lote = 0
        ubicacion = 5

    return [lote,ubicacion]
        
    
def get_lote(tipo_lote, ubicacion):
    global stoploss
    global evento    
    ligero = 0.12
    mediano = 0.21
    pesado = 0.3
    todo = 0.4
    
    if(tipo_lote == "TODO"):
        if(ubicacion == 1 or ubicacion == 2):
            lote = ligero
        elif(ubicacion == 3):
            lote = mediano
        elif(ubicacion == 4):
            if(evento == "ANULADA"):
                lote = todo
            else:
                lote = pesado
        elif(ubicacion == 5):
            lote = 0
    elif(tipo_lote == "LIGERO"):
        if(ubicacion == 1 or ubicacion == 2):
            lote = ligero
        elif(ubicacion == 3):
            lote = ligero
        elif(ubicacion == 4):            
            lote = ligero
        elif(ubicacion == 5):
            lote = 0
    else:
        lote = 0
    
    return lote   
        
def get_ganancia():
    global pip,digits,lote,paperturareal,evento,operacion,lote_ubicacion
    global ganancia_orden,ganancia_dia,lista_ordenes,perdida_max
    global flag_ganancia_1, flag_ganancia_2,flag_ganancia_3
    flag_excel = 0
    
    data = trading("GET",3,simbolo,stoploss,0)
    pcierre = round(float(data[0]),digits)
    volumen = lote*100000
    if(operacion == "BUY"):        
        num_pips = round((pcierre - paperturareal)*pow(10,digits),0)
    else:
        num_pips = round((paperturareal - pcierre)*pow(10,digits),0)
    valor_pip = (pip/paperturareal)*volumen
    # Definición de la comisión de acuerdo al lotaje
    if(lote == 0.12):
        comision = 0.66
    elif(lote == 0.21):
        comision = 1.16
    elif(lote == 0.3):
        comision = 1.66
    elif(lote == 0.4):
        comision = 2.2
    else:
        comision = 0
    ganancia_orden = valor_pip*num_pips -0.5
    ganancia_dia += ganancia_orden - comision
    # Validación si la operación fue con perdidas o gannacias(loss o win)
    if(ganancia_orden - comision < 0):
        loss = 1
        win = 0
    else:
        loss = 0
        win = 1   
    # Código para registrar ordenes en el documento de excell
    dtn = datetime.datetime.now(pytz.timezone('Europe/London'))
    fecha = str(dtn.date())
    fecha = "{}/{}/{}".format(fecha.split("-")[2],fecha.split("-")[1],fecha.split("-")[0])
    lista_ordenes.append([fecha,evento,operacion,lote_ubicacion[1],paperturareal,pcierre,num_pips,lote,-1*comision,ganancia_orden,loss,win])
    while True:
        try:
            doc=openpyxl.load_workbook("H:\ESTUDIOS PROFESIONALES\TRADING\Test Robot TE v6.xlsx")     #Ingrese el nombre del archivo en excel con su respectiva extensión .xlsx
        except:
            time.sleep(0.5)
        else:
            flag_excel = 1
        finally:
            pass
        if(flag_excel == 1):
            break
            
    hoja=doc.get_sheet_by_name("TE GBP-JPY")                #El usuario debe seleccionar y escribir el nombre de la hoja a escanear, se guarda en la variable hoja
    # Código para detectar la fila donde se debe empezar a llenar
    i=""                                                                                       #La variable i es para contar el número de url's
    for fila in hoja.rows:
        if(i!=""):
            break
        #Primero for loop para recorrer fila por fila
        for columna in fila:                                                                    #Segundo for loop para recorrer por columna
            if("A"==columna.coordinate[0]):            
                                                                  #Condicional if para solo agregar los valores de la columna escogida
                if(hoja[columna.coordinate].value==None):
                    #print(columna.coordinate[1:])
                    i = columna.coordinate[1:]
                    break
    i = int(i)
    for k in range(len(lista_ordenes)):
        for j in range(len(lista_ordenes[0])):
            if(j == 0):
                hoja['A{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 1):
                hoja['B{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 2):
                hoja['C{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 3):
                hoja['D{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 4):
                hoja['E{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 5):
                hoja['F{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 6):
                hoja['G{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 7):
                hoja['H{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 8):
                hoja['I{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 9):
                hoja['J{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 10):
                hoja['M{}'.format(i)] = lista_ordenes[k][j]
            elif(j == 11):
                hoja['N{}'.format(i)] = lista_ordenes[k][j]            
        i += 1
    doc.save("H:\ESTUDIOS PROFESIONALES\TRADING\Test Robot TE v6.xlsx")
    lista_ordenes = []     
    # Definición de la perdida maxima
    if(ganancia_dia < 15):
        perdida_max = -15
    elif(ganancia_dia >=15 and ganancia_dia < 20):
        flag_ganancia_1 = 1
    elif(ganancia_dia >=20 and ganancia_dia < 25):
        flag_ganancia_2 = 1
        if(flag_ganancia_1 == 0):
            flag_ganancia_1 = 1
    elif(ganancia_dia >= 25):
        flag_ganancia_3 = 1
        if(flag_ganancia_1 == 0):
            flag_ganancia_1 = 1
        if(flag_ganancia_2 == 0):
            flag_ganancia_2 = 1
    
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
lote_ubicacion = [0,5]
cont_velas = 0
#--------------------------------------------+
# Variables usadas en las Ordenes de Trading +
#--------------------------------------------+
stoploss = 0.0
ticket = ""
paperturareal = 0.0
paperturaflot = 0.0
lote = 0.0
pcierre = 0.0
comision = 0.0
num_pips = 0
ganancia_orden = 0.0
ganancia_dia = 0.0
perdida_max = -15
flag_ganancia_1 = 0
flag_ganancia_2 = 0
flag_ganancia_3 = 0
lista_ordenes = []
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
hora = 0
#--------------------------------------------+
# Loop que permite operar sincronizadamente  +
#--------------------------------------------+

locale.setlocale(locale.LC_ALL,'es-CO')
dtn = datetime.datetime.now(pytz.timezone('Europe/London'))
minutos = 60 - dtn.minute 
hora = dtn.hour + 1
if(hora < 25 and hora >= 12):
    x = 24-hora+5
    #minutos = minutos + 30
elif(dtn.hour > 0 and dtn.hour < 5):
    x = 5-hora
    #minutos = minutos + 30
elif(dtn.hour < 12 and dtn.hour >= 5):
    x = 0
    minutos = 0

print("Hora Europa: {}:{}".format(dtn.hour,dtn.minute))    
print("{} horas con {} minutos en espera.".format(x,minutos))
time.sleep(x*3600 + minutos*60)
print("Termino el temporizador, ahora iniciara el loop de la aplicación.")
dtn = datetime.datetime.now(pytz.timezone('Europe/London'))
print("Hora Europa: {}:{}".format(dtn.hour,dtn.minute))
dtc = datetime.datetime.now(pytz.timezone('America/Bogota'))
print("Hora Colombia-Bogotá:{}:{}".format(dtc.hour,dtc.minute))

print("Simbolo: ",simbolo)
while True:
    if(ganancia_dia <= perdida_max):
        break
    if(hora >= 10):            
        break    
    cont = 0.0    
    cont_tempo_10ms = 0
    cont_tempo_100ms = 0
    cont_tempo_seg = 0
    flag_donchian = 2
    flag_trailstop = 0
    flag_condiciones = 0
    flag_evento = 0
    lista_dis_emalenta = []
    lista_angulo_emarapida = []
    lote = 0.0
    cont_velas = 0
    #os.system('cls')
    # Datos recibidos:"RSI_PASADO|RSI_ACTUAL|EMA_LENTA_M5|EMA_RAPIDA_M5|EMA_LENTA_M30_PASADO|EMA_LENTA_M30_ACTUAL|DONCHIAN_SUP|DONCHIAN_INF"
    sma_20 = get_indicador("MA")    
    data = trading("GET",3,simbolo,stoploss,0)   
    digits = trading("GET",2,simbolo,stoploss,0)
    pip = (10*pow(10,-digits))/10
    precio = round(float(data[0]),digits)
    time.sleep(0.12)
    velas = get_vela(21)
    cuerpo_vp20 = get_promedio(velas)
    print("Cuerpo_Vp20:", cuerpo_vp20)
    print("Precio:",precio)
    if(precio > 1.5*cuerpo_vp20 + float(sma_20[0])):
        time.sleep(120.01- hora_server())   # Temporizador para esperar la siguiente vela
        print("Zona de no operacion: 5ta ubicación")
    else:             
        print("1. El Precio Dentro de la Zona de Eventos.")
        print("Precio:",precio)
        print("Zona Superior sin eventos:", 1.5*cuerpo_vp20 + float(sma_20[0]))
        print("SMA-20:",sma_20[0])        
    while(precio <= 1.5*cuerpo_vp20 + float(sma_20[0])):   # El Precio esta dentro de la zona de eventos factibles
        # Verificación de los Eventos
        # 1. Verificacón de Vela Elefante
        flag_trailstop = 0
        lote_ubicacion = [0,5]
        flag_evento = 0
        flag_condiciones = 0
        cont_velas = 0
        cont = 0        
        velas = get_vela(2)
        cuerpo = velas[-2][3]
        cola = velas[-2][1]
        mecha = velas[-2][2]
        maximo = velas[-2][-3]
        minimo = velas[-2][-2]
        maximo1 = velas[-1][-3]
        minimo1 = velas[-1][-2]        
        if(cuerpo >= 1.5*cuerpo_vp20 and cuerpo <= 3*cuerpo_vp20):      # Vela Elefante de Cuerpo Grande 
            if(velas[-2][0] == "VERDE"):        # Vela Elefante Alcista
                if(cuerpo > 2*cola and cuerpo > 2*mecha ):       # Las mechas y las sombras son menores que el cuerpo

                    print("2.Vela Elefante Alcista")
                    cont_tempo_seg = 120.01- hora_server()
                    cont = 0
                    while(cont < cont_tempo_seg):
                        lote_ubicacion = [0,5]                        
                        data = trading("GET",3,simbolo,stoploss,0)
                        precio = round(float(data[0]),digits)                        
                        if(precio > maximo):       # Verficacion del evento alcista
                            print("3.Cumple el evento Vela Elefante Alcista")
                            stoploss = minimo - 4*pip
                            operacion = "BUY"
                            evento = "ELEFANTE"
                            time.sleep(0.12)
                            flag_evento = 1
                            lote_ubicacion = get_ubicacion()                        
                            break
                        '''if(precio < minimo or minimo1 < minimo):
                            print("2.Vela Oso 180")
                            print("3.Cumple el evento Oso 180")
                            stoploss = maximo + 4*pip
                            operacion = "SELL"
                            evento = "OSO"
                            time.sleep(0.12)
                            flag_evento = 1
                            lote_ubicacion = get_ubicacion()                        
                            break'''
                        cont += 0.2
                        time.sleep(0.2)
            elif(velas[-2][0] == "ROJO"):        # Vela Elefante Bajista
                if(cuerpo > 2*cola and cuerpo > 2*mecha ):       # Las mechas y las sombras son menores que el cuerpo

                    print("2.Vela Elefante Bajista")
                    cont_tempo_seg = 120.01- hora_server()
                    cont = 0
                    while(cont < cont_tempo_seg):
                        lote_ubicacion = [0,5]                        
                        data = trading("GET",3,simbolo,stoploss,0)
                        precio = round(float(data[0]),digits)                        
                        if(precio < minimo):       # Verficacion del evento bajista
                            print("3.Cumple el evento Vela Elefante Bajista")
                            stoploss = maximo +4*pip
                            operacion = "SELL"
                            evento = "ELEFANTE"
                            time.sleep(0.12)
                            flag_evento = 1
                            lote_ubicacion = get_ubicacion()
                            break
                        '''if(precio > maximo or maximo1 > maximo):
                            print("2.Vela Toro 180")
                            print("3.Cumple el evento Toro 180 Alcista")
                            stoploss = minimo - 4*pip
                            operacion = "BUY"
                            evento = "TORO"
                            time.sleep(0.12)
                            flag_evento = 1
                            lote_ubicacion = get_ubicacion()                        
                            break'''
                        cont += 0.2
                        time.sleep(0.2)
            else:
                lote_ubicacion = [0,5]
        # 2. Verificación Vela Elefante Martillo 
        if(cola + mecha >= 1.5*cuerpo_vp20 and cola + mecha <= 3*cuerpo_vp20 and flag_evento == 0):          
            if(4*cuerpo < cola or 4*cuerpo < mecha ):
                if(cuerpo >= 0.3*cuerpo_vp20):
                    if(cola >= 3*mecha):        # Vela Elefante martillo Alcista    
                        print("2.Vela Elefante Martillo Alcista")
                        cont_tempo_seg = 120.01- hora_server()
                        cont = 0
                        while(cont < cont_tempo_seg):
                            lote_ubicacion = [0,5]                        
                            data = trading("GET",3,simbolo,stoploss,0)
                            precio = round(float(data[0]),digits)                        
                            if(precio > maximo):       # Verficacion del evento alcista
                                print("3.Cumple el evento Vela Elefante Martillo Alcista")
                                stoploss = minimo - 4*pip
                                operacion = "BUY"
                                evento = "ELEFANTE"
                                time.sleep(0.12)
                                flag_evento = 1
                                lote_ubicacion = get_ubicacion()
                                break
                            '''if(precio < minimo):
                                print("2.Vela Oso 180")
                                print("3.Cumple el evento Oso 180")
                                stoploss = maximo + 4*pip
                                operacion = "SELL"
                                evento = "OSO"
                                time.sleep(0.12)
                                flag_evento = 1
                                lote_ubicacion = get_ubicacion()                        
                                break'''
                            cont += 0.2
                            time.sleep(0.2)
                    elif(mecha >= 3*cola):        # Vela Elefante martillo Bajista
    
                        print("2.Vela Elefante Martillo Bajista")
                        cont_tempo_seg = 120.01- hora_server()
                        cont = 0
                        while(cont < cont_tempo_seg):
                            lote_ubicacion = [0,5]                        
                            data = trading("GET",3,simbolo,stoploss,0)
                            precio = round(float(data[0]),digits)                        
                            if(precio < minimo):       # Verficacion del evento bajista
                                print("3.Cumple el evento Vela Elefante Martillo Bajista")
                                stoploss = maximo +4*pip
                                operacion = "SELL"
                                evento = "ELEFANTE"
                                time.sleep(0.12)
                                flag_evento = 1
                                lote_ubicacion = get_ubicacion()
                                break
                            '''if(precio > maximo):
                                print("2.Vela Toro 180")
                                print("3.Cumple el evento Toro 180 Alcista")
                                stoploss = minimo - 4*pip
                                operacion = "BUY"
                                evento = "TORO"
                                time.sleep(0.12)
                                flag_evento = 1
                                lote_ubicacion = get_ubicacion()                        
                                break'''
                            cont += 0.2
                            time.sleep(0.2)
                    else:
                        lote_ubicacion = [0,5]                        
        # 3. Verificacion Toro u Oso 180
        if(cuerpo >= 0.7*cuerpo_vp20 and cuerpo <= 3*cuerpo_vp20 and flag_evento == 0):      
            if(velas[-2][0] == "ROJO"):        # Toro 180 Alcista
                cont_tempo_seg = 120.01- hora_server()
                cont = 0
                while(cont < cont_tempo_seg):
                    lote_ubicacion = [0,5]                        
                    data = trading("GET",3,simbolo,stoploss,0)
                    precio = round(float(data[0]),digits)                        
                    if(precio > maximo):       # Verficacion del evento Toro 180 alcista
                        print("2.Toro 180 Alcista")
                        print("3.Cumple el evento Toro 180 Alcista")                        
                        stoploss = minimo - 4*pip
                        operacion = "BUY"
                        evento = "TORO"
                        time.sleep(0.12)
                        flag_evento = 1
                        lote_ubicacion = get_ubicacion()
                        break
                    cont += 0.2
                    time.sleep(0.2)
            elif(velas[-2][0] == "VERDE"):        # Oso 180 Bajista                
                cont_tempo_seg = 120.01- hora_server()
                cont = 0
                while(cont < cont_tempo_seg):
                    lote_ubicacion = [0,5]                        
                    data = trading("GET",3,simbolo,stoploss,0)
                    precio = round(float(data[0]),digits)                        
                    if(precio < minimo):       # Verficacion del evento Oso 180 bajista
                        print("3.Cumple el evento Oso 180 Bajista")
                        stoploss = maximo +4*pip
                        operacion = "SELL"
                        evento = "OSO"
                        time.sleep(0.12)
                        flag_evento = 1
                        lote_ubicacion = get_ubicacion()
                        break
                    cont += 0.2
                    time.sleep(0.2)
            else:
                lote_ubicacion = [0,5]                    

        # 4. Verificacion Vela Anulada
        if(cuerpo >= 0.7*cuerpo_vp20 and cuerpo <= 3*cuerpo_vp20 and flag_evento == 0):      
            if(velas[-2][0] == "ROJO"):        # Vela Anulada Alcista
                cont_tempo_seg = 120.01- hora_server()
                cont = 0
                cont_velas = 0
                while True:
                    velas = get_vela(3)
                    cuerpo = velas[-2][3]
                    cola = velas[-2][1]
                    mecha = velas[-2][-2]
                    maximo1 = velas[-2][-3]
                    minimo1 = velas[-2][-2]
                    lote_ubicacion = [0,5]                        
                    data = trading("GET",3,simbolo,stoploss,0)
                    precio = round(float(data[0]),digits)                        
                    if(minimo1 < minimo):
                        print("No cumplio las condiciones de Vela Anulada Alcista")
                        break
                    if(precio < minimo):
                        print("No cumplio las condiciones de Vela Anulada Alcista")
                        break                    
                    if(precio > maximo):       # Verficacion del evento Vela Anulada alcista
                        print("2.Vela Anulada Alcista")
                        print("3.Cumple el evento Vela Anulada Alcista")                        
                        stoploss = minimo - 4*pip
                        operacion = "BUY"
                        evento = "ANULADA"
                        time.sleep(0.12)
                        flag_evento = 1
                        lote_ubicacion = get_ubicacion()
                        break
                    time.sleep(0.2)
                    cont += 0.2
                    if(cont >= cont_tempo_seg ):
                        cont_tempo_seg = 120.01- hora_server()
                        cont = 0
                        cont_velas =+ 1
                    if(cont_velas == 6):
                        cont_velas = 0
                        cont = 0
                        print("No cumplio las condiciones de Vela Anulada Alcista")
                        break                    
                    
            elif(velas[-2][0] == "VERDE"):        # Vela Anulada Bajista
                cont_tempo_seg = 120.01- hora_server()
                cont = 0
                cont_velas = 0
                while True:
                    velas = get_vela(3)
                    cuerpo = velas[-2][3]
                    cola = velas[-2][1]
                    mecha = velas[-2][-2]
                    maximo1 = velas[-2][-3]
                    minimo1 = velas[-2][-2]                    
                    lote_ubicacion = [0,5]                        
                    data = trading("GET",3,simbolo,stoploss,0)
                    precio = round(float(data[0]),digits)
                    if(maximo1 > maximo):
                        print("No cumplio las condiciones de Vela Anulada Bajista")
                        break
                    if(precio > maximo):
                        print("No cumplio las condiciones de Vela Anulada Bajista")
                        break
                    if(precio < minimo):       # Verficacion del evento Oso 180 bajista
                        print("2.Vela Anulada Bajista")
                        print("3.Cumple el evento Vela Anulada Bajista")
                        stoploss = maximo +4*pip
                        operacion = "SELL"
                        evento = "ANULADA"
                        time.sleep(0.12)
                        flag_evento = 1
                        lote_ubicacion = get_ubicacion()
                        break
                    cont += 0.2
                    time.sleep(0.2)
                    if(cont >= cont_tempo_seg ):
                        cont_tempo_seg = 120.01- hora_server()
                        cont = 0
                        cont_velas =+ 1
                    if(cont_velas == 6):
                        cont_velas = 0
                        cont = 0
                        print("No cumplio las condiciones de Vela Anulada Bajista")
                        break
                    
            else:
                lote_ubicacion = [0,5]                            
              


        if(lote_ubicacion[0] > 0):      # Cumple condiciones para operar
            time.sleep(0.12)
            sma_20 = get_indicador("MA")
            if(operacion == "BUY"):      # Señal de Confirmación de entrada
                if(lote_ubicacion[1] < 4 and float(sma_20[0]) > float(sma_20[1]) ):
                    flag_condiciones = 1
                if(lote_ubicacion[1] == 4):
                    flag_condiciones = 1
                if(flag_condiciones == 1):
                    print("4. Se cumple las condiciones para operar")
                    print("5. Tipo de Operación: Buy (UP)")
                    lote = lote_ubicacion[0]
                    data = trading("GET",3,simbolo,stoploss,0)
                    precio = round(float(data[0]),digits)
                    print("Distancia Stoploss: ",abs(precio - stoploss))
                    if(abs(precio - stoploss) <= 9*pip):
                        print("No cumplio condiciones de Distancia de stoploss minima: 10 pips")
                        break
                    ticket = trading("OPEN",0,simbolo,stoploss,0)
                    #cont = 1
                    print("Ticket: ",ticket)
                    if(int(ticket) > 0):
                        data = trading("GET",1,simbolo,stoploss,0)
                    else:
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
                        print("P.AperturaReal:",paperturareal)
                        print("P.AperturaFlot:",paperturaflot)
                        print("Stoploss:",stoploss)
                        print("DtrailStop:",Dtrailstop)
                        print("Flag_Trailstop:",flag_trailstop)                        
                        while True:
                     
                            data = trading("GET",1,simbolo,stoploss,0)
                            if(len(data) > 1):
                                bid = float(data[4])
                                stoploss = float(data[1])
                                if(bid >= (paperturareal + 2*Dtrailstop) and flag_trailstop == 0):
                                    stoploss += Dtrailstop
                                    print("Flag_Trailstop:",flag_trailstop)
                                    if(flag_trailstop !=2):
                                        res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                        print("Res_MODIFICAR:",res)
                                        if(res == 1):                                
                                            paperturaflot += Dtrailstop
                                            flag_trailstop += 1
                                        elif(res == 0):
                                            flag_donchian = 2
                                            break
                                        else:
                                            stoploss -= Dtrailstop
                                elif(bid >= (paperturareal + 3*Dtrailstop) and flag_trailstop == 1):
                                    stoploss += (Dtrailstop)
                                    print("Flag_Trailstop:",flag_trailstop)
                                    if(flag_trailstop !=2):
                                        res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                        print("Res_MODIFICAR:",res)
                                        if(res == 1):                                
                                            paperturaflot += Dtrailstop
                                            flag_trailstop += 1
                                        elif(res == 0):
                                            flag_donchian = 2
                                            break
                                        else:
                                            stoploss -= Dtrailstop
                                    
                                elif(bid >= (paperturareal + 4*Dtrailstop) and flag_trailstop == 2):       # Condición para entrar en trailstop flag_trailstop=2
                                    stoploss = paperturareal
                                    res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                    print("6. Etapa de Trailstop")
                                    time.sleep(0.12)
                                    ma = get_indicador("MA_TRAILINGSTOP")
                                    emalenta_m5_actual = float(ma[0])
                                    while True:
                                        time.sleep(0.12)
                                        ma = get_indicador("MA_TRAILINGSTOP")                                            
                                        emalenta_m5_actual = float(ma[0])
                                        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        while(len(data) != 2):
                                            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        precio = round(float(data[0]),digits)
                                        if(emalenta_m5_actual >= precio or precio <= paperturareal+15*pip or res == 0):
                                            print("7. Se cumplieron las condiciones para el cierre de la operacion: ",)
                                            print("EMA Lenta: ", emalenta_m5_actual)
                                            print("Precio Apertura + 15 Pips: ", paperturareal+15*pip)
                                            print("Precio: ", precio)
                                            get_ganancia()
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
                                            stoploss = emalenta_m5_actual
                                            res = trading("MODIFICAR",0,simbolo,stoploss,0)                                                
                                            time.sleep(0.2)
                                    # Actualización de precio  e indicadores
                                    time.sleep(0.12)
                                    sma_20 = get_indicador("MA")    
                                    data = trading("GET",3,simbolo,stoploss,0)
                                    digits = trading("GET",2,simbolo,stoploss,0)
                                    pip = (10*pow(10,-digits))/10
                                    precio = round(float(data[0]),digits)
                                    time.sleep(0.12)
                                    velas = get_vela(21)
                                    cuerpo_vp20 = get_promedio(velas)                                               
                                    break
                            else:
                                if(data[0]=="Orden Cerrada"):
                                    get_ganancia()
                                    break                                
                                flag_donchian = 2
                                pass
                            time.sleep(0.2)
                else:
                    print("No cumplio las condiciones de la tendencia de la SMA-20")                            

            elif(operacion == "SELL"):
                
                if(lote_ubicacion[1] < 4 and float(sma_20[0]) < float(sma_20[1]) ):
                    flag_condiciones = 1
                if(lote_ubicacion[1] == 4):
                    flag_condiciones = 0
                if(flag_condiciones == 1):                
                    print("4. Se cumple las condiciones para operar")
                    print("5. Tipo de Operación: Sell (DOWN)")
                    lote = lote_ubicacion[0]
                    data = trading("GET",3,simbolo,stoploss,0)
                    precio = round(float(data[0]),digits)
                    print("Distancia Stoploss: ",abs(precio - stoploss))
                    if(abs(precio - stoploss) <= 9*pip):
                        print("No cumplio condiciones de Distancia de stoploss minima: 10 pips")
                        break                    
                    ticket = trading("OPEN",1,simbolo,stoploss,0)
                    cont = 1
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
                        print("P.AperturaReal:",paperturareal)
                        print("P.AperturaFlot:",paperturaflot)
                        print("Stoploss:",stoploss)
                        print("DtrailStop:",Dtrailstop)
                        print("Flag_Trailstop:",flag_trailstop)                        
                        while True:
                     
                            data = trading("GET",1,simbolo,stoploss,0)
                            if(len(data) > 1):
                                ask = float(data[5])
                                stoploss = float(data[1])
                                if(ask <= (paperturareal - 2*Dtrailstop) and flag_trailstop == 0 ):
                                    stoploss -= Dtrailstop
                                    print("Flag_Trailstop:",flag_trailstop)
                                    if(flag_trailstop !=2):
                                        res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                        if(res == 1):                                
                                            paperturaflot -= Dtrailstop
                                            flag_trailstop += 1
                                        elif(res == 0):
                                            flag_donchian = 2
                                            break
                                        else:
                                            stoploss += Dtrailstop
                                elif(ask <= (paperturareal - 3*Dtrailstop) and flag_trailstop == 1):
                                    stoploss -= (Dtrailstop)
                                    print("Flag_Trailstop:",flag_trailstop)
                                    if(flag_trailstop !=2):
                                        res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                        if(res == 1):                                
                                            paperturaflot -= Dtrailstop
                                            flag_trailstop += 1
                                        elif(res == 0):
                                            flag_donchian = 2
                                            break
                                        else:
                                            stoploss += Dtrailstop                                            
                                elif(ask <= (paperturareal - 4*Dtrailstop) and flag_trailstop == 2):       # Condición para entrar en trailstop flag_trailstop=2
                                    stoploss = paperturareal
                                    res = trading("MODIFICAR",0,simbolo,stoploss,0)                                       
                                    print("6. Etapa de Trailstop")
                                    time.sleep(0.12)
                                    ma = get_indicador("MA_TRAILINGSTOP")
                                    emalenta_m5_actual = float(ma[0])
                                    while True:
                                        time.sleep(0.12)
                                        ma = get_indicador("MA_TRAILINGSTOP")                                            
                                        emalenta_m5_actual = float(ma[0])                                            
                                        data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        while(len(data) != 2):
                                            data = parser_data(zeromq_mt4_ea_client("TRADE|GET|123456|3"))
                                        precio = round(float(data[0]),digits)
                                        if(emalenta_m5_actual <= precio or precio >= paperturareal-15*pip or res == 0):
                                            print("7. Se cumplieron las condiciones para el cierre de la operacion: ",)
                                            print("EMA Lenta: ", emalenta_m5_actual)
                                            print("Precio Apertura - 15 Pips: ", paperturareal-15*pip)
                                            print("Precio: ", precio)
                                            get_ganancia()
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
                                            stoploss = emalenta_m5_actual
                                            res = trading("MODIFICAR",0,simbolo,stoploss,0)
                                            time.sleep(0.2)
                                    # Actualización de precio e indicadores
                                    time.sleep(0.12)
                                    sma_20 = get_indicador("MA")    
                                    data = trading("GET",3,simbolo,stoploss,0)   
                                    digits = trading("GET",2,simbolo,stoploss,0)
                                    pip = (10*pow(10,-digits))/10
                                    precio = round(float(data[0]),digits) 
                                    time.sleep(0.12)
                                    velas = get_vela(21)
                                    cuerpo_vp20 = get_promedio(velas)                                                
                                    break
                            else:
                                if(data[0]=="Orden Cerrada"):
                                    get_ganancia()
                                    break                                
                                flag_donchian = 2
                                pass
                            time.sleep(0.2)
                else:
                    print("No cumplio las condiciones de la tendencia de la SMA-20")
            else:
                print("No cumplio las condiciones de la tendencia de la SMA-20")

        else:
            flag_donchian = 2
            #print("No cumplio las condiciones para operar")
            #break   # No se cumple las condiciones de entrada y se sale del loop   
        # Actualización de precio  e indicadores
        total_flag = flag_ganancia_1 + flag_ganancia_2 + flag_ganancia_3
        if(total_flag == 0):
            perdida_max = -15
        elif(total_flag == 1):
            perdida_max = 15 - 15*0.4
        elif(total_flag == 2):
            perdida_max = 20 - 20*0.30
        else:
            perdida_max = 25 -25*0.20
        if(ganancia_dia <= perdida_max):
            break
        locale.setlocale(locale.LC_ALL,'es-CO')
        dtn = datetime.datetime.now(pytz.timezone('Europe/London'))
        hora = dtn.hour
        if(hora >= 10):            
            break        
        time.sleep(0.12)
        sma_20 = get_indicador("MA")    
        data = trading("GET",3,simbolo,stoploss,0)    
        digits = trading("GET",2,simbolo,stoploss,0)
        pip = (10*pow(10,-digits))/10
        precio = round(float(data[0]),digits)
        #time.sleep(0.5)
        velas = get_vela(21)
        cuerpo_vp20 = get_promedio(velas)
        
        #break
    time.sleep(0.5)
print("Ganancias Dia:",ganancia_dia)

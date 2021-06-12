# -*- coding: utf-8 -*-
"""
Created on Sat Apr 28 15:22:20 2018

@author: Personal

Código que descompone el mensaje en pequeñas partes, y lo devuelve en una lista.
Sirve para módelos de RNN con 160 timesteps, y solo recibe datos Close.
"""

def parser(open1,high,low,close):
    lista = []
    try:
        open1 = open1.split('|')
        high = high.split('|')
        low = low.split('|')
        close = close.split('|')
        
    except:
        print("Error en los datos obtenidos del Servidor")
        return lista
    finally:
        pass
    
    if(open1[1]=="OPEN"):
        for i,dato in enumerate(open1): 
            if(i>=2):
                try:
                    lista.append([float(dato),float(high[i]),float(low[i]),float(close[i])])     # Se arma la lista de 180 pasos para la RNN
                except:
                    print("Error en el rango de la lista")
                    lista = []
                    return lista

    return lista[:180]
# Función para obtener los valores del Donchian Channel
def parser_donchian(dato1):
    lista = []
    try:        
        dato1 = dato1.split('|')        

    except:
        print("Error en los datos obtenidos del Servidor")
        return lista
    finally:
        pass
    
    try:
        if(dato1[1]=="HIGH" or dato1[1]=="LOW" or dato1[1]=="OPEN" or dato1[1]=="CLOSE" ):
            for i,dato in enumerate(dato1): 
                if(i>=2):
                    try:
                        lista.append(float(dato))     # Se arma la lista 
                    except:
                        print("Error en el rango de la lista")
                        lista = []
                        return lista
    except:
        lista = []
        return lista
    
    return lista

def parser_data(data):
    lista = []
    try:
        lista = data.split('|')
        
    except:
        print("Error en los datos obtenidos del Servidor")
        lista = []
        return lista
    finally:
        pass   
    return lista
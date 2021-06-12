import openpyxl                             #Libreria para tratamiento de documentos excel
import datetime
import locale
import pytz

dtn = datetime.datetime.now(pytz.timezone('Europe/London'))
fecha = str(dtn.date())
fecha = "{}/{}/{}".format(fecha.split("-")[2],fecha.split("-")[1],fecha.split("-")[0])
lista_ordenes = [[fecha,'OSO','SELL',1,1.45123,1.45105,18,0.21,-1.16,10.23,0,1],[fecha,'TORO','BUY',4,1.46135,1.4200,65,0.3,-1.66,31.05,0,1],[fecha,'TORO','BUY',3,1.46135,1.4200,-36,0.3,-1.66,-31.05,1,0]]

doc=openpyxl.load_workbook("H:\ESTUDIOS PROFESIONALES\TRADING\Test Robot TE 1.xlsx")     #Ingrese el nombre del archivo en excel con su respectiva extensión .xlsx

hoja=doc.get_sheet_by_name("TE EUR-USD")                #El usuario debe seleccionar y escribir el nombre de la hoja a escanear, se guarda en la variable hoja
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

doc.save("H:\ESTUDIOS PROFESIONALES\TRADING\Test Robot TE 1.xlsx")
import cv2
import numpy as np
import time
import board
import busio
import adafruit_mlx90640
import datetime

# La comunicación I2C se hace en pines SCL y SDA
i2c = busio.I2C(board.SCL, board.SDA)
# Variable para el sensor
mlx = adafruit_mlx90640.MLX90640(i2c)
# Definimos valores límite de medición por encima o por debajo emite alerta
# y la tasa de refresco del sensor. Estos tres datos son requeridos al usuario
maximo = int(input("Introduce la temperatura maxima: "))
minimo = int(input("Introduce la temperatura minima: "))
tasa_refresco = int(input("Introduce la tasa de refresco (2 o 4): "))
# Fijamos la frecuencia de refresco según lo definido por el usuario
if tasa_refresco == 2:
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
elif tasa_refresco == 4:
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
else:
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
# Array para informacion de los 768 sensores IR
frame = np.zeros((24*32,))  
# Numero maximo de intentos de acceder a informacion del sensor
intentos = 5
# Tamaño para el display
desired_size = (640, 480)

# Bucle infinito de lectura
while True:
    contador_intentos = 0
    while contador_intentos < intentos:
        try:
            # Capturamos el frame (array ) del sensor
            mlx.getFrame(frame)
            # Se convierte el array en una matriz de 24 filas y 32 columnas
            data_array = np.reshape(frame, (24, 32))
            # Se normaliza la imagen, pasando todos los valores a encontrarse en el rango 0-255
            data_normalized = cv2.normalize(data_array, None, 0, 255, cv2.NORM_MINMAX)
            # Aplicamos Gaussian Blur (filtro de suavizado gaussiano)
            data_blurred = cv2.GaussianBlur(data_normalized, (5, 5), 0)
            # Aplicamos un mapa de color para la visualización por pantalla
            data_color = cv2.applyColorMap(np.uint8(data_blurred), cv2.COLORMAP_JET)
            # Convertir a YUV y ecualiza el histograma del canal Y
            # Y = 0.30 R + 0.59 G + 0.11 B
            # U = 0.493 (B-Y)
            # V = 0.877 (R-Y)
            data_yuv = cv2.cvtColor(data_color, cv2.COLOR_BGR2YUV)
            data_yuv[:,:,0] = cv2.equalizeHist(data_yuv[:,:,0])
            # Volvemos de YUV a BGR despues de ecualizar canal Y
            # R = Y + 1.139V
            # G = Y − 0.394U − 0.581V
            # B = Y + 2.032U 
            data_equalized = cv2.cvtColor(data_yuv, cv2.COLOR_YUV2BGR)
            # Ajustamos tamañano de la imagen al tamaño definido para el display
            data_resized = cv2.resize(data_equalized, desired_size, interpolation=cv2.INTER_LINEAR)
            # MOSTRAR IMAGEN:
            # Escribimos en la base de la imagen mostrada, la temperatura media detectada por los sensores IR
            cv2.putText(data_resized, 'Temperatura media: {0:2.1f}C ({1:2.1f}F)'.\
      format(np.mean(frame),(((9.0/5.0)*np.mean(frame))+32.0)), (15,460), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
            # Comprobamos si la temperatura media supera el máximo definido
            if np.mean(frame) > maximo:
                # si supera el máximo emitimos una alerta de temperatura máxima superada escribiéndolo en el centro de la imagen
                cv2.putText(data_resized, 'ALERTA: TEMP. MAXIMA SUPERADA', (15,240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
            # Comprobamos si la temperatura media es inferior al mínimo
            if np.mean(frame) < minimo:
                # si está por debajo del mínimo emitimos una alerta de temperatura mínima superada escribiéndolo en el centro de la imagen
                cv2.putText(data_resized, 'ALERTA: TEMP. MINIMA SUPERADA', (15,240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
            # Mostramos la imagen con todos los mensajes que sean necesarios: Temperatura media y/o alertas
            cv2.imshow('Imagen Térmica', data_resized)
            # Si se pulsa la tecla 'q', se cierra la aplicación
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # La tecla 'p' permite realizar una captura de la situación actual de la medición (imagen)
            if cv2.waitKey(1) & 0xFF == ord('p'):
                # Obtenemos fecha y hora actual
                hora_actual = datetime.datetime.now()
                # Guardamos una imagen con la captura tomada, bajo el nombre de archivo de la fecha y hora actual (png)
                cv2.imwrite(hora_actual.strftime('%H:%M:%S_%d-%m-%Y')+'.png', data_resized)
                # Preparamos para mostrar una nueva ventana con la captura tomada, escribiendo el nombre del archivo (png)
                cv2.putText(data_resized, 'Captura: ' + hora_actual.strftime('%H:%M:%S_%d-%m-%Y')+'.png', (15,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
                cv2.imshow('Imagen Térmica Capturada', data_resized)
                break
        except ValueError:
            contador_intentos += 1
        except RuntimeError as e:
            contador_intentos += 1
            if contador_intentos >= intentos:
                print(f"Error tras {intentos} intentos con el error: {e}")
                break
    # Condición de parada del bucle infinito: tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break

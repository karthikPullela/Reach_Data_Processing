import time
import serial
import socket
import math

from gps.GPS import GPSInit, saveCoor, processCoordinates, calcVelGPS
from communication.sendUDP import initSocket, sendPacket, killSocket
from altimeter.altitudeCalculation import altitudeCalc
from accel import findInertialFrameAccel

#Initiate variables
oldtime = time.time()
oldGPSTime = time.time()

lat2 = 0
lon2 = 0
GPSInit()
velocity = [0,0,0]
position = [0,0,0]

def processData(dataString):
	'''
	parse string 
	create array with elements deliminated by spaces
	contents should be as follows
	data[0] = timestamp
	data[1] = pressure
	data[2] = temperature
	data[3] = gyroX
	data[4] = gyroY
	data[5] = gyroZ
	data[6] = accelX
	data[7] = accelY
	data[8] = accelZ
	data[9] = gps Time
	data[10] = lon
	data[11] = lat
	data[12] = gpsAlt
	data[13] = speed
	data[14] = course
	'''
	data = dataString.split(",")
	
	#had problems with only reading in a few data 
	if (len(data) < 9):
		print "not enough data"
		continue
	#print len(data)

	#DO STUFF WITH DATA
	#convert from string type
	for i in range(len(data)-1):
		data[i] = float(data[i])

	if (len(data) < 12):
		gpsRecieved = False
		print "no coordinates"
	else: 
		gpsRecieved = True

	#establish time elapsed
	dt = data[0] - oldtime
	oldtime = data[0]

	#append altitude calculated from pressure
	data.append(altitudeCalc(data[1]+500))

	#process acceleration
	acceleration = findInertialFrameAccel(data[6], data[7], data[8], data[3], data[4], data[7], dt)
	
	#integrate to find velocity
	velocity[0] = velocity[0] + acceleration[0]*dt
	velocity[1] = velocity[1] + acceleration[1]*dt
	velocity[2] = velocity[2] + acceleration[2]*dt

	#integrate to find position
	position[0] = position[0] + velocity[0]*dt
	position[1] = position[1] + velocity[1]*dt
	position[2] = position[2] + velocity[2]*dt

	#set acceleration data to inertial fram acceleration data
	data[6] = acceleration[0]
	data[7] = acceleration[1]
	data[8] = acceleration[2]

	#append velocity and position data to transmitted data
	data.append(velocity[0]) 
	data.append(velocity[1])
	data.append(velocity[2])
	data.append(position[0])
	data.append(position[1])
	data.append(position[2])

	#Process GPS coordinates
	if data[9] != oldGPSTime:
		longitude = data[10]
		latitude = data[11]
		latDeg = math.floor(latitude)
		lonDeg = math.floor(longitude)

		latMin = float(latitude) - latDeg
		lonMin = float(longitude) - lonDeg
	    
		lat = float(latDeg)+float(latMin)/60
	 	lon = float(lonDeg)-float(lonMin)/60
	    
		saveCoor(lon, lat, data[12])
	    
	    #speed calculation from gps data:
		#push the last new value to the old and then set the new value 
		lat1 = lat2
	 	lat2 = lat
		lon1 = lon2
		lon2 = lon

		dt = data[9] - oldGPSTime
		#specific to GPS because GPS not expected as often
		oldGPSTime = data[9]
		#calcVelGPS(lat1, lon1, lat2, lon2, dt)

	print "data: " + str(data)
	
with open("bigTest.txt") as test:
	for line in test:
		processData(line)
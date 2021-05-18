import serial
import struct

ser = serial.Serial('/dev/ttyAMA0',230400, timeout =1) #Open port with baud rate, 9600
tryAgain = True
while tryAgain:
	try:
		if ser.in_waiting > 0: #check if we have started receiving data
			while True:
				if ser.in_waiting == 0:
					break

				data = ser.read(24) #Read up to 24 bytes, only have a 16 byte buffer
				xyz = struct.unpack('ddd', data) #Unpack data
				#print(xyz) #print tuple
				len = (xyz[0]**2+xyz[1]**2+xyz[2]**2)**(1/2) #Compute length
				pcklen = struct.pack('d',len) #Pack processed data
				ser.write(pcklen) #Write processed data to port
	except Exception as e:
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		print(e)
	except KeyboardInterrupt:
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		ser.close()
		print('/nPort closed')
		tryAgain = False

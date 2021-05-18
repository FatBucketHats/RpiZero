import serial
import struct
import numpy as np
import traceback
import sys

ser = serial.Serial('/dev/ttyAMA0', 230400, timeout=1)
tryAgain = True

print('initialising')
# set these variables
tAvg = 150
smplRate = 16
tau = np.logspace(0,2,num=100)
#tau = np.array([3,4,5])
n = np.array([1])

# derived variables which we will need
numStoredI = int(round(tau[-1]*smplRate))
print(numStoredI)
print()
S1 = 0
S = np.zeros((len(tau),len(n)))
smplsInTAvg = round(tAvg*smplRate)
print(smplsInTAvg)
# create arrays for vector components
x = np.zeros(numStoredI)
y = np.zeros(numStoredI)
z = np.zeros(numStoredI)

# set counters
i = 0
append_index = 0
print('waiting')
while tryAgain:
	try:
		if ser.in_waiting > 0:
			while True:
				if ser.in_waiting ==  0:
					break
				else:
					data = ser.read(24)
					xyz = struct.unpack('ddd', data)
					if i < numStoredI:
						x[i] = xyz[0]
						y[i] = xyz[1]
						z[i] = xyz[2]
						i+=1
						continue
					else:
						tau_i = 0
						for lag in tau:
							smpl_separation = int(round(append_index - lag*smplRate))
							S1 = ((x[smpl_separation]-xyz[0])**2 + (y[smpl_separation]-xyz[1])**2 + (z[smpl_separation]-xyz[2])**2)**(1/2)
							order_i=0
							for order in n:
								S[tau_i, order_i] += S1**order
								order_i+=1
							tau_i += 1
					x[append_index] = xyz[0]
					y[append_index] = xyz[1]
					z[append_index] = xyz[2]
					append_index+=1
					if append_index == numStoredI: append_index=0

					if i == smplsInTAvg:
						print('writing')
						print(smplsInTAvg-numStoredI)
						S = S*(1/(smplsInTAvg-numStoredI))
						for write_i in range(len(S)):
							dat = struct.pack('d'*len(n), *S[write_i])
							ser.write(dat)
						# reset
						i=0
						append_index == 0
						S = np.zeros((len(tau),len(n)))
						x = np.zeros(numStoredI)
						y = np.zeros(numStoredI)
						z = np.zeros(numStoredI)
						ser.reset_input_buffer()
						break
					i+=1
	except Exception as e:
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		print(e)
		print(traceback.format_exc())
		sys.exit()
	except KeyboardInterrupt:
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		ser.close()
		print('\nPort closed')
		tryAgain = False

import serial
import struct
import numpy as np
import sys
import time

# open serial port
ser = serial.Serial('/dev/ttyAMA0', 230400, timeout=1)

# set these variables
tAvg =  60*40
smplRate = 16
tau = np.logspace(0,2,num=100)
n = np.array([2])

# derived variables which we will need
numIndicies = int(round(tau[-1]*smplRate))
smplsInTAvg = round(tAvg*smplRate)
S1 = 0
S = np.zeros((len(n),len(tau)))
print(numIndicies)

# create arrays for vector components
x = np.zeros(numIndicies)
y = np.zeros(numIndicies)
z = np.zeros(numIndicies)

# set counters
append_index = 0
print('waiting...')

# prepare and start loop
while 1:
	try:
        	# listen for data on serial port
		if ser.in_waiting > 0:
			# fill up component arrays with t avg data
			for i in range(numIndicies):
				# read in data
				xyz = struct.unpack('ddd', ser.read(24))

				# fill current index
				x[i], y[i], z[i] = xyz[0], xyz[1], xyz[2]
			strt = time.time()
			# once component arrays are full begin computing str fn for each new vector
			while 1:
				# read in data
				xyz = struct.unpack('ddd', ser.read(24))

				# use list comprehension to get component values at all sample separations, may be able to determine sample sep more efficently
				sampleSep = [int(append_index-l*smplRate) for l in tau]
				# compute length for all lags
				xyzs = ((np.array([x[i] for i in sampleSep])-xyz[0])**2 + (np.array([y[i] for i in sampleSep])-xyz[1])**2 + (np.array([z[i] for i in sampleSep])-xyz[2])**2)**(0.5)

				# raise to order n and append to S
				S += [xyzs**o for o in n]

				# append current data
				x[append_index] = xyz[0]
				y[append_index] = xyz[1]
				z[append_index] = xyz[2]
				append_index+=1

				# loop back to index zero if parsed though whole component array
				if append_index == numIndicies: append_index=0
				i+=1

				# if t avg has elapsed write vectors to port
				if i == smplsInTAvg:
					end=time.time()
					print(end-strt)
					# transpose and average S
					S = (S.T)*(1/(smplsInTAvg-numIndicies))

					# write S to port
					for write_i in range(len(S)):
						dat = struct.pack('d'*len(n), *S[write_i])
						ser.write(dat)

					# reset
					i=0
					append_index == 0
					S = np.zeros((len(tau),len(n)))
					x = np.zeros(numIndicies)
					y = np.zeros(numIndicies)
					z = np.zeros(numIndicies)
					ser.reset_input_buffer()
					break

			break

	except Exception as e:
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		print(e)
		sys.exit()
	except KeyboardInterrupt:
		end = time.time()
		print((i-numIndicies)/(end-strt))
		ser.reset_input_buffer()
		ser.reset_output_buffer()
		ser.close()
		print('\nPort closed')
		tryAgain = False

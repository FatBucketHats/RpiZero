import serial
import struct
import numpy as np
import sys

# open serial port
ser = serial.Serial('/dev/ttyAMA0', 230400, timeout=1)

# set these variables
tAvg = 150
smplRate = 16
tau = np.logspace(0,2,num=100)
n = np.array([2])

# derived variables which we will need
numIndicies = int(round(tau[-1]*smplRate))
smplsInTAvg = round(tAvg*smplRate)
S1 = 0
S = np.zeros((len(tau),len(n)))

# create arrays for vector components
x = np.zeros(numIndicies)
y = np.zeros(numIndicies)
z = np.zeros(numIndicies)

# set counters
i = 0
append_index = 0
print('waiting...')
# prepare and start loop
tryAgain = True
while tryAgain:
    try:
        # listen for data on serial port
        if ser.in_waiting > 0:
            while True:
                # if no data is waiting, break loop
                if ser.in_waiting ==  0: break
                    
                # read in and unpack 24 bytes of data, 8 for each component of a vector
                data = ser.read(24)
                xyz = struct.unpack('ddd', data)
                
                # fill component arrays, else compute str fn for current data
                if i < numIndicies:
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
                    if append_index == numIndicies: append_index=0

                    # if t avg has elapsed write vectors to port
                    if i == smplsInTAvg:
                        S = S*(1/(smplsInTAvg-numIndicies))
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
                    
                    # append to counter
                    i+=1
    except Exception as e:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print(e)
        sys.exit()
    except KeyboardInterrupt:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.close()
        print('\nPort closed')
        tryAgain = False

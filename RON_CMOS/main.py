import sys
import time 


sys.path.append("..")
import ron
import gain

# st = time.time() 
# ron = ron.RON('-5.0C_highGain')
# #ron.subRON(2,2)
# ron.calcRON()  

# et = time.time()
# elapsed_time = et - st
# print('Execution time:', elapsed_time, 'seconds')

# ron.plotStatistics() 

gain = gain.GAIN('-5.0C_Flat_lowGain')

print(gain.calcGain()) 
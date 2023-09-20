import sys
import time 


sys.path.append("..")
import ron
import gain
import dc 

def testRON():
    st = time.time() 
    ron = ron.RON('-10.0C_highGain')
    #ron.subRON(2,2)
    ron.calcRON()  
    et = time.time()
    elapsed_time = et - st
    print('Execution time:', elapsed_time, 'seconds')
    ron.plotStatistics(ron.clippedData) 

def testGain():
    gain = gain.GAIN('gain_frames')
    res = gain.calcGain()
    print(res) 

# gain = gain.GAIN('gain_frames')
# res = gain.calcGain()
# print(res)
 
dc = dc.DC('dark_current', 300)
res = dc.stackDarkCurrent()

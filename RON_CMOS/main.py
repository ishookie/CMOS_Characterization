import sys
import time 


sys.path.append("..")
import ron
import gain
import dc 

def testRON():
    st = time.time() 
    ronObject = ron.RON('6443BiasFrames')
    #ron.subRON(2,2)
    ronObject.calcRON()   
    et = time.time()
    elapsed_time = et - st
    print('Execution time:', elapsed_time, 'seconds') 

def testGain():
    test = gain.GAIN('lightFrames', 'darkFrames')
    test.doTheThing()


def testPixelWiseGain():
    test = gain.GAIN('lightFrames', 'darkFrames')
    test.pixelWiseGain() 

def testDC():
    darkCurrent = dc.DC('dcTest')
    darkCurrent.diffFrame()
    darkCurrent.graphDCvsTIME()


testRON() 
# #*****THERE IS A BUG WHERE IF YOU HAVE TO IMMEDIETLY CREATE
# # THE TUBLE WITH TEMPERATURE AND DC VALUE WHEN THE OBJECT IS FIRST
# # CREATED OR ELSE THE VALUES ARE WRONG I HAVE NO IDEA WHY DO IT IN  
# # THE ORDER I HAVE HERE **************
# dc1 = dc.DC('-5Cdc_1min')
# dct1 = (dc1.stackDarkCurrent(), dc1.t)

# dc25 = dc.DC('-5Cdc_2.5min')
# dct25 = (dc25.stackDarkCurrent(), dc25.t)

# dc5 = dc.DC('-5Cdc_5min')
# dct5 = (dc5.stackDarkCurrent(), dc5.t)

# dc75 = dc.DC('-5Cdc_7.5min')
# dct75 = (dc75.stackDarkCurrent(), dc75.t)

# dc10 = dc.DC('-5Cdc_10min')
# dct10 = (dc10.stackDarkCurrent(), dc10.t)

# dc30 = dc.DC('-5Cdc_30min')
# dct30 = (dc30.stackDarkCurrent(), dc30.t)
# # # Create tubles
# # # (dc value (e-), Exposure Time (s))

# # This is not pretty :(
# # append tubles to alist
# res = [] 
# res.append(dct1)
# res.append(dct25)
# res.append(dct5)
# res.append(dct75)
# res.append(dct10)
# res.append(dct30) 
# print(res) 
# dc1.graphDCvsTIME(res)
# # gain = gain.GAIN('gain_frames')
# res = gain.calcGain()
# print(res)
 
# dc0 = dc.DC('-5Cdc_1min')
# res = dc0.stackDarkCurrent()
# print(res) 

# dc1 = dc.DC('-5Cdc_5min')
# res1 = dc1.stackDarkCurrent()
# print(res1) 
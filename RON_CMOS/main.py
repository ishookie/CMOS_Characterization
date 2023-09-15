import sys
import time 


sys.path.append("..")
import ron

st = time.time() 
ron = ron.RON('11.0C')
ron.subRON(2,2)
# ron.calcRON()  

et = time.time()
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')
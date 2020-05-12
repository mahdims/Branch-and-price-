
from time import time
from Input import Input
from Model2 import Model2
from ColumnGeneration import ColumnGen
import cPickle as Pick

def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)
        
def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj
    
Runtimes={}
for NN in [10]:
    #NN=30 # number of nodes
    M = 3 # number of vehicles 
    Q = 250 # vehicles Capacity
    C = 0.75 # percentage of demand as Initial inventory in depot
    Lambda=0.5
    Data=Input(NN,M,Q,C,Lambda)
    epsilon=200
    save_object(Data,'Model_Data.pkl')
    
    start=time()
    ModelObjval=Model2(Data,epsilon)
    Model_runtime=time()-start
    print("Model Runtime: %f" %Model_runtime)
    Runtimes[(NN,M)] = Model_runtime
    
    start=time()
    #ColGObjval=ColumnGen(Data,epsilon)
    ColumnGen_runtime=time()-start
    
    print("Model optimal value: %f" %ModelObjval)
    print("Model Runtime: %f" %Model_runtime)
    print("N = %d , M = %d" %(NN,M))
    #print("Column Generation optimal value: %f" %ColGObjval)
    #print("Column Generation Runtime: %f" %ColumnGen_runtime)
    
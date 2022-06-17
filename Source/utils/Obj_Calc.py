"""
Created on Thu May 02 20:12:01 2019

@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""
import  numpy as np
import itertools as it 





def objvalue(Data,Y, Col_dic):
    
     Gc=Data.Gc
     G=Data.G
     Lambda = Data.Lambda
     TotalD=Data.total_demand
     
      
        
     if isinstance(Y, list):
         Travel_time=sum( [Col_dic[r].travel_time for r in Col_dic.keys()]  )
         inx=range(len(Y))
     else:
         Travel_time=sum( [Col_dic[r].travel_time*Y[r] for r in Col_dic.keys()]  )
         inx=[ i  for i in Y.keys() if Y[i]!=0]
     Del= np.array( [ np.array(Col_dic[i].RDP)* Y[i] for i in inx] )
     Del=np.sum(Del, axis=0)
     
     gini=[]
     for i,j in it. product(Gc.nodes,repeat=2):
        gini.append( abs( Del[i]*G.node[j]['demand'] - Del[j]*G.node[i]['demand']  ) )
            
     Equity = sum( [Gc.node[i]['demand'] - Del[i]  for i in Gc.nodes]) + (Lambda/TotalD)*sum(gini)  

     return(Travel_time,Equity)








def Obj_Calc( Data , Y , Col_dic ):
    Gc=Data.Gc
    NN=Data.NN
    Lambda=0.5
    roundingTR=0.8
    selected_R_D=[]
    TotalD=Data.total_demand 
    if isinstance(Y, list):
        
        for inx in Y:
            selected_R_D.append(Col_dic[inx])
    else:
        for inx,a in Y.items():
            if a >=roundingTR:
                selected_R_D.append(Col_dic[inx])
        
    All_RDP=np.vstack([np.array(r_d.RDP)*Y[inx] for inx , r_d in Col_dic.items() ])
    
    try:
        RDP = np.vstack([r_d.RDP for r_d in selected_R_D])
        RDP = np.sum(RDP,axis=0)
        TT= [abs(RDP[i]*Gc.node[j]['demand']-RDP[j]*Gc.node[i]['demand'] )   for i,j in  it.permutations(Gc.nodes(),2) ]
        Obj = sum( [ Gc.node[i]['demand'] - RDP[i] for i in Gc.nodes() ]) + (Lambda/TotalD) * sum( TT  )  
        print(Obj)
    except:
        print("No selected RD meet rounding thershold %f" %roundingTR)

    
    All_RDP =np.sum(All_RDP , axis=0)
    TT= [abs(All_RDP[i]*Gc.node[j]['demand']-All_RDP[j]*Gc.node[i]['demand'] )   for i,j in  it.permutations(Gc.nodes(),2) ]
    Accurate_Obj = sum( [ Gc.node[i]['demand'] - All_RDP[i] for i in Gc.nodes() ]) + (Lambda/TotalD) * sum( TT  )  
    
    
    print(Accurate_Obj)
   
        
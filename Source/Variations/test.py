"""
Created on Fri May 10 22:53:26 2019
@author: User
# -*- coding: utf-8 -*-
Created on Sat Mar 23 16:35:58 2019
@author: User
"""

import time
from gurobipy import *
import numpy as np

N = 500
Q = 200
#q= [4,3,3,0,0]
d= np.random.randint(1,3,N)
#d= np.array( [1.0,1,2,10,2] )
Phi = np.random.randint(1,10,(N,N))
#Phi= np.array( [[10, 10, 0, 0, 10],
# [8, -9 ,1 ,5 ,6],
# [7, 9, -1, 3, -9],
# [6, 2, -9, 6, 3],
# [-1, 8, 6, 1, 6]] )
upper_q = 5
start = time.time()
LP = Model()
q = LP.addVars(N, ub = upper_q)
LP.setObjective(quicksum([Phi[i,j]*d[j]*q[i]for i in range(N) for j in range(N)])
                - quicksum([Phi[i,j]*d[i]*q[j]for i in range(N) for j in range(N)])
                , GRB.MAXIMIZE)
LP.addConstr(quicksum(q) <= Q)
#LP.addConstrs(q[i]<=4 for i in range(N))
LP.optimize()
q_opt = LP.getAttr('x',q)
print([a[1] for a in q_opt.items()])
print (time.time()-start)

start = time.time()
nominator = Phi.dot(d)
dominator = np.array(d.dot(Phi),dtype=float)
Values = {}
for inx, a in enumerate(nominator):
    if a > 0:
        if dominator[inx] > 0:
            Values[inx] = a-dominator[inx]
        else:
            Values[inx] = a + abs(dominator[inx])
    else:
        if dominator[inx] < 0:
            Values[inx] = abs(dominator[inx]) - abs(a)
        else:
            Values[inx] = - abs(a) - dominator[inx]


remaining_Q = Q
q_heuristic = {}
while Values:
    next_2_assign = max( Values.keys() , key= lambda x: Values[x] )
    if Values[next_2_assign] >= 0 :
        q_heuristic[next_2_assign] = min(remaining_Q , upper_q )
        remaining_Q -= q_heuristic[next_2_assign]
    else:
        q_heuristic[next_2_assign] = 0
    del Values[next_2_assign]

print(q_heuristic.values())
print (time.time() - start)
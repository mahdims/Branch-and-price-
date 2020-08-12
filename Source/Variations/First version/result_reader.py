# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 16:42:09 2019

@author: generic
"""
import cPickle as Pick

def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)
        
#R_dic=read_object("TObj_R_Kartal" )


Case_name = "Kartal"
#Case_name = "Van"
for NN in [13]:#[60,30,15]:
    
    M ={60: 9,
        30: 5,
        15: 3,
        13:3}   # numbe
    #R_dic=read_object("TObj_R_Van%s"%(NN) )
    #File_name = "Van_%s_result%s" %(NN,inst)
    #Result=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\Van\%s' %File_name) 
    for inst in range(1,31):
        
        
        if inst<=10:
            ins_type="T"
        elif inst<=20:
            ins_type="VT"
            inst-=10
        else:
            ins_type="VTL"
            inst-=20
                  
        
        '''
        if inst<=5:
            ins_type="T"
        elif inst<=10:
            ins_type="VT"
        else:
            ins_type="VTL"
        '''
            
        Problem_name= '%s_%s_%d' %(Case_name,ins_type,inst) 
        #Problem_name= 'Van_%d_%d_%d' %(NN,M[NN],inst)
        File_name = "%s_NewModel" %Problem_name
        #File_name = "%s_Modelresult" %Problem_name
        #File_name = "%s_BnPresult" %Problem_name
        Result=read_object('G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s' %(Case_name,File_name) ) 

          
        a=Result[Problem_name]
        print ( "%s %s %s %s %s" %(Problem_name, a[0],a[1],a[2],a[3]))
        #print ( "%s %s %s %s %s %s" %(Problem_name, a[0],a[1],a[2],a[3] ,a[4]))
        #Result[Problem_name]=A[inst-1]
        

#save_object(Result,'G:\My Drive\\1-PhD thesis\equitable relief routing\Code\Van\%s' %File_name )
'''     
              
Case_name="Kartal"       
ins_type = "VTL"
for inst in range(1,31): 
     
    #result=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s_Modelresult' %(Case_name,File_name)  )
    #a=result[File_name] 
    #print ( "%s %s %s %s %s" %(File_name, a[0],a[1],a[2],a[3] ))
    if inst<=10:
        ins_type="T"
    elif inst<=20:
        ins_type="VT"
        inst-=10
    else:
        ins_type="VTL"
        inst-=20
    File_name= '%s_%s_%d' %(Case_name,ins_type,inst) 
    R=R_dic[File_name ]
    print ( "%s %s " %(File_name, 100*R) )


'''
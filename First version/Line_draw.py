# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 19:45:32 2019

@author: generic
"""

import xlrd
import numpy as np 
import xlsxwriter

loc = ('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\Van\VanRawData.xlsx') 
wb = xlrd.open_workbook(loc) 



lines=[]
pernode=0
node_sheet=wb.sheet_by_name("NS%s" %NN)
Ycord=[38.467971] + node_sheet.col_values(3)[1:]
Xcord=[43.332131] + node_sheet.col_values(4)[1:] 

workbook = xlsxwriter.Workbook('%s_lines.xlsx' %File_name)
worksheet = workbook.add_worksheet()
row=1
worksheet.write(0, 0,  "ID")
worksheet.write(0, 1,  "Xcoord1")
worksheet.write(0, 2,  "Ycoord1")
worksheet.write(0, 3,  "Xcoord2")
worksheet.write(0, 4,  "Ycoord2")
count=0
for r_d in Node.best_Route:
    r=r_d.route
    pernode=0
    for node in r[1:]:
        if node==NN+1:
            node=0
        worksheet.write(row, 0,  count)
        worksheet.write(row, 1,  Xcord[pernode])
        worksheet.write(row, 2,  Ycord[pernode])
        worksheet.write(row, 3,  Xcord[node])
        worksheet.write(row, 4,  Ycord[node])
        row += 1
        count+=1
        pernode=node
        
workbook.close()
    
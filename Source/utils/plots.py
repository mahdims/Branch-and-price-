"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""
import math
from pandas_ods_reader import read_ods
import matplotlib.pyplot as plt
import numpy as np
import os
BASEDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

def pareto_plot(instance_name, two_objs, nondominant=[]):
    x =[]
    y =[]
    for key, val in two_objs.items():
        if val in nondominant:
            x.append(val[0])
            y.append(val[1])
            #plt.plot(val[0], val[1], '-o', linestyle="-", markersize=6, color='green')
        else:
            continue
            plt.plot(val[0], val[1], 's', markersize=4, color='red')

    # plt.legend(numpoints=1)
    # plt.ylim(-1.2, 1.2)
    plt.plot(x, y, '-o', linestyle="-", markersize=5, color='black')
    plt.title(f"The Pareto front of {instance_name}")
    plt.xlabel("IAAF", fontweight="bold")
    plt.ylabel("Total route length", fontweight="bold")
    plt.show()


def TwoObj_percentage(All_nondominat, Ins_Type="All"):
    x = [a[0] for a in All_nondominat]
    y = [a[1] for a in All_nondominat]
    fig, ax = plt.subplots(ncols=1)
    plt.plot(x, y, 'o', markersize=6, color='black')
    ax.plot(ax.get_xlim(), ax.get_xlim())
    plt.title(f"Changes in IAAF and and total route length for instances of type {Ins_Type}")
    plt.xlabel("Decrease in IAAF(%)", fontweight="bold")
    plt.ylabel("Increase in total route length(%)", fontweight="bold")
    plt.show()


def GiniVsIAAF(Full_info_Sols):
    #for ins_type in Full_info_Sols:
    All_sorted = sorted(Full_info_Sols, key= lambda x: x[0])
    x = [a[0] for a in All_sorted]
    y1 = [a[3] for a in All_sorted]
    y2 = [a[4] for a in All_sorted]
    y3 = [a[5] for a in All_sorted]
    fig, ax = plt.subplots(ncols=3)
    ax[0].plot(x, y1, 'o', markersize=6, color='black')
    ax[1].plot(x, y2, '*', markersize=6, color='blue')
    ax[2].plot(x, y3, 'o')

    ax[0].set_title(f"Gini index and IAAF")
    ax[1].set_title("Unsatisfied demand and IAAF")
    ax[0].set_ylabel("Gini Index", fontweight="bold")
    ax[1].set_ylabel("Unsatisfied demand", fontweight="bold")
    ax[0].set_xlabel("IAAF", fontweight="bold")
    ax[1].set_xlabel("IAAF", fontweight="bold")
    plt.show()

    x = [a[4] for a in All_sorted]
    y1 = [a[0] for a in All_sorted]
    y2 = [a[3] for a in All_sorted]

    fig, ax = plt.subplots(ncols=2)
    ax[1].plot(x, y1, 'o', markersize=6, color='black')
    ax[0].plot(x, y2, '*', markersize=6, color='blue')

    ax[0].set_title(f"Unsatisfied demand and Gini index")
    ax[1].set_title("Unsatisfied demand and IAAF")
    ax[1].set_ylabel("IAAF", fontweight="bold")
    ax[0].set_ylabel("Gini index", fontweight="bold")
    ax[1].set_xlabel("Unsatisfied demand", fontweight="bold")
    ax[0].set_xlabel("Unsatisfied demand", fontweight="bold")


    plt.show()


def capacity_plot(name, All_sols):
    sorted_sols = sorted(All_sols.items(), key= lambda x: float(x[0]))
    x = [float(a[0]) for a in sorted_sols]
    y1 = [float(a[1][0]) for a in sorted_sols]
    y2 = [float(a[1][6]) for a in sorted_sols]
    fig, ax = plt.subplots(ncols=2)
    ax[0].plot(x, y1, 'o', markersize=6, color='black')
    ax[1].plot(x, y2, 'o', markersize=6, color='black')
    fig.suptitle(f"Vehicle capacity analysis for instance {name}", size=14)
    ax[0].set_xlabel("Vehicle capacity coefficient (\u03B6\u00b3)", labelpad=7, fontweight="bold")
    ax[1].set_xlabel("Vehicle capacity coefficient (\u03B6\u00b3)", labelpad=7, fontweight="bold")
    ax[0].set_ylabel("IAAF", fontweight="bold")
    ax[1].set_ylabel("Gini index", fontweight="bold")

    Ticks = []
    for a in np.arange(min(x), max(x), 0.2):
        Ticks.append(round(a, 1))
        Ticks.append(" ")
    #Ticks.append(max(x))

    ax[0].set_xticks(x)
    ax[1].set_xticks(x)
    ax[0].set_xticklabels(Ticks)
    ax[1].set_xticklabels(Ticks)

    plt.show()




def gap_plot(Case_name):
    base_path = BASEDIR+"/Data/New_results_May_June_22.ods"
    sheet = Case_name + "Gap"
    df = read_ods(base_path, sheet)
    lables = df.iloc[:, 0].tolist()
    x = [a for a in range(len(lables))]
    y1 = df.iloc[:, 1].tolist() # Van : 3
    y2 = df.iloc[:, 2].tolist() # Van : 4
    fig, ax = plt.subplots(ncols=1)
    plt.plot(x, y1 , 'o', markersize=4, color='blue')
    plt.plot(x, y2, 'o', markersize=4, color='orange')
    plt.title(f"Changes in IAAF and and total route length for instances of type {Case_name}")
    plt.xlabel("Decrease in IAAF(%)", fontweight="bold")
    plt.ylabel("Increase in total route length(%)", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(lables)
    plt.xticks(rotation=45)
    plt.show()

if __name__ == "__main__":
    gap_plot("Kartal")
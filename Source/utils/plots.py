"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""
import math

import matplotlib.pyplot as plt
import numpy as np

def pareto_plot(instance_name, two_objs, nondominant=[]):

    for key, val in two_objs.items():
        if val in nondominant:
            plt.plot(val[0], val[1], 'o', markersize=6, color='green')
        else:
            continue
            plt.plot(val[0], val[1], 's', markersize=4, color='black')

    # plt.legend(numpoints=1)
    # plt.ylim(-1.2, 1.2)
    plt.title(f"The Pareto front of {instance_name}")
    plt.xlabel("IAAF")
    plt.ylabel("Total route length")
    plt.show()


def TwoObj_percentage(All_nondominat, Ins_Type="All"):
    x = [a[0] for a in All_nondominat]
    y = [a[1] for a in All_nondominat]
    fig, ax = plt.subplots(ncols=1)
    plt.plot(x, y, 'o', markersize=6, color='black')
    ax.plot(ax.get_xlim(), ax.get_xlim())
    plt.title(f"Changes in IAAF and and total route length for instances of type {Ins_Type}")
    plt.xlabel("Decrease in IAAF(%)")
    plt.ylabel("Increase in total route length(%)")
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
    ax[0].set_ylabel("Gini Index")
    ax[1].set_ylabel("Unsatisfied demand")
    ax[0].set_xlabel("IAAF")
    ax[1].set_xlabel("IAAF")
    plt.show()

    x = [a[4] for a in All_sorted]
    y1 = [a[0] for a in All_sorted]
    y2 = [a[3] for a in All_sorted]

    fig, ax = plt.subplots(ncols=2)
    ax[1].plot(x, y1, 'o', markersize=6, color='black')
    ax[0].plot(x, y2, '*', markersize=6, color='blue')

    ax[0].set_title(f"Unsatisfied demand and Gini index")
    ax[1].set_title("Unsatisfied demand and IAAF")
    ax[1].set_ylabel("IAAF")
    ax[0].set_ylabel("Gini index")
    ax[1].set_xlabel("Unsatisfied demand")
    ax[0].set_xlabel("Unsatisfied demand")


    plt.show()


def capacity_plot(name, All_sols):
    sorted_sols = sorted(All_sols.items(), key= lambda x: float(x[0]))
    x = [float(a[0]) for a in sorted_sols]
    y1 = [float(a[1][0]) for a in sorted_sols]
    y2 = [float(a[1][6]) for a in sorted_sols]
    fig, ax = plt.subplots(ncols=2)
    ax[0].plot(x, y1, 'o', markersize=6, color='black')
    ax[1].plot(x, y2, 'o', markersize=6, color='black')
    fig.suptitle(f"Vehicle capacity analysis for instance {name}")
    ax[0].set_xlabel("Vehicle capacity coefficient (\u03B6\u00b3)", labelpad=7)
    ax[1].set_xlabel("Vehicle capacity coefficient (\u03B6\u00b3)", labelpad=7)
    ax[0].set_ylabel("IAAF")
    ax[1].set_ylabel("Gini index")

    Ticks = []
    for a in np.arange(min(x), max(x), 0.2):
        Ticks.append(round(a, 1))
        Ticks.append(" ")
    #Ticks.append(max(x))

    ax[0].set_xticks(x, labels=Ticks)
    ax[1].set_xticks(x, labels=Ticks)
    # plt.xticks(ticks=Ticks)
    plt.show()



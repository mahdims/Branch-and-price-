"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import matplotlib.pyplot as plt


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
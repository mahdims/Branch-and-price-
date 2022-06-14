"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import matplotlib.pyplot as plt


def pareto_plot(instance_name, two_objs):
    x = []
    y = []
    for key , val in two_objs.items():
        x.append(val[0])
        y.append(val[1])

    #plt.legend(numpoints=1)
    #plt.ylim(-1.2, 1.2)
    plt.title(f"The Pareto front of instance {instance_name}")
    plt.plot(x, y, 'o', color='black')
    plt.show()
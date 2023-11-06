import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

qq = ['K_A', 'K_T', 'K_VT', 'K_VTL', 'V15_A', 'V15_T', 'V15_VT',
                     'V15_VTL', 'V30_A', 'V30_T', 'V30_VT', 'V30_VTL', 'V60_A', 'V60_T',
                     'V60_VT', 'V60_VTL']


# Sample dataset (replace with your own data)
data = {'Instance': ['Kartal_A', 'Kartal_T', 'Kartal_VT', 'Kartal_VTL', 'Van15_A', 'Van15_T', 'Van15_VT',
                     'Van15_VTL', 'Van30_A', 'Van30_T', 'Van30_VT', 'Van30_VTL', 'Van60_A', 'Van60_T',
                     'Van60_VT', 'Van60_VTL'],
        'MinUnD_Gini': [0.47789, 0.19270, 0.09620, 0.11120, 0.22280, 0.11080, 0.11800, 0.22050, 0.23300, 0.12220, 0.12020, 0.23125, 0.22860, 0.12720, 0.12380, 0.23750],
        'MinGini_UnsatDemand': [233.43, 51.79, 16.28, 16.28, 51.42, 15.05, 16.28, 100.24, 41.18, 16.28, 16.28, 66.52,
                                36.69, 15.81, 15.81, 35.66],
        'IAAF_Gini': [0.13433, 0.09120, 0.03180, 0.02750, 0.22280, 0.07240, 0.07240, 0.22050, 0.23300, 0.09200, 0.09160, 0.23125, 0.22860, 0.10900, 0.10940, 0.21160],
        'IAAF_UnsatDemand': [0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001]}

def add_bar_labels(bars, ax):
    for bar in bars:
        height = bar.get_height()
        ax.annotate('{:.2f}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=7)

def plot_1():


    df = pd.DataFrame(data)

    # Set bar width and positions
    bar_width = 0.25
    x = np.arange(len(df['Instance']))

    # Add space between instance types
    spacing = 1
    x = np.array([i + int(i/4) * spacing for i in x])

    fig, ax = plt.subplots()

    # Plot Gini Index bars
    rects1 = ax.bar(x - bar_width, df['MinUnD_Gini'], bar_width, label='MinUnD - Gini Index')

    rects3 = ax.bar(x + bar_width, df['IAAF_Gini'], bar_width, label='IAAF - Gini Index', hatch='/', edgecolor='black', alpha=0.5)

    # Plot Unsatisfied Demand bars

    rects5 = ax.bar(x , df['MinGini_UnsatDemand'], bar_width, label='MinGini - Unsatisfied Demand', edgecolor='black', alpha=0.5)
    rects6 = ax.bar(x + 2 * bar_width , df['IAAF_UnsatDemand'], bar_width, label='IAAF - Unsatisfied Demand', hatch='/', edgecolor='black', alpha=0.5)

    # Configure the x-axis
    ax.set_xticks(x)
    ax.set_xticklabels(df['Instance'])

    # Configure the y-axis
    ax.set_ylabel('Percentage Change')

    # Add a legend
    ax.legend()

    # Set a title for the chart
    plt.title('Percentage Change in Gini Index and Unsatisfied Demand by Objective')

    # Show the plot
    plt.show()
def plot_2():
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    width = 14
    height = 6

    df = pd.DataFrame(data)

    # Set bar width and positions
    bar_width = 0.5
    x = np.arange(len(df['Instance']))

    # Add space between instance types
    spacing = 0.3
    x = np.array([i + int(i) * spacing for i in x])

    # Gini Index Plot
    fig1, ax1 = plt.subplots(figsize=(width, height))

    rects1 = ax1.bar(x-bar_width/2, df['MinUnD_Gini'], bar_width, label='MinUnD - Gini Index')
    rects2 = ax1.bar(x+bar_width/2, df['IAAF_Gini'], bar_width, label='IAAF - Gini Index', hatch='/', edgecolor='black', alpha=0.5)
    add_bar_labels(rects1, ax1)
    add_bar_labels(rects2, ax1)

    ax1.set_xticks(x)
    ax1.set_xticklabels(df['Instance'], fontsize=8)
    ax1.set_xlabel('Instances type', fontsize=13)
    ax1.set_ylabel('Gini Index', fontsize=13)
    ax1.legend()
    plt.title('Comparison of Gini Index for MinUnD and IAAF Objectives',fontsize=14)

    plt.savefig('Gini_inx.pdf', bbox_inches='tight')
    # Unsatisfied Demand Plot
    fig2, ax2 = plt.subplots(figsize=(width, height))

    rects3 = ax2.bar(x-bar_width/2, df['MinGini_UnsatDemand'], bar_width, label='MinGini - Unsatisfied Demand')
    rects4 = ax2.bar(x+ bar_width/2, df['IAAF_UnsatDemand'], bar_width, label='IAAF - Unsatisfied Demand',
                     hatch='/', edgecolor='black', alpha=0.5)
    add_bar_labels(rects3, ax2)
    add_bar_labels(rects4, ax2)

    ax2.set_xticks(x)
    ax2.set_xticklabels(df['Instance'], fontsize=8)
    ax2.set_xlabel('Instances type', fontsize=13)
    ax2.set_ylabel('Percentage Increase in Unsatisfied Demand Compared \n to MinUnD Objective (e.i.,Perfect Efficiency)', fontsize=12)
    ax2.legend()
    plt.title('Comparison of Percentage Increase in Unsatisfied Demand for \n MinGini and IAAF Objectives Relative to MinUnD Objective', fontsize=14)

    plt.savefig('UnD.pdf', bbox_inches='tight')
    # Show the plots
    plt.show()


plot_2()
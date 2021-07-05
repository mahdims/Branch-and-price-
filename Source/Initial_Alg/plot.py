import matplotlib.pyplot as plt


data1 = [(50,90),(100,95),(500,90),(1000,91),(5000,93),(10000,94),(12500,94),(20000,94)]
x1 = [i[0] for i in data1]
y1 = [i[1] for i in data1]

data2 = [(50,82),(100,92),(500,92),(1000,92),(5000,95),(10000,96),(12500,96),(20000,96)]
x2 = [i[0] for i in data2]
y2 = [i[1] for i in data2]

plt.plot(x1, y1, '-*', color='red')
plt.plot(x2, y2, '-o', color='blue')

# plt.xlim(0, 1.8)

plt.legend(["Decision Tree", "KNN"])
plt.ylabel('Accuracy Rate')
plt.xlabel("Number of the Training Examples")

plt.show()
plt.savefig("AccuracyRate.pdf")
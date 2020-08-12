


def get_best_estimate(items_sorted, capacity, selections):
    value = 0
    weight = 0
    for idx in xrange(len(items_sorted)):
        if idx < len(selections) and selections[idx] == 0: continue
        i = items_sorted[idx]
        if weight + i.weight > capacity:
            value += i.value * (((capacity - weight) * 1.0) / i.weight) 
            break
        value += i.value
        weight += i.weight

    return value
    

class Node():
    best_value = 0
    LowerBound = 0
    Node_list = []
    
    def __init__(self, ID,PID,RMP, Sub, Col_set):
        self.ID=ID
        self.Parent_ID=PID
        self.RMP = RMP
        self.Sub = Sub
        self.Col_set = Col_set
        
        Node.Node_list.append(self)

    def get_left_child(self):
        item = Node.items_sorted[self.index]
        return Node(self.value + item.value, self.room - item.weight, self.selections + [1], self.estimate)
    
    def get_right_child(self):
        item = Node.items_sorted[self.index]
        return Node(self.value, self.room, self.selections + [0], -1)
    
    def is_leaf(self):
        return self.index == len(Node.items_sorted)
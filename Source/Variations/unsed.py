
def relocate_edges(paths, edges2keep):
    # This function change the input paths to put two node connected by edges2keep in the same route
    sol = Solution(paths)
    sets = []

    list1 = [set(e) for e in edges2keep]
    while len(list1):
        To_keep = 1
        currentE = list1.pop(0)
        if 0 in currentE:
            continue
        for e in list1:
            if currentE & e:
                list1.append(currentE | e)
                list1.remove(e)
                To_keep = 0
                break
        if To_keep:
            sets.append(currentE)

    for s in sets:
        S_list = list(s)
        I_inx = sol.Find_the_route([S_list[0]])
        for js in S_list:
            if js not in sol.routes[I_inx].route:
                J_inx = sol.Find_the_route([js])
                sol.routes[J_inx].remove(js)
                sol.routes[I_inx].route.insert(1, js)

    return sol.routes


def Nodes_selection(selected_nodes, edges2keep):
    ## Obsulate
    # This function will select the nodes that connected to selected_nodes by edges2keep
    # Since they should be together in any other route as well, they should move together too
    output = []
    sets = []
    if edges2keep:
        list1 = [set(e) for e in edges2keep]
        while len(list1):
            To_keep = 1
            currentE = list1.pop(0)
            if 0 in currentE:
                continue
            for e in list1:
                if currentE & e:
                    list1.append(currentE | e)
                    list1.remove(e)
                    To_keep = 0
                    break
            if To_keep:
                sets.append(currentE)

        for n in selected_nodes:
            indi = 0
            for s in sets:
                if n in s:
                    output.append(list(s))
                    indi = 1
                    break
            if indi == 0:
                output.append([n])

    else:
        for n in selected_nodes:
            output.append([n])

    return output
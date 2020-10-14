o = open("Density_Count.txt", "r")
for i in o:
    list(i)
print(i)
print(o)
mylist = i.split(',')
del mylist[-1]
for x in range(4):
    mylist[x] = int(mylist[x])

# print(mylist)
sl = sum(mylist)
# print(sl)
lst = []


def myround(x, base=5):
    return round(x*base)/base


for a in range(4):
    j = mylist[a]*4/sl
    j = myround(j)
    lst.append(j)
    # print(lst[a])
f = open("Output_signal_time.txt", "w+")
for c in lst:
    f.write(str(c)+",")
    # print(c)
f.close()
f1 = open("Output_signal_time.txt", "r+")

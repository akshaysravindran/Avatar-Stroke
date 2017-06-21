from headers.classTrial import Trial

t = Trial(1, 3)
t.readImpedance()
t.readChannelLocation()

print t.impedanceBefore
print t.impedanceAfter
print t.locationFile
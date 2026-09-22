"""Independent geometric ended-interval integration, copied without collection code."""
import numpy as np
def ended_overlap(left,right,amount,duration,queries,hours):
 p=[];c=[]
 for q in queries:
  keep=(right<=q)&(right>q-hours*3600);length=right[keep]-np.maximum(left[keep],q-hours*3600)
  p.append(float(np.sum(length/duration[keep]*amount[keep])));c.append(float(np.clip(np.sum(length)/(hours*3600),0,1)))
 return np.array(p),np.array(c)

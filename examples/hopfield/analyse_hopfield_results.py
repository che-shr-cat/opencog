#!/usr/bin/python

import pylab as p
import numpy as N
import glob
import os
import sys
import re
import pdb

def loadResultOfOneRun(basename="test"):
    """ Returns an dictionary of before/after/diff """
    results={}
    results["diff"] = N.loadtxt(basename + 'diff.csv', delimiter=",")
    results["after"] = N.loadtxt(basename + 'after.csv', delimiter=",")
    results["before"] = N.loadtxt(basename + 'before.csv', delimiter=",")
    return results

def loadAllResults(path="./"):
    """Uses naming scheme of test-hopfield.sh script"""
    configs = {}
    result_files = glob.glob(os.path.join(path, "results_n_*_d_*_*.csv"))
    for r in result_files:
	print "Loading " + r
	pattern = r"results_n_(\d+)_d_(\d\.\d+)_(\w+).csv"
	m = re.search(pattern, r)
	g = m.groups()
	configs[(g[0],g[1])] = 0
    configkeys = configs.keys()
    for r in configkeys:
	configs[r] = loadResultOfOneRun(os.path.join(path, "results_n_" + r[0] +
		    "_d_" + r[1] + "_"))
    return configs

def scaleResults(results):
    """ Scale diff values to -1..1 based on potential range. """

    for k in results.keys():
	bArray = results[k]['before']
	dArray = results[k]['diff']
	# just copying to easily make
	# correct size array
	newDArray = results[k]['diff']

	for i in range(0,N.size(dArray,axis=0)):
	    if N.size(dArray,axis=0) == N.size(dArray):
		if dArray[i] < 0:
		    if bArray[i] != 0:
			newDArray[i]=dArray[i]/bArray[i] 
		    else:
			newDArray[i]=0
		else:
		    if bArray[i] != 1:
			newDArray[i]=dArray[i]/(1.0-bArray[i])
		    else:
			newDArray[i]=0

	    else:
		for j in range(0,N.size(dArray,axis=1)):
		    if dArray[i,j] < 0:
			if bArray[i,j] != 0:
			    newDArray[i,j]=dArray[i,j]/bArray[i,j]
			else:
			    newDArray[i,j]=0
		    else:
			if bArray[i,j] != 1:
			    newDArray[i,j]=dArray[i,j]/(1.0-bArray[i,j])
			else:
			    newDArray[i,j]=0

	results[k]['diff'] = newDArray


def plotAfterAndDiff(results, size, density,path="./"):
    """ Takes structure generated by loadAllResults, and
	plots both diff and after values for run at size
	and density """
    pArray = results[(size,density)]['after'].conj().T
    xticks=N.arange(1,N.size(pArray,axis=0)+1)
    f=p.figure(1)
    f.clear()
    f.text(.5, .94, 'Results for size ' + size + ', link density ' + density, horizontalalignment='center')
    p.subplot(211)
    lines = p.plot(xticks, pArray)
    p.setp(lines, linestyle='-', color='#999999', linewidth=0.5)
    if (pArray.ndim > 1):
	mArray=N.mean(pArray,axis=1)
    else: 
	mArray=pArray
    p.plot(xticks, mArray,'r')
    p.axhline(0, color='c')
    p.xlim(xticks[0], xticks[-1])
    p.ylabel('Similarity')
    p.title('Similarity between retrieved and imprinted patterns')
    pArray = results[(size,density)]['diff'].conj().T
    sp=p.subplot(212)
    lines = p.plot(xticks, pArray)
    p.setp(lines, linestyle='-', color='#999999', linewidth=0.5)
    if (pArray.ndim > 1):
	mArray=N.mean(pArray,axis=1)
    else: 
	mArray=pArray
    p.axhline(0, color='c')
    p.plot(xticks, mArray,'r')
    p.xlim(xticks[0], xticks[-1])
    p.xlabel('Cycle')
    p.ylabel('Similarity difference')
    p.title('Difference in cue and retrieved pattern similarities')

def myformatter(x, pos):
     return '%1.2f'%(x)

def plotDistOfCycle(results,size,path="./",cycle=-1):
    """ Plot histogram of final performance for each pattern.
	Optionally chance cycle parameter to plot histogram
	for a given cycle.
    """
    pArray = {}

    # find densities
    for k in results.keys():
	if k[0] == size:
	    # get results for each density
	    pArray[k[1]] = results[k]['diff'].conj().T
    
    # find min and max values across densities, then create a bin sequence
    b_min = 0.0
    b_max = 0.0

    temp_keys=pArray.keys()
    for d in temp_keys:
	if N.rank(pArray[d]) == 1:
	    del pArray[d]
	    continue
	if min(pArray[d][cycle,:]) < b_min:
	    b_min = min(pArray[d][cycle,:])
	if max(pArray[d][cycle,:]) > b_max:
	    b_max = max(pArray[d][cycle,:])
    if len(pArray) == 0:
	return
    
    bin_width = (b_max-b_min)/10.0
    if b_min != b_max:
	mybins=N.arange(b_min+(bin_width/2),b_max+(bin_width/2),bin_width)
    else:
	bin_width=1
	b_max=1
	mybins=[b_min,b_min+bin_width]
    # work out bar width based on number of densities and bin sequence width
    bar_width = bin_width/len(pArray)

    p.figure(0)
    # bin results of each density
    myhist={}
    for d in pArray.keys():
	myhist[d] = p.hist(pArray[d][cycle,:],bins=mybins,align="center")

    p.figure(0).clear()
    ax = p.subplot(111)
    offset=0
    bars=[]
    c_list=['b','g','r','c','m','y']
    # plot each result
    densities = myhist.keys()
    for d in densities:
	#bars.append(p.bar(myhist[d][1]+(offset*bar_width),myhist[d][0],color=c_list[offset%len(c_list)],width=bar_width))
	my_color = c_list[offset%len(c_list)]
	bars.append(p.plot(myhist[d][1],myhist[d][0],color=my_color))
	offset+=1
	p_gt_one = (N.sum(pArray[d][cycle,:]>=0.0)/float(len(pArray[d][cycle,:]))) * 100.0
	p.figure(0).text(0.01,0.90-(offset*0.05),"%d%%>=0"%p_gt_one,horizontalalignment='left',color=my_color,size='smaller')

    formatter = p.FuncFormatter(myformatter)
    ax.xaxis.set_major_formatter(formatter)
    p.xticks(N.arange(b_min,b_max,bin_width))
    p.xlabel("Similarity difference")
    p.ylabel("Frequency")
    p.legend(tuple([i[0] for i in bars]),tuple(densities),shadow=True)
    p.axvline(0)
    p.title("Frequency distribution for performance of size %d"%int(size))
    #pdb.set_trace()


# Expects pathname for the directory with hopfield network results
def main(argv):
    path=argv[0]
    results = loadAllResults(argv[0])
    sizes=[]
    for i in results:
	if i[0] not in sizes:
	    sizes.append(i[0])

	plotAfterAndDiff(results,i[0],i[1],argv[0])
	p.savefig(os.path.join(path,'results_n_' + i[0] + '_d_' + i[1] + '.png'),dpi=70)

    for i in sizes:
	plotDistOfCycle(results,i,argv[0])
	p.savefig(os.path.join(path,'perf_dist_n_' + i + '.png'),dpi=70)

    scaleResults(results)
    for i in results:
	plotAfterAndDiff(results,i[0],i[1],argv[0])
	p.savefig(os.path.join(path,'results_scaled_n_' + i[0] + '_d_' + i[1] + '.png'),dpi=70)

    for i in sizes:
	plotDistOfCycle(results,i,argv[0])
	p.savefig(os.path.join(path,'perf_dist_scaled_n_' + i + '.png'),dpi=70)

if __name__ == "__main__":
    main(sys.argv[1:])

    


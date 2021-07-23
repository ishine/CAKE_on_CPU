import pandas
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
import os
import re
import sys



def plot_cake_vs_armpl_cpu(M,N,K,mc,kc,alpha,fname = 'cake_vs_armpl', ntrials=10):
	plt.rcParams.update({'font.size': 12})
	markers = ['o','v','s','d','^']
	colors = ['b','g','aqua','k','m','r']
	labels = ['CAKE Observed', 'ARMPL Observed', 'CAKE Optimal','CAKE extrapolated', 'ARMPL extrapolated']
	NUM_CPUs = [1,2,3,4]
	gflops_cpu_arr=[];gflops_cake_arr=[];dram_bw_cake_arr=[];dram_bw_cpu_arr=[];cake_mem_acc_arr=[]
	dram_bw_cpu = 0; dram_bw_cake = 0; gflops_cpu = 0; gflops_cake = 0; cake_mem_acc = 0
	#
	for i in range(len(NUM_CPUs)):
		for j in range(1,ntrials+1):
			a = open('reports_arm/report_arm_%d-%d' % (NUM_CPUs[i],j),'r').read().split('\n')
			cpu_time = float(re.search(r'\d+\.\d+', a[7]).group())
			# multiply by 64 bytes since external memory reqeust PMU
			# in ARM is expressed in terms of number of cache lines
			dram_bw_cpu += ((int(re.search(r'\d+', a[5]).group())*64.0) / cpu_time) / (10.0**9)
			gflops_cpu += (float(M*N*K) / cpu_time) / (10**9)
			#
			a = open('reports_arm/report_cake_%d-%d' % (NUM_CPUs[i],j),'r').read().split('\n')
			cpu_time = float(re.search(r'\d+\.\d+', a[7]).group())
			dram_bw_cake += ((int(re.search(r'\d+', a[5]).group())*64.0) / cpu_time) / (10.0**9)
			gflops_cake += (float(M*N*K) / cpu_time) / (10**9)# / (float(NUM_CPUs[i]))
			cake_mem_acc += cake_cpu_DRAM_accesses(M,N,K,mc,kc,alpha,NUM_CPUs[i]) / cpu_time
		#
		dram_bw_cpu_arr.append(dram_bw_cpu / ntrials)
		dram_bw_cake_arr.append(dram_bw_cake / ntrials)
		gflops_cpu_arr.append(gflops_cpu / ntrials)
		gflops_cake_arr.append(gflops_cake / ntrials)
		cake_mem_acc_arr.append(cake_mem_acc / ntrials)
		dram_bw_cpu = 0; dram_bw_cake = 0; gflops_cpu = 0; gflops_cake = 0; cake_mem_acc = 0
	#
	# plt.subplot(1, 2, 1)
	plt.figure(figsize = (6,4))
	plt.plot(list(NUM_CPUs), list(dram_bw_cpu_arr), label = labels[1],  marker = markers[1], color = colors[4])
	plt.plot(list(NUM_CPUs), list(dram_bw_cake_arr), label = labels[0],  marker = markers[0], color = colors[5])
	plt.plot(list(NUM_CPUs), list(cake_mem_acc_arr), label = labels[2], color = colors[5], linewidth = 2, linestyle='dashed')
	#
	plt.title('(a) DRAM Bandwidth in CAKE vs ARMPL')
	plt.xlabel("Number of Cores", fontsize = 18)
	plt.xticks(NUM_CPUs)
	plt.ylabel("Avg. DRAM Bw (GB/s)", fontsize = 18)
	plt.legend(loc = "center right", prop={'size': 10})
	plt.savefig("%s_dram.pdf" % fname, bbox_inches='tight')
	# plt.show()
	# plt.clf()
	# plt.close('all')
	#
	plt.figure(figsize = (6,4))
	x = np.array(list(range(3,9)))
	# y = [gflops_cpu_arr[-1]]*11
	y = [gflops_cpu_arr[-2] + (gflops_cpu_arr[-1] - gflops_cpu_arr[-2])*i - 0.006*i*i for i in range(4)]
	y += 2*[y[-1]]
	plt.plot(x, y, color = colors[4], linestyle = 'dashed', label = labels[4])
	#
	plt.plot(list(range(1,9)), [gflops_cake_arr[0]+i*(gflops_cake_arr[1]-gflops_cake_arr[0]) for i in range(8)], 
		label = labels[3], linewidth = 2, linestyle = 'dashed', color = colors[5])
	plt.xticks(list(range(1,9)))
	#
	plt.plot(list(NUM_CPUs), list(gflops_cake_arr), label = labels[0],  marker = markers[2], color = colors[5])
	plt.plot(list(NUM_CPUs), list(gflops_cpu_arr), label = labels[1],  marker = markers[3], color = colors[4])
	#
	plt.ticklabel_format(useOffset=False, style='plain')
	plt.title('(b) Computation Throughput of CAKE vs ARMPL')
	plt.xlabel("Number of Cores", fontsize = 18)
	# plt.xticks(NUM_CPUs)
	plt.ylabel("Throughput (GFLOP/s)", fontsize = 18)
	plt.legend(loc = "upper left", prop={'size': 12})
	plt.savefig("%s_perf.pdf" % fname, bbox_inches='tight')
	# plt.suptitle('Performance of CAKE vs ARMPL', fontsize = 18)
	plt.show()
	plt.clf()
	plt.close('all')




if __name__ == '__main__':
	plot_cake_vs_armpl_cpu(3000,3000,3000,48,48,1,ntrials=int(sys.argv[1]))
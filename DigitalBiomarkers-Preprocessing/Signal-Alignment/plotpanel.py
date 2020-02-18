import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.spatial.distance import seuclidean
from dtw import dtw
from visualization import scatter_vis
import math


def get_link(x, y, path, vertical_mov, shift_time):
    # make use of the feature of continuous increasing
    # make sure that x and y are 2D ndArray
    for i in range(len(path[0])):
        head_num = path[0][i]
        tail_num = path[1][i]
        plt.plot((x[head_num][0], y[tail_num][0]+shift_time), (x[head_num][1], y[tail_num][1]+vertical_mov), 'r')

def hdf_to_dict(hdf_file):
    # Read all the keys in the file
    with pd.HDFStore(hdf_file, mode='r') as hdf:
        keys = hdf.keys()

    # Read all tables, store in dictionary
    data = {}
    for key in keys: data[key] = pd.read_hdf(hdf_file, key)
    return data

def cal_devi(path, avg_density):
    list = pd.value_counts(path[1]).values
    avg_devi = sum(abs(np.array(list)-avg_density))/len(path[1])
    return avg_devi

ecg_analysis_file = pd.read_csv('csv/ecg_analysis.csv')
ecg_analysis = pd.DataFrame(ecg_analysis_file)

alg_hdf = '/home/jyh/CS/ecg/ibeat/ibeat/Subject044/SE_GENERIC_DATA_EVENT_6671_001/Subject044_Device010_ibeat_alg.hdf'
alg_data = hdf_to_dict(alg_hdf)

ppg_analysis = alg_data['/pulse_rate_alg']
# pick up utc and bpm_raw
ppg_analysis = ppg_analysis.loc[:, ['utc', 'bpm_raw']]

ecg_analysis = ecg_analysis.loc[:, ['utc', 'ecg_heart_rate']]

ppg_st = 1527109390
ppg_chunk_len = 200
# ppg_st = 1527109000
# ppg_chunk_len = 400
ecg_match_len = ppg_chunk_len
abs_drift_val = 20
shift_time = 0
min_d = 0
final_matrix = 0
final_path = 0
act_density=0

ppg_et = ppg_st + ppg_chunk_len

def dist_with_punish(x, y):
    if(math.fabs(x[1]-y[1])>30):
        print("punished at "+str(x[0])+" and "+str(x[1]))
        return math.fabs(x[1]-y[1])
    else:
        #print("punished at" + (x[0], x[1]))
        return math.fabs(x[1]-y[1])+2*math.fabs(x[0]-shift-y[0])

for shift in np.arange(-abs_drift_val, abs_drift_val, 1):

    ecg_st = ppg_st + shift
    ecg_et = ecg_st + ecg_match_len

    ecg_hr = ecg_analysis[(ecg_analysis.utc > ecg_st) & (ecg_analysis.utc < ecg_et)]
    ppg_hr = ppg_analysis[(ppg_analysis.utc > ppg_st) & (ppg_analysis.utc < ppg_et)]

    avg_density = len(ecg_hr)/len(ppg_hr)

    # utc_var = np.hstack((ecg_hr.utc.values, ppg_hr.utc.values)).var()
    # rate_var = np.hstack((ecg_hr.ecg_heart_rate.values, ppg_hr.bpm_raw.values)).var()

    # print(utc_var, rate_var)

    # norm = lambda x, y: seuclidean(x, y, [utc_var,rate_var])

    # norm = dist_with_punish
    norm = lambda x, y: math.fabs(x[1] - y[1])

    # changed Manhattan distance
    # norm = lambda x, y: math.fabs(x[1]-y[1])+1*math.fabs(x[0]-shift-y[0])

    # norm = lambda x, y: np.abs(x - y)
    # only absolute value
    # d, cost_matrix, acc_cost_matrix, path = dtw(ecg_hr.ecg_heart_rate.values.reshape(-1,1), ppg_hr.bpm_raw.values.reshape(-1,1), dist=norm)

    # include time variant utc26
    d, cost_matrix, acc_cost_matrix, path = dtw(ecg_hr.values, ppg_hr.values, dist=norm)

    # calculate the
    # if(shift==-12):
    #     w_list = []
    #     devi_list = []
    #     for w in np.arange(0, 20, 0.1):
    #         norm = lambda x, y: math.fabs(x[1]-y[1])+w*math.fabs(x[0]-shift-y[0])
    #         d, cost_matrix, acc_cost_matrix, path = dtw(ecg_hr.values, ppg_hr.values, dist=norm)
    #         avg_devi = cal_devi(path, avg_density)
    #         w_list.append(w)
    #         devi_list.append(avg_devi)
    #         print("w is " + str(w))
    #         print("devi is " + str(avg_devi))
    #     fig, ax = plt.subplots(figsize=(20, 10))
    #     ax.set_ylabel('devivation from avg density')
    #     ax.set_xlabel('weight of time')
    #     ax.plot(w_list, devi_list)
    #     plt.show()
    # avg_devi = cal_devi(path, avg_density)
    # print("devi is"+str(avg_devi))

    if (shift == -abs_drift_val):
        final_matrix = acc_cost_matrix
        final_path = path
        min_d = d
        shift_time = -abs_drift_val
    print(d, min_d, shift_time, shift)
    #     print(ecg_st, ecg_et)

    # if (shift == -11):
    #     plt.imshow(acc_cost_matrix.T, origin='lower', cmap='gray', interpolation='nearest')
    #     plt.plot(path[0], path[1], 'w')
    #     plt.show()

    if (d < min_d):
        shift_time = shift
        min_d = d
        final_matrix = acc_cost_matrix
        print("final path belongs to " + str(final_path[1].shape))
        final_path = path

print(shift_time)
plt.imshow(acc_cost_matrix.T, origin='lower', cmap='gray', interpolation='nearest')
plt.plot(final_path[0], final_path[1], 'w')
plt.show()

# ### DTW is sensitive to the noise.
# Near the end of ECG signal will prove it.

fig, ax = plt.subplots(figsize=(20, 10))

# ax[0].set_xlim([1527108100,1527108500])

# shift_time = -23 prove sensitivity
true_shift_time = -11
print(shift_time)

ecg_hr = ecg_analysis[
    (ecg_analysis.utc > ppg_st + shift_time) & (ecg_analysis.utc < ppg_st + shift_time + ppg_chunk_len)]
ecg_hr1 = ecg_analysis[
    (ecg_analysis.utc > ppg_st + true_shift_time) & (ecg_analysis.utc < ppg_st + true_shift_time + ppg_chunk_len)]
ppg_hr = ppg_analysis[(ppg_analysis.utc > ppg_st) & (ppg_analysis.utc < ppg_st + ppg_chunk_len)]

vertical_mov = -150

# the x, y should be in the ssame order as dtw function
get_link(ecg_hr.values, ppg_hr.values, final_path, vertical_mov, shift_time)

# when ecg is at 1st, ppg at 2nd
ax.scatter(ecg_hr.utc, ecg_hr.ecg_heart_rate, c='k', marker='.', label='ecg heart rate')
ax.scatter(ppg_hr.utc + shift_time, ppg_hr.bpm_raw+vertical_mov, label='PPG heart rate', c='b')
ax.legend(fontsize='30')
ax.set_xlabel('Time stamp', fontsize = '20')

plt.show()

scatter_vis(ecg_hr, ppg_hr, shift_time, 'real shift graph')
plt.show()
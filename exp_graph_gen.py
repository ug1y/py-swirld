import numpy as np
from swirld import test
import math, os, time, json

EXPS_DATA_PATH = 'GenGraph'
if not os.path.exists(EXPS_DATA_PATH):
    os.mkdir(EXPS_DATA_PATH)


def run_once(n, steps, ref_mode=0):
    nodes = test(n, steps, ref_mode)
    node0 = nodes[0]
    res = {}
    res['rounds'] = node0.round[node0.head]
    idd = {}
    for (h, d) in node0.in_degree.items():
        idd[d] = idd[d] + 1 if d in idd else 1
    res['degree'] = sorted(idd.items())
    vals = np.array(list(idd.keys()))
    weis = np.array(list(idd.values()))
    ave = np.average(vals, weights=weis)
    var = np.average((vals - ave) ** 2, weights=weis)
    res['stderr'] = math.sqrt(var)
    return res


def exec_exp(n, s, m, c=100):
    work = os.path.join(EXPS_DATA_PATH, 'n' + str(n) + '_s' + str(s) + '_m' + str(m))
    if not os.path.exists(work):
        os.mkdir(work)
    for i in range(c):
        print('executing progress =====> ' + str(i+1) + '/' + str(c))
        res = run_once(n, s, m)
        ct = time.strftime('%Y%m%d_%H%M%S')
        with open(os.path.join(work, ct), 'w', encoding='utf-8') as f:
            f.write(json.dumps(res))


def comp_avg(n, s, m):
    work = os.path.join(EXPS_DATA_PATH, 'n' + str(n) + '_s' + str(s) + '_m' + str(m))
    if not os.path.exists(work):
        return
    files = os.listdir(work)
    if 'avg_data' in files:
        files.remove('avg_data')
    data = []
    for name in files:
        with open(os.path.join(work, name), 'r', encoding='utf-8') as f:
            data.append(json.loads(f.read()))

    avg_data = {}
    count = len(files)
    sum_r = 0.0
    sum_d = {}
    sum_s = 0.0
    for i in range(count):
        sum_r += data[i]['rounds']
        for item in data[i]['degree']:
            if item[0] in sum_d:
                sum_d[item[0]] += item[1]
            else:
                sum_d[item[0]] = 0.0 + item[1]
        sum_s += data[i]['stderr']

    avg_data['rounds'] = sum_r / count
    avg_d = {}
    for k in sum_d.keys():
        avg_d[k] = sum_d[k] / count
    avg_data['degree'] = avg_d
    avg_data['stderr'] = sum_s / count

    print(avg_data)
    with open(os.path.join(work, 'avg_data'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(avg_data))


if __name__ == '__main__':
    nodes = 6  # n=3f+1, 4, 7, 10, 13
    steps = 10000  # total events or blocks
    ref_mode = 0  # 0: gossip, 1: height, 3: differ, 5: random
    count = 100  # running multiple times to get average
    # executing the experiments
    exec_exp(nodes, steps, ref_mode, count)
    # computing the average result
    comp_avg(nodes, steps, ref_mode)


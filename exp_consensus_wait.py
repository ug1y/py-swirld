import numpy as np
from swirld import test
import os, time, json

EXP_DATA_PATH = 'WaitConsensus'
if not os.path.exists(EXP_DATA_PATH):
    os.mkdir(EXP_DATA_PATH)


def run_once(n, steps):
    nodes = test(n, steps)
    node0 = nodes[0]

    loc_wait = {}
    for fk in node0.fameby.keys():
        if node0.hg[fk].c == node0.pk:
            loc_wait[node0.round[fk]] = node0.round[node0.fameby[fk]] - node0.round[fk]
    arr_loc_wait = np.array(list(loc_wait.values()))
    stat_loc_wait = {'avg': float(np.average(arr_loc_wait)),
                     'min': int(np.min(arr_loc_wait)),
                     'max': int(np.max(arr_loc_wait))}

    glo_wait = {}
    for c in node0.consensus:
        decide = []
        for w in node0.witnesses[c].values():
            decide.append(node0.round[node0.fameby[w]])
        glo_wait[c] = max(decide) - c
    arr_glo_wait = np.array(list(glo_wait.values()))
    stat_glo_wait = {'avg': float(np.average(arr_glo_wait)),
                     'min': int(np.min(arr_glo_wait)),
                     'max': int(np.max(arr_glo_wait))}

    progress = {'total': node0.round[node0.head], 'finish': len(node0.consensus)}

    return {'stat_loc_wait': stat_loc_wait, 'stat_glo_wait': stat_glo_wait, 'progress': progress}


def exec_exp(n, s, c=100):
    work = os.path.join(EXP_DATA_PATH, 'n' + str(n) + '_s' + str(s))
    if not os.path.exists(work):
        os.mkdir(work)
    for i in range(c):
        print('executing progress =====> ' + str(i + 1) + '/' + str(c), end='')
        start = time.perf_counter()
        res = run_once(n, s)
        end = time.perf_counter()
        print(', time used ' + str(end - start) + 's')
        ct = time.strftime('%Y%m%d_%H%M%S')
        with open(os.path.join(work, ct), 'w', encoding='utf-8') as f:
            f.write(json.dumps(res))
    return work


def comp_avg(work, name):
    if not os.path.exists(work):
        return
    files = os.listdir(work)
    if name in files:
        files.remove(name)
    data = []
    for file in files:
        with open(os.path.join(work, file), 'r', encoding='utf-8') as f:
            data.append(json.loads(f.read()))

    avg_data = {}
    count = len(files)
    sum_stat_loc_wait = {'avg': 0.0, 'min': 0.0, 'max': 0.0}
    sum_stat_glo_wait = {'avg': 0.0, 'min': 0.0, 'max': 0.0}
    sum_progress = {'total': 0.0, 'finish': 0.0}

    for i in range(count):
        sum_stat_loc_wait['avg'] += data[i]['stat_loc_wait']['avg']
        sum_stat_loc_wait['min'] += data[i]['stat_loc_wait']['min']
        sum_stat_loc_wait['max'] += data[i]['stat_loc_wait']['max']
        sum_stat_glo_wait['avg'] += data[i]['stat_glo_wait']['avg']
        sum_stat_glo_wait['min'] += data[i]['stat_glo_wait']['min']
        sum_stat_glo_wait['max'] += data[i]['stat_glo_wait']['max']
        sum_progress['total'] += data[i]['progress']['total']
        sum_progress['finish'] += data[i]['progress']['finish']
    avg_data['stat_loc_wait'] = {'avg': sum_stat_loc_wait['avg'] / count,
                                 'min': sum_stat_loc_wait['min'] / count,
                                 'max': sum_stat_loc_wait['max'] / count}
    avg_data['stat_glo_wait'] = {'avg': sum_stat_glo_wait['avg'] / count,
                                 'min': sum_stat_glo_wait['min'] / count,
                                 'max': sum_stat_glo_wait['max'] / count}
    avg_data['progress'] = {'total': sum_progress['total'] / count,
                            'finish': sum_progress['finish'] / count}

    print('\nhashgraph algorithm -> ' + str(work))
    print(str(avg_data) + '\n')
    with open(os.path.join(work, name), 'w', encoding='utf-8') as f:
        f.write('hashgraph algorithm -> ' + str(work) + '\n')
        f.write(json.dumps(avg_data))


def clear_avg_data(name):
    dirs = os.listdir(EXP_DATA_PATH)
    for d in dirs:
        os.remove(os.path.join(EXP_DATA_PATH, d, name))
    print('clear all average data done !')


def dump_avg_data(name):
    dirs = os.listdir(EXP_DATA_PATH)
    for d in dirs:
        comp_avg(os.path.join(EXP_DATA_PATH, d), name)
    print('dump all average data done !')


def test_res_data():
    nodes = 4  # n=3f+1, 4, 7, 10, 13, 16, 19, 22, 25, 28
    steps = 1000  # total events or blocks
    count = 10  # running multiple times to get average
    print('[running experiments with nodes=' + str(nodes) + ', steps=' + str(steps) + ']')
    # executing the experiments
    work = exec_exp(nodes, steps, count)
    # computing the average result
    comp_avg(work, '00_avg_data')


if __name__ == '__main__':
    test_res_data()
    # dump_avg_data('00_avg_data')
    # clear_avg_data('00_avg_data')

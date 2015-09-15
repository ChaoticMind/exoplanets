#!/usr/bin/env python
import json
import random
import pprint
import statistics
import matplotlib.pyplot as plt


def import_data(filename):
    with open(filename) as f:
        raw = f.read()
    data = json.loads(raw)
    return data


def plot_sequential_orbital_period(data):
    '''sample1'''
    plt.figure(1)
    plt.subplot(3, 1, 1)
    relevant = [x['period'] for x in data]
    plt.plot(relevant, 'b-', linewidth=0.5)
    plt.ylabel('Orbital period (days)')
    plt.title('Orbital periods in order of dataset')

    plt.subplot(3, 1, 2)
    random.shuffle(relevant)
    plt.plot(relevant, 'g-', linewidth=0.5)
    plt.ylabel('Orbital period (days)')
    plt.title('Orbital periods in another random order')


def plot_sorted_orbital_period(data):
    '''sample2'''
    # plt.figure(2)
    axes = plt.subplot(3, 1, 3)
    relevant = sorted([x['period'] for x in data])
    # relevant = sorted([str(x['period']) for x in data])
    # print(relevant)
    plt.plot(relevant, 'r,')
    axes.set_yscale('linear')
    # plt.axis([0, 1200, 0, 100])
    plt.ylabel('Orbital period (days)')
    plt.title('Sorted orbital periods')


def plot_histogram_orbital_period(data):
    '''sample3'''
    plt.figure(2)
    relevant = [x['period'] for x in data]
    n, bins, patches = plt.hist(
        relevant, bins=50, normed=False, facecolor='green', alpha=0.75,
        log=False)

    mu = statistics.mean(relevant)
    sigma = statistics.stdev(relevant)
    bin_width = bins[1] - bins[0]

    plt.xlabel('Orbital periods (days)')
    plt.ylabel('n_samples')
    plt.text(60, 820, r'$\mu={},\ \sigma={}$'.format(
        round(mu, 2), round(sigma, 2)), fontsize=14)
    total = len(relevant)
    for n, b in zip(n, bins):
        if n:
            plt.annotate(
                '{} ({}%)'.format(int(n), round(100*n/total, 1)),
                xy=(b + bin_width/2, n), xytext=(b + bin_width/3, n + 115),
                fontsize=8, color='blue', rotation="vertical",
                # arrowprops=dict(facecolor='black', shrink=0.05),
                )
    plt.title('Histogram of orbital periods of {} exoplanets'.format(total))


def main():
    meta = import_data('export.txt')
    data = meta['data']
    del meta['data']
    print(meta)

    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(data[0])

    plt.style.use('ggplot')
    plot_sequential_orbital_period(data)
    plot_sorted_orbital_period(data)
    plot_histogram_orbital_period(data)
    plt.show()
    plt.close('all')


if __name__ == '__main__':
    main()

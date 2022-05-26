import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import toml


table = toml.load("outputs_july27/NET_v_pwv.toml")

pwv_ref = 1.0

nrow, ncol = 2, 2
fig = plt.figure(figsize=[12 * ncol, 6 * nrow])
iplot = 0

for key in table.keys():
    if key.endswith(".yaml"):
        subtable = table[key]
        iplot += 1
        ax = fig.add_subplot(nrow, ncol, iplot)
        ax.set_title(key)
        for band in subtable:
            pwv = np.array(subtable[band]["pwv"]) * 1e-3
            net = np.array(subtable[band]["NET"])
            pivot_pwv = subtable[band]["xdefault"] * 1e-3
            p = np.polyfit(pwv, net, 2)
            pivot_net = np.polyval(p, pivot_pwv)
            plt.plot(pwv, net / pivot_net, label=f"{band} : {pivot_net:.1f}", lw=3)
            #plt.plot(np.log(pwv), np.log((net / pivot_net) ** 2), label=f"{band} : {pivot_net:.1f}", lw=3)
            p /= pivot_net
            x = np.linspace(0, 6, 100)
            plt.plot(x, np.polyval(p, x), "k--", label=f"{band} : fit = {p[2]:.6f}, {p[1]:.6f}, {p[0]:.6f}")
            #plt.plot(np.log(x), np.log(np.polyval(p, x) ** 2), "k--", label=f"{band} : fit = {p[2]:.6f}, {p[1]:.6f}, {p[0]:.6f}")
            print(f"{key} {band} {p[2]:.6f}, {p[1]:.6f}, {p[0]:.6f}")
        ax.set_ylim([0, 3])
        ax.set_xlabel("PWV [mm]")
        ax.set_ylabel("NET factor")
        plt.legend(loc="best")
fig.savefig("NET_v_pwv_fit.png")
plt.show()

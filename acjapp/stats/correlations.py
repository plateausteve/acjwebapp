#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv("datafile.csv")
data.loc[data["Gender"] == "F", "Gender Color"] = 10
data.loc[data["Gender"] == "M", "Gender Color"] = 30
data.loc[data["Gender"] == "N", "Gender Color"] = 50


x = data["Percentile CDAT"]
y = data["Percentile Obs"]
colors = data["Gender Color"]


plt.scatter(x, y, c = colors, alpha=0.5)
plt.title("CDAT and Observation Percentiles")
plt.ylim(-5, 105)
plt.xlim(-5, 105)
plt.xlabel("Percentile on CDAT")
plt.ylabel("Percentile by Observation")
plt.show()


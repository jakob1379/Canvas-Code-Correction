import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import scipy.spatial as sp
import scipy.cluster.hierarchy as hc
parser = argparse.ArgumentParser()
parser.add_argument("path", help="path to similarity file")
args = parser.parse_args()

# load data
df = pd.read_csv(
    args.path,
    header=None,
    delimiter=" ",
    names=["Person1", "Person2", "Similarity %"],
    skiprows=1,
    skipfooter=1
)

df["Person1"] = df["Person1"].str.extract(r'submissions/([a-zA-Z0-9]+)')
df["Person2"] = df["Person2"].str.extract(r'submissions/([a-zA-Z0-9]+)')

df1 = df.pivot_table(index="Person1", columns="Person2",
                     values="Similarity %", fill_value=1)

sns.clustermap(
    df1,
    cmap="vlag",
    xticklabels=False,
    yticklabels=False)

outname = args.path.split(".")[0] + '_hclust.pdf'
plt.savefig(outname, format='pdf', dpi=300)
print("Created hclust diagram at:", outname)

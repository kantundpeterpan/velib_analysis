import pandas as pd
df = pd.read_csv("./cluster_profiles.csv").set_index("cluster")
wide = df.reset_index().melt(id_vars=['cluster'])
wide['variable'] = wide.variable.str.replace("hour_", "")
wide.columns = ['cluster', 'hour', 'avg_rel_avail']
wide.to_csv('cluster_profiles_wide.csv')
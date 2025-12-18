
import plotly.express as px
import pandas as pd

df = pd.DataFrame({"x":[1,2,3], "y":[1,4,2]})
fig = px.line(df, x="x", y="y", title="test")
fig.write_image("kaleido_test.png")
print("ok")


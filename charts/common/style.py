# --- charts/common/style.py ---
import plotly.graph_objects as go

def apply_common_layout(fig, title):
    fig.update_layout(
        title=title,
        template="simple_white",
        font=dict(family="Arial", size=14),
        margin=dict(l=60, r=30, t=60, b=60),
        xaxis=dict(tickmode='linear'),
        yaxis=dict(title="CO₂eq (kt)"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

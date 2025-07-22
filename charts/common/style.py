# charts/common/style.py
import plotly.graph_objects as go

def apply_common_layout(fig: go.Figure) -> go.Figure:
    """
    Apply uniform styling to all figures:
      - simple white template
      - Arial font, size 14
      - consistent margins
      - light grid lines on both axes
      - slanted x-axis ticks for readability
      - centered horizontal legend below plot
    Does NOT set titles or axis labels — those should be defined in each chart.
    """
    fig.update_layout(
        template="simple_white",
        font=dict(family="Arial", size=14),
        margin=dict(l=60, r=30, t=60, b=60),
        xaxis=dict(
            tickmode='linear',
            #tickangle=45,
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )
    return fig

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px 

# Plot raw data
def plot_line(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    df = df.sort_values(by=['timestamp'])
    
    fig = px.line(df, x='timestamp', y='sentiment', color='esg_category', markers=True)
    
    fig.layout.update(title_text='Sentiment Trend Analysis',title_x=0.3, xaxis_title="Date", yaxis_title="Sentiment", xaxis_rangeslider_visible=True)
    # fig.update_layout(paper_bgcolor = "rgba(0,0,0,0)",
    #               plot_bgcolor = "rgba(0,0,0,0)")
    fig.update_yaxes(range = [-1,1])
    st.plotly_chart(fig, use_container_width = True)
    
    
def plot_scatter(df):
    # Create figure with Plotly
    fig = go.Figure()

    # Iterate through each unique esg_category
    for category in df['esg_category'].unique():
        temp_df = df[df['esg_category'] == category]
        fig.add_trace(go.Scatter(
            x=temp_df['timestamp'],
            y=temp_df['sentiment'],
            mode='lines + markers',
            name=category,
            visible=True if category == 'Climate Change' else False
        ))

    # Update layout
    fig.update_layout(
        title='Sentiment on news articles over time for different ESG categories',title_x=0.20,title_y=0.95,
        xaxis=dict(title='Timestamp'),
        yaxis=dict(title='Sentiment'),
        # paper_bgcolor = "rgba(0,0,0,0)",
        #           plot_bgcolor = "rgba(0,0,0,0)"
    )
    
    # Create dropdown menu for different categories
    buttons = []
    for category in df['esg_category'].unique():
        buttons.append(
            dict(method='update',
                label=category,
                args=[{'visible': [category == cat for cat in df['esg_category'].unique()]}])
        )

    fig.update_layout(
        updatemenus=[
            dict(
                type = 'buttons',
                buttons=buttons,
                direction='left',
                showactive=True,
                x=1.4,
                xanchor='right',
                y=1.2,
                yanchor='top'
            )
        ],
        # paper_bgcolor = "rgba(0,0,0,0)",
        #           plot_bgcolor = "rgba(0,0,0,0)"
    )
    fig.update_yaxes(range = [-1,1])
    st.plotly_chart(fig, use_container_width = True)
    
def plot_bar(pillar, values, bar_color):
    
    fig = go.Figure(go.Bar(
            x=values,
            y=pillar,
            # text=text1,           

            orientation='h',
            text=values,
            textposition='outside',  # Display text outside bars
            texttemplate='%{text}'  # Format for displaying text
            ))
    fig.update_layout(
    autosize=False,
    minreducedwidth=250,
    minreducedheight=250,
    # width=250,
    height=300,
    # paper_bgcolor = "rgba(0,0,0,0)",
    #               plot_bgcolor = "rgba(0,0,0,0)"
                  )
    fig.update_traces(width=0.6, marker_color= bar_color) 
    fig.update_layout(xaxis_range=[0,100])
        

    st.plotly_chart(fig, use_container_width=True)

def plot_donut(label, value, chart_color, chart_margin, plot_height ):
    fig = go.Figure(data=[go.Pie(labels=['', ''], 
                                 values=[value, 100-value], 
                                 hole=0.7, 
                                 marker_colors=[chart_color,'#DAE3ED'],
                                 textinfo='none'
                                 )])
    fig.update_layout(title_text=label,
                      title_x=0.40,height = plot_height,
                      margin=dict(l=chart_margin, r=chart_margin, t=chart_margin, b=chart_margin),
                      showlegend=False,
                      annotations= [dict(text=str(value)+"%", x=0.5, y=0.5, font_size=20, showarrow=False)],
                #       paper_bgcolor = "rgba(0,0,0,0)",
                #   plot_bgcolor = "rgba(0,0,0,0)"
                )
    fig.update_traces(hoverinfo='skip')
    st.plotly_chart(fig, use_container_width=True)     

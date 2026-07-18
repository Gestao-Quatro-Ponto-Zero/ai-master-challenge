from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import os
import json
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI

app = Flask(__name__)

# Load data
df = pd.read_csv("master_table.csv")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    # Calc Metrics
    churn_rate = df['churn_flag'].mean() * 100
    avg_mrr = df['current_mrr'].mean()
    usage_avg = df['usage_last_30'].mean()
    
    # Chart 1: Churn by Industry
    industry_churn = df.groupby('industry')['churn_flag'].mean().reset_index()
    industry_churn['churn_flag'] = industry_churn['churn_flag'] * 100
    fig_ind = px.bar(
        industry_churn.sort_values('churn_flag', ascending=False), 
        x='industry', y='churn_flag', 
        color='churn_flag', color_continuous_scale='Reds',
        labels={'industry': 'Setor/Indústria', 'churn_flag': 'Taxa de Cancelamento (%)'}
    )
    fig_ind.update_traces(hovertemplate='<b>Setor:</b> %{x}<br><b>Taxa de Cancelamento:</b> %{y:.1f}%<extra></extra>')
    fig_ind.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0'),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    # Chart 2: Usage vs Churn
    df_box = df.copy()
    df_box['Status'] = df_box['churn_flag'].map({True: 'Cancelou (Churn)', False: 'Ativo'})
    fig_use = px.box(
        df_box, x='Status', y='usage_last_30', color='Status',
        color_discrete_map={'Ativo': '#A3A3A3', 'Cancelou (Churn)': '#FF1A1A'},
        labels={'usage_last_30': 'Volume de Uso (30 dias)', 'Status': 'Status do Cliente'}
    )
    fig_use.update_traces(hovertemplate='<b>Status:</b> %{x}<br><b>Uso (30d):</b> %{y}<extra></extra>')
    fig_use.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0'),
        margin=dict(l=20, r=20, t=20, b=20)
    )

    metrics = {
        "churn_rate": f"{churn_rate:.1f}%",
        "avg_mrr": f"${avg_mrr:,.0f}",
        "usage_avg": f"{usage_avg:.1f}"
    }

    return jsonify({
        "metrics": metrics,
        "fig_ind": json.loads(fig_ind.to_json()),
        "fig_use": json.loads(fig_use.to_json())
    })

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    api_key = data.get("api_key", "")
    prompt = data.get("prompt", "")
    
    if not api_key:
        return jsonify({"error": "API Key is required"}), 400
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
        
    try:
        os.environ["OPENAI_API_KEY"] = api_key
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            verbose=False, 
            agent_type="openai-tools",
            allow_dangerous_code=True
        )
        response = agent.invoke(prompt)
        return jsonify({"response": response["output"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

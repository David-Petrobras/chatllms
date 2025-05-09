import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import StringIO
import openai  # Usando a importação no estilo antigo

# Configuração da página
st.set_page_config(
    page_title="Assistente de Dados com IA",
    page_icon="📊",
    layout="wide"
)

# Definir CSS personalizado
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #e6f3ff;
    }
    .chat-message.assistant {
        background-color: #f0f2f5;
    }
    .chat-message .content {
        margin-left: 1rem;
    }
    .sidebar .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do estado da sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'df' not in st.session_state:
    st.session_state.df = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'model' not in st.session_state:
    st.session_state.model = "gpt-3.5-turbo"

# Título do aplicativo
st.title("Assistente de Dados com IA 🤖📊")

# Configuração do sidebar
with st.sidebar:
    st.header("Configurações")
    
    # Campo para API Key
    api_key = st.text_input("OpenAI API Key", value=st.session_state.api_key, type="password")
    if api_key:
        st.session_state.api_key = api_key

    # Seleção do modelo
    model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    selected_model = st.selectbox("Modelo", model_options, index=model_options.index(st.session_state.model))
    st.session_state.model = selected_model
    
    # Upload de arquivo
    uploaded_file = st.file_uploader("Upload de Arquivo", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            file_name = uploaded_file.name
            if file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.session_state.df = df
            st.session_state.file_name = file_name
            st.success(f"Arquivo '{file_name}' carregado com sucesso!")
            
            with st.expander("Visualizar primeiras linhas"):
                st.dataframe(df.head())
            
            # Informações do DataFrame
            st.write(f"Linhas: {df.shape[0]}, Colunas: {df.shape[1]}")
            
            # Estatísticas básicas
            with st.expander("Estatísticas básicas"):
                buffer = StringIO()
                df.info(buf=buffer)
                info_str = buffer.getvalue()
                st.text(info_str)
                st.write("Estatísticas numéricas:")
                st.dataframe(df.describe())
        
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo: {e}")
    
    # Botão para limpar o chat
    if st.button("Limpar Chat"):
        st.session_state.messages = []

    st.markdown("---")
    st.markdown("Desenvolvido por David Vieira usando Streamlit e OpenAI")

# Função para gerar resposta do assistente
def generate_response(prompt):
    if not st.session_state.api_key:
        return "⚠️ Por favor, insira sua chave API da OpenAI no menu lateral."
    
    if st.session_state.df is None:
        return "⚠️ Por favor, carregue um arquivo CSV ou Excel para começar."
    
    try:
        # Preparar o contexto do dataframe
        df_info = f"""
        Nome do arquivo: {st.session_state.file_name}
        Formato dos dados:
        {st.session_state.df.dtypes.to_string()}
        
        Primeiras 5 linhas:
        {st.session_state.df.head().to_string()}
        
        Estatísticas básicas:
        {st.session_state.df.describe().to_string()}
        
        Colunas: {', '.join(st.session_state.df.columns.tolist())}
        """
        
        # Preparar as mensagens
        messages = [
            {"role": "system", "content": f"""Você é um assistente analítico de dados. 
            Você tem acesso aos seguintes dados:
            
            {df_info}
            
            Ajude o usuário a analisar e extrair insights desses dados.
            Se for solicitado para realizar análises, forneça o código Python que poderia ser usado.
            Se precisar criar visualizações, sugira o tipo de gráfico mais apropriado e forneça o código que poderia ser usado.
            Seja preciso, direto e detalhado em suas respostas."""}
        ]
        
        # Adicionar histórico de conversa
        for message in st.session_state.messages:
            messages.append({"role": message["role"], "content": message["content"]})
        
        # Adicionar a nova pergunta
        messages.append({"role": "user", "content": prompt})
        
        # Chamar a API (usando o estilo antigo de API)
        openai.api_key = st.session_state.api_key
        response = openai.ChatCompletion.create(
            model=st.session_state.model,
            messages=messages,
            temperature=0.2,
            max_tokens=2000
        )
        
        return response['choices'][0]['message']['content']
    
    except Exception as e:
        return f"⚠️ Erro ao gerar resposta: {str(e)}"

# Função para executar código e mostrar resultados
def run_code_and_show(code_block):
    # Extrair apenas o código Python (remover ```python e ```)
    if "```python" in code_block:
        code = code_block.split("```python")[1].split("```")[0].strip()
    elif "```" in code_block:
        code = code_block.split("```")[1].split("```")[0].strip()
    else:
        code = code_block
    
    try:
        # Criar um ambiente local para execução segura do código
        local_vars = {
            "pd": pd, 
            "np": np, 
            "px": px,
            "df": st.session_state.df,
            "st": st
        }
        
        # Executar o código
        exec(code, {}, local_vars)
        
        # Se o código criar uma figura com plotly, ele já será mostrado pelo st
        return "✅ Código executado com sucesso!"
    except Exception as e:
        return f"⚠️ Erro ao executar o código: {str(e)}"

# Exibir mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Se houver código na resposta, adicionar um botão para executá-lo
        if message["role"] == "assistant" and "```python" in message["content"]:
            code_blocks = message["content"].split("```python")
            for i in range(1, len(code_blocks)):
                if "```" in code_blocks[i]:
                    code_block = "```python" + code_blocks[i].split("```")[0] + "```"
                    if st.button(f"Executar código #{i}", key=f"run_code_{len(st.session_state.messages)}_{i}"):
                        result = run_code_and_show(code_block)
                        st.write(result)

# Campo de entrada para nova pergunta
if prompt := st.chat_input("Digite sua pergunta sobre os dados..."):
    # Adicionar a pergunta do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Exibir a pergunta do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Gerar e exibir a resposta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = generate_response(prompt)
        message_placeholder.markdown(response)
        
        # Se houver código na resposta, adicionar um botão para executá-lo
        if "```python" in response:
            code_blocks = response.split("```python")
            for i in range(1, len(code_blocks)):
                if "```" in code_blocks[i]:
                    code_block = "```python" + code_blocks[i].split("```")[0] + "```"
                    if st.button(f"Executar código", key=f"run_code_{len(st.session_state.messages)}_{i}"):
                        result = run_code_and_show(code_block)
                        st.write(result)
    
    # Adicionar a resposta ao histórico
    st.session_state.messages.append({"role": "assistant", "content": response})
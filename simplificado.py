# Importando os pacotes necessários
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("OPENAI_ASSISTANT_ID")

st.set_page_config(page_title="Assistente profissional")


def load_openai_client_and_assistant():
    """
    Inicializa o cliente OpenAI, carrega o assistente e cria uma thread.
    """
    client = OpenAI(api_key=api_key)
    my_assistant = client.beta.assistants.retrieve(assistant_id)
    thread = client.beta.threads.create()
    return client, my_assistant, thread


client, my_assistant, assistant_thread = load_openai_client_and_assistant()


def wait_on_run(run, thread):
    """
    Monitora o status de uma execução do assistente até que seja concluída.
    """
    while run.status in {"queued", "in_progress"}:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id)
    return run


def get_assistant_response(user_input=""):
    """
    Envia uma entrada do usuário ao assistente e retorna a resposta formatada.
    """
    try:
        # Adiciona a mensagem do usuário à thread
        message = client.beta.threads.messages.create(
            thread_id=assistant_thread.id, role="user", content=user_input
        )

        # Cria um processo (run) para o assistente processar
        run = client.beta.threads.runs.create(
            thread_id=assistant_thread.id, assistant_id=assistant_id
        )

        # Aguarda a conclusão do processo
        run = wait_on_run(run, assistant_thread)

        # Recupera as mensagens adicionadas após a última mensagem do usuário
        messages = client.beta.threads.messages.list(
            thread_id=assistant_thread.id, order="asc", after=message.id
        )

        # Extrai o valor do texto da resposta
        response_content = messages.data[0].content
        if isinstance(response_content, list):
            # Se o conteúdo for uma lista, extraímos o texto do primeiro bloco de tipo 'text'
            for block in response_content:
                if block.type == "text" and hasattr(block.text, "value"):
                    return block.text.value
        elif hasattr(response_content, "text") and hasattr(response_content.text, "value"):
            # Para conteúdo direto que tenha `text.value`
            return response_content.text.value

        return "Nenhuma resposta válida foi encontrada."
    except Exception as e:
        # Exibe mensagem de erro no Streamlit caso algo dê errado
        st.error(f"Erro ao processar sua solicitação: {e}")
        return "Erro ao processar sua solicitação."


if "messages" not in st.session_state:
    st.session_state.messages = []


def submit():
    """
    Manipula a entrada do usuário e exibe a resposta.
    """
    if st.session_state.query:
        st.session_state.messages.append(
            {"role": "user", "content": st.session_state.query})
        user_input = st.session_state.query
        st.session_state.query = ''
        response = get_assistant_response(user_input)
        st.session_state.messages.append(
            {"role": "assistant", "content": response})


st.title("Assistente Virtual")
st.text_input("Digite sua pergunta:", key="query", on_change=submit)

for message in st.session_state.messages:
    message_box = st.chat_message(message["role"])
    message_box.markdown(message['content'])

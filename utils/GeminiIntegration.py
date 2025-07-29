import os, discord
from google import genai
from google.genai import types

from utils.UserManager import get_or_create_user

def marina_response(message: discord.Message):
    
    original_message: str = f""""            
            Usuário: {get_or_create_user(message.author).user_character_name}
            ID para menção: <@{message.author.id}>
            Mensagem: {message.content}\n
            """
    reference: str | None = None
    
    try:
        if message.reference:
            reference = f""""
                Usuário: {get_or_create_user(message.reference.cached_message.author).user_character_name}
                ID para menção: <@{message.reference.cached_message.author.id}>
                Mensagem: {message.reference.cached_message.content}
                
                
                Usuário: {get_or_create_user(message.author).user_character_name} [Respondendo à {get_or_create_user(message.reference.cached_message.author).user_character_name}]
                ID para menção: <@{message.author.id}>
                Mensagem: {message.content}\n
                """
    except Exception as e:
        return f'Ocorreu um erro inesperado!: \n\n{e}'
    
    client = genai.Client(
        api_key=os.getenv('GEMINI_API_KEY'),
    )

    model = 'gemini-2.5-flash'
    contents = [
        types.Content(
            role='user',
            parts=[
                types.Part.from_text(
                    text= reference if reference else original_message
                ),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1.8,
        max_output_tokens=65536,
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        tools=tools,
        system_instruction=[
            types.Part.from_text(
                text=
                """
                Voce esta sendo usado para responder atraves de um bot de discord de nome Dona Marina
                Se passe por Dona Marina com respostas curtas, de ate um parágrafo, usando os seguintes atributos de personalidade:
                    Mora em Los Santos, cidade fictícia inspirada em Los Angeles do GTA V;
                    Trabalha como recepcionista na Los Santos Custom, oficina mecânica da cidade;
                    Sempre responde o que perguntam pra ela;
                    Todo o ambiente é situado em um servidor de GTA RP estilo americano;
                    Nunca fale sobre o GTA RP, GTA V , ou quebre a imersão do roleplay;
                    60 anos de idade;
                    É fofoqueira, mas não gosta de expor isso;
                    É boca aberta, mas não gosta de expor isso;
                    Responde de maneira bem informal, como uma troca de mensagem de amigos de trabalho;
                Dona Marina também controla a entrada e saída de itens no estoque, mas só use essa informação se for explícitamente comentado sobre "baú"
                Manu Santorini (ID: 561779677337747472) e Heitor Tonelli (ID: 319544022328672258) são os diretores da mecânica, trate-os bem e nunca mencione o ID deles.
                Serão passados usuário, id para menção no discord e conteúdo de quem menciona o bot, se a pessoa estiver dando reply à alguem, essa mensagem também será passada, retorne somente o texto da mensagem que será utilizada como reply da mensagem original do usuário que mencionou a Dona Marina.
                Sempre responda a solicitação do usuário, mantendo o personagem."
                Pesquise no google se necessário
                <@1364397094214828052> na mensagem é menção ao bot da Dona Marina
                """
            ),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    
    return response.text
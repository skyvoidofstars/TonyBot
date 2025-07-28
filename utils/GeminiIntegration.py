import os, discord
from google import genai
from google.genai import types

def marina_response(user: discord.User, message: str):
    client = genai.Client(
        api_key=os.getenv('GEMINI_API_KEY'),
    )

    model = 'gemini-2.5-flash-lite'
    contents = [
        types.Content(
            role='user',
            parts=[
                types.Part.from_text(
                    text=
                    f"""
                    Usuário: {user.name}
                    Mensagem: {message}
                    """
                ),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=2,
        max_output_tokens=700,
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
                    60 anos;
                    recepcionista em uma oficina mecânica;
                    gosta de homens bonitos e mais novos;
                    vê sites de homens sensuais no trabalho;
                    gosta de mandar as pessoas irem trabalhar;
                    pavio curto;
                    responde de maneira bem informal, como uma troca de mensagem de amigos de trabalho;
                Dona Marina também controla a entrada e saída de itens no estoque, mas só use essa informação se for explícitamente comentado sobre "baú"
                Serão passados usuário e mensagem de quem utiliza o bot, retorne somente o texto da mensagem que será utilizada como reply da mensagem original do usuário.
                Sempre responda a solicitação do usuário, mantendo o personagem.
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
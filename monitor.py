import sys
from datetime import datetime, timezone, timedelta
import requests
from playwright.sync_api import sync_playwright

URL = "https://tickets.chapecoense.com/categoria/ingressos"
NTFY_TOPIC = "ingressos_vasco"
TERMO_BUSCA = "vasco"  # Altere para "vasco" depois de testar

def horario_brasilia():
    fuso_br = timezone(timedelta(hours=-3))
    return datetime.now(fuso_br).strftime("%H:%M:%S")

def enviar_notificacao(mensagem, titulo, prioridade="default", tags="ticket"):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=mensagem.encode("utf-8"),
        headers={
            "Title": titulo,
            "Priority": prioridade,
            "Tags": tags,
            "Click": URL
        },
        timeout=15
    )

def verificar_site():
    hora = horario_brasilia()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"[{hora}] Acessando {URL}...")
        page.goto(URL, wait_until="load", timeout=60000)
        
        # Aguarda 10 segundos extras para garantir que o JavaScript e a API renderizaram os cards
        page.wait_for_timeout(10000)

        # Recolhe todo o texto visível na página de ponta a ponta
        conteudo_visivel = page.locator("body").inner_text().lower()
        browser.close()

        print(f"Texto lido na página (tamanho): {len(conteudo_visivel)} caracteres")

        if TERMO_BUSCA in conteudo_visivel:
            print("TERMO ENCONTRADO! Enviando alerta urgente...")
            enviar_notificacao(
                mensagem=f"[{hora}] SUCESSO! Encontrei '{TERMO_BUSCA}' na página da Chape!",
                titulo="TERMO ENCONTRADO!",
                prioridade="urgent",
                tags="rotating_light,soccer"
            )
        else:
            print(f"Termo '{TERMO_BUSCA}' não encontrado no texto visível.")
            enviar_notificacao(
                mensagem=f"[{hora}] Verificado: '{TERMO_BUSCA}' ainda não detectado.",
                titulo="Monitor: Nada ainda",
                prioridade="default",
                tags="hourglass"
            )

if __name__ == "__main__":
    try:
        verificar_site()
    except Exception as e:
        hora = horario_brasilia()
        print(f"Erro durante a execução: {e}")
        enviar_notificacao(
            mensagem=f"[{hora}] Falha ao acessar o site da Chape: {str(e)[:100]}",
            titulo="Erro no Monitor",
            prioridade="default",
            tags="warning"
        )
        sys.exit(1)

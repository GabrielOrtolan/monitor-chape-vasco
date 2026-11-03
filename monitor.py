import sys
from datetime import datetime, timezone, timedelta
import requests
from playwright.sync_api import sync_playwright

URL = "https://tickets.chapecoense.com/categoria/ingressos"
NTFY_TOPIC = "ingressos_vasco"
TERMO_BUSCA = "Mirassol"

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
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        conteudo_visivel = page.inner_text("body").lower()
        html_completo = page.content().lower()
        browser.close()

        if TERMO_BUSCA in conteudo_visivel or TERMO_BUSCA in html_completo:
            print("JOGO ENCONTRADO! Enviando alerta urgente...")
            enviar_notificacao(
                mensagem=f"[{hora}] CORRE! Os ingressos para Chapecoense x Vasco saíram! Toque para abrir.",
                titulo="INGRESSOS LIBERADOS!",
                prioridade="urgent",
                tags="rotating_light,soccer"
            )
        else:
            print("Ainda nada. Enviando status negativo...")
            enviar_notificacao(
                mensagem=f"[{hora}] Verificado: Ainda sem ingressos do Vasco no site.",
                titulo="Monitor Chape x Vasco: Nada ainda",
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
            titulo="Erro no Monitor de Ingressos",
            prioridade="default",
            tags="warning"
        )
        sys.exit(1)

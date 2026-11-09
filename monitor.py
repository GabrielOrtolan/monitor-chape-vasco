import sys
import time
from datetime import datetime, timezone, timedelta
import requests
from playwright.sync_api import sync_playwright

URL = "https://tickets.chapecoense.com/categoria/ingressos"
NTFY_TOPIC = "ingressos_vasco"
TERMO_BUSCA = "vasco"

def horario_brasilia():
    fuso_br = timezone(timedelta(hours=-3))
    return datetime.now(fuso_br).strftime("%H:%M:%S")

def enviar_notificacao(mensagem, titulo, prioridade="default", tags="ticket"):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=mensagem.encode("utf-8"),
            headers={
                "Title": titulo,
                "Priority": prioridade,
                "Tags": tags,
                "Click": URL
            },
            timeout=10
        )
    except Exception as e:
        print(f"Erro ao enviar ntfy: {e}")

def disparar_alarme_30x():
    print("INICIANDO SEQUÊNCIA DE 30 DISPAROS PARA ACORDAR!")
    for i in range(1, 31):
        hora = horario_brasilia()
        print(f"Disparando alerta {i}/30...")
        enviar_notificacao(
            mensagem=f"[{i}/30 - {hora}] ACORDA! Os ingressos de Chapecoense x Vasco saíram! Toque para comprar!",
            titulo="🚨 ACORDA! INGRESSOS LIBERADOS! 🚨",
            prioridade="urgent",
            tags="rotating_light,soccer,loudspeaker"
        )
        # Pausa de 2 segundos para tocar continuamente por 1 minuto sem tomar bloqueio (rate limit) do ntfy
        time.sleep(2)

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
        
        # Aguarda 10 segundos para garantir que os cards carregaram via JavaScript
        page.wait_for_timeout(10000)

        conteudo_visivel = page.locator("body").inner_text().lower()
        browser.close()

        print(f"Texto lido na página: {len(conteudo_visivel)} caracteres.")

        if TERMO_BUSCA in conteudo_visivel:
            print("JOGO DO VASCO ENCONTRADO!")
            disparar_alarme_30x()
        else:
            print(f"[{hora}] Ainda sem ingressos do Vasco. Seguindo monitoramento em silêncio...")
            # Se quiser que continue avisando mesmo quando não achar, basta remover o '#' das 5 linhas abaixo:
            # enviar_notificacao(
            #     mensagem=f"[{hora}] Verificado: Ainda sem ingressos do Vasco.",
            #     titulo="Monitor: Nada ainda",
            #     prioridade="low",
            #     tags="hourglass"
            # )

if __name__ == "__main__":
    try:
        verificar_site()
    except Exception as e:
        hora = horario_brasilia()
        print(f"Erro durante a execução: {e}")
        sys.exit(1)

"""
╔══════════════════════════════════════════════════════════════╗
║         AGENTE SENTINELA GEOPOLÍTICO  v3.1                  ║
║  9 Teatros Globais · Telegram · Relatório diário 22h        ║
║  Coleta silenciosa: 08h, 13h, 18h  |  Relatório: 22h       ║
║  SP → Sapucaí Mirim, Serra da Mantiqueira                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import anthropic, requests, feedparser, json, os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════
# CREDENCIAIS  (definidas no arquivo .env)
# ══════════════════════════════════════════════════════════════
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
NEWS_API_KEY      = os.getenv("NEWS_API_KEY")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

EMOJIS = {1:"🟢", 2:"🟡", 3:"🟠", 4:"🔴", 5:"🚨"}
LABELS = {1:"NORMAL", 2:"ATENCAO", 3:"ALERTA", 4:"CRITICO", 5:"EMERGENCIA"}

# ══════════════════════════════════════════════════════════════
# 9 TEATROS DE CONFLITO
# peso = multiplicador no calculo do nivel global ponderado
# ══════════════════════════════════════════════════════════════
TEATROS = {

    "brasil_eua": {
        "nome":       "Brasil x EUA / Paraguai",
        "peso":       3,
        "impacto_sp": "DIRETO - gatilho primario de evacuacao SP para Sapucai Mirim",
        "keywords":   [
            "Brasil EUA tensao diplomatica", "tropas americanas Paraguai",
            "Trump Brasil tarifa", "Triplice Fronteira base militar",
            "SOFA Paraguai acordo", "sancao Brasil EUA",
        ],
        "rss_filtro": ["brasil", "eua", "paraguai", "fronteira", "trump",
                       "lula", "tarifa", "itamaraty"],
    },

    "russia_ucrania": {
        "nome":       "Russia x Ucrania / OTAN",
        "peso":       2,
        "impacto_sp": "INDIRETO - energia, commodities, cambio e inflacao no Brasil",
        "keywords":   [
            "Russia Ukraine war offensive", "Ucrania ofensiva",
            "OTAN Russia escalada", "NATO Russia nuclear threat",
            "Putin mobilizacao", "Kiev ataque russo",
        ],
        "rss_filtro": ["russia", "ucrania", "ukraine", "otan", "nato",
                       "nuclear", "putin", "kiev"],
    },

    "europa_balticos": {
        "nome":       "Europa / Balticos / Balcas",
        "peso":       1,
        "impacto_sp": "INDIRETO - estabilidade OTAN, capital europeu e comercio com UE",
        "keywords":   [
            "Baltic states Russia military threat", "Serbia Kosovo conflict",
            "Poland military buildup NATO", "Europa instabilidade tensao",
        ],
        "rss_filtro": ["baltico", "baltic", "servia", "kosovo", "polonia",
                       "hungria", "ue crise"],
    },

    "china_taiwan": {
        "nome":       "China x Taiwan / Pacifico",
        "peso":       2,
        "impacto_sp": "INDIRETO - colapso supply chain, semicondutores e exportacoes BR",
        "keywords":   [
            "China Taiwan strait military", "Taiwan invasao China",
            "EUA China conflito Pacifico", "TSMC Taiwan war risk",
            "South China Sea escalation",
        ],
        "rss_filtro": ["china", "taiwan", "estreito", "strait", "tsmc",
                       "pacifico", "semicondutor"],
    },

    "indo_pacifico": {
        "nome":       "Indo-Pacifico / Coreia / Japao",
        "peso":       1,
        "impacto_sp": "INDIRETO - comercio asiatico e exportacoes brasileiras",
        "keywords":   [
            "North Korea missile launch nuclear", "Japan military rearmament",
            "India Pakistan border conflict", "AUKUS alliance",
        ],
        "rss_filtro": ["coreia", "korea", "japao", "japan", "india",
                       "paquistao", "aukus", "kim"],
    },

    "oriente_medio": {
        "nome":       "Oriente Medio / Golfo Persico",
        "peso":       2,
        "impacto_sp": "INDIRETO - petroleo, combustivel, frete maritimo e inflacao Brasil",
        "keywords":   [
            "Israel Iran attack war", "Iran nuclear program collapse",
            "Hormuz Strait blockade oil", "Hezbollah Israel",
            "Hamas Gaza", "Huti Red Sea attack",
        ],
        "rss_filtro": ["israel", "ira", "iran", "gaza", "petroleo",
                       "golfo", "hormuz", "hezbollah", "hamas", "huti"],
    },

    "america_latina": {
        "nome":       "America Latina / Cone Sul",
        "peso":       2,
        "impacto_sp": "MODERADO - migracao, fronteiras, instabilidade e Mercosul",
        "keywords":   [
            "Venezuela crise Maduro colapso", "Argentina Milei instabilidade",
            "Colombia guerrilha conflito", "Mercosul crise",
            "Bolivia instabilidade",
        ],
        "rss_filtro": ["venezuela", "argentina", "milei", "maduro",
                       "colombia", "mercosul", "bolivia"],
    },

    "africa": {
        "nome":       "Africa / Sahel / Chifre da Africa",
        "peso":       1,
        "impacto_sp": "BAIXO - rotas maritimas, commodities e fluxo migratorio global",
        "keywords":   [
            "Sahel conflict coup Mali Niger Burkina Faso",
            "Sudan civil war 2025", "Congo DRC conflict militia",
            "Somalia al-Shabaab attack",
        ],
        "rss_filtro": ["sahel", "sudao", "sudan", "congo", "mali",
                       "niger", "somalia", "burkina", "africa golpe"],
    },

    "cyber_guerra": {
        "nome":       "Cyber / Guerra Digital Global",
        "peso":       2,
        "impacto_sp": "TRANSVERSAL - bancos, energia eletrica e comunicacoes em SP",
        "keywords":   [
            "cyberattack critical infrastructure 2025",
            "ataque cibernetico Brasil governo",
            "ransomware sistemas publicos",
            "Russia China cyber espionage warfare",
        ],
        "rss_filtro": ["cyber", "cibernetico", "ransomware", "hacker",
                       "ataque digital", "infraestrutura critica"],
    },
}

# ══════════════════════════════════════════════════════════════
# FONTES RSS GLOBAIS
# ══════════════════════════════════════════════════════════════
RSS_FEEDS = [
    "https://agenciabrasil.ebc.com.br/rss/politica/feed.xml",
    "https://feeds.folha.uol.com.br/mundo/rss091.xml",
    "https://www.bbc.com/portuguese/topics/c77jz3mdm8yt.rss",
    "https://feeds.reuters.com/reuters/worldNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.dw.com/rdf/rss-en-world",
    "https://feeds.skynews.com/feeds/rss/world.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
]

# ══════════════════════════════════════════════════════════════
# COLETA DE NOTICIAS
# ══════════════════════════════════════════════════════════════
def coletar_noticias(tid, teatro):
    noticias = []

    for kw in teatro["keywords"][:3]:
        try:
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": kw, "sortBy": "publishedAt",
                        "pageSize": 3, "apiKey": NEWS_API_KEY},
                timeout=10,
            )
            for art in r.json().get("articles", [])[:2]:
                noticias.append(f"[{art['source']['name']}] {art['title']}")
        except Exception as e:
            print(f"    NewsAPI erro: {e}")

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                titulo = entry.get("title", "")
                if any(f in titulo.lower() for f in teatro["rss_filtro"]):
                    noticias.append(f"[RSS] {titulo}")
        except:
            pass

    return list(dict.fromkeys(noticias))[:15]

# ══════════════════════════════════════════════════════════════
# ANALISE POR TEATRO — Claude
# ══════════════════════════════════════════════════════════════
PROMPT_TEATRO = """Voce e analista senior de inteligencia geopolitica focado em seguranca familiar.

PERFIL DO USUARIO:
- Familia em Sao Paulo capital (esposa + 3 filhos)
- Refugio: Sitio em Sapucai Mirim, Serra da Mantiqueira, MG (230km de SP)
- Teatro em analise: {nome}
- Impacto em SP: {impacto_sp}

ESCALA DE RISCO:
1 = Normal/Estavel
2 = Atencao (sinais de deterioracao)
3 = Alerta (preparar saida 2-4 semanas)
4 = Critico (sair em 48-72h)
5 = Emergencia (sair AGORA)

Retorne SOMENTE JSON valido, sem markdown, sem texto adicional:
{{
  "nivel": <1-5>,
  "resumo": "<1 frase direta sobre o cenario>",
  "eventos": ["<fato concreto 1>", "<fato concreto 2>"],
  "tendencia": "<estavel|deteriorando|melhorando>",
  "impacto_brasil": "<como afeta SP/Brasil especificamente, 1 frase>"
}}"""

def analisar_teatro(tid, teatro, noticias):
    if not noticias:
        return {"nivel":1,"resumo":"Sem noticias relevantes.",
                "eventos":[],"tendencia":"estavel","impacto_brasil":"Sem impacto."}

    system = PROMPT_TEATRO.format(nome=teatro["nome"], impacto_sp=teatro["impacto_sp"])
    texto  = "\n".join(f"- {n}" for n in noticias[:15])

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=system,
            messages=[{"role":"user","content":f"Noticias coletadas:\n{texto}"}],
        )
        raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"    Erro Claude ({tid}): {e}")
        return {"nivel":1,"resumo":"Erro na analise.","eventos":[],
                "tendencia":"estavel","impacto_brasil":"Indisponivel."}

# ══════════════════════════════════════════════════════════════
# RELATORIO CONSOLIDADO NOTURNO — Claude
# ══════════════════════════════════════════════════════════════
PROMPT_RELATORIO = """Voce e diretor de inteligencia estrategica.

Produza relatorio diario consolidado para familia em Sao Paulo com refugio em
Sapucai Mirim (Mantiqueira, MG, 230km de SP via Fernao Dias).

Conecte eventos globais ao impacto concreto na vida da familia. Seja direto e acionavel.

Retorne SOMENTE JSON valido, sem markdown:
{{
  "nivel_global": <1-5 ponderado pelos pesos dos teatros>,
  "titulo_do_dia": "<manchete de 1 frase resumindo o dia geopolitico>",
  "narrativa": "<3-4 frases: eventos globais conectados ao impacto direto em SP/familia>",
  "teatro_mais_critico": "<nome do teatro de maior risco hoje>",
  "recomendacao_familia": "<1 acao concreta e especifica para a familia fazer HOJE>",
  "gatilhos_ativos": ["<gatilho ativo 1 se houver - senao lista vazia>"],
  "previsao_24h": "<o que monitorar nas proximas 24 horas, 1-2 frases>",
  "status_sitio": "<avaliacao do sitio em Sapucai Mirim hoje>"
}}"""

def gerar_relatorio(resultados):
    resumo = [
        {
            "teatro":         TEATROS[tid]["nome"],
            "peso":           TEATROS[tid]["peso"],
            "nivel":          d["analise"]["nivel"],
            "resumo":         d["analise"]["resumo"],
            "tendencia":      d["analise"]["tendencia"],
            "impacto_brasil": d["analise"]["impacto_brasil"],
            "eventos":        d["analise"].get("eventos", []),
        }
        for tid, d in resultados.items()
    ]
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=900,
            system=PROMPT_RELATORIO,
            messages=[{"role":"user",
                       "content": f"Dados dos 9 teatros:\n{json.dumps(resumo,ensure_ascii=False,indent=2)}"}],
        )
        raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  Erro relatorio consolidado: {e}")
        return None

# ══════════════════════════════════════════════════════════════
# TELEGRAM
# ══════════════════════════════════════════════════════════════
def telegram(texto):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("  AVISO: Telegram nao configurado no .env")
        return False

    url    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    partes = [texto[i:i+4000] for i in range(0, len(texto), 4000)]
    ok     = True

    for i, parte in enumerate(partes):
        prefixo = f"[{i+1}/{len(partes)}]\n" if len(partes) > 1 else ""
        try:
            r = requests.post(url, json={
                "chat_id":    TELEGRAM_CHAT_ID,
                "text":       prefixo + parte,
                "parse_mode": "HTML",
            }, timeout=15)
            if r.status_code != 200:
                print(f"  Telegram erro HTTP {r.status_code}: {r.text[:150]}")
                ok = False
        except Exception as e:
            print(f"  Telegram excecao: {e}")
            ok = False
    return ok

# ══════════════════════════════════════════════════════════════
# FORMATACAO DO RELATORIO DIARIO
# ══════════════════════════════════════════════════════════════
def formatar_relatorio(relatorio, resultados, agora):
    ng  = relatorio.get("nivel_global", 1)
    sep = "=" * 36

    linhas = ""
    for tid, d in resultados.items():
        n = d["analise"]["nivel"]
        linhas += f"{EMOJIS[n]} {TEATROS[tid]['nome']}: {n}/5 - {d['analise']['resumo']}\n"

    gt     = relatorio.get("gatilhos_ativos", [])
    gt_txt = "\n".join(f"- {g}" for g in gt) if gt else "Nenhum gatilho ativo"

    safehouse = (
        "ATENCAO: ACIONE PROTOCOLO - mova familia para Sapucai Mirim!"
        if ng >= 3 else
        "Sapucai Mirim: STATUS OK - sem necessidade de acao imediata"
    )

    return (
        f"SENTINELA - RELATORIO DIARIO\n"
        f"Data: {agora}\n"
        f"{sep}\n\n"
        f"{EMOJIS[ng]} NIVEL GLOBAL: {ng}/5 - {LABELS[ng]}\n"
        f"MANCHETE: {relatorio.get('titulo_do_dia','')}\n\n"
        f"SITUACAO:\n{relatorio.get('narrativa','')}\n\n"
        f"9 TEATROS:\n{linhas}\n"
        f"GATILHOS:\n{gt_txt}\n\n"
        f"MAIS CRITICO: {relatorio.get('teatro_mais_critico','')}\n\n"
        f"ACAO HOJE:\n{relatorio.get('recomendacao_familia','')}\n\n"
        f"PROXIMAS 24H:\n{relatorio.get('previsao_24h','')}\n\n"
        f"SITIO: {relatorio.get('status_sitio','')}\n\n"
        f"{sep}\n"
        f"{safehouse}"
    )

# ══════════════════════════════════════════════════════════════
# HORARIOS ATIVOS (hora de Brasilia = UTC - 3)
# Task unica no PythonAnywhere: roda a cada hora (00 minutos)
# O script decide o que fazer com base no horario atual
# ══════════════════════════════════════════════════════════════

# Horarios de coleta silenciosa (sem envio Telegram)
HORAS_COLETA   = {8, 13, 18}

# Horario do relatorio diario completo (envia no Telegram)
HORA_RELATORIO = 22

def ciclo_coleta(agora):
    """Coleta e analisa os 9 teatros. Retorna resultados."""
    resultados = {}
    for tid, teatro in TEATROS.items():
        print(f"\n  [{teatro['nome']}]")
        noticias = coletar_noticias(tid, teatro)
        print(f"    {len(noticias)} noticias coletadas")
        analise  = analisar_teatro(tid, teatro, noticias)
        print(f"    Nivel {analise['nivel']}/5 | {analise['tendencia']} | {analise['resumo'][:50]}...")
        resultados[tid] = {"analise": analise, "noticias": noticias}

    # Log local
    with open("log_sentinela.txt", "a", encoding="utf-8") as f:
        niveis = " | ".join(
            f"{TEATROS[tid]['nome'].split()[0][:6]} {d['analise']['nivel']}"
            for tid, d in resultados.items()
        )
        f.write(f"[{agora}] {niveis}\n")

    # Snapshot JSON
    with open("snapshot_atual.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": agora,
            "teatros": {
                tid: {
                    "nivel":    d["analise"]["nivel"],
                    "resumo":   d["analise"]["resumo"],
                    "tendencia":d["analise"]["tendencia"],
                }
                for tid, d in resultados.items()
            }
        }, f, ensure_ascii=False, indent=2)

    return resultados


def main():
    # Horario de Brasilia = UTC - 3
    from datetime import timezone, timedelta
    tz_brasil = timezone(timedelta(hours=-3))
    agora_dt  = datetime.now(tz_brasil)
    agora     = agora_dt.strftime("%d/%m/%Y %H:%M")
    hora      = agora_dt.hour

    print(f"\n{'='*55}")
    print(f"  SENTINELA v3.2 - {agora} (horario Brasilia)")

    # ── Hora inativa: encerra imediatamente sem gastar nada ───
    if hora not in HORAS_COLETA and hora != HORA_RELATORIO:
        print(f"  Hora {hora}h: fora do agendamento. Encerrando.")
        print(f"  Proximas execucoes: 08h, 13h, 18h (coleta) | 22h (relatorio)")
        print(f"{'='*55}\n")
        return

    # ── Hora ativa: define o modo ─────────────────────────────
    modo = "RELATORIO NOTURNO 22h" if hora == HORA_RELATORIO else f"COLETA SILENCIOSA {hora}h"
    print(f"  Modo: {modo}")
    print(f"{'='*55}")

    # Executa coleta em todos os horarios ativos
    resultados = ciclo_coleta(agora)

    if hora == HORA_RELATORIO:
        # Gera e envia relatorio completo no Telegram
        print("\n  Gerando relatorio consolidado...")
        relatorio = gerar_relatorio(resultados)
        if relatorio:
            msg = formatar_relatorio(relatorio, resultados, agora)
            ok  = telegram(msg)
            print(f"  Telegram: {'OK - enviado' if ok else 'FALHOU'}")
            with open(f"relatorio_{agora_dt.strftime('%Y%m%d')}.txt",
                      "w", encoding="utf-8") as f:
                f.write(msg)
            print(f"  Arquivo: relatorio_{agora_dt.strftime('%Y%m%d')}.txt")
        else:
            print("  FALHA ao gerar relatorio")
    else:
        # Coleta silenciosa: apenas log local
        niveis_v = [d["analise"]["nivel"] for d in resultados.values()]
        print(f"\n  Coleta concluida. Nivel maximo: {EMOJIS[max(niveis_v)]} {max(niveis_v)}/5")
        print(f"  Proximo ciclo ativo: { {8:13, 13:18, 18:22}.get(hora, 8) }h")

    print(f"\n{'='*55}")
    print(f"  CONCLUIDO - {agora}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()

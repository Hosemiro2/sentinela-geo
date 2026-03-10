"""
╔══════════════════════════════════════════════════════════════╗
║         AGENTE SENTINELA GEOPOLÍTICO  v4.0                  ║
║  9 Teatros · Telegram · Portal Web Auto-Atualizado          ║
║  Coleta silenciosa: 08h, 13h, 18h  |  Relatório: 22h       ║
║  SP → Sapucaí Mirim, Serra da Mantiqueira                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import anthropic, requests, feedparser, json, os, subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
NEWS_API_KEY      = os.getenv("NEWS_API_KEY")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

EMOJIS = {1:"🟢", 2:"🟡", 3:"🟠", 4:"🔴", 5:"🚨"}
LABELS = {1:"NORMAL", 2:"ATENCAO", 3:"ALERTA", 4:"CRITICO", 5:"EMERGENCIA"}
CORES  = {1:"#27AE60", 2:"#C9A000", 3:"#E07020", 4:"#C0392B", 5:"#8B0000"}

TEATROS = {
    "brasil_eua": {
        "nome": "Brasil x EUA / Paraguai", "peso": 3,
        "impacto_sp": "DIRETO - gatilho primario de evacuacao SP para Sapucai Mirim",
        "keywords": ["Brasil EUA tensao diplomatica","tropas americanas Paraguai","Trump Brasil tarifa","Triplice Fronteira base militar","SOFA Paraguai acordo","sancao Brasil EUA"],
        "rss_filtro": ["brasil","eua","paraguai","fronteira","trump","lula","tarifa","itamaraty"],
    },
    "russia_ucrania": {
        "nome": "Russia x Ucrania / OTAN", "peso": 2,
        "impacto_sp": "INDIRETO - energia, commodities, cambio e inflacao no Brasil",
        "keywords": ["Russia Ukraine war offensive","Ucrania ofensiva","OTAN Russia escalada","NATO Russia nuclear threat","Putin mobilizacao","Kiev ataque russo"],
        "rss_filtro": ["russia","ucrania","ukraine","otan","nato","nuclear","putin","kiev"],
    },
    "europa_balticos": {
        "nome": "Europa / Balticos / Balcas", "peso": 1,
        "impacto_sp": "INDIRETO - estabilidade OTAN, capital europeu e comercio com UE",
        "keywords": ["Baltic states Russia military threat","Serbia Kosovo conflict","Poland military buildup NATO","Europa instabilidade tensao"],
        "rss_filtro": ["baltico","baltic","servia","kosovo","polonia","hungria","ue crise"],
    },
    "china_taiwan": {
        "nome": "China x Taiwan / Pacifico", "peso": 2,
        "impacto_sp": "INDIRETO - colapso supply chain, semicondutores e exportacoes BR",
        "keywords": ["China Taiwan strait military","Taiwan invasao China","EUA China conflito Pacifico","TSMC Taiwan war risk","South China Sea escalation"],
        "rss_filtro": ["china","taiwan","estreito","strait","tsmc","pacifico","semicondutor"],
    },
    "indo_pacifico": {
        "nome": "Indo-Pacifico / Coreia / Japao", "peso": 1,
        "impacto_sp": "INDIRETO - comercio asiatico e exportacoes brasileiras",
        "keywords": ["North Korea missile launch nuclear","Japan military rearmament","India Pakistan border conflict","AUKUS alliance"],
        "rss_filtro": ["coreia","korea","japao","japan","india","paquistao","aukus","kim"],
    },
    "oriente_medio": {
        "nome": "Oriente Medio / Golfo Persico", "peso": 2,
        "impacto_sp": "INDIRETO - petroleo, combustivel, frete maritimo e inflacao Brasil",
        "keywords": ["Israel Iran attack war","Iran nuclear program collapse","Hormuz Strait blockade oil","Hezbollah Israel","Hamas Gaza","Huti Red Sea attack"],
        "rss_filtro": ["israel","ira","iran","gaza","petroleo","golfo","hormuz","hezbollah","hamas","huti"],
    },
    "america_latina": {
        "nome": "America Latina / Cone Sul", "peso": 2,
        "impacto_sp": "MODERADO - migracao, fronteiras, instabilidade e Mercosul",
        "keywords": ["Venezuela crise Maduro colapso","Argentina Milei instabilidade","Colombia guerrilha conflito","Mercosul crise","Bolivia instabilidade"],
        "rss_filtro": ["venezuela","argentina","milei","maduro","colombia","mercosul","bolivia"],
    },
    "africa": {
        "nome": "Africa / Sahel / Chifre da Africa", "peso": 1,
        "impacto_sp": "BAIXO - rotas maritimas, commodities e fluxo migratorio global",
        "keywords": ["Sahel conflict coup Mali Niger Burkina Faso","Sudan civil war 2025","Congo DRC conflict militia","Somalia al-Shabaab attack"],
        "rss_filtro": ["sahel","sudao","sudan","congo","mali","niger","somalia","burkina","africa golpe"],
    },
    "cyber_guerra": {
        "nome": "Cyber / Guerra Digital Global", "peso": 2,
        "impacto_sp": "TRANSVERSAL - bancos, energia eletrica e comunicacoes em SP",
        "keywords": ["cyberattack critical infrastructure 2025","ataque cibernetico Brasil governo","ransomware sistemas publicos","Russia China cyber espionage warfare"],
        "rss_filtro": ["cyber","cibernetico","ransomware","hacker","ataque digital","infraestrutura critica"],
    },
}

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
# COLETA
# ══════════════════════════════════════════════════════════════
def coletar_noticias(tid, teatro):
    noticias = []
    for kw in teatro["keywords"][:3]:
        try:
            r = requests.get("https://newsapi.org/v2/everything",
                params={"q":kw,"sortBy":"publishedAt","pageSize":3,"apiKey":NEWS_API_KEY},timeout=10)
            for art in r.json().get("articles",[])[:2]:
                noticias.append({"titulo":art["title"],"fonte":art["source"]["name"],"url":art.get("url",""),"resumo":art.get("description","")})
        except: pass
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                titulo = entry.get("title","")
                if any(f in titulo.lower() for f in teatro["rss_filtro"]):
                    noticias.append({"titulo":titulo,"fonte":url.split("/")[2],"url":entry.get("link",""),"resumo":entry.get("summary","")[:200]})
        except: pass
    seen = set()
    unique = []
    for n in noticias:
        if n["titulo"] not in seen:
            seen.add(n["titulo"])
            unique.append(n)
    return unique[:15]

# ══════════════════════════════════════════════════════════════
# ANALISE
# ══════════════════════════════════════════════════════════════
PROMPT_TEATRO = """Voce e analista senior de inteligencia geopolitica focado em seguranca familiar.
PERFIL: Familia em Sao Paulo, refugio em Sapucai Mirim MG (230km via Fernao Dias).
Teatro: {nome} | Impacto SP: {impacto_sp}
ESCALA: 1=Normal 2=Atencao 3=Alerta(preparar saida 2-4sem) 4=Critico(sair 48-72h) 5=Emergencia(sair AGORA)
Retorne SOMENTE JSON valido sem markdown:
{{"nivel":<1-5>,"resumo":"<1 frase>","eventos":["<fato1>","<fato2>"],"tendencia":"<estavel|deteriorando|melhorando>","impacto_brasil":"<1 frase>"}}"""

def analisar_teatro(tid, teatro, noticias):
    if not noticias:
        return {"nivel":1,"resumo":"Sem noticias relevantes.","eventos":[],"tendencia":"estavel","impacto_brasil":"Sem impacto."}
    system = PROMPT_TEATRO.format(nome=teatro["nome"],impacto_sp=teatro["impacto_sp"])
    texto = "\n".join(f"- {n['titulo']}" for n in noticias[:15])
    try:
        msg = client.messages.create(model="claude-sonnet-4-20250514",max_tokens=400,system=system,
            messages=[{"role":"user","content":f"Noticias:\n{texto}"}])
        raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"    Erro Claude ({tid}): {e}")
        return {"nivel":1,"resumo":"Erro na analise.","eventos":[],"tendencia":"estavel","impacto_brasil":"Indisponivel."}

PROMPT_RELATORIO = """Voce e diretor de inteligencia estrategica. Produza relatorio diario para familia em SP com refugio em Sapucai Mirim MG.
Retorne SOMENTE JSON valido sem markdown:
{{"nivel_global":<1-5>,"titulo_do_dia":"<manchete>","narrativa":"<3-4 frases>","teatro_mais_critico":"<nome>","recomendacao_familia":"<1 acao concreta>","gatilhos_ativos":["<gatilho se houver>"],"previsao_24h":"<1-2 frases>","status_sitio":"<avaliacao>"}}"""

def gerar_relatorio(resultados):
    resumo = [{"teatro":TEATROS[tid]["nome"],"peso":TEATROS[tid]["peso"],"nivel":d["analise"]["nivel"],"resumo":d["analise"]["resumo"],"tendencia":d["analise"]["tendencia"],"impacto_brasil":d["analise"]["impacto_brasil"],"eventos":d["analise"].get("eventos",[])} for tid,d in resultados.items()]
    try:
        msg = client.messages.create(model="claude-sonnet-4-20250514",max_tokens=900,system=PROMPT_RELATORIO,
            messages=[{"role":"user","content":f"9 teatros:\n{json.dumps(resumo,ensure_ascii=False,indent=2)}"}])
        raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  Erro relatorio: {e}")
        return None

# ══════════════════════════════════════════════════════════════
# GERAR HTML DO PORTAL (v4.0)
# ══════════════════════════════════════════════════════════════
def gerar_html(resultados, relatorio, agora):
    ng = relatorio.get("nivel_global", 1) if relatorio else max(d["analise"]["nivel"] for d in resultados.values())
    cor_global = CORES[ng]
    label_global = LABELS[ng]
    titulo_dia = relatorio.get("titulo_do_dia","") if relatorio else ""
    narrativa = relatorio.get("narrativa","") if relatorio else ""
    recomendacao = relatorio.get("recomendacao_familia","") if relatorio else ""
    previsao = relatorio.get("previsao_24h","") if relatorio else ""
    status_sitio = relatorio.get("status_sitio","") if relatorio else ""
    teatro_critico = relatorio.get("teatro_mais_critico","") if relatorio else ""
    gatilhos = relatorio.get("gatilhos_ativos",[]) if relatorio else []
    safehouse_alert = ng >= 3

    # Cards dos teatros
    theater_cards = ""
    for tid, d in resultados.items():
        a = d["analise"]
        n = a["nivel"]
        cor = CORES[n]
        noticias_html = ""
        for noticia in d.get("noticias",[])[:3]:
            url = noticia.get("url","#")
            fonte = noticia.get("fonte","")
            titulo_n = noticia.get("titulo","")
            noticias_html += f'<div class="news-item"><div class="news-bar" style="background:{cor}"></div><div class="news-body"><span class="news-src">{fonte}</span><a href="{url}" target="_blank" class="news-title">{titulo_n}</a></div></div>'
        eventos_html = "".join(f"<li>{e}</li>" for e in a.get("eventos",[]))
        tendencia_icon = "↑" if a["tendencia"]=="deteriorando" else ("↓" if a["tendencia"]=="melhorando" else "→")
        theater_cards += f"""
        <div class="theater-card" style="border-left:3px solid {cor}">
          <div class="tc-header">
            <div>
              <div class="tc-name">{TEATROS[tid]['nome']}</div>
              <div class="tc-level" style="color:{cor}">{n}/5 — {LABELS[n]}</div>
            </div>
            <div class="tc-num" style="color:{cor}">{n}</div>
          </div>
          <div class="tc-resumo">{a['resumo']}</div>
          <div class="tc-kpis">
            <span class="kpi-pill">Tendência {tendencia_icon}</span>
            <span class="kpi-pill">Fontes: {len(d.get('noticias',[]))}</span>
            <span class="kpi-pill">Peso: {TEATROS[tid]['peso']}</span>
          </div>
          {'<ul class="tc-eventos">' + eventos_html + '</ul>' if eventos_html else ''}
          {('<div class="tc-news">' + noticias_html + '</div>') if noticias_html else ''}
        </div>"""

    # Gatilhos
    gatilhos_html = "".join(f"<li>⚡ {g}</li>" for g in gatilhos) if gatilhos else "<li>Nenhum gatilho ativo</li>"

    # Contagens KPI
    teatros_alerta = sum(1 for d in resultados.values() if d["analise"]["nivel"] >= 3)
    total_fontes = sum(len(d.get("noticias",[])) for d in resultados.values())
    prob_conflito = min(95, ng * 15 + teatros_alerta * 5)

    safehouse_html = f"""<div class="safehouse-alert {'safehouse-danger' if safehouse_alert else 'safehouse-ok'}">
      {'🔴 PROTOCOLO ACIONADO — MOVA FAMÍLIA PARA SAPUCAÍ MIRIM IMEDIATAMENTE' if safehouse_alert else '🟢 SAPUCAÍ MIRIM: STATUS OK — Sem necessidade de ação imediata'}
    </div>""" if safehouse_alert else f"""<div class="safehouse-alert safehouse-ok">🟢 SAPUCAÍ MIRIM: STATUS OK — {status_sitio}</div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<title>SENTINELA — Monitor Geopolítico Global</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Crimson+Pro:ital,wght@0,300;0,400;1,300&family=JetBrains+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{{--gold:#C9A84C;--gold-dim:#5A4820;--black:#060606;--b2:#0E0E0E;--b3:#161616;--b4:#1E1E1E;--b5:#262626;--white:#F0EAD6;--white-dim:#7A7060;--red:#C0392B;--orange:#E07020;--yellow:#C9A000;--green:#27AE60;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--black);color:var(--white);font-family:'Crimson Pro',serif;font-size:16px;line-height:1.6;}}
header{{position:sticky;top:0;z-index:500;background:rgba(6,6,6,.97);backdrop-filter:blur(16px);border-bottom:1px solid var(--gold-dim);display:flex;align-items:center;justify-content:space-between;padding:0 28px;height:58px;}}
.logo{{font-family:'Cinzel',serif;font-size:19px;font-weight:900;letter-spacing:.16em;color:var(--gold);display:flex;align-items:center;gap:10px;}}
.logo svg{{width:26px;height:26px;}}
nav a{{font-family:'Cinzel',serif;font-size:10px;letter-spacing:.1em;color:var(--white-dim);text-decoration:none;padding:5px 11px;border:1px solid transparent;transition:all .2s;margin-left:2px;}}
nav a:hover{{color:var(--gold);border-color:var(--gold-dim);}}
.live{{display:flex;align-items:center;gap:5px;font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--gold);}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:var(--gold);animation:blink 2s infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.2;}}}}
.banner{{background:linear-gradient(90deg,rgba({",".join(str(int(cor_global.lstrip("#")[i:i+2],16)) for i in (0,2,4))},0.12),rgba(201,168,76,0.03));border-bottom:1px solid rgba({",".join(str(int(cor_global.lstrip("#")[i:i+2],16)) for i in (0,2,4))},0.3);padding:10px 28px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;}}
.badge{{background:{cor_global};color:#000;font-weight:700;padding:2px 10px;font-family:'Cinzel',serif;font-size:11px;letter-spacing:.08em;}}
.banner-text{{font-style:italic;flex:1;font-size:14px;opacity:.85;}}
.banner-time{{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--white-dim);white-space:nowrap;}}
.layout{{display:grid;grid-template-columns:1fr 320px;min-height:calc(100vh - 80px);}}
.main{{border-right:1px solid var(--b4);}}
.sidebar{{background:var(--b2);}}
.sec-head{{padding:14px 24px;border-bottom:1px solid var(--b4);display:flex;align-items:center;justify-content:space-between;}}
.sec-title{{font-family:'Cinzel',serif;font-size:10px;letter-spacing:.18em;color:var(--gold);text-transform:uppercase;display:flex;align-items:center;gap:8px;}}
.sec-title::before{{content:'';width:14px;height:1px;background:var(--gold);}}
.sec-meta{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--white-dim);}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--b4);border-bottom:1px solid var(--b4);}}
.kpi-card{{background:var(--black);padding:18px 16px;text-align:center;}}
.kpi-icon{{font-size:20px;margin-bottom:6px;}}
.kpi-value{{font-family:'Cinzel',serif;font-size:26px;color:var(--gold);line-height:1;}}
.kpi-label{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--white-dim);letter-spacing:.08em;margin-top:5px;text-transform:uppercase;}}
.kpi-sub{{font-size:11px;color:var(--white-dim);margin-top:3px;font-style:italic;}}
.theater-card{{padding:16px 24px;border-bottom:1px solid var(--b3);transition:background .15s;}}
.theater-card:hover{{background:var(--b2);}}
.tc-header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:6px;}}
.tc-name{{font-family:'Cinzel',serif;font-size:10px;letter-spacing:.08em;color:var(--white-dim);text-transform:uppercase;}}
.tc-level{{font-size:12px;margin-top:2px;}}
.tc-num{{font-family:'Cinzel',serif;font-size:36px;font-weight:900;line-height:1;opacity:.6;}}
.tc-resumo{{font-size:14px;color:var(--white);margin-bottom:8px;font-style:italic;}}
.tc-kpis{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;}}
.kpi-pill{{font-family:'JetBrains Mono',monospace;font-size:9px;padding:2px 8px;border:1px solid var(--b5);color:var(--white-dim);}}
.tc-eventos{{font-size:12px;color:var(--white-dim);padding-left:16px;margin-bottom:8px;}}
.tc-eventos li{{margin-bottom:2px;}}
.tc-news{{margin-top:8px;}}
.news-item{{display:flex;gap:8px;margin-bottom:6px;}}
.news-bar{{width:2px;flex-shrink:0;border-radius:1px;}}
.news-body{{}}
.news-src{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--white-dim);display:block;}}
.news-title{{font-size:12px;color:var(--white);text-decoration:none;line-height:1.3;display:block;}}
.news-title:hover{{color:var(--gold);}}
.narrativa-section{{padding:20px 24px;border-bottom:1px solid var(--b4);background:var(--b2);}}
.narrativa-text{{font-size:15px;line-height:1.7;font-style:italic;color:var(--white);opacity:.9;margin-bottom:12px;}}
.rec-box{{background:var(--b3);border-left:3px solid var(--gold);padding:12px 16px;font-size:14px;}}
.rec-label{{font-family:'Cinzel',serif;font-size:9px;letter-spacing:.12em;color:var(--gold);margin-bottom:4px;}}
.gatilhos{{padding:16px 24px;border-bottom:1px solid var(--b4);}}
.gatilhos ul{{list-style:none;font-size:13px;color:var(--white-dim);}}
.gatilhos li{{padding:4px 0;border-bottom:1px solid var(--b3);}}
.safehouse-alert{{padding:12px 24px;font-family:'Cinzel',serif;font-size:11px;letter-spacing:.08em;text-align:center;border-bottom:1px solid var(--b4);}}
.safehouse-danger{{background:rgba(192,57,43,.2);color:#E74C3C;border-color:rgba(192,57,43,.4);animation:pulse-bg 2s infinite;}}
.safehouse-ok{{background:rgba(39,174,96,.1);color:var(--green);border-color:rgba(39,174,96,.2);}}
@keyframes pulse-bg{{0%,100%{{opacity:1;}}50%{{opacity:.7;}}}}
.market-section{{padding:16px 16px 0;}}
.market-title{{font-family:'Cinzel',serif;font-size:9px;letter-spacing:.14em;color:var(--gold);text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:7px;}}
.market-title::before{{content:'';width:10px;height:1px;background:var(--gold);}}
.market-item{{padding:10px 0;border-bottom:1px solid var(--b3);display:flex;align-items:center;justify-content:space-between;}}
.market-name{{font-family:'JetBrains Mono',monospace;font-size:11px;}}
.market-sub{{font-size:10px;color:var(--white-dim);}}
.price-val{{font-family:'JetBrains Mono',monospace;font-size:12px;text-align:right;}}
.price-chg{{font-family:'JetBrains Mono',monospace;font-size:10px;text-align:right;}}
.up{{color:#27AE60;}}.down{{color:var(--red);}}
.commodity-item{{padding:9px 0;border-bottom:1px solid var(--b3);display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;}}
.commodity-name{{font-size:13px;}}
.commodity-price{{font-family:'JetBrains Mono',monospace;font-size:11px;text-align:right;}}
.commodity-chg{{font-family:'JetBrains Mono',monospace;font-size:10px;text-align:right;min-width:48px;}}
.alert-log{{padding:12px 16px;}}
.log-item{{padding:8px 0;border-bottom:1px solid var(--b3);display:flex;gap:8px;}}
.log-text{{font-size:12px;line-height:1.4;}}
.log-time{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--white-dim);margin-top:2px;}}
footer{{border-top:1px solid var(--gold-dim);padding:16px 28px;display:flex;align-items:center;justify-content:space-between;background:var(--b2);}}
.footer-logo{{font-family:'Cinzel',serif;font-size:11px;letter-spacing:.14em;color:var(--gold-dim);}}
.footer-info{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--white-dim);text-align:right;}}
canvas.sparkline{{display:block;}}
@media(max-width:860px){{.layout{{grid-template-columns:1fr;}}.kpi-grid{{grid-template-columns:repeat(2,1fr);}}}}
</style>
</head>
<body>
<header>
  <div class="logo">
    <svg viewBox="0 0 28 28" fill="none"><path d="M14 2L26 7V15C26 21 20 26 14 27C8 26 2 21 2 15V7L14 2Z" stroke="#C9A84C" stroke-width="1.5" fill="rgba(201,168,76,0.08)"/><path d="M9 14L12 17L19 11" stroke="#C9A84C" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
    SENTINELA
  </div>
  <nav>
    <a href="#kpis">KPIs</a>
    <a href="#teatros">Teatros</a>
    <a href="#noticias">Notícias</a>
    <a href="#mercados">Mercados</a>
  </nav>
  <div class="live"><div class="live-dot"></div>AO VIVO</div>
</header>

<div class="banner">
  <span class="badge">NÍVEL {ng}/5 — {label_global}</span>
  <div class="banner-text">{titulo_dia}</div>
  <div class="banner-time">{agora} (Brasília)</div>
</div>

<div class="layout">
<div class="main">

  <!-- SAFEHOUSE -->
  {safehouse_html}

  <!-- KPIs -->
  <div id="kpis">
    <div class="sec-head"><div class="sec-title">Indicadores Globais</div><div class="sec-meta">Atualizado: {agora}</div></div>
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-icon">🛡️</div><div class="kpi-value" style="color:{cor_global}">{ng}/5</div><div class="kpi-label">Nível Global</div><div class="kpi-sub">{label_global}</div></div>
      <div class="kpi-card"><div class="kpi-icon">⚡</div><div class="kpi-value">{teatros_alerta}</div><div class="kpi-label">Teatros em Alerta</div><div class="kpi-sub">de 9 monitorados</div></div>
      <div class="kpi-card"><div class="kpi-icon">📡</div><div class="kpi-value">{total_fontes}</div><div class="kpi-label">Fontes Coletadas</div><div class="kpi-sub">Últimas 24h</div></div>
      <div class="kpi-card"><div class="kpi-icon">📈</div><div class="kpi-value" style="color:{'var(--red)' if prob_conflito>60 else 'var(--yellow)'}">{prob_conflito}%</div><div class="kpi-label">Prob. Escalada</div><div class="kpi-sub">Score composto</div></div>
      <div class="kpi-card"><div class="kpi-icon">🎯</div><div class="kpi-value" style="font-size:14px;padding-top:4px">{teatro_critico[:20]}</div><div class="kpi-label">Teatro Crítico</div><div class="kpi-sub">Maior risco hoje</div></div>
      <div class="kpi-card"><div class="kpi-icon">🌐</div><div class="kpi-value">{"Alto" if teatros_alerta>=5 else "Médio" if teatros_alerta>=3 else "Baixo"}</div><div class="kpi-label">Contágio Regional</div><div class="kpi-sub">{teatros_alerta} teatros interligados</div></div>
      <div class="kpi-card"><div class="kpi-icon">⏱️</div><div class="kpi-value" id="hora-local">—</div><div class="kpi-label">Hora Brasília</div><div class="kpi-sub">Tempo real</div></div>
      <div class="kpi-card"><div class="kpi-icon">🏔️</div><div class="kpi-value" style="color:var(--green);font-size:18px;padding-top:4px">{"ATIVO" if ng>=3 else "OK"}</div><div class="kpi-label">Sapucaí Mirim</div><div class="kpi-sub">{"Protocolo ativo" if ng>=3 else "Posição estratégica"}</div></div>
    </div>
  </div>

  <!-- NARRATIVA -->
  <div class="narrativa-section">
    <div class="sec-title" style="margin-bottom:12px;">Análise do Dia</div>
    <div class="narrativa-text">{narrativa}</div>
    <div class="rec-box"><div class="rec-label">Ação Recomendada Hoje</div>{recomendacao}</div>
  </div>

  <!-- GATILHOS -->
  <div class="gatilhos">
    <div class="sec-head" style="padding:0;border:0;margin-bottom:10px;"><div class="sec-title">Gatilhos Ativos</div></div>
    <ul>{gatilhos_html}</ul>
  </div>

  <!-- TEATROS -->
  <div id="teatros">
    <div class="sec-head"><div class="sec-title">9 Teatros Geopolíticos</div></div>
    {theater_cards}
  </div>

</div><!-- /main -->

<!-- SIDEBAR -->
<div class="sidebar" id="mercados">
  <div class="sec-head" style="background:var(--b2);"><div class="sec-title">Mercados</div><div class="live" style="font-size:9px;"><div class="live-dot" style="width:5px;height:5px;"></div>Tempo real</div></div>
  <div class="market-section">
    <div class="market-title">Bolsas de Valores</div>
    <div class="market-item"><div><div class="market-name">S&P 500</div><div class="market-sub">EUA · SPX</div></div><canvas class="sparkline" id="sp500-c" width="55" height="22"></canvas><div><div class="price-val" id="sp500-v">—</div><div class="price-chg" id="sp500-ch">—</div></div></div>
    <div class="market-item"><div><div class="market-name">IBOVESPA</div><div class="market-sub">Brasil · IBOV</div></div><canvas class="sparkline" id="ibov-c" width="55" height="22"></canvas><div><div class="price-val" id="ibov-v">—</div><div class="price-chg" id="ibov-ch">—</div></div></div>
    <div class="market-item"><div><div class="market-name">DAX</div><div class="market-sub">Alemanha</div></div><canvas class="sparkline" id="dax-c" width="55" height="22"></canvas><div><div class="price-val" id="dax-v">—</div><div class="price-chg" id="dax-ch">—</div></div></div>
    <div class="market-item"><div><div class="market-name">Nikkei 225</div><div class="market-sub">Japão</div></div><canvas class="sparkline" id="nkk-c" width="55" height="22"></canvas><div><div class="price-val" id="nkk-v">—</div><div class="price-chg" id="nkk-ch">—</div></div></div>
    <div class="market-item"><div><div class="market-name">USD/BRL</div><div class="market-sub">Câmbio</div></div><canvas class="sparkline" id="usd-c" width="55" height="22"></canvas><div><div class="price-val" id="usd-v">—</div><div class="price-chg" id="usd-ch">—</div></div></div>

    <div class="market-title" style="margin-top:16px;">Commodities Estratégicas</div>
    <div class="commodity-item"><div class="commodity-name">🛢️ Petróleo WTI</div><div class="commodity-price" id="oil-v">—</div><div class="commodity-chg" id="oil-ch">—</div></div>
    <div class="commodity-item"><div class="commodity-name">🥇 Ouro</div><div class="commodity-price" id="gold-v">—</div><div class="commodity-chg" id="gold-ch">—</div></div>
    <div class="commodity-item"><div class="commodity-name">🌽 Soja</div><div class="commodity-price" id="soy-v">—</div><div class="commodity-chg" id="soy-ch">—</div></div>
    <div class="commodity-item"><div class="commodity-name">⚙️ Minério Ferro</div><div class="commodity-price" id="iron-v">—</div><div class="commodity-chg" id="iron-ch">—</div></div>
    <div class="commodity-item"><div class="commodity-name">🌾 Trigo</div><div class="commodity-price" id="wht-v">—</div><div class="commodity-chg" id="wht-ch">—</div></div>

    <div class="market-title" style="margin-top:16px;">Log de Alertas</div>
    <div class="alert-log">
      <div class="log-item"><div>{"🔴" if ng>=4 else "🟠" if ng>=3 else "🟡"}</div><div><div class="log-text">{titulo_dia[:80]}</div><div class="log-time">{agora}</div></div></div>
      {"".join(f'<div class="log-item"><div>⚡</div><div><div class="log-text">{g}</div><div class="log-time">{agora}</div></div></div>' for g in gatilhos[:3])}
      <div class="log-item"><div>📍</div><div><div class="log-text">{status_sitio[:80]}</div><div class="log-time">{agora}</div></div></div>
      <div class="log-item"><div>🔮</div><div><div class="log-text">{previsao[:80]}</div><div class="log-time">Próx. 24h</div></div></div>
    </div>
  </div>
</div>
</div><!-- /layout -->

<footer>
  <div class="footer-logo">🛡️ SENTINELA v4.0 — Monitor Geopolítico Global</div>
  <div class="footer-info">Dados: NewsAPI + RSS · Análise: Claude AI<br>Atualizado 4× ao dia via GitHub Actions · {agora}</div>
</footer>

<script>
function updateTime(){{const n=new Date();document.getElementById('hora-local').textContent=n.toLocaleTimeString('pt-BR',{{timeZone:'America/Sao_Paulo',hour:'2-digit',minute:'2-digit'}});}}
updateTime();setInterval(updateTime,10000);

async function fetchMarket(sym,vid,cid,cvs){{
  try{{
    const url=`https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=5d`;
    const proxy=`https://api.allorigins.win/get?url=${{encodeURIComponent(url)}}`;
    const r=await fetch(proxy);const data=await r.json();
    const result=JSON.parse(data.contents).chart.result[0];
    const closes=result.indicators.quote[0].close.filter(Boolean);
    const cur=closes[closes.length-1],prev=closes[closes.length-2];
    const chg=((cur-prev)/prev*100).toFixed(2);const up=chg>=0;
    document.getElementById(vid).textContent=cur>10000?cur.toLocaleString('pt-BR',{{maximumFractionDigits:0}}):(sym.includes('BRL')?'R$ ':'')+cur.toFixed(2);
    const el=document.getElementById(cid);el.textContent=(up?'▲':'▼')+Math.abs(chg)+'%';el.className='price-chg '+(up?'up':'down');
    if(cvs){{const c=document.getElementById(cvs);if(c){{const ctx=c.getContext('2d');const mn=Math.min(...closes),mx=Math.max(...closes),rng=mx-mn||1;ctx.clearRect(0,0,55,22);ctx.beginPath();ctx.strokeStyle=up?'#27AE60':'#C0392B';ctx.lineWidth=1.5;closes.forEach((v,i)=>{{const x=(i/(closes.length-1))*53+1,y=20-((v-mn)/rng*18);i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);}});ctx.stroke();}}}}
  }}catch(e){{}}
}}
async function fetchCom(sym,vid,cid,pfx='$'){{
  try{{
    const url=`https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=2d`;
    const proxy=`https://api.allorigins.win/get?url=${{encodeURIComponent(url)}}`;
    const r=await fetch(proxy);const data=await r.json();
    const result=JSON.parse(data.contents).chart.result[0];
    const closes=result.indicators.quote[0].close.filter(Boolean);
    const cur=closes[closes.length-1],prev=closes[closes.length-2]||cur;
    const chg=((cur-prev)/prev*100).toFixed(2);const up=chg>=0;
    document.getElementById(vid).textContent=pfx+cur.toFixed(2);
    const el=document.getElementById(cid);el.textContent=(up?'▲':'▼')+Math.abs(chg)+'%';el.className='commodity-chg '+(up?'up':'down');
  }}catch(e){{}}
}}
fetchMarket('^GSPC','sp500-v','sp500-ch','sp500-c');
fetchMarket('^BVSP','ibov-v','ibov-ch','ibov-c');
fetchMarket('^GDAXI','dax-v','dax-ch','dax-c');
fetchMarket('^N225','nkk-v','nkk-ch','nkk-c');
fetchMarket('BRL=X','usd-v','usd-ch','usd-c');
fetchCom('CL=F','oil-v','oil-ch');fetchCom('GC=F','gold-v','gold-ch');
fetchCom('ZS=F','soy-v','soy-ch');fetchCom('TIO=F','iron-v','iron-ch');fetchCom('ZW=F','wht-v','wht-ch');
</script>
</body></html>"""
    return html

# ══════════════════════════════════════════════════════════════
# GIT PUSH AUTOMATICO
# ══════════════════════════════════════════════════════════════
def publicar_portal(html, agora):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("  index.html gerado com sucesso")

        token = GITHUB_TOKEN
        if not token:
            print("  AVISO: GITHUB_TOKEN nao configurado — portal nao publicado")
            return False

        # Configura git
        subprocess.run(["git","config","user.email","sentinela@geopolitico.br"],capture_output=True)
        subprocess.run(["git","config","user.name","Sentinela Bot"],capture_output=True)

        # Atualiza remote com token
        subprocess.run(["git","remote","set-url","origin",
            f"https://x-access-token:{token}@github.com/Hosemiro2/sentinela-geo.git"],capture_output=True)

        subprocess.run(["git","add","index.html"],capture_output=True)
        result = subprocess.run(["git","commit","-m",f"Portal atualizado: {agora}"],capture_output=True,text=True)

        if "nothing to commit" in result.stdout:
            print("  Portal: sem mudancas")
            return True

        push = subprocess.run(["git","push"],capture_output=True,text=True)
        if push.returncode == 0:
            print(f"  Portal publicado: hosemiro2.github.io/sentinela-geo")
            return True
        else:
            print(f"  Erro no push: {push.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  Erro ao publicar portal: {e}")
        return False

# ══════════════════════════════════════════════════════════════
# TELEGRAM
# ══════════════════════════════════════════════════════════════
def telegram(texto):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("  AVISO: Telegram nao configurado")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    partes = [texto[i:i+4000] for i in range(0,len(texto),4000)]
    ok = True
    for i,parte in enumerate(partes):
        prefixo = f"[{i+1}/{len(partes)}]\n" if len(partes)>1 else ""
        try:
            r = requests.post(url,json={"chat_id":TELEGRAM_CHAT_ID,"text":prefixo+parte,"parse_mode":"HTML"},timeout=15)
            if r.status_code!=200:
                print(f"  Telegram erro {r.status_code}: {r.text[:100]}")
                ok=False
        except Exception as e:
            print(f"  Telegram excecao: {e}")
            ok=False
    return ok

def formatar_relatorio(relatorio, resultados, agora):
    ng = relatorio.get("nivel_global",1)
    linhas = ""
    for tid,d in resultados.items():
        n=d["analise"]["nivel"]
        linhas += f"{EMOJIS[n]} {TEATROS[tid]['nome']}: {n}/5 - {d['analise']['resumo']}\n"
    gt = relatorio.get("gatilhos_ativos",[])
    gt_txt = "\n".join(f"- {g}" for g in gt) if gt else "Nenhum gatilho ativo"
    safehouse = "ATENCAO: ACIONE PROTOCOLO - mova familia para Sapucai Mirim!" if ng>=3 else "Sapucai Mirim: STATUS OK"
    return (f"SENTINELA - RELATORIO DIARIO\nData: {agora}\n{'='*36}\n\n"
            f"{EMOJIS[ng]} NIVEL GLOBAL: {ng}/5 - {LABELS[ng]}\n"
            f"MANCHETE: {relatorio.get('titulo_do_dia','')}\n\n"
            f"SITUACAO:\n{relatorio.get('narrativa','')}\n\n"
            f"9 TEATROS:\n{linhas}\nGATILHOS:\n{gt_txt}\n\n"
            f"MAIS CRITICO: {relatorio.get('teatro_mais_critico','')}\n\n"
            f"ACAO HOJE:\n{relatorio.get('recomendacao_familia','')}\n\n"
            f"PROXIMAS 24H:\n{relatorio.get('previsao_24h','')}\n\n"
            f"SITIO: {relatorio.get('status_sitio','')}\n\n"
            f"{'='*36}\n{safehouse}\n\n"
            f"🌐 Portal: hosemiro2.github.io/sentinela-geo")

# ══════════════════════════════════════════════════════════════
# COLETA PRINCIPAL
# ══════════════════════════════════════════════════════════════
HORAS_COLETA = {8,13,18}
HORA_RELATORIO = 22

def ciclo_coleta(agora):
    resultados = {}
    for tid,teatro in TEATROS.items():
        print(f"\n  [{teatro['nome']}]")
        noticias = coletar_noticias(tid,teatro)
        print(f"    {len(noticias)} noticias coletadas")
        analise = analisar_teatro(tid,teatro,noticias)
        print(f"    Nivel {analise['nivel']}/5 | {analise['tendencia']} | {analise['resumo'][:50]}...")
        resultados[tid] = {"analise":analise,"noticias":noticias}
    with open("log_sentinela.txt","a",encoding="utf-8") as f:
        niveis = " | ".join(f"{TEATROS[tid]['nome'].split()[0][:6]} {d['analise']['nivel']}" for tid,d in resultados.items())
        f.write(f"[{agora}] {niveis}\n")
    with open("snapshot_atual.json","w",encoding="utf-8") as f:
        json.dump({"timestamp":agora,"teatros":{tid:{"nivel":d["analise"]["nivel"],"resumo":d["analise"]["resumo"],"tendencia":d["analise"]["tendencia"]} for tid,d in resultados.items()}},f,ensure_ascii=False,indent=2)
    return resultados

def main():
    from datetime import timezone, timedelta
    tz_brasil = timezone(timedelta(hours=-3))
    agora_dt = datetime.now(tz_brasil)
    agora = agora_dt.strftime("%d/%m/%Y %H:%M")
    hora = agora_dt.hour
    print(f"\n{'='*55}")
    print(f"  SENTINELA v4.0 - {agora} (horario Brasilia)")
    # Detecta se foi acionado manualmente (GitHub Actions workflow_dispatch)
    manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    if hora not in HORAS_COLETA and hora != HORA_RELATORIO and not manual:
        print(f"  Hora {hora}h: fora do agendamento. Encerrando.")
        print(f"  Proximas execucoes: 08h, 13h, 18h (coleta) | 22h (relatorio)")
        print(f"{'='*55}\n")
        return
    modo = "RELATORIO NOTURNO 22h" if (hora==HORA_RELATORIO or manual) else f"COLETA SILENCIOSA {hora}h"
    print(f"  Modo: {modo}")
    print(f"{'='*55}")
    resultados = ciclo_coleta(agora)
    relatorio = None
    if hora == HORA_RELATORIO or manual:
        print("\n  Gerando relatorio consolidado...")
        relatorio = gerar_relatorio(resultados)
        if relatorio:
            msg = formatar_relatorio(relatorio,resultados,agora)
            ok = telegram(msg)
            print(f"  Telegram: {'OK' if ok else 'FALHOU'}")
            with open(f"relatorio_{agora_dt.strftime('%Y%m%d')}.txt","w",encoding="utf-8") as f:
                f.write(msg)
        else:
            print("  FALHA ao gerar relatorio")
    else:
        niveis_v = [d["analise"]["nivel"] for d in resultados.values()]
        print(f"\n  Coleta concluida. Nivel maximo: {EMOJIS[max(niveis_v)]} {max(niveis_v)}/5")

    # SEMPRE gera e publica o portal (em todos os horarios ativos)
    print("\n  Gerando portal web...")
    html = gerar_html(resultados, relatorio, agora)
    publicar_portal(html, agora)

    print(f"\n{'='*55}")
    print(f"  CONCLUIDO - {agora}")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()

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
GITHUB_TOKEN      = os.environ.get("GIT_TOKEN") or os.getenv("GIT_TOKEN")

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
    CORES_MAP = {1:"#287848",2:"#B89000",3:"#C86820",4:"#B83030",5:"#7B0000"}
    LABELS_MAP = {1:"NORMAL",2:"ATENÇÃO",3:"ALERTA",4:"CRÍTICO",5:"CATÁSTROFE"}
    cor_global = CORES_MAP[ng]
    label_global = LABELS_MAP[ng]
    titulo_dia   = relatorio.get("titulo_do_dia","") if relatorio else ""
    narrativa    = relatorio.get("narrativa","") if relatorio else ""
    recomendacao = relatorio.get("recomendacao_familia","") if relatorio else ""
    previsao     = relatorio.get("previsao_24h","") if relatorio else ""
    status_sitio = relatorio.get("status_sitio","") if relatorio else ""
    teatro_critico = relatorio.get("teatro_mais_critico","") if relatorio else ""
    gatilhos     = relatorio.get("gatilhos_ativos",[]) if relatorio else []
    safehouse_alert = ng >= 3
    teatros_alerta  = sum(1 for d in resultados.values() if d["analise"]["nivel"] >= 3)
    total_fontes    = sum(len(d.get("noticias",[])) for d in resultados.values())
    prob_conflito   = min(95, ng * 15 + teatros_alerta * 5)

    # ── Marcadores do mapa ──────────────────────────────────────────────────
    MAP_POS = {
        "brasil_eua":    ("15%","70%"),
        "russia_otan":   ("54%","22%"),
        "europa":        ("47%","18%"),
        "china_taiwan":  ("82%","38%"),
        "indo_pacifico": ("88%","30%"),
        "oriente_medio": ("60%","40%"),
        "america_latina":("16%","58%"),
        "africa":        ("47%","55%"),
        "cyber":         ("50%","8%"),
    }
    THEATER_ICONS = {
        "brasil_eua":"🇧🇷","russia_otan":"🇷🇺","europa":"🇪🇺",
        "china_taiwan":"🇨🇳","indo_pacifico":"🌏","oriente_medio":"🕌",
        "america_latina":"🌎","africa":"🌍","cyber":"🌐",
    }
    map_markers = ""
    for tid, d in resultados.items():
        if tid not in MAP_POS: continue
        n = d["analise"]["nivel"]
        c = CORES_MAP[n]
        lx, ly = MAP_POS[tid]
        nome = TEATROS[tid]["nome"]
        icon = THEATER_ICONS.get(tid, "●")
        map_markers += (
            '<div class="t-marker" style="left:' + lx + ';top:' + ly + ';color:' + c + '">'
            '<div class="t-ring"><div class="t-dot"></div></div>'
            '<div class="t-tooltip">' + icon + ' ' + nome[:30] + ' NV ' + str(n) + '</div>'
            '</div>'
        )

    # ── Cards dos teatros ───────────────────────────────────────────────────
    TC_CLASS = {1:"tc-l1",2:"tc-l2",3:"tc-l3",4:"tc-l4",5:"tc-l4"}
    theater_cards = ""
    for tid, d in resultados.items():
        a = d["analise"]
        n = a["nivel"]
        cor = CORES_MAP[n]
        icon = THEATER_ICONS.get(tid,"●")
        nome = TEATROS[tid]["nome"]
        tendencia_icon = "↑" if a["tendencia"]=="deteriorando" else ("↓" if a["tendencia"]=="melhorando" else "→")
        noticias_html = ""
        for noticia in d.get("noticias",[])[:3]:
            url    = noticia.get("url","#")
            fonte  = noticia.get("fonte","")
            titulo_n = noticia.get("titulo","")[:90]
            noticias_html += (
                '<div class="tc-news-item">'
                '<div class="tc-news-bar" style="background:' + cor + '"></div>'
                '<div><span class="tc-news-src">' + fonte + '</span>'
                '<a href="' + url + '" target="_blank" class="tc-news-title">' + titulo_n + '</a></div>'
                '</div>'
            )
        tc_cls = TC_CLASS.get(n, 'tc-l1')
        resumo = a.get("resumo","").replace('"','&quot;')
        tend_cap = a["tendencia"].capitalize()
        nf_count = len(d.get("noticias",[]))
        peso = TEATROS[tid]["peso"]
        news_block = ('<div class="tc-news">' + noticias_html + '</div>') if noticias_html else ""
        theater_cards += (
            '<div class="tc ' + tc_cls + '" data-num="' + str(n) + '">'
            '<div class="tc-header">'
            '<div class="tc-name">' + icon + ' ' + nome + '</div>'
            '<div class="tc-score" style="color:' + cor + '">' + str(n) + '</div>'
            '</div>'
            '<div class="tc-resumo">' + resumo + '</div>'
            '<div class="tc-meta">'
            '<span class="tc-tag">' + tendencia_icon + ' ' + tend_cap + '</span>'
            '<span class="tc-tag">' + str(nf_count) + ' fontes</span>'
            '<span class="tc-tag">Peso ' + str(peso) + '</span>'
            '</div>'
            + news_block +
            '</div>'
        )

    # ── Gatilhos ─────────────────────────────────────────────────────────────
    gatilhos_html = "".join(f'<div class="log-row"><div class="log-icon">⚡</div><div class="log-body"><div class="log-text">{g}</div><div class="log-time">{agora}</div></div></div>' for g in gatilhos) if gatilhos else '<div class="log-row"><div class="log-icon">✅</div><div class="log-body"><div class="log-text">Nenhum gatilho ativo</div></div></div>'

    # ── Safehouse ─────────────────────────────────────────────────────────────
    if safehouse_alert:
        sh_class = "safehouse safehouse-danger"
        sh_text  = "🔴 PROTOCOLO ATIVO — MOVA FAMÍLIA PARA SAPUCAÍ MIRIM IMEDIATAMENTE"
    else:
        sh_class = "safehouse safehouse-ok"
        sh_text  = f"🟢 SAPUCAÍ MIRIM: STATUS OK — {status_sitio}"

    # ── Cor RGB para gradiente ────────────────────────────────────────────────
    h = cor_global.lstrip("#")
    rgb = f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

    # ════════════════════════════════════════════════════════════════════════════
    #  HTML PREMIUM
    # ════════════════════════════════════════════════════════════════════════════
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<title>SENTINELA — Monitor Geopolítico Global</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=Cinzel:wght@400;600;900&family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --gold:#C9A84C;--gold-light:#E8C97A;--gold-dim:#6B5420;--gold-glow:rgba(201,168,76,0.15);
  --black:#040404;--b1:#080808;--b2:#0C0C0C;--b3:#121212;--b4:#181818;--b5:#202020;--b6:#2A2A2A;
  --cream:#F0E8D0;--cream-dim:#9A9080;
  --red:#B83030;--orange:#C86820;--yellow:#B89000;--green:#287848;
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--black);color:var(--cream);font-family:'EB Garamond',serif;font-size:16px;line-height:1.65;overflow-x:hidden;cursor:crosshair;}}
body::before{{content:'';position:fixed;inset:0;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");pointer-events:none;z-index:9999;opacity:0.5;}}
::-webkit-scrollbar{{width:4px;}}::-webkit-scrollbar-track{{background:var(--b1);}}::-webkit-scrollbar-thumb{{background:var(--gold-dim);}}
/* HEADER */
header{{position:sticky;top:0;z-index:200;background:rgba(4,4,4,0.97);backdrop-filter:blur(20px);border-bottom:1px solid var(--gold-dim);height:56px;display:flex;align-items:center;padding:0 32px;gap:32px;}}
.logo{{font-family:'Cinzel',serif;font-weight:900;font-size:18px;letter-spacing:0.25em;color:var(--gold);display:flex;align-items:center;gap:10px;white-space:nowrap;}}
.logo-emblem{{width:30px;height:30px;border:1.5px solid var(--gold);display:flex;align-items:center;justify-content:center;clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);background:rgba(201,168,76,0.08);font-size:13px;animation:emblem-glow 4s ease-in-out infinite;}}
@keyframes emblem-glow{{0%,100%{{box-shadow:0 0 0 rgba(201,168,76,0);}}50%{{box-shadow:0 0 12px rgba(201,168,76,0.3);}}}}
nav{{display:flex;flex:1;justify-content:center;}}
nav a{{font-family:'Cinzel',serif;font-size:9px;letter-spacing:0.18em;color:var(--cream-dim);text-decoration:none;padding:6px 16px;border:1px solid transparent;transition:all 0.25s;text-transform:uppercase;}}
nav a:hover{{color:var(--gold);border-color:var(--gold-dim);background:var(--gold-glow);}}
.live-pill{{display:flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:0.1em;color:var(--gold);border:1px solid var(--gold-dim);padding:4px 10px;}}
.pulse{{width:5px;height:5px;border-radius:50%;background:var(--gold);animation:pulse-dot 2s infinite;}}
@keyframes pulse-dot{{0%,100%{{opacity:1;transform:scale(1);}}50%{{opacity:0.3;transform:scale(0.7);}}}}
/* TICKER */
.ticker{{background:linear-gradient(90deg,rgba({rgb},0.18),rgba(201,168,76,0.04),rgba({rgb},0.18));border-bottom:1px solid rgba({rgb},0.35);padding:0 32px;height:40px;display:flex;align-items:center;gap:20px;overflow:hidden;}}
.ticker-label{{font-family:'Cinzel',serif;font-size:9px;letter-spacing:0.15em;color:{cor_global};white-space:nowrap;display:flex;align-items:center;gap:8px;border-right:1px solid rgba({rgb},0.3);padding-right:20px;}}
.ticker-badge{{background:{cor_global};color:#000;font-weight:700;padding:2px 8px;font-size:9px;letter-spacing:0.1em;}}
.ticker-text{{font-style:italic;font-size:14px;color:var(--cream);opacity:0.9;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ticker-time{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--cream-dim);white-space:nowrap;}}
/* HERO */
.hero{{display:grid;grid-template-columns:1fr 340px;border-bottom:1px solid var(--b5);}}
.map-panel{{position:relative;background:var(--b1);border-right:1px solid var(--b5);padding:24px 28px;overflow:hidden;}}
.map-panel-title{{font-family:'Cinzel',serif;font-size:9px;letter-spacing:0.2em;color:var(--gold);text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:10px;}}
.map-panel-title::before{{content:'';width:20px;height:1px;background:var(--gold);}}
.world-map-wrap{{position:relative;width:100%;height:320px;}}
#leafmap{{width:100%;height:100%;background:#080808;}}.leaflet-tile-pane{{filter:brightness(0.35) saturate(0.2);}}
/* MAP MARKERS */
.t-marker{{position:absolute;transform:translate(-50%,-50%);cursor:pointer;}}
.t-ring{{width:16px;height:16px;border-radius:50%;border:2px solid currentColor;display:flex;align-items:center;justify-content:center;position:relative;animation:marker-pulse 3s ease-in-out infinite;}}
.t-ring::before{{content:'';position:absolute;width:26px;height:26px;border-radius:50%;border:1px solid currentColor;opacity:0;animation:marker-ripple 3s ease-out infinite;}}
.t-ring::after{{content:'';position:absolute;width:38px;height:38px;border-radius:50%;border:1px solid currentColor;opacity:0;animation:marker-ripple 3s ease-out infinite 0.5s;}}
.t-dot{{width:6px;height:6px;border-radius:50%;background:currentColor;}}
@keyframes marker-pulse{{0%,100%{{transform:scale(1);}}50%{{transform:scale(1.15);}}}}
@keyframes marker-ripple{{0%{{transform:scale(0.4);opacity:0.8;}}100%{{transform:scale(1.6);opacity:0;}}}}
.t-tooltip{{position:absolute;bottom:22px;left:50%;transform:translateX(-50%);background:var(--b3);border:1px solid var(--gold-dim);padding:5px 10px;font-family:'JetBrains Mono',monospace;font-size:8px;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity 0.2s;z-index:10;letter-spacing:0.05em;color:var(--cream);}}
.t-marker:hover .t-tooltip{{opacity:1;}}
.map-legend{{position:absolute;bottom:20px;right:20px;display:flex;flex-direction:column;gap:4px;}}
.legend-item{{display:flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:0.05em;}}
.legend-dot{{width:8px;height:8px;border-radius:50%;border:1.5px solid;}}
/* STATUS PANEL */
.status-panel{{padding:24px 20px;display:flex;flex-direction:column;gap:0;}}
.status-title{{font-family:'Cinzel',serif;font-size:9px;letter-spacing:0.2em;color:var(--gold);text-transform:uppercase;margin-bottom:20px;display:flex;align-items:center;gap:8px;}}
.status-title::before{{content:'';width:16px;height:1px;background:var(--gold);}}
.global-level-display{{text-align:center;padding:24px 0;border:1px solid var(--b5);margin-bottom:16px;background:var(--b2);position:relative;overflow:hidden;}}
.global-level-display::before{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at center,rgba({rgb},0.08) 0%,transparent 70%);pointer-events:none;}}
.gl-num{{font-family:'Cinzel Decorative',serif;font-size:64px;line-height:1;color:{cor_global};text-shadow:0 0 40px rgba({rgb},0.4);}}
.gl-label{{font-family:'Cinzel',serif;font-size:10px;letter-spacing:0.25em;color:{cor_global};margin-top:4px;opacity:0.8;}}
.gl-sublabel{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--cream-dim);margin-top:8px;}}
.kpi-pills{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;}}
.kpi-pill{{background:var(--b3);border:1px solid var(--b5);padding:10px 12px;transition:border-color 0.2s;}}
.kpi-pill:hover{{border-color:var(--gold-dim);}}
.kpi-pill-val{{font-family:'Cinzel',serif;font-size:20px;color:var(--gold);line-height:1;}}
.kpi-pill-lbl{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--cream-dim);letter-spacing:0.08em;margin-top:4px;text-transform:uppercase;}}
.safehouse{{padding:14px 16px;font-family:'Cinzel',serif;font-size:9px;letter-spacing:0.1em;text-align:center;border:1px solid;text-transform:uppercase;}}
.safehouse-danger{{background:rgba(184,48,48,0.12);border-color:rgba(184,48,48,0.5);color:#E05050;animation:danger-pulse 2.5s infinite;}}
.safehouse-ok{{background:rgba(40,120,72,0.1);border-color:rgba(40,120,72,0.4);color:#50B880;}}
@keyframes danger-pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.7;}}}}
/* ANALYSIS */
.analysis-strip{{background:var(--b2);border-bottom:1px solid var(--b5);padding:24px 32px;display:grid;grid-template-columns:1fr 1fr;gap:24px;}}
.analysis-block{{border-left:2px solid var(--gold-dim);padding-left:16px;}}
.analysis-label{{font-family:'Cinzel',serif;font-size:8px;letter-spacing:0.2em;color:var(--gold);text-transform:uppercase;margin-bottom:8px;}}
.analysis-text{{font-size:15px;font-style:italic;line-height:1.6;color:var(--cream);opacity:0.9;}}
.rec-box{{background:var(--b3);border-left:3px solid var(--gold);padding:12px 16px;margin-top:12px;}}
.rec-label{{font-family:'Cinzel',serif;font-size:8px;letter-spacing:0.15em;color:var(--gold);margin-bottom:6px;text-transform:uppercase;}}
/* THEATERS */
.section-header{{padding:16px 32px;border-bottom:1px solid var(--b5);display:flex;align-items:center;justify-content:space-between;}}
.section-title{{font-family:'Cinzel',serif;font-size:9px;letter-spacing:0.2em;color:var(--gold);text-transform:uppercase;display:flex;align-items:center;gap:10px;}}
.section-title::before{{content:'';width:20px;height:1px;background:var(--gold);}}
.section-meta{{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--cream-dim);}}
.theaters-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--b5);}}
.tc{{background:var(--black);padding:20px 24px;border-left:3px solid transparent;transition:background 0.2s;position:relative;overflow:hidden;}}
.tc::after{{content:attr(data-num);position:absolute;right:-10px;bottom:-20px;font-family:'Cinzel Decorative',serif;font-size:80px;font-weight:700;opacity:0.04;line-height:1;pointer-events:none;}}
.tc:hover{{background:var(--b2);}}
.tc-l4{{border-left-color:var(--red);}}
.tc-l3{{border-left-color:var(--orange);}}
.tc-l2{{border-left-color:var(--yellow);}}
.tc-l1{{border-left-color:var(--green);}}
.tc-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}}
.tc-name{{font-family:'Cinzel',serif;font-size:8px;letter-spacing:0.12em;color:var(--cream-dim);text-transform:uppercase;line-height:1.4;flex:1;padding-right:8px;}}
.tc-score{{font-family:'Cinzel Decorative',serif;font-size:32px;line-height:1;font-weight:700;}}
.tc-resumo{{font-size:13px;font-style:italic;color:var(--cream);opacity:0.75;line-height:1.45;margin-bottom:10px;}}
.tc-meta{{display:flex;gap:8px;flex-wrap:wrap;}}
.tc-tag{{font-family:'JetBrains Mono',monospace;font-size:8px;padding:2px 7px;border:1px solid var(--b6);color:var(--cream-dim);letter-spacing:0.05em;}}
.tc-news{{margin-top:12px;border-top:1px solid var(--b4);padding-top:10px;}}
.tc-news-item{{display:flex;gap:8px;margin-bottom:7px;}}
.tc-news-bar{{width:2px;border-radius:1px;flex-shrink:0;margin-top:3px;min-height:14px;}}
.tc-news-src{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--cream-dim);display:block;margin-bottom:1px;}}
.tc-news-title{{font-size:11px;color:var(--cream);text-decoration:none;line-height:1.35;display:block;opacity:0.8;transition:opacity 0.15s;}}
.tc-news-title:hover{{opacity:1;color:var(--gold-light);}}
/* BOTTOM GRID */
.bottom-grid{{display:grid;grid-template-columns:320px 1fr;border-bottom:1px solid var(--b5);min-height:500px;}}
.markets-panel{{background:var(--b1);border-right:1px solid var(--b5);overflow-y:auto;}}
.mkts-section{{padding:20px 20px 16px;}}
.mkts-title{{font-family:'Cinzel',serif;font-size:8px;letter-spacing:0.18em;color:var(--gold);text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:8px;}}
.mkts-title::before{{content:'';width:12px;height:1px;background:var(--gold);}}
.mkt-row{{padding:11px 0;border-bottom:1px solid var(--b3);display:grid;grid-template-columns:1fr 50px auto;gap:8px;align-items:center;}}
.mkt-name{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--cream);}}
.mkt-sub{{font-size:10px;color:var(--cream-dim);margin-top:1px;}}
.mkt-price{{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--cream);text-align:right;}}
.mkt-chg{{font-family:'JetBrains Mono',monospace;font-size:9px;margin-top:1px;text-align:right;}}
.up{{color:#50B878;}}.dn{{color:#C85050;}}
.com-row{{padding:9px 0;border-bottom:1px solid var(--b3);display:grid;grid-template-columns:1fr auto auto;gap:8px;align-items:center;}}
.com-name{{font-size:13px;}}
.com-price{{font-family:'JetBrains Mono',monospace;font-size:11px;text-align:right;}}
.com-chg{{font-family:'JetBrains Mono',monospace;font-size:9px;text-align:right;min-width:46px;}}
/* LOG */
.log-row{{padding:9px 0;border-bottom:1px solid var(--b3);display:flex;gap:10px;align-items:flex-start;}}
.log-icon{{font-size:13px;flex-shrink:0;}}
.log-text{{font-size:12px;line-height:1.4;}}
.log-time{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--cream-dim);margin-top:2px;}}
/* NEWS FEED */
.news-panel{{overflow-y:auto;}}
.news-filters{{padding:12px 24px;border-bottom:1px solid var(--b5);display:flex;gap:6px;flex-wrap:wrap;}}
.filter-btn{{font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:0.08em;padding:4px 10px;border:1px solid var(--b5);background:transparent;color:var(--cream-dim);cursor:pointer;transition:all 0.15s;text-transform:uppercase;}}
.filter-btn:hover,.filter-btn.active{{border-color:var(--gold-dim);color:var(--gold);background:var(--gold-glow);}}
.news-card{{padding:16px 24px;border-bottom:1px solid var(--b3);display:grid;grid-template-columns:3px 1fr;gap:14px;transition:background 0.15s;cursor:pointer;}}
.news-card:hover{{background:var(--b2);}}
.news-accent{{border-radius:1px;}}
.news-meta{{display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap;}}
.news-theater{{font-family:'Cinzel',serif;font-size:8px;letter-spacing:0.12em;color:var(--gold);text-transform:uppercase;}}
.news-source{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--cream-dim);padding:1px 6px;border:1px solid var(--b5);}}
.news-time{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--b6);margin-left:auto;}}
.news-title{{font-size:15px;color:var(--cream);line-height:1.4;margin-bottom:4px;}}
.news-summary{{font-size:12px;font-style:italic;color:var(--cream-dim);line-height:1.4;}}
.news-link{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--gold-dim);text-decoration:none;display:inline-flex;align-items:center;gap:4px;margin-top:6px;transition:color 0.15s;}}
.news-link:hover{{color:var(--gold);}}
/* FOOTER */
footer{{border-top:1px solid var(--gold-dim);background:var(--b2);padding:20px 32px;display:flex;align-items:center;justify-content:space-between;}}
.footer-brand{{font-family:'Cinzel',serif;font-size:10px;letter-spacing:0.18em;color:var(--gold-dim);}}
.footer-info{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--cream-dim);text-align:right;line-height:1.6;}}
/* ANIMATIONS */
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px);}}to{{opacity:1;transform:translateY(0);}}}}
.tc{{animation:fadeIn 0.4s ease both;}}
.tc:nth-child(1){{animation-delay:.05s}}.tc:nth-child(2){{animation-delay:.1s}}.tc:nth-child(3){{animation-delay:.15s}}
.tc:nth-child(4){{animation-delay:.2s}}.tc:nth-child(5){{animation-delay:.25s}}.tc:nth-child(6){{animation-delay:.3s}}
.tc:nth-child(7){{animation-delay:.35s}}.tc:nth-child(8){{animation-delay:.4s}}.tc:nth-child(9){{animation-delay:.45s}}
@media(max-width:1100px){{.hero{{grid-template-columns:1fr;}}.theaters-grid{{grid-template-columns:repeat(2,1fr);}}.bottom-grid{{grid-template-columns:1fr;}}}}
@media(max-width:700px){{.theaters-grid{{grid-template-columns:1fr;}}.analysis-strip{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<header>
  <div class="logo"><div class="logo-emblem">🛡</div>SENTINELA</div>
  <nav>
    <a href="#mapa">Mapa</a><a href="#teatros">Teatros</a>
    <a href="#noticias">Notícias</a><a href="#mercados">Mercados</a>
  </nav>
  <div style="display:flex;align-items:center;gap:16px;">
    <div class="live-pill"><div class="pulse"></div>AO VIVO</div>
    <span style="font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--cream-dim)" id="hdr-t">—</span>
  </div>
</header>
<div class="ticker">
  <div class="ticker-label"><span class="ticker-badge">NÍV {ng}/5</span> {label_global}</div>
  <div class="ticker-text">{titulo_dia}</div>
  <div class="ticker-time">{agora} (Brasília)</div>
</div>
<!-- HERO -->
<div class="hero" id="mapa">
  <div class="map-panel">
    <div class="map-panel-title">Mapa de Alertas Geopolíticos</div>
    <div class="world-map-wrap" style="height:320px;position:relative;">
      <div id="leafmap" style="width:100%;height:100%;border-radius:0;"></div>
      <div class="map-legend">      </div>
    </div>
  </div>
  <!-- STATUS -->
  <div class="status-panel">
    <div class="status-title">Status Global</div>
    <div class="global-level-display">
      <div class="gl-num">{ng}</div>
      <div class="gl-label">{label_global}</div>
      <div class="gl-sublabel" id="upd-t">Atualizado: {agora}</div>
    </div>
    <div class="kpi-pills">
      <div class="kpi-pill">
        <div class="kpi-pill-val" style="color:{cor_global}">{teatros_alerta}</div>
        <div class="kpi-pill-lbl">Teatros em Alerta</div>
      </div>
      <div class="kpi-pill">
        <div class="kpi-pill-val">{total_fontes}</div>
        <div class="kpi-pill-lbl">Fontes Coletadas</div>
      </div>
      <div class="kpi-pill">
        <div class="kpi-pill-val" style="color:{'var(--red)' if prob_conflito>60 else 'var(--yellow)'};font-size:16px">{prob_conflito}%</div>
        <div class="kpi-pill-lbl">Prob. Escalada</div>
      </div>
      <div class="kpi-pill">
        <div class="kpi-pill-val" id="hora-p" style="font-size:14px;padding-top:3px">—</div>
        <div class="kpi-pill-lbl">Hora Brasília</div>
      </div>
    </div>
    <div class="{sh_class}">{sh_text}</div>
  </div>
</div>
<!-- ANALYSIS -->
<div class="analysis-strip">
  <div class="analysis-block">
    <div class="analysis-label">Análise do Dia</div>
    <div class="analysis-text">{narrativa}</div>
  </div>
  <div class="analysis-block">
    <div class="analysis-label">Ação Recomendada</div>
    <div class="analysis-text">{previsao}</div>
    <div class="rec-box">
      <div class="rec-label">Para Sua Família</div>
      <div style="font-size:14px">{recomendacao}</div>
    </div>
  </div>
</div>
<!-- THEATERS -->
<div id="teatros" style="border-bottom:1px solid var(--b5)">
  <div class="section-header">
    <div class="section-title">9 Teatros Geopolíticos</div>
    <div class="section-meta">Claude AI · {agora}</div>
  </div>
  <div class="theaters-grid">{theater_cards}</div>
</div>
<!-- BOTTOM GRID -->
<div class="bottom-grid">
  <div class="markets-panel" id="mercados">
    <div class="section-header" style="background:var(--b1)">
      <div class="section-title">Mercados</div>
      <div class="live-pill" style="font-size:8px"><div class="pulse" style="width:4px;height:4px"></div>Tempo real</div>
    </div>
    <div class="mkts-section">
      <div class="mkts-title">Bolsas de Valores</div>
      <div class="mkt-row"><div><div class="mkt-name">S&P 500</div><div class="mkt-sub">EUA · SPX</div></div><canvas id="c-sp" width="50" height="20"></canvas><div style="text-align:right"><div class="mkt-price" id="v-sp">—</div><div class="mkt-chg" id="ch-sp">—</div></div></div>
      <div class="mkt-row"><div><div class="mkt-name">IBOVESPA</div><div class="mkt-sub">Brasil</div></div><canvas id="c-ib" width="50" height="20"></canvas><div style="text-align:right"><div class="mkt-price" id="v-ib">—</div><div class="mkt-chg" id="ch-ib">—</div></div></div>
      <div class="mkt-row"><div><div class="mkt-name">DAX</div><div class="mkt-sub">Alemanha</div></div><canvas id="c-dx" width="50" height="20"></canvas><div style="text-align:right"><div class="mkt-price" id="v-dx">—</div><div class="mkt-chg" id="ch-dx">—</div></div></div>
      <div class="mkt-row"><div><div class="mkt-name">Nikkei 225</div><div class="mkt-sub">Japão</div></div><canvas id="c-nk" width="50" height="20"></canvas><div style="text-align:right"><div class="mkt-price" id="v-nk">—</div><div class="mkt-chg" id="ch-nk">—</div></div></div>
      <div class="mkt-row"><div><div class="mkt-name">USD/BRL</div><div class="mkt-sub">Câmbio</div></div><canvas id="c-us" width="50" height="20"></canvas><div style="text-align:right"><div class="mkt-price" id="v-us">—</div><div class="mkt-chg" id="ch-us">—</div></div></div>
      <div class="mkts-title" style="margin-top:20px">Commodities</div>
      <div class="com-row"><div class="com-name">🛢️ Petróleo WTI</div><div class="com-price" id="v-oil">—</div><div class="com-chg" id="ch-oil">—</div></div>
      <div class="com-row"><div class="com-name">🥇 Ouro</div><div class="com-price" id="v-gld">—</div><div class="com-chg" id="ch-gld">—</div></div>
      <div class="com-row"><div class="com-name">🌽 Soja</div><div class="com-price" id="v-soy">—</div><div class="com-chg" id="ch-soy">—</div></div>
      <div class="com-row"><div class="com-name">⚙️ Minério Ferro</div><div class="com-price" id="v-irf">—</div><div class="com-chg" id="ch-irf">—</div></div>
      <div class="com-row"><div class="com-name">🌾 Trigo</div><div class="com-price" id="v-wht">—</div><div class="com-chg" id="ch-wht">—</div></div>
      <div class="mkts-title" style="margin-top:20px">Log de Alertas</div>
      <div style="padding-bottom:16px">
        {gatilhos_html}
        <div class="log-row"><div class="log-icon">📍</div><div class="log-body"><div class="log-text">{status_sitio[:90]}</div><div class="log-time">{agora}</div></div></div>
      </div>
    </div>
  </div>
  <!-- NEWS FEED -->
  <div class="news-panel" id="noticias">
    <div class="section-header">
      <div class="section-title">Feed de Notícias</div>
      <div class="section-meta">Fontes verificadas com links originais</div>
    </div>
    <div class="news-filters" id="nf">
      <button class="filter-btn active" onclick="flt('all',this)">Todos</button>
    </div>
    <div id="nc"></div>
  </div>
</div>
<footer>
  <div class="footer-brand">🛡️ SENTINELA v4.0 — Monitor Geopolítico Global</div>
  <div class="footer-info">NewsAPI + RSS · Claude AI · GitHub Actions<br>Atualizado 4× ao dia · hosemiro2.github.io/sentinela-geo · {agora}</div>
</footer>
<script>
// CLOCK
function tick(){{
  const n=new Date();
  const t=n.toLocaleTimeString('pt-BR',{{timeZone:'America/Sao_Paulo',hour:'2-digit',minute:'2-digit',second:'2-digit'}});
  document.getElementById('hdr-t').textContent=t;
  document.getElementById('hora-p').textContent=t;
}}
tick(); setInterval(tick,1000);

// NEWS DATA from Python
const NEWS_DATA={{news_json_placeholder}};
const TCOLS={{"brasil_eua":"#C86820","russia_otan":"#C86820","europa":"#C86820","china_taiwan":"#C86820","indo_pacifico":"#B89000","oriente_medio":"#C86820","america_latina":"#B89000","africa":"#B89000","cyber":"#B89000"}};
const TNAMES={{"brasil_eua":"Brasil×EUA","russia_otan":"Rússia×OTAN","europa":"Europa","china_taiwan":"China×Taiwan","indo_pacifico":"Indo-Pacífico","oriente_medio":"Or. Médio","america_latina":"Am. Latina","africa":"África","cyber":"Cyber"}};

let CF='all';
function flt(f,btn){{
  CF=f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  render();
}}

function render(){{
  const data=CF==='all'?NEWS_DATA:NEWS_DATA.filter(n=>n.t===CF);
  document.getElementById('nc').innerHTML=data.map(n=>`
    <div class="news-card">
      <div class="news-accent" style="background:${{TCOLS[n.t]||'var(--gold)'}}"></div>
      <div class="news-body">
        <div class="news-meta">
          <span class="news-theater">${{TNAMES[n.t]||n.t}}</span>
          <span class="news-source">${{n.s}}</span>
          <span class="news-time">${{n.d}}</span>
        </div>
        <div class="news-title">${{n.h}}</div>
        <div class="news-summary">${{n.x}}</div>
        <a class="news-link" href="${{n.u}}" target="_blank">↗ Ver fonte original — ${{n.s}}</a>
      </div>
    </div>`).join('');
}}

// Build filter buttons
const theaters=[...new Set(NEWS_DATA.map(n=>n.t))];
const nf=document.getElementById('nf');
theaters.forEach(t=>{{
  const b=document.createElement('button');
  b.className='filter-btn';
  b.textContent=TNAMES[t]||t;
  b.onclick=()=>flt(t,b);
  nf.appendChild(b);
}});
render();

// MARKETS
function sparkline(id,data,up){{
  const c=document.getElementById(id);if(!c)return;
  const ctx=c.getContext('2d');c.width=50;c.height=20;
  const mn=Math.min(...data),mx=Math.max(...data),rng=mx-mn||1;
  ctx.clearRect(0,0,50,20);ctx.beginPath();
  ctx.strokeStyle=up?'#50B878':'#C85050';ctx.lineWidth=1.5;
  data.forEach((v,i)=>{{const x=(i/(data.length-1))*48+1,y=18-((v-mn)/rng*16);i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);}});
  ctx.stroke();
}}
async function mkt(sym,vi,ci,cv){{
  try{{
    const r=await fetch(`https://api.allorigins.win/get?url=${{encodeURIComponent(`https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=5d`)}}`);
    const d=JSON.parse((await r.json()).contents);
    const cl=d.chart.result[0].indicators.quote[0].close.filter(Boolean);
    const cur=cl[cl.length-1],prev=cl[cl.length-2];
    const chg=((cur-prev)/prev*100).toFixed(2);const up=chg>=0;
    document.getElementById(vi).textContent=cur>10000?cur.toLocaleString('pt-BR',{{maximumFractionDigits:0}}):(sym.includes('BRL')?'R$ ':'')+cur.toFixed(2);
    const el=document.getElementById(ci);el.textContent=(up?'▲':'▼')+Math.abs(chg)+'%';el.className='mkt-chg '+(up?'up':'dn');
    if(cv)sparkline(cv,cl,up);
  }}catch(e){{}}
}}
async function com(sym,vi,ci){{
  try{{
    const r=await fetch(`https://api.allorigins.win/get?url=${{encodeURIComponent(`https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=2d`)}}`);
    const d=JSON.parse((await r.json()).contents);
    const cl=d.chart.result[0].indicators.quote[0].close.filter(Boolean);
    const cur=cl[cl.length-1],prev=cl[cl.length-2]||cur;
    const chg=((cur-prev)/prev*100).toFixed(2);const up=chg>=0;
    document.getElementById(vi).textContent='$'+cur.toFixed(2);
    const el=document.getElementById(ci);el.textContent=(up?'▲':'▼')+Math.abs(chg)+'%';el.className='com-chg '+(up?'up':'dn');
  }}catch(e){{}}
}}
mkt('^GSPC','v-sp','ch-sp','c-sp');mkt('^BVSP','v-ib','ch-ib','c-ib');
mkt('^GDAXI','v-dx','ch-dx','c-dx');mkt('^N225','v-nk','ch-nk','c-nk');
mkt('BRL=X','v-us','ch-us','c-us');
com('CL=F','v-oil','ch-oil');com('GC=F','v-gld','ch-gld');com('ZS=F','v-soy','ch-soy');
com('TIO=F','v-irf','ch-irf');com('ZW=F','v-wht','ch-wht');
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
// LEAFLET MAP
const THEATERS_GEO = [
  {{name:"Brasil x EUA/Paraguai", lat:-15.8, lng:-47.9, nivel:{resultados.get("brasil_eua",{}).get("analise",{}).get("nivel",1)}, tid:"brasil_eua"}},
  {{name:"Russia x Ucrania/OTAN", lat:50.4, lng:30.5, nivel:{resultados.get("russia_otan",{}).get("analise",{}).get("nivel",1)}, tid:"russia_otan"}},
  {{name:"Europa/Balticos/Balcas", lat:54.7, lng:25.3, nivel:{resultados.get("europa",{}).get("analise",{}).get("nivel",1)}, tid:"europa"}},
  {{name:"China x Taiwan/Pacifico", lat:25.0, lng:121.5, nivel:{resultados.get("china_taiwan",{}).get("analise",{}).get("nivel",1)}, tid:"china_taiwan"}},
  {{name:"Indo-Pacifico/Coreia/Japao", lat:35.7, lng:139.7, nivel:{resultados.get("indo_pacifico",{}).get("analise",{}).get("nivel",1)}, tid:"indo_pacifico"}},
  {{name:"Oriente Medio/Golfo Persico", lat:29.3, lng:47.9, nivel:{resultados.get("oriente_medio",{}).get("analise",{}).get("nivel",1)}, tid:"oriente_medio"}},
  {{name:"America Latina/Cone Sul", lat:-23.5, lng:-46.6, nivel:{resultados.get("america_latina",{}).get("analise",{}).get("nivel",1)}, tid:"america_latina"}},
  {{name:"Africa/Sahel/Chifre", lat:15.5, lng:32.5, nivel:{resultados.get("africa",{}).get("analise",{}).get("nivel",1)}, tid:"africa"}},
  {{name:"Cyber/Guerra Digital", lat:48.9, lng:2.3, nivel:{resultados.get("cyber",{}).get("analise",{}).get("nivel",1)}, tid:"cyber"}},
];
const NV_COLORS = {{1:"#287848",2:"#B89000",3:"#C86820",4:"#B83030",5:"#7B0000"}};
const NV_LABELS = {{1:"NORMAL",2:"ATENCAO",3:"ALERTA",4:"CRITICO",5:"CATASTROFE"}};

function initMap(){{
  const map = L.map('leafmap', {{
    center: [20, 10], zoom: 2,
    zoomControl: true,
    attributionControl: false,
    minZoom: 1, maxZoom: 6
  }});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    subdomains: 'abcd', maxZoom: 6
  }}).addTo(map);

  THEATERS_GEO.forEach(t => {{
    const cor = NV_COLORS[t.nivel] || '#C9A84C';
    const icon = L.divIcon({{
      className: '',
      html: `<div style="width:14px;height:14px;border-radius:50%;border:2px solid ${{cor}};background:${{cor}}33;box-shadow:0 0 8px ${{cor}}88;animation:marker-pulse 3s infinite"></div>`,
      iconSize: [14,14], iconAnchor: [7,7]
    }});
    const marker = L.marker([t.lat, t.lng], {{icon}}).addTo(map);
    marker.bindPopup(`
      <div style="font-family:'Cinzel',serif;font-size:10px;letter-spacing:.1em;color:#C9A84C;background:#0C0C0C;border:1px solid #6B5420;padding:8px 12px;min-width:180px;">
        <div style="font-weight:900;margin-bottom:4px">${{t.name}}</div>
        <div style="color:${{cor}};font-size:13px">Nível ${{t.nivel}}/5 — ${{NV_LABELS[t.nivel]}}</div>
      </div>
    `, {{className:'sentinela-popup'}});
  }});
}}
if(document.getElementById('leafmap')) initMap();
</script>
</body>
</html>"""
    # Inject news JSON
    import json
    news_list = []
    THEATER_IDS = list(resultados.keys())
    for tid, d in resultados.items():
        for noticia in d.get("noticias", [])[:4]:
            news_list.append({
                "t": tid,
                "h": noticia.get("titulo","")[:120],
                "s": noticia.get("fonte",""),
                "u": noticia.get("url","#"),
                "x": noticia.get("titulo","")[:160],
                "d": agora,
            })
    html = html.replace("{news_json_placeholder}", json.dumps(news_list, ensure_ascii=False))
    return html


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

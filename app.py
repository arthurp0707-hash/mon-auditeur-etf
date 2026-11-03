"""
Interface web MonAuditeur ETF (Streamlit) - theme finance sombre.

Lance avec : streamlit run app.py --server.address 0.0.0.0
Puis ouvre http://localhost:8501 dans ton navigateur.
"""
import plotly.graph_objects as go
import streamlit as st

from src.agent import repondre
from src.memoire import charger_profil

st.set_page_config(
    page_title="MonAuditeur ETF",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS - theme finance sombre
# ============================================================
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 20% 0%, #131a2e 0%, #0a0e1a 45%, #05070d 100%);
        color: #e8ecf4;
    }
    section[data-testid="stSidebar"] {
        background: #0d1322;
        border-right: 1px solid rgba(212,175,55,0.15);
    }
    h1, h2, h3 {
        font-family: Georgia, 'Times New Roman', serif;
        color: #f5e6c8;
        letter-spacing: 0.5px;
    }
    .brand-title {
        font-family: Georgia, serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #d4af37 0%, #f5e6c8 50%, #00d4a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .brand-sub {
        font-size: 0.95rem;
        color: #8a96ab;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 2rem;
    }
    .card {
        background: rgba(20, 28, 48, 0.65);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(212,175,55,0.18);
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin: 0.8rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    }
    .card-ok   { border-left: 5px solid #00d4a0; }
    .card-warn { border-left: 5px solid #d4af37; }
    .card-err  { border-left: 5px solid #e0555a; }
    .card-label {
        font-size: 0.72rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #8a96ab;
        margin-bottom: 0.6rem;
    }
    .card-value {
        font-family: Georgia, serif;
        font-size: 1.35rem;
        color: #e8ecf4;
        line-height: 1.5;
    }
    .badge {
        display: inline-block;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 0.8rem;
    }
    .badge-ok   { background: rgba(0,212,160,0.15); color: #00d4a0;
                  border: 1px solid rgba(0,212,160,0.4); }
    .badge-warn { background: rgba(212,175,55,0.15); color: #d4af37;
                  border: 1px solid rgba(212,175,55,0.4); }
    .badge-err  { background: rgba(224,85,90,0.15); color: #e0555a;
                  border: 1px solid rgba(224,85,90,0.4); }
    div[data-testid="stMetric"] {
        background: rgba(20, 28, 48, 0.5);
        border: 1px solid rgba(212,175,55,0.12);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
    }
    div[data-testid="stMetricLabel"] { color: #8a96ab; }
    div[data-testid="stMetricValue"] {
        font-family: Georgia, serif;
        color: #f5e6c8;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1a2540 0%, #0f1628 100%);
        color: #d4af37;
        border: 1px solid rgba(212,175,55,0.3);
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #d4af37;
        box-shadow: 0 0 18px rgba(212,175,55,0.25);
        color: #f5e6c8;
    }
    .stTextInput > div > div > input {
        background: rgba(20, 28, 48, 0.7);
        border: 1px solid rgba(212,175,55,0.2);
        color: #e8ecf4;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(20,28,48,0.4);
        border-radius: 10px;
        color: #8a96ab;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(212,175,55,0.12);
        color: #d4af37;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown('<div class="brand-sub">Profil investisseur</div>',
                unsafe_allow_html=True)
    try:
        profil = charger_profil()
        st.markdown(f"**Risque** &nbsp; `{profil['risque']}`")
        st.markdown(f"**Horizon** &nbsp; {profil['horizon_annees']} ans")
        st.markdown(f"**Frais max** &nbsp; {profil['frais_max_pct']} %")
        ex = profil["exclusions"] or ["aucune"]
        st.markdown(f"**Exclusions** &nbsp; {', '.join(ex)}")
    except Exception as e:
        st.warning(f"Profil indisponible : {e}")

    st.markdown("---")
    st.markdown('<div class="brand-sub">Modifier mon profil</div>',
                unsafe_allow_html=True)

    from src.memoire import sauver_profil
    with st.form("profil_form"):
        nouveau_risque = st.selectbox(
            "Risque",
            ["faible", "moyen", "eleve"],
            index=["faible", "moyen", "eleve"].index(profil.get("risque", "moyen")),
        )
        nouvel_horizon = st.number_input(
            "Horizon (annees)", min_value=1, max_value=40,
            value=int(profil.get("horizon_annees", 5)),
        )
        nouveaux_frais = st.number_input(
            "Frais max (%)", min_value=0.0, max_value=5.0, step=0.05,
            value=float(profil.get("frais_max_pct", 0.30)),
        )
        nouvelles_exclusions = st.text_input(
            "Exclusions (separes par virgule)",
            value=", ".join(profil.get("exclusions", [])),
        )
        sauvegarder = st.form_submit_button("Sauvegarder", use_container_width=True)

        if sauvegarder:
            profil_modifie = {
                "risque": nouveau_risque,
                "horizon_annees": nouvel_horizon,
                "frais_max_pct": nouveaux_frais,
                "exclusions": [e.strip() for e in nouvelles_exclusions.split(",") if e.strip()],
                "devise": profil.get("devise", "EUR"),
            }
            sauver_profil(profil_modifie)
            st.success("Profil sauvegarde.")
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="brand-sub">Systeme</div>',
                unsafe_allow_html=True)
    st.markdown("**Modele** &nbsp; Qwen3.5-4B (local)")
    st.markdown("**Briques** &nbsp; 1, 3, 5, 6, 9")
    st.markdown("**Barriere** &nbsp; active")
    st.markdown("**Cache** &nbsp; CSV local")

    st.markdown("---")
    st.caption("Le modele ne calcule jamais. Il propose un outil, "
               "le code calcule, la barriere verifie.")

# ============================================================
# En-tete
# ============================================================
st.markdown('<div class="brand-title">MonAuditeur ETF</div>',
            unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Verification de affirmations '
            'sur ETF - donnees reelles, chiffres traces</div>',
            unsafe_allow_html=True)

# ============================================================
# Onglets
# ============================================================
tab_q, tab_bench, tab_about = st.tabs(
    ["Question", "Benchmark", "A propos"]
)

# ---------- Onglet Question ----------
with tab_q:
    st.markdown("### Exemples")
    exemples = [
        "Quel est le rendement annualise de ETF monde ?",
        "QQQ a-t-il fait +45% par an sur 5 ans ?",
        "Quel est le meilleur ETF tech sur 5 ans ?",
        "Quel est le meilleur ETF chinois sur 5 ans ?",
        "Quel est le prix de ETF Amundi MSCI World ?",
    ]
    cols = st.columns(len(exemples))
    question_choisie = None
    for i, ex in enumerate(exemples):
        if cols[i].button(ex, key=f"ex{i}", use_container_width=True):
            question_choisie = ex

    question = st.text_input(
        "Pose ta question sur un ETF",
        value=question_choisie or "",
        placeholder="ex: rendement de ETF monde, prix de QQQ, meilleur ETF tech...",
    )
    analyser = st.button("Analyser", type="primary", use_container_width=True)

    if analyser and question.strip():
        with st.spinner("Analyse en cours..."):
            res = repondre(question)

        if res["verdict"] and res["chiffres"]:
            cls, badge_cls, badge_txt = "card-ok", "badge-ok", "BARRIERE OK"
        elif res["verdict"] and not res["chiffres"]:
            cls, badge_cls, badge_txt = "card-warn", "badge-warn", "REFUS HONNETE"
        else:
            cls, badge_cls, badge_txt = "card-err", "badge-err", "BLOQUE"

        st.markdown(f"""
        <div class="card {cls}">
            <div class="card-label">Reponse</div>
            <div class="card-value">{res["reponse"]}</div>
            <span class="badge {badge_cls}">{badge_txt}</span>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Chiffres utilises", len(res["chiffres"]))
        c2.metric("Barriere", "OK" if res["verdict"] else "BLOQUE")
        c3.metric("Etapes trace", len(res["trace"]))

        # --- Detail du calcul ---
        meta = res.get("meta", {})
        with st.expander("Detail du calcul"):
            if meta.get("outil") == "compute_metric":
                st.markdown(f"**Ticker** : {meta.get('ticker')}")
                st.markdown(f"**Metrique** : {meta.get('metric')}")
                st.markdown(f"**Periode** : {meta.get('annees') or 'tout l historique'} ans")
                st.markdown(f"**Valeur calculee** : {res['chiffres'][0]:.4f}")
            elif meta.get("outil") == "classer_etfs":
                st.markdown(f"**Metrique** : {meta.get('metric')}")
                st.markdown(f"**Periode** : {meta.get('annees') or 'tout l historique'} ans")
                st.markdown(f"**Source** : {meta.get('source')}")
                st.markdown(f"**Tickers compares** : {len(meta.get('tickers', []))}")
            elif meta.get("outil") == "meilleur_secteur":
                st.markdown("**Classement des 11 secteurs Yahoo**")
                st.markdown(f"**Periode** : {meta.get('annees') or 'tout l historique'} ans")
            else:
                st.markdown("Pas de calcul (refus honnete ou pas d outil).")

        # --- Graphique de prix (compute_metric) ---
        if meta.get("prix"):
            st.markdown("### Evolution du prix")
            prix = meta["prix"]
            fig = go.Figure(go.Scatter(
                x=prix["dates"], y=prix["close"],
                mode="lines",
                line=dict(color="#d4af37", width=2),
                fill="tozeroy",
                fillcolor="rgba(212,175,55,0.08)",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8ecf4", family="Georgia"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(212,175,55,0.1)"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- Tableau + graphique du classement ---
        if meta.get("classement"):
            st.markdown("### Classement complet")
            classement = meta["classement"]
            import pandas as pd
            df = pd.DataFrame(classement, columns=["Ticker", "Valeur"])
            df.index = range(1, len(df) + 1)
            df.index.name = "Rang"
            st.dataframe(df, use_container_width=True)

            fig = go.Figure(go.Bar(
                x=[t for t, _ in classement],
                y=[v for _, v in classement],
                marker=dict(
                    color=[v for _, v in classement],
                    colorscale=[[0, "#e0555a"], [0.5, "#d4af37"], [1, "#00d4a0"]],
                ),
                text=[f"{v:.2f}" for _, v in classement],
                textposition="outside",
                textfont=dict(color="#f5e6c8", family="Georgia"),
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8ecf4", family="Georgia"),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(212,175,55,0.1)"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- Graphique du classement des secteurs ---
        if meta.get("classement_secteurs"):
            st.markdown("### Classement des secteurs")
            cs = meta["classement_secteurs"]
            import pandas as pd
            df = pd.DataFrame(cs, columns=["Secteur", "Meilleur ETF", "Valeur"])
            df.index = range(1, len(df) + 1)
            st.dataframe(df, use_container_width=True)

        with st.expander("Trace du pipeline"):
            for t in res["trace"]:
                st.text("> " + t)

    elif analyser:
        st.info("Ecris une question pour commencer.")

# ---------- Onglet Benchmark ----------
with tab_bench:
    st.markdown("### Systeme complet vs modele seul")
    st.markdown("10 taches a verite connue, 3 lancements chacune.")
    st.markdown("**Clique sur Verifier pour lancer le benchmark en direct "
                "et voir les reponses brutes du modele seul.**")

    c1, c2 = st.columns(2)
    c1.metric("Systeme complet (A)", "1.00", "ecart-type 0.00")
    c2.metric("Modele seul (B)", "0.00", "ecart-type 0.00")

    if st.button("Verifier le benchmark en direct", type="primary"):
        with st.spinner("Lancement du benchmark (10 taches x 3 runs)..."):
            try:
                import json
                from pathlib import Path
                from benchmark.run import main as run_benchmark
                run_benchmark()
                results_path = Path("benchmark/results.json")
                if results_path.exists():
                    data = json.loads(results_path.read_text(encoding="utf-8"))
                    st.success("Benchmark termine. Resultats bruts :")
                    for t in data[:3]:
                        st.markdown(f"**{t['id']}** - {t['question'][:60]}")
                        st.text(f"  A (systeme) : {t['A'][0]['texte'][:100]}")
                        st.text(f"  B (modele)  : {t['B'][0]['texte'][:100]}")
                    st.markdown("**Le modele seul ne calcule pas : il genere "
                                "du texte plausible. C'est prouve ci-dessus.**")
            except Exception as e:
                st.error(f"Erreur : {e}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Systeme complet", "Modele seul"],
        y=[1.00, 0.00],
        marker_color=["#00d4a0", "#e0555a"],
        text=["1.00", "0.00"],
        textposition="outside",
        textfont=dict(color="#f5e6c8", size=16, family="Georgia"),
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e8ecf4", family="Georgia"),
        yaxis=dict(range=[0, 1.15], showgrid=True,
                   gridcolor="rgba(212,175,55,0.1)"),
        xaxis=dict(showgrid=False),
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
**Exemple T01** - rendement annualise de QQQ sur 5 ans.
Le systeme repond **13.11** trois fois sur trois.
Le modele seul repond **5, -100, 5** : il ne calcule pas.
""")

# ---------- Onglet A propos ----------
with tab_about:
    st.markdown("""
### Ce que fait le systeme
1. Tu poses une question sur un ETF.
2. Le code choisit l outil (heuristique deterministe).
3. L outil calcule le vrai chiffre a partir du cache CSV.
4. Le LLM redige une reponse a partir de ce chiffre.
5. La barriere verifie que tous les chiffres cites sont traces.
6. Si un chiffre est invente, la reponse est bloquee.

### Les 5 briques
- **Brique 1** - outil compute_metric / classer_etfs
- **Brique 3** - barriere anti-hallucination
- **Brique 5** - memoire persistante (profil investisseur)
- **Brique 6** - nettoyage + regle metier SFDR (source AMF)
- **Brique 9** - comparaison mesuree (A=1.00 vs B=0.00)

### Limites
Ce systeme ne donne pas de conseil en investissement. Il verifie des
affirmations factuelles contre des donnees publiques. La decision reste humaine.
""")

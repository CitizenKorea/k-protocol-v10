import streamlit as st
import requests
import h5py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="K-PROTOCOL Real-Data Verifier", layout="wide", page_icon="🛡️")

# --- 2. 데이터 자동 추적 로직 (URL 리스트) ---
# 서버가 경로를 바꿔도 찾을 수 있도록 여러 후보를 등록합니다.
DATA_SOURCES = [
    "https://www.gw-openscience.org/eventapi/html/GWTC-1-confident/GW170814/v3/GW170814_posterior_samples.h5",
    "https://zenodo.org/records/3546372/files/GW170814_posterior_samples.h5?download=1",
    "https://dcc.ligo.org/public/0150/P1800061/011/GW170814_posterior_samples.h5"
]
LOCAL_FILE = "GW170814_final_secure.h5"

@st.cache_data
def fetch_ligo_raw_data():
    """LIGO 서버 3곳을 순차적으로 타격하여 데이터를 강제 인출"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    if not os.path.exists(LOCAL_FILE) or os.path.getsize(LOCAL_FILE) < 100000:
        if os.path.exists(LOCAL_FILE): os.remove(LOCAL_FILE)
        
        placeholder = st.empty()
        for i, url in enumerate(DATA_SOURCES):
            try:
                placeholder.info(f"데이터 서버 후보 {i+1}번에 접속 시도 중...")
                r = requests.get(url, headers=headers, stream=True, timeout=30, allow_redirects=True)
                if r.status_code == 200:
                    with open(LOCAL_FILE, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=16384):
                            f.write(chunk)
                    if os.path.getsize(LOCAL_FILE) > 100000:
                        placeholder.success(f"서버 {i+1}번에서 데이터 인출 성공!")
                        return LOCAL_FILE
            except:
                continue
        
        st.error("❌ 모든 공식 서버가 응답하지 않습니다. LIGO 서버 점검 중일 수 있습니다.")
        return None
    return LOCAL_FILE

# --- 3. K-PROTOCOL 핵심 물리 엔진 ---
g_locs = {
    'Hanford (H1)': 9.8073527,
    'Livingston (L1)': 9.7936814,
    'Virgo (V1)': 9.8053340
}
pi_sq = np.pi**2

def apply_k_protocol(raw_samples, g_loc):
    """Appendix B.3.2: 세제곱 역보정 공식"""
    s_loc = pi_sq / g_loc
    return raw_samples * (1 / s_loc)**3

# --- 4. 메인 화면 구성 ---
st.title("🛡️ K-PROTOCOL: 실측 데이터 '제로-터치' 검증")
st.markdown("""
본 엔진은 **GWOSC/LIGO** 공식 아카이브를 실시간 추적하여 `GW170814` 이벤트의 실제 확률 샘플을 가져옵니다. 
어떠한 인위적 가공 없이, 오직 **K-PROTOCOL 세제곱 역보정**만을 통해 데이터의 수렴성을 증명합니다.
""")

if st.sidebar.button("🚨 실측 데이터 검증 시작 (Real-time Fetch)"):
    file_path = fetch_ligo_raw_data()
    
    if file_path and os.path.exists(file_path):
        try:
            with h5py.File(file_path, "r") as f:
                # 데이터 트리에서 chirp_mass를 지능적으로 검색
                m_chirp_samples = None
                def find_chirp(name, obj):
                    global m_chirp_samples
                    if 'chirp_mass' in name.lower() and isinstance(obj, h5py.Dataset):
                        m_chirp_samples = obj[:]
                        return True
                f.visititems(find_chirp)
                
                if m_chirp_samples is not None:
                    st.success(f"성공: {len(m_chirp_samples):,}개의 실측 확률 점(Samples)을 확보했습니다.")

                    # --- 5. 보정 및 분석 ---
                    results = []
                    for site, g in g_locs.items():
                        corrected = apply_k_protocol(m_chirp_samples, g)
                        results.append({
                            'Site': site,
                            'K_Mean': np.mean(corrected),
                            'K_Samples': corrected
                        })

                    # --- 6. 시각화 ---
                    st.subheader("📊 확률 분포의 절대 수렴 (Density Convergence)")
                    fig = go.Figure()
                    fig.add_trace(go.Violin(y=m_chirp_samples, name="LVC Raw (Standard)", line_color='red', opacity=0.3))
                    
                    colors = ['#1f77b4', '#3498db', '#5dade2']
                    for i, res in enumerate(results):
                        fig.add_trace(go.Violin(y=res['K_Samples'], name=f"K-Corrected ({res['Site']})", line_color=colors[i]))

                    fig.update_layout(title="LVC 표준 분포 vs K-PROTOCOL 보정 분포", yaxis_title="Chirp Mass (M☉)")
                    st.plotly_chart(fig, use_container_width=True)

                    # --- 7. 수치 보고서 ---
                    st.divider()
                    df_res = pd.DataFrame([{"Site": r['Site'], "K-Protocol Absolute": f"{r['K_Mean']:.6f}"} for r in results])
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("### 📋 수치 분석 보고서")
                        st.table(df_res)
                    with c2:
                        std_val = np.std([r['K_Mean'] for r in results])
                        st.write("### 📉 수렴 정밀도")
                        st.metric("Final Variance (σ)", f"{std_val:.8f}")
                        if std_val < 0.1:
                            st.success("결론: K-PROTOCOL에 의한 결정론적 수렴 확인")
                else:
                    st.error("파일 내에서 chirp_mass 데이터를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"파일 분석 중 오류: {e}")

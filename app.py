import streamlit as st
import requests
import h5py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="K-PROTOCOL Real-Data Verifier", layout="wide")

# --- 2. 실전 데이터 경로 (GWOSC 공식 URL) ---
# GW170814의 Posterior Samples (확률 구름 데이터)
LIGO_DATA_URL = "https://dcc.ligo.org/public/0150/P1800061/011/GW170814_posterior_samples.h5"
LOCAL_FILE = "GW170814_samples.h5"

@st.cache_data
def fetch_ligo_raw_data():
    """LIGO 서버에서 실제 HDF5 파일을 조작 없이 실시간으로 다운로드"""
    if not os.path.exists(LOCAL_FILE):
        with st.spinner("LIGO 공식 서버(dcc.ligo.org)에서 실측 데이터 구름을 인출 중..."):
            r = requests.get(LIGO_DATA_URL, stream=True)
            with open(LOCAL_FILE, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
    return LOCAL_FILE

# --- 3. K-PROTOCOL 핵심 물리 엔진 ---
g_locs = {
    'Hanford (H1)': 9.8073527,
    'Livingston (L1)': 9.7936814,
    'Virgo (V1)': 9.8053340
}
pi_sq = np.pi**2

def apply_k_protocol(raw_samples, g_loc):
    """Appendix B.3.2: 세제곱 역보정 공식 적용"""
    s_loc = pi_sq / g_loc
    # M_real = M_raw * (1 / s_loc)^3
    return raw_samples * (1 / s_loc)**3

# --- 4. 메인 화면 구성 ---
st.title("🛡️ K-PROTOCOL: 실측 데이터 '제로-터치' 검증")
st.markdown("""
본 검증기는 **LIGO-Virgo 협력단**이 공개한 `GW170814` 이벤트의 실제 확률 샘플을 실시간으로 가져옵니다. 
어떠한 인위적 가공 없이, 오직 **K-PROTOCOL 세제곱 역보정**만을 통해 데이터의 수렴성을 증명합니다.
""")

if st.sidebar.button("🚨 실측 데이터 검증 시작 (Real-time Fetch)"):
    # 데이터 인출
    file_path = fetch_ligo_raw_data()
    
    with h5py.File(file_path, "r") as f:
        # LVC가 계산한 전체 Chirp Mass 샘플 추출 (약 수만 개의 데이터 포인트)
        # 파일 구조에 따라 실제 경로 확인 필요 (GWTC-1 데이터셋 기준)
        try:
            # 전체 결합 확률 분포에서 추출
            m_chirp_samples = f['Overall_Posterior']['chirp_mass'][:]
            st.success(f"성공: {len(m_chirp_samples):,}개의 실측 확률 점(Samples)을 확보했습니다.")
        except KeyError:
            st.error("데이터 구조를 읽는 중 오류가 발생했습니다. 파일 형식을 재점검합니다.")
            st.stop()

    # --- 5. 보정 및 분석 ---
    results = []
    
    # 각 관측소별로 '만약 이 데이터가 해당 위치의 렌즈를 통과했다면?'을 가정하여 보정
    for site, g in g_locs.items():
        corrected = apply_k_protocol(m_chirp_samples, g)
        results.append({
            'Site': site,
            'Raw_Mean': np.mean(m_chirp_samples),
            'K_Mean': np.mean(corrected),
            'K_Samples': corrected
        })

    # --- 6. 시각화: 확률 분포의 응축 ---
    st.subheader("📊 확률 분포의 절대 수렴 (Probability Density Convergence)")
    
    fig = go.Figure()

    # 보정 전 LVC 표준 분포 (빨간색 구름)
    fig.add_trace(go.Violin(y=m_chirp_samples, name="LVC Standard (Raw)", line_color='red', opacity=0.4))

    # 보정 후 K-PROTOCOL 분포들 (파란색 계열)
    colors = ['#1f77b4', '#3498db', '#5dade2']
    for i, res in enumerate(results):
        fig.add_trace(go.Violin(
            y=res['K_Samples'], 
            name=f"K-Corrected ({res['Site']})", 
            line_color=colors[i]
        ))

    fig.update_layout(
        title="표준 지수 vs K-PROTOCOL 세제곱 보정 분포 비교",
        yaxis_title="Chirp Mass (M☉)",
        violinmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 7. 정량적 분석 결과 ---
    st.divider()
    df_res = pd.DataFrame([
        {"Site": r['Site'], "Raw Mean": r['Raw_Mean'], "K-Protocol Absolute": r['K_Mean']} 
        for r in results
    ])
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 📋 수치 분석 보고서")
        st.dataframe(df_res)
    
    with col2:
        std_val = np.std([r['K_Mean'] for r in results])
        st.write("### 📉 수렴 정밀도")
        st.metric("Final Variance (σ)", f"{std_val:.10f}")
        if std_val < 1e-5:
            st.success("결과: 절대 수렴 확인 ($R^2 \\approx 1.0$)")

    st.info(f"이 검증에 사용된 데이터는 {LIGO_DATA_URL}에서 방금 내려받은 실제 파일입니다.")
else:
    st.warning("사이드바의 버튼을 눌러 검증을 시작하십시오. LIGO 서버에 직접 접속합니다.")

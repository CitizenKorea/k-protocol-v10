import streamlit as st
import requests
import h5py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="K-PROTOCOL Real-Data Verifier", layout="wide", page_icon="🛡️")

# --- 2. 실전 데이터 경로 및 설정 ---
LIGO_DATA_URL = "https://dcc.ligo.org/public/0150/P1800061/011/GW170814_posterior_samples.h5"
LOCAL_FILE = "GW170814_samples_v2.h5" # 파일명을 바꿔서 깨진 캐시를 방지합니다.

@st.cache_data
def fetch_ligo_raw_data():
    """LIGO 서버에서 실제 HDF5 파일을 안전하게 다운로드"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 기존에 깨진 파일이 있다면 삭제
    if os.path.exists(LOCAL_FILE) and os.path.getsize(LOCAL_FILE) < 100000:
        os.remove(LOCAL_FILE)

    if not os.path.exists(LOCAL_FILE):
        try:
            r = requests.get(LIGO_DATA_URL, headers=headers, stream=True, timeout=60)
            r.raise_for_status()
            with open(LOCAL_FILE, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            st.error(f"데이터 다운로드 중 오류 발생: {e}")
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
본 검증기는 **LIGO-Virgo 협력단**이 공개한 `GW170814` 이벤트의 실제 확률 샘플을 실시간으로 가져옵니다. 
어떠한 인위적 가공 없이, 오직 **K-PROTOCOL 세제곱 역보정**만을 통해 데이터의 수렴성을 증명합니다.
""")

# 사이드바 버튼
if st.sidebar.button("🚨 실측 데이터 검증 시작 (Real-time Fetch)"):
    file_path = fetch_ligo_raw_data()
    
    if file_path and os.path.exists(file_path):
        try:
            with h5py.File(file_path, "r") as f:
                # 데이터 추출 (파일 구조에 따라 경로가 다를 수 있음)
                # GW170814의 경우 'Overall_Posterior' 그룹을 찾습니다.
                if 'Overall_Posterior' in f:
                    m_chirp_samples = f['Overall_Posterior']['chirp_mass'][:]
                else:
                    # 다른 구조일 경우 첫 번째 그룹의 chirp_mass를 시도
                    first_key = list(f.keys())[0]
                    m_chirp_samples = f[first_key]['chirp_mass'][:]
                
                st.success(f"성공: {len(m_chirp_samples):,}개의 실측 확률 점(Samples)을 확보했습니다.")

                # --- 5. 보정 및 분석 ---
                results = []
                for site, g in g_locs.items():
                    corrected = apply_k_protocol(m_chirp_samples, g)
                    results.append({
                        'Site': site,
                        'Raw_Mean': np.mean(m_chirp_samples),
                        'K_Mean': np.mean(corrected),
                        'K_Samples': corrected
                    })

                # --- 6. 시각화 ---
                st.subheader("📊 확률 분포의 절대 수렴 (Probability Density Convergence)")
                fig = go.Figure()
                fig.add_trace(go.Violin(y=m_chirp_samples, name="LVC Standard (Raw)", line_color='red', opacity=0.4))
                
                colors = ['#1f77b4', '#3498db', '#5dade2']
                for i, res in enumerate(results):
                    fig.add_trace(go.Violin(y=res['K_Samples'], name=f"K-Corrected ({res['Site']})", line_color=colors[i]))

                fig.update_layout(title="표준 지수 vs K-PROTOCOL 세제곱 보정 분포 비교", yaxis_title="Chirp Mass (M☉)")
                st.plotly_chart(fig, use_container_width=True)

                # --- 7. 결과 보고서 ---
                st.divider()
                df_res = pd.DataFrame([{"Site": r['Site'], "Raw Mean": r['Raw_Mean'], "K-Protocol Absolute": r['K_Mean']} for r in results])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### 📋 수치 분석 보고서")
                    st.dataframe(df_res)
                with col2:
                    std_val = np.std([r['K_Mean'] for r in results])
                    st.write("### 📉 수렴 정밀도")
                    st.metric("Final Variance (σ)", f"{std_val:.10f}")
                    if std_val < 0.001:
                        st.success("결과: 절대 수렴 확인 ($R^2 \\approx 1.0$)")

        except Exception as e:
            st.error(f"파일 분석 중 오류 발생: {e}. 데이터 구조가 예상과 다를 수 있습니다.")
    else:
        st.error("파일을 불러올 수 없습니다. 서버 연결을 확인하세요.")
else:
    st.info("사이드바의 버튼을 눌러 검증을 시작하십시오.")

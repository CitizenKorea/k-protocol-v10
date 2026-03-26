import streamlit as st
import h5py
import numpy as np
import plotly.graph_objects as go
import os

# --- 설정 및 파일 경로 ---
MY_FILE = "GW170814_GWTC-1.hdf5" 

st.set_page_config(page_title="K-PROTOCOL Absolute Proof", layout="wide")

# --- CSS 스타일링 (Optional) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ K-PROTOCOL: 실측 데이터 확정적 검증")
st.markdown("LIGO/Virgo의 표준 중력파 데이터를 K-PROTOCOL 수식에 따라 절대 질량으로 보정하고 분석합니다.")

# --- 사이드바 및 파일 확인 ---
st.sidebar.header("⚙️ 분석 설정")
file_source = st.sidebar.radio("데이터 소스 선택", ["로컬 서버 파일", "파일 직접 업로드"])

target_file = None
if file_source == "로컬 서버 파일":
    if os.path.exists(MY_FILE):
        target_file = MY_FILE
        st.sidebar.success(f"✅ {MY_FILE} 연결됨")
    else:
        st.sidebar.error(f"❌ '{MY_FILE}' 파일이 서버에 없습니다.")
else:
    uploaded_file = st.sidebar.file_uploader("HDF5 파일 업로드", type=["hdf5", "h5"])
    if uploaded_file:
        target_file = uploaded_file

# --- 핵심 분석 함수 ---
def analyze_k_protocol(file_obj):
    found_data = {}
    
    def scan_file(name, obj):
        if isinstance(obj, h5py.Dataset):
            # chirp_mass 관련 키워드 검색
            target_names = ['chirp_mass', 'mchirp', 'mc', 'm_chirp']
            if any(tn in name.lower() for tn in target_names):
                found_data['path'] = name
                found_data['samples'] = obj[:]

    with h5py.File(file_obj, "r") as f:
        f.visititems(scan_file)
    
    return found_data

# --- 실행 버튼 ---
if st.sidebar.button("🚨 데이터 정밀 탐색 및 분석 시작"):
    if target_file is None:
        st.warning("분석할 파일을 먼저 선택하거나 업로드하세요.")
    else:
        try:
            with st.spinner("🔍 데이터셋 내부 전수 조사 중..."):
                result = analyze_k_protocol(target_file)

            if not result:
                st.error("❌ 파일 내에서 'chirp_mass' 데이터를 찾을 수 없습니다.")
                # 파일 구조 디버깅용 정보 출력
                with h5py.File(target_file, "r") as f:
                    keys = []
                    f.visit(lambda name: keys.append(name))
                    st.write("발견된 전체 경로 목록 (샘플):", keys[:10])
            else:
                m_chirp = result['samples']
                st.success(f"🎯 데이터 확보 완료! (경로: `{result['path']}`)")

                # --- K-PROTOCOL 보정 연산 ---
                # Hanford(H1) 중력 가속도 상수
                g_h1 = 9.8073527
                # 수식: (π^2 / g)^3 보정 계수
                correction_factor = (np.pi**2 / g_h1)**3
                corrected = m_chirp / correction_factor

                # --- 결과 리포트 (Metric) ---
                col1, col2, col3 = st.columns(3)
                col1.metric("샘플 수", f"{len(m_chirp):,}")
                col2.metric("표준 평균 질량", f"{np.mean(m_chirp):.4f} M☉")
                col3.metric("K-보정 절대 질량", f"{np.mean(corrected):.4f} M☉", 
                           delta=f"{np.mean(corrected)-np.mean(m_chirp):.4f}", delta_color="inverse")

                # --- 시각화 (Plotly) ---
                st.write("### 📊 데이터 분포 비교 분석")
                
                fig = go.Figure()
                # Raw Data
                fig.add_trace(go.Histogram(x=m_chirp, name="LVC Raw (Standard)", 
                                         nbinsx=50, opacity=0.6, marker_color='#FF4B4B'))
                # Corrected Data
                fig.add_trace(go.Histogram(x=corrected, name="K-Corrected (Absolute)", 
                                         nbinsx=50, opacity=0.6, marker_color='#0068C9'))

                fig.update_layout(
                    barmode='overlay',
                    title="표준 분포 vs K-PROTOCOL 보정 분포 비교",
                    xaxis_title="Chirp Mass (M☉)",
                    yaxis_title="빈도수 (Frequency)",
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                )
                st.plotly_chart(fig, use_container_width=True)

                # 바이올린 플롯 (상세 통계)
                fig_violin = go.Figure()
                fig_violin.add_trace(go.Violin(y=m_chirp, name="Standard", box_visible=True, line_color='#FF4B4B'))
                fig_violin.add_trace(go.Violin(y=corrected, name="K-Absolute", box_visible=True, line_color='#0068C9'))
                fig_violin.update_layout(title="상세 통계 분포 (Violin Plot)")
                st.plotly_chart(fig_violin, use_container_width=True)

                # --- 추가 데이터 정보 ---
                with st.expander("🔎 상세 데이터 보기"):
                    st.write("처음 10개 샘플 비교 (Raw vs Corrected)")
                    st.table(np.column_stack((m_chirp[:10], corrected[:10])))

        except Exception as e:
            st.error(f"⚠️ 분석 중 예기치 못한 오류가 발생했습니다: {e}")

import streamlit as st
import h5py
import numpy as np
import plotly.graph_objects as go
import os

# --- 설정 및 파일 경로 ---
MY_FILE = "GW170814_GWTC-1.hdf5" 

st.set_page_config(page_title="K-PROTOCOL Empirical Proof", layout="wide", page_icon="🔭")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ K-PROTOCOL: 실측 데이터 확정적 검증 엔진")
st.markdown("""
LIGO/Virgo의 실제 관측 확률 데이터(Posterior Samples)를 K-PROTOCOL의 기하학적 렌즈 모델에 대입합니다. 
LVC가 뭉뚱그려놓은 **네트워크 평균(Network Combined)** 데이터에는 **지구 평균 렌즈($S_{earth}$)**를 적용하여 렌즈를 벗겨내는 것이 논리적으로 완벽한 역공학(Reverse Engineering)입니다.
""")

# --- 사이드바 및 파일 확인 ---
st.sidebar.header("⚙️ 분석 설정")
file_source = st.sidebar.radio("📁 데이터 소스 선택", ["로컬 서버 파일", "파일 직접 업로드"])

target_file = None
if file_source == "로컬 서버 파일":
    if os.path.exists(MY_FILE):
        target_file = MY_FILE
        st.sidebar.success(f"✅ {MY_FILE} 연결됨")
    else:
        st.sidebar.error(f"❌ '{MY_FILE}' 파일이 서버에 없습니다.")
else:
    uploaded_file = st.sidebar.file_uploader("HDF5 파일 업로드", type=["hdf5", "h5", "h5py"])
    if uploaded_file:
        target_file = uploaded_file

st.sidebar.markdown("---")
st.sidebar.header("🔭 역보정 렌즈 타겟 선택")
st.sidebar.markdown("데이터의 출처에 맞는 중력 렌즈를 선택하여 렌즈 효과를 제거(역보정)합니다.")

# 관측소별 고유 중력 세팅
lens_options = {
    "🌍 지구 표준 평균 (네트워크 데이터용)": 9.80665,
    "🇺🇸 Hanford (H1) 단일 관측소": 9.8073527,
    "🇺🇸 Livingston (L1) 단일 관측소": 9.7936814,
    "🇮🇹 Virgo (V1) 단일 관측소": 9.8053340
}
selected_lens = st.sidebar.radio("렌즈 종류", list(lens_options.keys()))
g_target = lens_options[selected_lens]

# --- 핵심 분석 함수 ---
def analyze_k_protocol(file_obj):
    found_data = {}
    
    def scan_file(name, obj):
        # 이미 데이터를 찾았다면 더 이상 탐색하지 않음
        if 'samples' in found_data: 
            return

        if isinstance(obj, h5py.Dataset):
            # 1. 데이터셋이 구조적 배열(Structured Array)인 경우 컬럼 탐색
            if obj.dtype.names is not None:
                fields = obj.dtype.names
                
                # 1-1. chirp_mass 컬럼 직접 탐색
                target_names = ['chirp_mass', 'mchirp', 'mc', 'm_chirp']
                for field in fields:
                    if any(tn in field.lower() for tn in target_names):
                        found_data['path'] = f"{name} 내부 컬럼 ['{field}']"
                        found_data['samples'] = obj[field]
                        return
                
                # 1-2. m1, m2를 찾아 Chirp Mass 자동 계산 (Detector frame 우선 탐색)
                m1_field, m2_field = None, None
                for field in fields:
                    fl = field.lower()
                    if 'm1_detector_frame' in fl or 'mass_1' in fl or 'm1' in fl: 
                        if not m1_field: m1_field = field
                    if 'm2_detector_frame' in fl or 'mass_2' in fl or 'm2' in fl: 
                        if not m2_field: m2_field = field
                
                if m1_field and m2_field:
                    m1 = obj[m1_field]
                    m2 = obj[m2_field]
                    # Chirp Mass 계산 공식 적용
                    mc = ((m1 * m2)**(3/5)) / ((m1 + m2)**(1/5))
                    found_data['path'] = f"{name} (계산됨: {m1_field} & {m2_field})"
                    found_data['samples'] = mc
                    return

            # 2. 일반 HDF5 그룹/데이터셋 구조인 경우
            else:
                target_names = ['chirp_mass', 'mchirp', 'mc', 'm_chirp']
                if any(tn in name.lower() for tn in target_names):
                    found_data['path'] = name
                    found_data['samples'] = obj[:]
                    return

    with h5py.File(file_obj, "r") as f:
        # 파일 최상단에서 Overall_posterior (네트워크 평균)를 우선적으로 탐색
        if "Overall_posterior" in f:
            scan_file("Overall_posterior", f["Overall_posterior"])
        # 못 찾았을 경우 전체 뒤지기
        if 'samples' not in found_data:
            f.visititems(scan_file)
            
    return found_data

# --- 실행 버튼 ---
if st.sidebar.button("🚨 실측 데이터 렌즈 해체 시작"):
    if target_file is None:
        st.warning("분석할 파일을 먼저 선택하거나 업로드하세요.")
    else:
        try:
            with st.spinner("🔍 데이터셋 내부 컬럼 전수 조사 및 질량 합성 중..."):
                result = analyze_k_protocol(target_file)

            if not result or 'samples' not in result:
                st.error("❌ 파일 내에서 질량 데이터를 찾을 수 없습니다.")
            else:
                m_chirp = result['samples']
                st.success(f"🎯 실측 데이터 확보 완료! (추출 경로: `{result['path']}`)")

                # --- K-PROTOCOL 보정 연산 (선택된 렌즈 기반) ---
                pi_sq = np.pi**2
                s_loc = pi_sq / g_target
                
                # M_real = M_raw * (1 / S_loc)^3
                corrected = m_chirp * ((1 / s_loc)**3)

                # --- 결과 리포트 (Metric) ---
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("확보된 실측 샘플 수", f"{len(m_chirp):,}")
                col2.metric("선택된 국소 중력 ($g$)", f"{g_target:.7f}")
                col3.metric("LVC 원시 평균 질량", f"{np.mean(m_chirp):.4f} M☉")
                col4.metric("우주 절대 질량 (K-보정)", f"{np.mean(corrected):.4f} M☉", 
                           delta=f"{np.mean(corrected)-np.mean(m_chirp):.4f}", delta_color="inverse")

                # --- 시각화 (Plotly) ---
                st.write("### 📊 실측 데이터 렌즈 역보정 (Shift) 시각화")
                st.markdown(f"선택하신 렌즈(**{selected_lens}**)의 왜곡 지수($S_{{loc}}^3 = {(s_loc**3):.6f}$)를 제거하여, 가짜 질량 데이터가 실제 우주의 절대 질량으로 통째로 이동(Shift)하는 과정을 보여줍니다.")
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=m_chirp, name="LVC 원시 데이터 (렌즈 왜곡됨)", 
                                         nbinsx=100, opacity=0.6, marker_color='#FF4B4B'))
                fig.add_trace(go.Histogram(x=corrected, name="K-PROTOCOL 절대 질량 (렌즈 제거됨)", 
                                         nbinsx=100, opacity=0.7, marker_color='#0068C9'))

                fig.update_layout(
                    barmode='overlay',
                    title=f"렌즈 왜곡 제거에 따른 질량 분포 이동 ({selected_lens})",
                    xaxis_title="계산된 Chirp Mass (M☉)",
                    yaxis_title="확률 밀도 빈도수 (Frequency)",
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(255,255,255,0.8)'),
                    plot_bgcolor='white'
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ 분석 중 오류 발생: {e}")

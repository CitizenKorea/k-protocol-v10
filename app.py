import streamlit as st
import h5py
import numpy as np
import plotly.graph_objects as go
import os

# --- 설정 및 파일 경로 ---
MY_FILE = "GW170814_GWTC-1.hdf5" 

st.set_page_config(page_title="K-PROTOCOL Absolute Proof", layout="wide")

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
    uploaded_file = st.sidebar.file_uploader("HDF5 파일 업로드", type=["hdf5", "h5", "h5py"])
    if uploaded_file:
        target_file = uploaded_file

# --- 핵심 분석 함수 (구조적 배열 및 켤레 질량 자동 계산 지원) ---
def analyze_k_protocol(file_obj):
    found_data = {}
    
    def scan_file(name, obj):
        # 이미 데이터를 찾았다면 더 이상 탐색하지 않음
        if 'samples' in found_data: 
            return

        if isinstance(obj, h5py.Dataset):
            # 1. 데이터셋이 구조적 배열(Structured Array - GWTC-1 형태)인 경우 표 내부의 컬럼명을 탐색
            if obj.dtype.names is not None:
                fields = obj.dtype.names
                
                # 1-1. chirp_mass 컬럼이 직접 존재하는지 확인
                target_names = ['chirp_mass', 'mchirp', 'mc', 'm_chirp']
                for field in fields:
                    if any(tn in field.lower() for tn in target_names):
                        found_data['path'] = f"{name} 내부 컬럼 ['{field}']"
                        found_data['samples'] = obj[field]
                        return
                
                # 1-2. 없다면 m1, m2를 찾아 Chirp Mass 자동 계산
                m1_field, m2_field = None, None
                for field in fields:
                    fl = field.lower()
                    if 'm1' in fl or 'mass_1' in fl: m1_field = field
                    if 'm2' in fl or 'mass_2' in fl: m2_field = field
                
                if m1_field and m2_field:
                    m1 = obj[m1_field]
                    m2 = obj[m2_field]
                    # Chirp Mass 계산 공식 적용
                    mc = ((m1 * m2)**(3/5)) / ((m1 + m2)**(1/5))
                    found_data['path'] = f"{name} (계산됨: {m1_field} & {m2_field} 조합)"
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
        # 파일 최상단에서 Overall_posterior를 우선적으로 탐색
        if "Overall_posterior" in f:
            scan_file("Overall_posterior", f["Overall_posterior"])
        # 못 찾았을 경우 전체 뒤지기
        if 'samples' not in found_data:
            f.visititems(scan_file)
            
    return found_data

# --- 실행 버튼 ---
if st.sidebar.button("🚨 데이터 정밀 탐색 및 분석 시작"):
    if target_file is None:
        st.warning("분석할 파일을 먼저 선택하거나 업로드하세요.")
    else:
        try:
            with st.spinner("🔍 데이터셋 내부 컬럼 전수 조사 중..."):
                result = analyze_k_protocol(target_file)

            if not result or 'samples' not in result:
                st.error("❌ 파일 내에서 질량 데이터를 찾을 수 없습니다. (컬럼 내부까지 모두 탐색함)")
                # 디버깅용 정보 출력
                with h5py.File(target_file, "r") as f:
                    st.write("발견된 최상위 데이터 그룹:")
                    st.write(list(f.keys()))
                    if "Overall_posterior" in f and isinstance(f["Overall_posterior"], h5py.Dataset):
                        if f["Overall_posterior"].dtype.names is not None:
                            st.write("Overall_posterior 내부 컬럼 목록:")
                            st.write(f["Overall_posterior"].dtype.names)
            else:
                m_chirp = result['samples']
                st.success(f"🎯 데이터 확보 완료! (탐색 경로: `{result['path']}`)")

                # --- K-PROTOCOL 보정 연산 ---
                g_h1 = 9.8073527
                correction_factor = (np.pi**2 / g_h1)**3
                corrected = m_chirp / correction_factor

                # --- 결과 리포트 (Metric) ---
                col1, col2, col3 = st.columns(3)
                col1.metric("확보된 샘플 수", f"{len(m_chirp):,}")
                col2.metric("표준 평균 질량", f"{np.mean(m_chirp):.4f} M☉")
                col3.metric("K-보정 절대 질량", f"{np.mean(corrected):.4f} M☉", 
                           delta=f"{np.mean(corrected)-np.mean(m_chirp):.4f}", delta_color="inverse")

                # --- 시각화 (Plotly) ---
                st.write("### 📊 데이터 분포 비교 분석")
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=m_chirp, name="LVC Raw (Standard)", 
                                         nbinsx=50, opacity=0.6, marker_color='#FF4B4B'))
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

        except Exception as e:
            st.error(f"⚠️ 분석 중 오류 발생: {e}")

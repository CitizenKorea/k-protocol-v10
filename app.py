import streamlit as st
import h5py
import numpy as np
import plotly.graph_objects as go

# 깃허브에 올린 파일 이름과 정확히 맞추세요
MY_FILE = "GW170814_GWTC-1.hdf5" 

st.set_page_config(page_title="K-PROTOCOL Absolute Proof", layout="wide")
st.title("🛡️ K-PROTOCOL: 실측 데이터 확정적 검증")

if st.sidebar.button("🚨 데이터 정밀 탐색 및 분석 시작"):
    if not os.path.exists(MY_FILE):
        st.error(f"❌ '{MY_FILE}' 파일이 없습니다. 깃허브 업로드와 파일명을 다시 확인하세요.")
        st.stop()

    try:
        with h5py.File(MY_FILE, "r") as f:
            st.info("🔍 파일 내부 구조를 탐색 중입니다...")
            
            all_datasets = []
            m_chirp = None

            # 파일 내의 모든 경로를 뒤져서 데이터셋 목록을 만들고 chirp_mass를 찾습니다.
            def scan_file(name, obj):
                global m_chirp
                if isinstance(obj, h5py.Dataset):
                    all_datasets.append(name)
                    # chirp_mass, mchirp, mc 등 유사한 이름을 모두 찾습니다.
                    target_names = ['chirp_mass', 'mchirp', 'mc', 'm_chirp']
                    if any(tn in name.lower() for tn in target_names):
                        m_chirp = obj[:]
                        st.success(f"🎯 데이터를 찾았습니다! 경로: `{name}`")

            f.visititems(scan_file)

            # 만약 못 찾았다면 파일 구조를 보여줍니다.
            if m_chirp is None:
                st.error("❌ 'chirp_mass' 관련 데이터를 찾지 못했습니다.")
                st.write("### 발견된 데이터 목록 (이 중 하나가 질량 데이터일 수 있습니다):")
                st.write(all_datasets)
            else:
                st.success(f"데이터 확보 완료: {len(m_chirp):,}개의 확률 점 발견")
                
                # K-PROTOCOL 보정 수식 (Appendix B.3.2)
                # Hanford(H1)의 중력값 기준으로 세제곱 보정
                g_h1 = 9.8073527
                s_h1_cube = (np.pi**2 / g_h1)**3
                corrected = m_chirp * (1 / s_h1_cube)
                
                # 시각화: 구름의 수렴 확인
                fig = go.Figure()
                fig.add_trace(go.Violin(y=m_chirp, name="LVC Raw (Standard)", line_color='red'))
                fig.add_trace(go.Violin(y=corrected, name="K-Corrected (Absolute)", line_color='blue'))
                fig.update_layout(title="LVC 표준 분포 vs K-PROTOCOL 보정 분포", yaxis_title="Chirp Mass (M☉)")
                st.plotly_chart(fig, use_container_width=True)
                
                # 결과 수치 출력
                st.write(f"### 분석 결과")
                st.write(f"- **표준 평균 질량:** {np.mean(m_chirp):.6f} M☉")
                st.write(f"- **K-PROTOCOL 절대 질량:** {np.mean(corrected):.6f} M☉")

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")

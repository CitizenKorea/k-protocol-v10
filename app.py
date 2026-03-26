import streamlit as st
import h5py
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# 깃허브에 올린 파일 이름과 똑같이 적어주세요
MY_FILE = "GW170814_posterior_samples.h5" 

st.set_page_config(page_title="K-PROTOCOL Absolute Proof", layout="wide")
st.title("🛡️ K-PROTOCOL: 실측 데이터 확정적 검증")

if st.sidebar.button("🚨 내 리포지토리 데이터 분석 시작"):
    try:
        # 깃허브 리포지토리에 같이 들어있는 파일을 직접 읽습니다.
        with h5py.File(MY_FILE, "r") as f:
            m_chirp = None
            # 파일 내부를 뒤져서 chirp_mass 데이터셋을 찾습니다.
            def find_mass(name, obj):
                global m_chirp
                if 'chirp_mass' in name.lower() and isinstance(obj, h5py.Dataset):
                    m_chirp = obj[:]
                    return True
            f.visititems(find_mass)

            if m_chirp is not None:
                st.success(f"데이터 확보 완료: {len(m_chirp):,}개의 확률 점 발견")
                
                # K-PROTOCOL 보정 수식 (Appendix B.3.2)
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
            else:
                st.error("파일 구조 내에서 chirp_mass를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

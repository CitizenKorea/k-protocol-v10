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

# --- 1. 다국어 지원 텍스트 사전 (Korean / English) ---
lang_dict = {
    "Korean": {
        "page_title": "K-PROTOCOL 실측 데이터 확정적 검증 엔진",
        "app_title": "🛡️ K-PROTOCOL: 실측 데이터 확정적 검증 엔진",
        "intro": "LIGO/Virgo의 실제 관측 확률 데이터(Posterior Samples)를 K-PROTOCOL의 기하학적 렌즈 모델에 대입합니다. \n\nLVC가 뭉뚱그려놓은 **네트워크 평균(Network Combined)** 데이터에는 **지구 평균 렌즈($S_{earth}$)**를 적용하여 렌즈를 벗겨내는 것이 논리적으로 완벽한 역공학(Reverse Engineering)입니다.",
        "sidebar_lang": "🌐 언어 / Language",
        "sidebar_setting": "⚙️ 분석 설정",
        "data_source_label": "📁 데이터 소스 선택",
        "source_local": "로컬 서버 파일",
        "source_upload": "파일 직접 업로드",
        "file_connected": "✅ {} 연결됨",
        "file_not_found": "❌ '{}' 파일이 서버에 없습니다.",
        "upload_label": "HDF5 파일 업로드",
        "lens_header": "🔭 역보정 렌즈 타겟 선택",
        "lens_desc": "데이터의 출처에 맞는 중력 렌즈를 선택하여 렌즈 효과를 제거(역보정)합니다.",
        "lens_earth": "🌍 지구 표준 평균 (네트워크 데이터용)",
        "lens_h1": "🇺🇸 Hanford (H1) 단일 관측소",
        "lens_l1": "🇺🇸 Livingston (L1) 단일 관측소",
        "lens_v1": "🇮🇹 Virgo (V1) 단일 관측소",
        "lens_select": "렌즈 종류",
        "btn_start": "🚨 실측 데이터 렌즈 해체 시작",
        "warn_no_file": "분석할 파일을 먼저 선택하거나 업로드하세요.",
        "spin_search": "🔍 데이터셋 내부 컬럼 전수 조사 및 질량 합성 중...",
        "err_no_data": "❌ 파일 내에서 질량 데이터를 찾을 수 없습니다.",
        "succ_data": "🎯 실측 데이터 확보 완료! (추출 경로: `{}`)",
        "met_samples": "확보된 실측 샘플 수",
        "met_gravity": "선택된 국소 중력 ($g$)",
        "met_lvc": "LVC 원시 평균 질량",
        "met_k": "우주 절대 질량 (K-보정)",
        "plot_header": "### 📊 실측 데이터 렌즈 역보정 (Shift) 시각화",
        "plot_desc": "선택하신 렌즈(**{}**)의 왜곡 지수($S_{{loc}}^3 = {:.6f}$)를 제거하여, 가짜 질량 데이터가 실제 우주의 절대 질량으로 통째로 이동(Shift)하는 과정을 보여줍니다.",
        "plot_leg_raw": "LVC 원시 데이터 (렌즈 왜곡됨)",
        "plot_leg_k": "K-PROTOCOL 절대 질량 (렌즈 제거됨)",
        "plot_title": "렌즈 왜곡 제거에 따른 질량 분포 이동 ({})",
        "plot_x": "계산된 Chirp Mass (M☉)",
        "plot_y": "확률 밀도 빈도수 (Frequency)",
        "err_analysis": "⚠️ 분석 중 오류 발생: {}"
    },
    "English": {
        "page_title": "K-PROTOCOL Empirical Proof Engine",
        "app_title": "🛡️ K-PROTOCOL: Empirical Data Proof Engine",
        "intro": "Applies K-PROTOCOL's geometric lens model to actual LIGO/Virgo posterior samples. \n\nApplying the **Earth Standard Lens ($S_{earth}$)** to LVC's **Network Combined** data is the logically perfect reverse engineering method to remove the lens effect and reveal the absolute cosmic mass.",
        "sidebar_lang": "🌐 Language / 언어",
        "sidebar_setting": "⚙️ Analysis Settings",
        "data_source_label": "📁 Select Data Source",
        "source_local": "Local Server File",
        "source_upload": "Direct File Upload",
        "file_connected": "✅ {} Connected",
        "file_not_found": "❌ File '{}' not found on server.",
        "upload_label": "Upload HDF5 File",
        "lens_header": "🔭 Select Calibration Lens Target",
        "lens_desc": "Select the gravitational lens matching the data source to remove the distortion effect.",
        "lens_earth": "🌍 Earth Standard Avg (For Network Data)",
        "lens_h1": "🇺🇸 Hanford (H1) Single Observatory",
        "lens_l1": "🇺🇸 Livingston (L1) Single Observatory",
        "lens_v1": "🇮🇹 Virgo (V1) Single Observatory",
        "lens_select": "Lens Type",
        "btn_start": "🚨 Start Empirical Data Lens Deconstruction",
        "warn_no_file": "Please select or upload a file to analyze first.",
        "spin_search": "🔍 Scanning dataset columns and synthesizing mass...",
        "err_no_data": "❌ Mass data could not be found in the file.",
        "succ_data": "🎯 Empirical data secured! (Extraction path: `{}`)",
        "met_samples": "Secured Empirical Samples",
        "met_gravity": "Selected Local Gravity ($g$)",
        "met_lvc": "LVC Raw Average Mass",
        "met_k": "Absolute Cosmic Mass (K-Cal)",
        "plot_header": "### 📊 Visualizing Empirical Data Calibration (Shift)",
        "plot_desc": "By removing the distortion index ($S_{{loc}}^3 = {:.6f}$) of your selected lens (**{}**), the fake mass data shifts entirely to the true absolute mass of the universe.",
        "plot_leg_raw": "LVC Raw Data (Lens Distorted)",
        "plot_leg_k": "K-PROTOCOL Absolute Mass (Lens Removed)",
        "plot_title": "Mass Distribution Shift by Lens Removal ({})",
        "plot_x": "Calculated Chirp Mass (M☉)",
        "plot_y": "Probability Density Frequency",
        "err_analysis": "⚠️ Error during analysis: {}"
    }
}

# --- 2. 언어 선택 (사이드바 최상단) ---
st.sidebar.header(lang_dict["Korean"]["sidebar_lang"])
selected_lang = st.sidebar.radio("언어 선택", ("Korean", "English"), label_visibility="collapsed")
T = lang_dict[selected_lang]

# --- 3. 메인 화면 ---
st.title(T["app_title"])
st.markdown(T["intro"])
st.divider()

# --- 4. 내부 핵심 변수 (언어에 영향받지 않음) ---
internal_source_keys = ["local", "upload"]
source_labels = {
    "local": T["source_local"],
    "upload": T["source_upload"]
}

internal_lens_keys = ["earth", "h1", "l1", "v1"]
lens_g_values = {
    "earth": 9.80665,
    "h1": 9.8073527,
    "l1": 9.7936814,
    "v1": 9.8053340
}
lens_labels = {
    "earth": T["lens_earth"],
    "h1": T["lens_h1"],
    "l1": T["lens_l1"],
    "v1": T["lens_v1"]
}

# --- 5. 사이드바 및 파일 설정 ---
st.sidebar.markdown("---")
st.sidebar.header(T["sidebar_setting"])
selected_source_key = st.sidebar.radio(
    T["data_source_label"], 
    internal_source_keys, 
    format_func=lambda x: source_labels[x]
)

target_file = None
if selected_source_key == "local":
    if os.path.exists(MY_FILE):
        target_file = MY_FILE
        st.sidebar.success(T["file_connected"].format(MY_FILE))
    else:
        st.sidebar.error(T["file_not_found"].format(MY_FILE))
else:
    uploaded_file = st.sidebar.file_uploader(T["upload_label"], type=["hdf5", "h5", "h5py"])
    if uploaded_file:
        target_file = uploaded_file

st.sidebar.markdown("---")
st.sidebar.header(T["lens_header"])
st.sidebar.markdown(T["lens_desc"])

selected_lens_key = st.sidebar.radio(
    T["lens_select"], 
    internal_lens_keys, 
    format_func=lambda x: lens_labels[x], 
    label_visibility="collapsed"
)

g_target = lens_g_values[selected_lens_key]
selected_lens_text = lens_labels[selected_lens_key]

# --- 핵심 분석 함수 ---
def analyze_k_protocol(file_obj):
    found_data = {}
    
    def scan_file(name, obj):
        if 'samples' in found_data: 
            return

        if isinstance(obj, h5py.Dataset):
            if obj.dtype.names is not None:
                fields = obj.dtype.names
                target_names = ['chirp_mass', 'mchirp', 'mc', 'm_chirp']
                for field in fields:
                    if any(tn in field.lower() for tn in target_names):
                        found_data['path'] = f"{name} ['{field}']"
                        found_data['samples'] = obj[field]
                        return
                
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
                    mc = ((m1 * m2)**(3/5)) / ((m1 + m2)**(1/5))
                    found_data['path'] = f"{name} (계산됨: {m1_field} & {m2_field})"
                    found_data['samples'] = mc
                    return
            else:
                target_names = ['chirp_mass', 'mchirp', 'mc', 'm_chirp']
                if any(tn in name.lower() for tn in target_names):
                    found_data['path'] = name
                    found_data['samples'] = obj[:]
                    return

    with h5py.File(file_obj, "r") as f:
        if "Overall_posterior" in f:
            scan_file("Overall_posterior", f["Overall_posterior"])
        if 'samples' not in found_data:
            f.visititems(scan_file)
            
    return found_data

# --- 실행 버튼 ---
if st.sidebar.button(T["btn_start"]):
    if target_file is None:
        st.warning(T["warn_no_file"])
    else:
        try:
            with st.spinner(T["spin_search"]):
                result = analyze_k_protocol(target_file)

            if not result or 'samples' not in result:
                st.error(T["err_no_data"])
            else:
                m_chirp = result['samples']
                st.success(T["succ_data"].format(result['path']))

                # --- K-PROTOCOL 보정 연산 ---
                pi_sq = np.pi**2
                s_loc = pi_sq / g_target
                corrected = m_chirp * ((1 / s_loc)**3)

                # --- 결과 리포트 (Metric) ---
                col1, col2, col3, col4 = st.columns(4)
                col1.metric(T["met_samples"], f"{len(m_chirp):,}")
                col2.metric(T["met_gravity"], f"{g_target:.7f}")
                col3.metric(T["met_lvc"], f"{np.mean(m_chirp):.4f} M☉")
                col4.metric(T["met_k"], f"{np.mean(corrected):.4f} M☉", 
                           delta=f"{np.mean(corrected)-np.mean(m_chirp):.4f}", delta_color="inverse")

                # --- 시각화 (Plotly) ---
                st.write(T["plot_header"])
                
                # 렌즈 이름 파싱 (이모지 및 부가설명 제거)
                clean_lens_name = selected_lens_text.split(" ")[1] if " " in selected_lens_text else selected_lens_text
                
                st.markdown(T["plot_desc"].format(clean_lens_name, s_loc**3))
                
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=m_chirp, name=T["plot_leg_raw"], 
                                         nbinsx=100, opacity=0.6, marker_color='#FF4B4B'))
                fig.add_trace(go.Histogram(x=corrected, name=T["plot_leg_k"], 
                                         nbinsx=100, opacity=0.7, marker_color='#0068C9'))

                fig.update_layout(
                    barmode='overlay',
                    title=T["plot_title"].format(clean_lens_name),
                    xaxis_title=T["plot_x"],
                    yaxis_title=T["plot_y"],
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(255,255,255,0.8)'),
                    plot_bgcolor='white'
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
                
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(T["err_analysis"].format(e))

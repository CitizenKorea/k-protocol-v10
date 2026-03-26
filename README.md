# 🔭 K-PROTOCOL: Empirical Data Proof Engine
> **Reverse-engineering and calibrating LIGO/Virgo gravitational wave data based on the K-PROTOCOL geometric lens model.**

---

## 🇰🇷 한국어 (Korean)

### 📌 프로젝트 개요
본 프로젝트는 **K-PROTOCOL** 이론에 기반하여, LIGO/Virgo 관측소에서 발표한 중력파 실측 데이터(GWTC-1 등)에 포함된 '가짜 질량(Fake Mass)' 왜곡을 제거하는 정밀 역공학 도구입니다. 

지구의 국소 중력 환경이 관측 데이터에 미치는 렌즈 효과를 시각화하고, 이를 보정하여 우주의 **절대 질량(Absolute Cosmic Mass)**을 도출하는 과정을 투명하게 공개합니다.

### 🚀 핵심 기능
*   **실측 데이터 직접 분석:** LIGO의 `.hdf5` 포스터리어 샘플(Posterior Samples)을 직접 로드하여 분석합니다.
*   **다국어 지원 (한/영):** 사이드바의 라디오 버튼을 통해 인터페이스 언어를 실시간으로 전환합니다. (에러 방지 로직 탑재)
*   **국소 렌즈 역보정:** 
    *   🌍 **지구 표준 평균 ($S_{earth}$):** 네트워크 통합 데이터 보정용
    *   🇺🇸 **Hanford (H1) / Livingston (L1):** 단일 관측소 데이터 정밀 보정용
    *   🇮🇹 **Virgo (V1):** 유럽 관측소 데이터 보정용
*   **실시간 질량 합성 엔진:** 데이터셋 내에 `Chirp Mass` 컬럼이 직접 없더라도, $m_1, m_2$ 데이터를 탐색하여 물리 공식으로 자동 합성합니다.
*   **인터랙티브 시각화:** Plotly를 활용하여 렌즈 보정 전후의 질량 분포 이동(Shift)을 정밀하게 보여줍니다.

### 🛠 설치 및 실행 방법
1.  **저장소 클론:**
    ```bash
    git clone [https://github.com/your-username/k-protocol-v10.git](https://github.com/your-username/k-protocol-v10.git)
    cd k-protocol-v10
    ```
2.  **필수 라이브러리 설치:**
    ```bash
    pip install streamlit h5py numpy plotly
    ```
3.  **애플리케이션 실행:**
    ```bash
    streamlit run app.py
    ```

---

## 🇺🇸 English (English)

### 📌 Project Overview
This project is a high-precision reverse-engineering tool based on the **K-PROTOCOL** theory. It is designed to identify and remove 'Fake Mass' distortions in empirical gravitational wave data (e.g., GWTC-1) released by the LIGO/Virgo collaboration.

By visualizing how the Earth's local gravitational environment distorts observations, this engine calibrates the data to reveal the **Absolute Cosmic Mass** of binary black hole systems.

### 🚀 Key Features
*   **Empirical Data Analysis:** Directly loads and analyzes LIGO's `.hdf5` posterior samples.
*   **Multilingual Support (KR/EN):** Real-time language switching via the sidebar with robust error-handling logic.
*   **Local Lens Calibration:** 
    *   🌍 **Earth Standard Avg ($S_{earth}$):** For calibrating network-combined data.
    *   🇺🇸 **Hanford (H1) / Livingston (L1):** For precise single-observatory calibration.
    *   🇮🇹 **Virgo (V1):** For European observatory data calibration.
*   **Real-time Mass Synthesis Engine:** Automatically finds $m_1, m_2$ and synthesizes `Chirp Mass` if the column is missing in the dataset.
*   **Interactive Visualization:** Utilizes Plotly to display the distribution shift before and after lens calibration.

### 🛠 Installation & Quick Start
1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/k-protocol-v10.git](https://github.com/your-username/k-protocol-v10.git)
    cd k-protocol-v10
    ```
2.  **Install Dependencies:**
    ```bash
    pip install streamlit h5py numpy plotly
    ```
3.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

---

### ⚠️ Disclaimer
This software is intended for theoretical physics research and verification of the K-PROTOCOL. All calculations are performed based on the geometric lens models proposed in the theory.

---
© 2026 K-PROTOCOL Project. All Rights Reserved.

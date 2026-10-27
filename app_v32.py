
import json
import calendar
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="나의 운동 도우미",
    page_icon="💪",
    layout="wide"
)

DATA_FILE = Path(__file__).with_name("workout_data.json")

# =====================================================
# 디자인
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

html, body, [class*="stApp"] {
    font-family: 'Noto Sans KR', sans-serif;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #f1f5ff, #f4fbf7, #eef7ff);
}
.block-container {
    max-width: 1320px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
h1, h2, h3 {
    color: #243b53;
    font-weight: 750;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #e8efff, #edf8f1);
}
div.stButton > button,
div.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] button,
button[kind="primary"],
button[kind="secondary"] {
    background: #E2F5D8 !important;
    background-color: #E2F5D8 !important;
    color: #315B3B !important;
    border: 1px solid #B8DDAA !important;
    border-radius: 12px !important;
    min-height: 42px;
    font-weight: 650;
    box-shadow: none !important;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover {
    background: #D4EDC8 !important;
    background-color: #D4EDC8 !important;
    color: #244C30 !important;
    border-color: #9CCB8C !important;
}
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    border: 1.5px solid #75B88B !important;
    border-radius: 12px !important;
    background: white !important;
}
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border: 2px solid #75B88B !important;
    box-shadow: 0 0 0 2px rgba(117,184,139,.15) !important;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,.94);
    border: 1px solid #dfe8f2;
    padding: 14px;
    border-radius: 16px;
}
[data-testid="stExpander"] {
    background: rgba(255,255,255,.8);
    border: 1px solid #dfe8f2;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 운동 데이터
# =====================================================
LEVELS = {
    "초보자": {"count": 3, "sets": 2, "rest": 75},
    "중급자": {"count": 5, "sets": 3, "rest": 60},
    "상급자": {"count": 6, "sets": 4, "rest": 60},
    "엘리트": {"count": 7, "sets": 4, "rest": 90},
}
ENVIRONMENTS = ["맨몸 운동", "덤벨 등 장비", "헬스장"]
BODY_PARTS = ["가슴", "등", "어깨", "팔", "복근", "하체", "전신"]

RAW_EXERCISES = {
    "가슴": [
        ("벽 푸시업", "맨몸", 3, 5, "벽에 손을 대고 몸을 천천히 가까이 가져갔다가 밀어냅니다.", ["가슴", "팔"], False),
        ("무릎 푸시업", "맨몸", 3.5, 5, "무릎을 바닥에 대고 몸통을 곧게 유지하며 팔을 굽혔다 폅니다.", ["가슴", "팔"], False),
        ("일반 푸시업", "맨몸", 3.8, 5, "몸을 일직선으로 유지하고 가슴을 낮췄다가 밀어 올립니다.", ["가슴", "팔"], True),
        ("손 넓게 푸시업", "맨몸", 4, 5, "손을 어깨보다 조금 넓게 두고 푸시업을 합니다.", ["가슴", "팔"], True),
        ("덤벨 플로어 프레스", "덤벨", 3.8, 6, "누워서 덤벨을 가슴 위로 밀어 올립니다.", ["가슴", "팔"], False),
        ("덤벨 플라이", "덤벨", 3.5, 6, "누워서 팔을 양옆으로 벌렸다가 가슴 위로 모읍니다.", ["가슴", "어깨"], False),
        ("체스트 프레스", "헬스장", 4, 6, "기구 손잡이를 가슴 앞에서 앞으로 밀어냅니다.", ["가슴", "팔"], False),
        ("펙덱 플라이", "헬스장", 3.8, 6, "기구 패드를 가슴 앞에서 모았다가 천천히 벌립니다.", ["가슴"], False),
    ],
    "등": [
        ("버드독", "맨몸", 3, 5, "네발기기 자세에서 반대쪽 팔과 다리를 뻗습니다.", ["등", "복근"], False),
        ("슈퍼맨", "맨몸", 3.2, 5, "엎드려 팔과 다리를 무리하지 않는 범위에서 들어 올립니다.", ["등"], False),
        ("벽 천사", "맨몸", 2.8, 5, "벽에 등을 대고 팔을 편안한 범위에서 위아래로 움직입니다.", ["등", "어깨"], False),
        ("덤벨 로우", "덤벨", 3.8, 6, "상체를 숙이고 덤벨을 허리 쪽으로 당깁니다.", ["등", "팔"], False),
        ("덤벨 리버스 플라이", "덤벨", 3.5, 5, "상체를 숙인 채 가벼운 덤벨을 양옆으로 벌립니다.", ["등", "어깨"], False),
        ("랫풀다운", "헬스장", 4, 6, "바를 목 뒤가 아닌 가슴 앞으로 당깁니다.", ["등", "팔"], False),
        ("시티드 로우", "헬스장", 4, 6, "허리를 세우고 손잡이를 배 쪽으로 당깁니다.", ["등", "팔"], False),
    ],
    "어깨": [
        ("어깨 돌리기", "맨몸", 2.5, 4, "어깨에 힘을 빼고 천천히 앞뒤로 돌립니다.", ["어깨"], False),
        ("맨손 팔 들기", "맨몸", 2.8, 5, "팔을 양옆으로 어깨 높이까지 천천히 들어 올립니다.", ["어깨"], False),
        ("벽 엔젤", "맨몸", 2.8, 5, "벽에 등을 대고 팔을 편안한 범위에서 움직입니다.", ["어깨", "등"], False),
        ("팔 원 그리기", "맨몸", 2.5, 4, "팔을 옆으로 들고 작은 원을 천천히 그립니다.", ["어깨"], False),
        ("덤벨 숄더 프레스", "덤벨", 4, 6, "덤벨을 어깨 높이에서 머리 위로 밀어 올립니다.", ["어깨", "팔"], False),
        ("레터럴 레이즈", "덤벨", 3.5, 5, "가벼운 덤벨을 몸 옆에서 어깨 높이까지 들어 올립니다.", ["어깨"], False),
        ("머신 숄더 프레스", "헬스장", 4, 6, "기구 손잡이를 머리 위로 천천히 밀어 올립니다.", ["어깨", "팔"], False),
    ],
    "팔": [
        ("팔꿈치 굽혔다 펴기", "맨몸", 2.5, 4, "팔꿈치를 편안하게 굽혔다 펴며 관절을 부드럽게 움직입니다.", ["팔"], False),
        ("벽 삼두근 푸시업", "맨몸", 3, 5, "벽을 짚고 팔꿈치를 몸 가까이에 두어 밀어냅니다.", ["팔", "가슴"], False),
        ("수건 당기기", "맨몸", 2.5, 4, "수건 양끝을 잡고 양옆으로 당깁니다.", ["팔"], False),
        ("덤벨 컬", "덤벨", 3.5, 6, "팔꿈치를 몸 옆에 두고 덤벨을 들어 올립니다.", ["팔"], False),
        ("해머 컬", "덤벨", 3.5, 6, "엄지가 위를 향하게 덤벨을 잡고 팔꿈치를 굽힙니다.", ["팔"], False),
        ("덤벨 킥백", "덤벨", 3.3, 5, "상체를 숙이고 팔꿈치를 고정한 채 팔을 뒤로 폅니다.", ["팔"], False),
        ("케이블 푸시다운", "헬스장", 3.8, 6, "팔꿈치를 고정하고 케이블 손잡이를 아래로 누릅니다.", ["팔"], False),
    ],
    "복근": [
        ("복식 호흡", "맨몸", 2, 4, "편안하게 호흡하면서 배에 부드럽게 힘을 줍니다.", ["복근"], False),
        ("데드버그", "맨몸", 3, 5, "누워서 반대쪽 팔과 다리를 번갈아 뻗습니다.", ["복근"], False),
        ("플랭크", "맨몸", 3.5, 5, "몸통이 꺾이지 않게 복부에 힘을 주고 버팁니다.", ["복근"], False),
        ("크런치", "맨몸", 3.3, 5, "누워서 복부에 힘을 주고 어깨를 살짝 들어 올립니다.", ["복근"], False),
        ("리버스 크런치", "맨몸", 3.5, 5, "무릎을 배 쪽으로 당기며 골반을 살짝 들어 올립니다.", ["복근"], False),
        ("바이시클 크런치", "맨몸", 3.8, 5, "반대쪽 팔꿈치와 무릎을 천천히 가까이합니다.", ["복근"], True),
        ("케이블 크런치", "헬스장", 3.8, 6, "복부에 힘을 주어 상체를 천천히 굽힙니다.", ["복근"], False),
    ],
    "하체": [
        ("의자 앉았다 일어나기", "맨몸", 3, 5, "안정적인 의자에 앉았다가 발바닥으로 바닥을 밀며 일어납니다.", ["하체"], False),
        ("종아리 들기", "맨몸", 2.8, 5, "벽을 짚고 발뒤꿈치를 들어 올렸다 내립니다.", ["하체"], False),
        ("글루트 브리지", "맨몸", 3, 5, "누워서 무릎을 세우고 엉덩이를 들어 올립니다.", ["하체"], False),
        ("스쿼트", "맨몸", 3.8, 6, "엉덩이를 뒤로 보내며 앉았다가 일어납니다.", ["하체"], True),
        ("뒤로 런지", "맨몸", 3.8, 5, "한 발을 뒤로 내딛고 무릎을 굽혔다 돌아옵니다.", ["하체"], True),
        ("고블릿 스쿼트", "덤벨", 4, 6, "덤벨을 가슴 앞에 들고 천천히 앉았다 일어납니다.", ["하체"], False),
        ("덤벨 루마니안 데드리프트", "덤벨", 4, 6, "등을 중립으로 유지하며 덤벨을 내렸다 들어 올립니다.", ["하체"], False),
        ("레그 프레스", "헬스장", 4, 6, "기구 발판을 밀고 무릎을 잠그지 않은 채 돌아옵니다.", ["하체"], False),
        ("레그 컬", "헬스장", 3.8, 6, "기구에서 허벅지 뒤쪽을 사용해 무릎을 굽힙니다.", ["하체"], False),
    ],
    "전신": [
        ("제자리 걷기", "맨몸", 2.8, 5, "팔을 자연스럽게 흔들며 제자리에서 걷습니다.", ["전신", "하체"], False),
        ("저충격 스텝 터치", "맨몸", 3.2, 5, "좌우로 한 발씩 옮기며 가볍게 움직입니다.", ["전신", "하체"], False),
        ("버드독", "맨몸", 3, 5, "네발기기 자세에서 반대쪽 팔과 다리를 뻗습니다.", ["전신", "등"], False),
        ("스쿼트", "맨몸", 3.8, 6, "엉덩이를 뒤로 보내며 앉았다가 일어납니다.", ["전신", "하체"], True),
        ("무릎 높여 걷기", "맨몸", 3.2, 5, "제자리에서 한쪽씩 무릎을 편안하게 들어 올립니다.", ["전신", "하체"], False),
        ("덤벨 데드리프트", "덤벨", 4, 7, "등을 중립으로 유지하며 덤벨을 내렸다 들어 올립니다.", ["전신", "등", "하체"], False),
        ("덤벨 스쿼트", "덤벨", 4, 6, "가벼운 덤벨을 들고 안정적으로 앉았다 일어납니다.", ["전신", "하체"], False),
        ("실내 자전거", "헬스장", 4, 7, "편안한 강도로 일정한 속도로 페달을 밟습니다.", ["전신", "하체"], False),
    ],
}


def make_exercises():
    return {
        part: [
            {
                "name": r[0],
                "equipment": r[1],
                "met": r[2],
                "minutes": r[3],
                "tip": r[4],
                "parts": r[5],
                "impact": "높음" if r[6] else "낮음",
            }
            for r in rows
        ]
        for part, rows in RAW_EXERCISES.items()
    }


EXERCISES = make_exercises()


# =====================================================
# 자극 부위 이미지
# =====================================================
def muscle_svg(body):
    red = "#E84949"
    skin = "#E7ECE9"
    outline = "#879A92"

    head = """
    <path d="M105 20 Q105 7 120 7 Q135 7 135 20
    L133 35 Q130 43 120 43 Q110 43 107 35 Z"/>
    """

    body_base = """
    <path d="M112 39 L112 51 L128 51 L128 39 Z"/>
    <path d="M111 47 Q98 48 86 56 L76 78 Q75 86 83 88
    L94 69 L96 111 Q120 122 144 111 L146 69 L157 88
    Q165 86 164 78 L154 56 Q142 48 129 47 Z"/>
    <path d="M86 57 Q78 62 76 74 L65 104 Q63 110 69 113
    Q74 115 77 108 L91 79 L98 63 Z"/>
    <path d="M154 57 Q162 62 164 74 L175 104 Q177 110 171 113
    Q166 115 163 108 L149 79 L142 63 Z"/>
    <path d="M97 109 Q106 115 118 115 L115 155 L108 198
    Q105 204 99 201 Q95 199 97 192 L98 154 L91 119 Z"/>
    <path d="M122 115 Q134 115 143 109 L149 119 L142 154
    L143 192 Q145 199 139 201 Q133 204 130 198 L125 155 Z"/>
    """

    shapes = {
        "가슴": """
        <path d="M96 59 Q105 52 118 58 L118 78
        Q106 81 97 72 Z"/>
        <path d="M122 58 Q135 52 144 59 L143 72
        Q134 81 122 78 Z"/>
        """,
        "등": """
        <path d="M99 55 Q108 50 118 54 L118 91
        Q107 91 99 82 Z"/>
        <path d="M122 54 Q132 50 141 55 L141 82
        Q133 91 122 91 Z"/>
        """,
        "어깨": """
        <path d="M98 52 Q89 52 85 61 Q83 69 92 72 L101 61 Z"/>
        <path d="M142 52 Q151 52 155 61 Q157 69 148 72 L139 61 Z"/>
        """,
        "팔": """
        <path d="M84 64 Q80 70 77 82 L70 103
        Q72 108 75 103 L87 78 L93 66 Z"/>
        <path d="M156 64 Q160 70 163 82 L170 103
        Q168 108 165 103 L153 78 L147 66 Z"/>
        """,
        "복근": """
        <path d="M108 79 Q120 82 132 79 L132 108
        Q120 114 108 108 Z"/>
        """,
        "하체": """
        <path d="M98 117 L116 119 L112 151 L106 179
        L101 192 L98 190 L100 153 Z"/>
        <path d="M124 119 L142 117 L140 153 L142 190
        L139 192 L134 179 L128 151 Z"/>
        """,
        "전신": """
        <path d="M96 59 Q105 52 118 58 L118 78 Q106 81 97 72 Z"/>
        <path d="M122 58 Q135 52 144 59 L143 72 Q134 81 122 78 Z"/>
        <path d="M98 52 Q89 52 85 61 L92 72 L101 61 Z"/>
        <path d="M142 52 Q151 52 155 61 L148 72 L139 61 Z"/>
        <path d="M108 79 Q120 82 132 79 L132 108 Q120 114 108 108 Z"/>
        <path d="M84 64 L77 82 L70 103 L75 103 L87 78 Z"/>
        <path d="M156 64 L163 82 L170 103 L165 103 L153 78 Z"/>
        <path d="M98 117 L116 119 L112 151 L106 179 L101 192 L98 190 L100 153 Z"/>
        <path d="M124 119 L142 117 L140 153 L142 190 L139 192 L134 179 L128 151 Z"/>
        """
    }

    selected = shapes.get(body, shapes["전신"])

    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 225"
         width="100%" height="280" role="img">
      <defs>
        <linearGradient id="skinGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#FAFCFB"/>
          <stop offset="100%" stop-color="{skin}"/>
        </linearGradient>
      </defs>
      <g fill="url(#skinGrad)" stroke="{outline}" stroke-width="1.5"
         stroke-linejoin="round">
        {head}
        {body_base}
      </g>
      <g fill="{red}" stroke="#F2A0A0" stroke-width="0.7"
         stroke-linejoin="round">
        {selected}
      </g>
      <g fill="none" stroke="{outline}" stroke-width="0.7" opacity="0.55">
        <path d="M120 48 L120 112"/>
        <path d="M96 72 Q120 82 144 72"/>
        <path d="M98 117 L120 122 L142 117"/>
      </g>
      <circle cx="48" cy="215" r="5" fill="{red}"/>
      <text x="59" y="219" font-size="10" fill="#526A62">
        주요 자극 부위
      </text>
    </svg>
    """


# =====================================================
# 데이터 관리
# =====================================================
def default_data():
    return {"profile": {}, "records": [], "weekly": {}, "memos": {}}


def load_data():
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                base = default_data()
                for key in base:
                    if key in raw and isinstance(raw[key], type(base[key])):
                        base[key] = raw[key]
                return base
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return default_data()


def save_data():
    try:
        DATA_FILE.write_text(
            json.dumps(st.session_state.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except OSError:
        return False


# Enter를 누르면 한 줄 메모를 저장합니다.
def save_memo(day_key):
    memo_key = f"memo_{day_key}"
    text = st.session_state.get(memo_key, "")

    st.session_state.data.setdefault("memos", {})
    st.session_state.data["memos"][day_key] = text.strip()

    save_data()


def equipment_ok(item, environment):
    if environment == "맨몸 운동":
        return item["equipment"] == "맨몸"
    if environment == "덤벨 등 장비":
        return item["equipment"] in ("맨몸", "덤벨")
    return True


def recommendations(body, environment, quiet, count):
    all_items = list(EXERCISES.get(body, EXERCISES["전신"]))

    for part, items in EXERCISES.items():
        if part != body:
            all_items.extend(items)

    result = []
    seen = set()

    for item in all_items:
        if item["name"] in seen:
            continue
        if not equipment_ok(item, environment):
            continue
        if quiet and item["impact"] == "높음":
            continue

        result.append(item)
        seen.add(item["name"])

        if len(result) >= count:
            break

    return result


def reps_for(item):
    name = item["name"]
    if "플랭크" in name:
        return "20~30초"
    if any(word in name for word in ["걷기", "자전거", "스텝"]):
        return "30~60초"
    if any(word in name for word in ["호흡", "돌리기", "원 그리기"]):
        return "10~15회 또는 30초"
    return "8~12회"


def estimate_calories(items, weight, level):
    cfg = LEVELS[level]
    active = sum(item["minutes"] for item in items) * cfg["sets"]

    kcal = sum(
        item["met"] * 3.5 * weight / 200
        * item["minutes"] * cfg["sets"]
        for item in items
    )

    rest = len(items) * max(0, cfg["sets"] - 1) * cfg["rest"] / 60
    return max(1, round(kcal)), round(active + rest)


# =====================================================
# 앱 초기 상태
# =====================================================
if "data" not in st.session_state:
    st.session_state.data = load_data()

if "page" not in st.session_state:
    st.session_state.page = "settings"

if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today().isoformat()

if "selected_exercises" not in st.session_state:
    st.session_state.selected_exercises = []

data = st.session_state.data
profile = data["profile"]


# =====================================================
# 사이드바
# =====================================================
with st.sidebar:
    st.title("🍃 나의 운동 도우미")

    if st.button("신체 정보 및 설정", use_container_width=True):
        st.session_state.page = "settings"
        st.rerun()

    if st.button("운동 기록 달력", use_container_width=True):
        st.session_state.page = "journal"
        st.rerun()

    st.caption("기록 파일: workout_data.json")


# =====================================================
# 설정 화면
# =====================================================
if st.session_state.page == "settings":
    st.title("나의 운동 도우미")
    st.write("신체 정보와 운동 환경을 설정해 주세요.")

    with st.form("profile_form"):
        left, right = st.columns(2)

        with left:
            age = st.number_input(
                "나이", 10, 100, int(profile.get("age", 25))
            )
            height = st.number_input(
                "키(cm)", 100.0, 230.0,
                float(profile.get("height", 170.0)), step=0.5
            )
            weight = st.number_input(
                "몸무게(kg)", 25.0, 250.0,
                float(profile.get("weight", 65.0)), step=0.5
            )

            levels = list(LEVELS)
            saved_level = profile.get("level", "초보자")
            level = st.selectbox(
                "운동 수준",
                levels,
                index=levels.index(saved_level) if saved_level in levels else 0
            )

        with right:
            saved_env = profile.get("environment", ENVIRONMENTS[0])
            environment = st.selectbox(
                "운동 환경",
                ENVIRONMENTS,
                index=ENVIRONMENTS.index(saved_env)
                if saved_env in ENVIRONMENTS else 0
            )

            noises = ["걱정돼요", "괜찮아요"]
            saved_noise = profile.get("noise", noises[0])
            noise = st.selectbox(
                "소음이 있는 운동",
                noises,
                index=noises.index(saved_noise)
                if saved_noise in noises else 0
            )

            purposes = [
                "체지방 감소", "근력 향상", "건강 유지",
                "체력 향상", "근육 증가", "운동 습관 만들기"
            ]
            saved_purpose = profile.get("purpose", purposes[0])
            purpose = st.selectbox(
                "운동 목표",
                purposes,
                index=purposes.index(saved_purpose)
                if saved_purpose in purposes else 0
            )

            frequency = st.selectbox(
                "주당 운동 횟수",
                [1, 2, 3, 4, 5, 6, 7],
                index=max(0, min(6, int(profile.get("frequency", 3)) - 1)),
                format_func=lambda x: f"주 {x}회"
            )

        submitted = st.form_submit_button(
            "설정 저장하고 달력으로 이동",
            type="primary",
            use_container_width=True
        )

    if submitted:
        data["profile"] = {
            "age": age,
            "height": height,
            "weight": weight,
            "level": level,
            "environment": environment,
            "noise": noise,
            "purpose": purpose,
            "frequency": frequency,
            "setup_complete": True
        }

        if save_data():
            st.session_state.page = "journal"
            st.rerun()
        else:
            st.error("설정을 저장하지 못했습니다. 파일 권한을 확인해 주세요.")


# =====================================================
# 운동 추천 화면
# =====================================================
elif st.session_state.page == "recommend":
    if not profile.get("setup_complete"):
        st.warning("먼저 신체 정보와 운동 설정을 입력해 주세요.")

        if st.button("설정 화면으로 이동"):
            st.session_state.page = "settings"
            st.rerun()

    else:
        st.title("오늘의 운동 추천")
        st.caption(f"운동 날짜: {st.session_state.selected_date}")

        body = st.selectbox("운동 부위", BODY_PARTS)
        level = profile.get("level", "초보자")
        cfg = LEVELS[level]

        quiet = (
            profile.get("environment") != "헬스장"
            and profile.get("noise") == "걱정돼요"
        )

        items = recommendations(
            body,
            profile.get("environment", ENVIRONMENTS[0]),
            quiet,
            cfg["count"]
        )

        left, right = st.columns([1, 1.3], gap="large")

        with left:
            st.markdown("### 자극 부위 이미지")

            components.html(
                muscle_svg(body),
                height=300,
                scrolling=False
            )

            st.caption(
                f"선택 부위: {body} · 붉게 색칠된 영역을 참고하세요."
            )

        with right:
            st.markdown("### 추천 운동 목록")
            st.write("운동을 마쳤다면 **운동 완료** 버튼을 눌러 표시하세요.")

            selected = set(st.session_state.selected_exercises)

            for i, item in enumerate(items):
                with st.container(border=True):
                    name_col, button_col = st.columns([2.2, 1])

                    with name_col:
                        st.markdown(f"**{item['name']}**")
                        st.caption(
                            f"장비: {item['equipment']} · 강도: {item['impact']}"
                        )

                    with button_col:
                        chosen = item["name"] in selected

                        if st.button(
                            "✓ 운동 완료" if chosen else "운동 완료",
                            key=f"exercise_{body}_{i}_{item['name']}",
                            use_container_width=True,
                            type="primary" if chosen else "secondary"
                        ):
                            if chosen:
                                selected.discard(item["name"])
                            else:
                                selected.add(item["name"])

                            st.session_state.selected_exercises = list(selected)
                            st.rerun()

                    st.caption(
                        f"권장: {cfg['sets']}세트 × {reps_for(item)}"
                        f" · 세트당 약 {item['minutes']}분"
                    )
                    st.write(item["tip"])

        selected_items = [
            item for item in items if item["name"] in selected
        ]

        if selected_items:
            kcal, mins = estimate_calories(
                selected_items,
                float(profile.get("weight", 65)),
                level
            )
        else:
            kcal, mins = 0, 0

        a, b, c = st.columns(3)
        a.metric("완료 표시한 운동", f"{len(selected_items)}개")
        b.metric("예상 시간", f"{mins}분")
        c.metric("예상 칼로리", f"{kcal} kcal")

        if st.button(
            "완료한 운동 기록 저장",
            type="primary",
            use_container_width=True
        ):
            if not selected_items:
                st.warning("운동을 하나 이상 완료 표시해 주세요.")
            else:
                data["records"].append({
                    "date": st.session_state.selected_date,
                    "body": body,
                    "level": level,
                    "exercises": [x["name"] for x in selected_items],
                    "sets": cfg["sets"],
                    "minutes": mins,
                    "kcal": kcal,
                    "kind": "추천 운동",
                    "details": [
                        {
                            "name": x["name"],
                            "sets": cfg["sets"],
                            "reps": reps_for(x)
                        }
                        for x in selected_items
                    ]
                })

                if save_data():
                    st.session_state.selected_exercises = []
                    st.session_state.page = "journal"
                    st.rerun()
                else:
                    st.error("운동 기록 저장에 실패했습니다.")

        if st.button("달력으로 돌아가기"):
            st.session_state.selected_exercises = []
            st.session_state.page = "journal"
            st.rerun()


# =====================================================
# 달력 화면
# =====================================================
elif st.session_state.page == "journal":
    st.title("운동 기록 달력")
    st.caption(
        "날짜별 운동을 시작하거나 메모를 작성하세요. "
        "메모를 입력하고 Enter를 누르면 저장됩니다."
    )

    today = date.today()
    years = list(range(today.year - 3, today.year + 3))

    c1, c2 = st.columns(2)

    with c1:
        year = st.selectbox(
            "연도", years, index=years.index(today.year)
        )

    with c2:
        month = st.selectbox(
            "월",
            list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda m: f"{m}월"
        )

    records = [
        r for r in data.get("records", [])
        if isinstance(r, dict)
    ]

    # 요일 표시
    for col, weekday in zip(
        st.columns(7),
        ["일", "월", "화", "수", "목", "금", "토"]
    ):
        col.markdown(f"**{weekday}**")

    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)

    for week in weeks:
        cols = st.columns(7, gap="small")

        for col, day in zip(cols, week):
            with col:
                if day.month != month:
                    st.write("")
                    continue

                day_key = day.isoformat()
                todays = [
                    r for r in records if r.get("date") == day_key
                ]

                memo = data.get("memos", {}).get(day_key, "")

                bg = (
                    "#DFF4E5" if todays
                    else "#EAF1FF" if day == today
                    else "#FFFFFF"
                )
                border = "#75B88B" if todays else "#D6E2EF"

                # 날짜 및 운동 기록 표시
                label = f"<b style='font-size:1.1rem'>{day.day}일</b>"

                if day == today:
                    label += (
                        "<br><span style='color:#4263A0;"
                        "font-size:.8rem'>오늘</span>"
                    )

                if todays:
                    label += (
                        "<br><span style='color:#286B53;"
                        "font-weight:700;font-size:.8rem'>"
                        f"운동 완료 {len(todays)}회</span>"
                    )

                    for record in todays[:2]:
                        names = ", ".join(record.get("exercises", []))
                        label += (
                            "<br><span style='font-size:.72rem'>"
                            f"{names[:45]}</span>"
                        )

                # 저장된 메모를 해당 날짜의 운동 목록 아래에 표시
                if memo:
                    safe_memo = (
                        memo.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace('"', "&quot;")
                        .replace("'", "&#39;")
                    )
                    label += (
                        "<br><span style='display:block;margin-top:5px;"
                        "padding:5px;background:#F0F8E9;"
                        "border-radius:6px;color:#315B3B;"
                        "font-size:.75rem;white-space:pre-wrap;"
                        "overflow-wrap:anywhere'>"
                        f"📝 {safe_memo}</span>"
                    )

                st.markdown(
                    f"<div style='padding:9px 7px;background:{bg};"
                    f"border:1px solid {border};border-radius:12px;"
                    f"min-height:90px;line-height:1.5;margin-bottom:5px'>"
                    f"{label}</div>",
                    unsafe_allow_html=True
                )

                if st.button(
                    "추천 운동",
                    key=f"start_{day_key}",
                    use_container_width=True
                ):
                    st.session_state.selected_date = day_key
                    st.session_state.selected_exercises = []
                    st.session_state.page = "recommend"
                    st.rerun()

                # 한 줄 메모: Enter 입력 시 on_change 콜백으로 저장
                with st.expander("＋ 메모", expanded=False):
                    st.caption(day_key)

                    memo_widget_key = f"memo_{day_key}"

                    # 기존 메모가 있으면 입력칸에 불러오기
                    if memo_widget_key not in st.session_state:
                        st.session_state[memo_widget_key] = memo

                    st.text_input(
                        "날짜 메모",
                        key=memo_widget_key,
                        placeholder="메모 입력 후 Enter를 누르세요",
                        label_visibility="collapsed",
                        on_change=save_memo,
                        args=(day_key,)
                    )

                    st.caption(
                        "Enter를 누르면 저장되고 달력 날짜 칸에 표시됩니다."
                    )

    # =================================================
    # 월간 요약
    # =================================================
    month_records = [
        r for r in records
        if str(r.get("date", "")).startswith(f"{year}-{month:02d}")
    ]

    st.divider()
    st.subheader(f"{year}년 {month}월 요약")

    completed_days = {
        r.get("date") for r in month_records if r.get("date")
    }
    st.metric("운동한 날짜", f"{len(completed_days)}일")

    if month_records:
        df = pd.DataFrame([
            {
                "날짜": r.get("date", ""),
                "부위": r.get("body", ""),
                "난이도": r.get("level", ""),
                "기록 종류": r.get("kind", "추천 운동"),
                "완료 운동": ", ".join(r.get("exercises", [])),
                "세트": r.get("sets", 0),
                "시간(분)": r.get("minutes", 0),
                "예상 칼로리": r.get("kcal", 0)
            }
            for r in month_records
        ])

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        with st.expander("운동별 세트 및 횟수 보기"):
            for record in month_records:
                st.markdown(
                    f"**{record.get('date', '')} · "
                    f"{', '.join(record.get('exercises', []))}**"
                )

                for detail in record.get("details", []):
                    st.write(
                        f"- {detail.get('name', '')}: "
                        f"{detail.get('sets', 1)}세트 × "
                        f"{detail.get('reps', '횟수 미기록')}"
                    )

        st.download_button(
            "이번 달 기록 CSV 다운로드",
            df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"workout_{year}-{month:02d}.csv",
            mime="text/csv"
        )

    # 삭제 시 설정과 메모는 유지
    st.divider()

    with st.expander("운동 기록 모두 삭제"):
        st.warning("삭제하면 저장된 운동 기록을 복구할 수 없습니다.")

        confirm_delete = st.checkbox(
            "운동 기록을 모두 삭제하는 데 동의합니다."
        )

        if st.button(
            "기록 삭제 확인",
            disabled=not confirm_delete
        ):
            data["records"] = []
            data["weekly"] = {}

            if save_data():
                st.success(
                    "운동 기록을 삭제했습니다. 설정과 메모는 유지됩니다."
                )
                st.rerun()
            else:
                st.error("기록 삭제 사항을 저장하지 못했습니다.")


st.divider()
st.caption(
    "운동 중 통증이나 어지러움이 생기면 중단하세요. "
    "칼로리는 참고용 추정치이며 실제 소모량과 다를 수 있습니다."
)

import datetime
import streamlit as st

# Page Configuration for Mobile
st.set_page_config(page_title="Corporate Quest", page_icon="⚔️", layout="centered")

# Initialize Connection to Streamlit's built-in persistent storage (SQLite database)
conn = st.connection("sql", type="sql")

# Create tables if they don't exist yet
with conn.session as s:
    s.execute(
        "CREATE TABLE IF NOT EXISTS user_stats (id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER, gold INTEGER, streak INTEGER, last_daily_date TEXT)"
    )
    s.execute(
        "CREATE TABLE IF NOT EXISTS quest_history (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, quest_type TEXT, xp_earned INTEGER, gold_earned INTEGER)"
    )
    s.execute(
        "CREATE TABLE IF NOT EXISTS stat_tree (name TEXT PRIMARY KEY, points INTEGER)"
    )
    s.commit()


# Load or Initialize User Data
def load_data():
    df_user = conn.query("SELECT * FROM user_stats WHERE id = 1", ttl=0)
    if df_user.empty:
        with conn.session as s:
            s.execute(
                "INSERT INTO user_stats (id, xp, level, gold, streak, last_daily_date) VALUES (1, 0, 1, 0, 0, '')"
            )
            for stat in ["Diplomacy", "Intellect", "Execution"]:
                s.execute(
                    "INSERT OR IGNORE INTO stat_tree (name, points) VALUES (:name, 0)",
                    {"name": stat},
                )
            s.commit()
        return 0, 1, 0, 0, ""
    else:
        row = df_user.iloc[0]
        return (
            int(row["xp"]),
            int(row["level"]),
            int(row["gold"]),
            int(row["streak"]),
            str(row["last_daily_date"]),
        )


def update_user(xp, level, gold, streak, last_daily_date):
    with conn.session as s:
        s.execute(
            "UPDATE user_stats SET xp=:xp, level=:level, gold=:gold, streak=:streak, last_daily_date=:last_daily WHERE id=1",
            {
                "xp": xp,
                "level": level,
                "gold": gold,
                "streak": streak,
                "last_daily": last_daily_date,
            },
        )
        s.commit()


def log_quest(quest_type, xp, gold):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with conn.session as s:
        s.execute(
            "INSERT INTO quest_history (timestamp, quest_type, xp_earned, gold_earned) VALUES (:ts, :qt, :xp, :gold)",
            {"ts": now, "qt": quest_type, "xp": xp, "gold": gold},
        )
        s.commit()


def update_stat(stat_name, amount):
    with conn.session as s:
        s.execute(
            "UPDATE stat_tree SET points = points + :amt WHERE name = :name",
            {"amt": amount, "name": stat_name},
        )
        s.commit()


# Load current stats into session state variables
xp, level, gold, streak, last_daily_date = load_data()
xp_needed = level * 300

# App Header / Character Sheet
st.title("⚔️ Corporate Quest RPG")
st.markdown(f"**Title:** Level {level} Operative")

# Progress Bar
progress = min(xp / xp_needed, 1.0)
st.progress(
    progress, text=f"XP: {xp} / {xp_needed} to Level {level + 1}"
)

col1, col2 = st.columns(2)
with col1:
    st.metric(label="💰 Gold Balance", value=gold)
with col2:
    st.metric(label="🛡️ Active Streak", value=f"{streak} Days")

st.divider()

# Level Up Logic Check
if xp >= xp_needed:
    xp -= xp_needed
    level += 1
    update_user(xp, level, gold, streak, last_daily_date)
    st.balloons()
    st.success(f"🎉 LEVEL UP! You are now Level {level}!")
    st.rerun()

# Quest Board (Logging Tasks)
st.subheader("📜 Quest Board")
st.markdown("Claim your rewards after finishing tasks in Microsoft To Do:")

col_a, col_b = st.columns(2)

with col_a:
    if st.button("🔴 Raid Boss\n(+500 XP, +100 Gold)", use_container_width=True):
        xp += 500
        gold += 100
        update_stat("Execution", 2)
        log_quest("Raid Boss", 500, 100)
        update_user(xp, level, gold, streak, last_daily_date)
        st.rerun()

    if st.button(
        "🟠 Dungeon Quest\n(+200 XP, +40 Gold)", use_container_width=True
    ):
        xp += 200
        gold += 40
        update_stat("Intellect", 1)
        log_quest("Dungeon Quest", 200, 40)
        update_user(xp, level, gold, streak, last_daily_date)
        st.rerun()

with col_b:
    if st.button("🟢 Side Quest\n(+50 XP, +10 Gold)", use_container_width=True):
        xp += 50
        gold += 10
        update_stat("Diplomacy", 1)
        log_quest("Side Quest", 50, 10)
        update_user(xp, level, gold, streak, last_daily_date)
        st.rerun()

    if st.button("🔵 Grunt Work\n(+10 XP, +2 Gold)", use_container_width=True):
        xp += 10
        gold += 2
        log_quest("Grunt Work", 10, 2)
        update_user(xp, level, gold, streak, last_daily_date)
        st.rerun()

# Inbox Zero Daily Bonus Section
st.divider()
st.subheader("📥 Daily Inbox Zero Bonus")
today_str = datetime.date.today().strftime("%Y-%m-%d")

if last_daily_date == today_str:
    st.success("✅ Inbox Zero bonus already claimed for today!")
else:
    st.info(
        "Did you clear your inbox by 5:00 PM? Claim your daily operational bonus!"
    )
    if st.button(
        "🎯 Claim Inbox Zero Bonus (+150 XP, +30 Gold)", use_container_width=True
    ):
        xp += 150
        gold += 30
        last_daily_date = today_str
        log_quest("Inbox Zero Bonus", 150, 30)
        update_user(xp, level, gold, streak, last_daily_date)
        st.success("Bonus claimed! Well cleared.")
        st.rerun()

st.divider()

# Character Stats Display
st.subheader("📊 Stat Tree")
df_stats = conn.query("SELECT * FROM stat_tree", ttl=0)
for index, row in df_stats.iterrows():
    st.text(f"{row['name']}: {row['points']} pts")

st.divider()

# Loot Shop (Redeeming Real-World Rewards)
st.subheader("🛒 The Loot Shop")
rewards = {
    "☕ Specialty Coffee (200 Gold)": 200,
    "🚪 Early Friday Logout (1,000 Gold)": 1000,
    "🎮 15 Mins Guilt-Free Break (150 Gold)": 150,
}

for item, cost in rewards.items():
    if st.button(f"Buy: {item}", use_container_width=True):
        if gold >= cost:
            gold -= cost
            update_user(xp, level, gold, streak, last_daily_date)
            log_quest(f"Purchased: {item.split('(')[0]}", 0, -cost)
            st.success(f"Purchased! Enjoy your reward: {item.split('(')[0]}")
            st.rerun()
        else:
            st.error("Not enough Gold! Go clear more quests.")

st.divider()

# History Log Audit Trail
st.subheader("📜 Quest History")
df_history = conn.query(
    "SELECT timestamp, quest_type, xp_earned, gold_earned FROM quest_history ORDER BY id DESC LIMIT 10",
    ttl=0,
)
if not df_history.empty:
    st.dataframe(df_history, use_container_width=True, hide_index=True)
else:
    st.text("No quests completed yet. Time to start grinding!")

import streamlit as st
import mysql.connector
import requests
import urllib.parse

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EcoCycle: E-Waste Management Portal",
    page_icon="♻️",
    layout="wide"
)

# --- CUSTOM CSS FOR BEAUTIFUL ECO-THEMED COVER PAGE ---
st.markdown("""
    <style>
    .hero-container {
        background: linear-gradient(135deg, #134e5e 0%, #71b280 100%);
        padding: 4rem 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 1.25rem;
        font-weight: 300;
        margin-bottom: 2rem;
        opacity: 0.95;
    }
    .feature-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2e7d32;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        height: 100%;
        color: #333333;
    }
    </style>
""", unsafe_allow_html=True)

# --- TELEGRAM CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "8236825484:AAFTAQFvRJUGfM2OZP0UlPrwo4Yvz2KdM68"

def send_telegram_alert(lead_id, name, phone, category, condition):
    """Automatically detects your Chat ID from t.me/BVB_EWaste_bot and sends an instant push notification."""
    try:
        updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(updates_url, timeout=5).json()
        
        if response.get("ok") and response.get("result"):
            chat_id = response["result"][-1]["message"]["chat"]["id"]
            
            message = (
                f"🚨 *New E-Waste Deposit Lead!* 🚨\n\n"
                f"🔖 *Lead ID:* #EW-{lead_id}\n"
                f"👤 *Name:* {name}\n"
                f"📞 *Phone:* {phone}\n"
                f"📦 *Category:* {category}\n"
                f"⚡ *Condition:* {condition}\n\n"
                f"Check your Admin Portal to coordinate pickup!"
            )
            
            send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            requests.post(send_url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram notification error: {e}")

# --- DATABASE CONNECTION HANDLER ---
def get_db_connection(password=None):
    """Establishes connection to Aiven Cloud MySQL (production) or local MySQL (development)."""
    try:
        if "mysql" in st.secrets:
            return mysql.connector.connect(
                host=st.secrets["mysql"]["host"],
                port=int(st.secrets["mysql"]["port"]),
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                database=st.secrets["mysql"]["database"],
                charset="utf8",
                ssl_disabled=False
            )
        else:
            pwd = password if password else "sa"
            return mysql.connector.connect(
                host="localhost",
                user="root",
                password=pwd,
                database="ewaste_db",
                charset="utf8"
            )
    except mysql.connector.Error as err:
        st.error(f"🚨 Database Connection Error: {err}")
        raise err

# --- AUTOMATIC TABLE CREATION ON STARTUP ---
def init_db():
    """Automatically creates the database table if it doesn't already exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ewaste_leads (
                lead_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                email VARCHAR(255),
                address TEXT NOT NULL,
                pincode VARCHAR(20) NOT NULL,
                item_category VARCHAR(100) NOT NULL,
                item_details TEXT NOT NULL,
                item_condition VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'Pending',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Table Init Notice: {e}")

# Run table initialization automatically
init_db()

# --- NAVIGATION TABS ---
tab_home, tab_form, tab_admin = st.tabs(["🏠 Home / Overview", "📝 Deposit E-Waste", "🛠️ Admin Portal"])

# ==========================================
# TAB 1: COVER PAGE / LANDING HOME
# ==========================================
with tab_home:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">🌍 EcoCycle E-Waste Portal</div>
            <div class="hero-subtitle">Transforming electronic waste management through responsible recycling, seamless deposits, and transparent tracking.</div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("💡 Why Responsible E-Waste Management Matters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="feature-card">
                <h3>♻️ Secure Disposal</h3>
                <p>Ensure your obsolete gadgets, mobile phones, laptops, and home appliances are recycled safely without harming landfills.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="feature-card">
                <h3>📦 Easy Scheduling</h3>
                <p>Submit your deposit details in seconds through our streamlined portal and get instant confirmation tracking IDs.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
            <div class="feature-card">
                <h3>🔍 Real-Time Tracking</h3>
                <p>Monitor your collection leads from pending status all the way to verified authorization and recycling approval.</p>
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.info("👉 **Ready to dispose of your electronics?** Click on the **'Deposit E-Waste'** tab above to submit your items, or head to the **'Admin Portal'** if you are the collection manager.")

# ==========================================
# TAB 2: PUBLIC DEPOSIT FORM
# ==========================================
with tab_form:
    st.header("♻️ Schedule Your E-Waste Deposit")
    st.write("Fill out the form below with your contact details and device information. Our collection team will review your request and get in touch.")

    with st.form("ewaste_form", clear_on_submit=True):
        st.subheader("1. Personal Information")
        full_name = st.text_input("Full Name *")
        phone = st.text_input("Phone Number * (Include country code, e.g., 919876543210)")
        email = st.text_input("Email Address (Optional)")
        
        st.subheader("2. Pickup Address")
        address = st.text_area("Complete Street Address *")
        pincode = st.text_input("PIN Code / Postal Code *")
        
        st.subheader("3. E-Waste Item Details")
        item_category = st.selectbox(
            "Item Category *",
            ["Select Category", "Mobile Phone / Tablet", "Laptop / Computer", "Home Appliances", "Batteries & Chargers", "TV & Monitors", "Other Electronics"]
        )
        
        item_details = st.text_area("Item Description (e.g., Brand, model, quantity) *")
        
        item_condition = st.radio(
            "Condition of Items *",
            ["Working", "Dead / Non-Working", "Damaged / Broken Parts"],
            horizontal=True
        )
        
        submitted = st.form_submit_button("Submit Deposit Request")

    if submitted:
        if not full_name or not phone or not address or not pincode or item_category == "Select Category" or not item_details:
            st.error("Please fill in all mandatory fields marked with an asterisk (*).")
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                query = """
                    INSERT INTO ewaste_leads 
                    (full_name, phone, email, address, pincode, item_category, item_details, item_condition, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
                """
                values = (full_name, phone, email, address, pincode, item_category, item_details, item_condition)
                
                cursor.execute(query, values)
                conn.commit()
                lead_id = cursor.lastrowid
                
                cursor.close()
                conn.close()
                
                # Trigger Direct Telegram Push Notification
                send_telegram_alert(lead_id, full_name, phone, item_category, item_condition)
                
                st.success(f"🎉 Deposit Request Submitted Successfully! Your Tracking ID is **#EW-{lead_id}**.")
                st.info("We have received your details. Our collection team will contact you shortly.")
                
            except mysql.connector.Error as err:
                st.error(f"Database Error: {err}")

# ==========================================
# TAB 3: ADMIN DASHBOARD (CLOUD SECURE)
# ==========================================
with tab_admin:
    st.header("🔐 Admin Portal & Lead Management")
    st.write("Manage and authorize incoming e-waste collection leads stored in your cloud database.")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM ewaste_leads ORDER BY timestamp DESC")
        leads = cursor.fetchall()
        
        cursor.close()
        conn.close()

        st.success("✅ Secure Cloud Database Connected: Admin Dashboard Unlocked")
        
        if not leads:
            st.info("No deposit leads found in the database yet.")
        else:
            st.metric("Total Deposit Leads", len(leads))
            
            for lead in leads:
                with st.expander(f"Lead #EW-{lead['lead_id']} | {lead['full_name']} ({lead['item_category']}) - [{lead['status']}]"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Phone:** {lead['phone']}")
                        st.write(f"**Email:** {lead['email'] if lead['email'] else 'N/A'}")
                        st.write(f"**Address:** {lead['address']} (PIN: {lead['pincode']})")
                        st.write(f"**Submitted On:** {lead['timestamp']}")
                    
                    with col2:
                        st.write(f"**Category:** {lead['item_category']}")
                        st.write(f"**Description:** {lead['item_details']}")
                        st.write(f"**Condition:** {lead['item_condition']}")
                        st.write(f"**Current Status:** `{lead['status']}`")

                    st.markdown("---")
                    
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    
                    with btn_col1:
                        whatsapp_url = f"https://wa.me/{lead['phone']}?text=Hi%20{lead['full_name']},%20regarding%20your%20e-waste%20deposit%20request%20%23EW-{lead['lead_id']}..."
                        st.markdown(f"[💬 Chat on WhatsApp]({whatsapp_url})", unsafe_allow_html=True)
                    
                    with btn_col2:
                        new_status = st.selectbox(
                            "Update Status", 
                            ["Pending", "Scheduled", "Collected", "Approved"], 
                            index=["Pending", "Scheduled", "Collected", "Approved"].index(lead['status']),
                            key=f"status_{lead['lead_id']}"
                        )
                    
                    with btn_col3:
                        if st.button("Save Status", key=f"save_{lead['lead_id']}"):
                            try:
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE ewaste_leads SET status = %s WHERE lead_id = %s", (new_status, lead['lead_id']))
                                conn.commit()
                                cursor.close()
                                conn.close()
                                st.success(f"Status updated to {new_status}!")
                                st.rerun()
                            except mysql.connector.Error as err:
                                st.error(f"Error updating: {err}")

    except mysql.connector.Error as err:
        st.error(f"❌ Cloud Database Connection Error: {err}")
        st.info("Please check your Aiven credentials in Streamlit Secrets.")

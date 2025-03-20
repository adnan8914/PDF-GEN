import streamlit as st
from docx import Document
from datetime import datetime, timedelta
import os
from docx.oxml.ns import qn
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
import uuid
import tempfile
import re
import base64

# Try to import docx2pdf, but provide a fallback if it's not available
try:
    from docx2pdf import convert
    PDF_CONVERSION_AVAILABLE = True
except ImportError:
    PDF_CONVERSION_AVAILABLE = False

# Proposal configurations
PROPOSAL_CONFIG = {
    "Make, Manychat & CRM Automation": {
        "template": "Make, Manychat & CRM Automation.docx",
        "pricing_fields": [
            ("ManyChat Automation", "MC-Price"),
            ("Make Automation", "M-Price"),
            ("CRM Automations", "C-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "Make & Manychat Automation": {
        "template": "Make & Manychat Automation.docx",
        "pricing_fields": [
            ("ManyChat Automation", "MC-Price"),
            ("Make Automation", "M-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "Ai Calling, Make, Manychat and CRM Automation": {
        "template": "Ai Calling, Make, Manychat and CRM Automation.docx",
        "pricing_fields": [
            ("AI Calling + CRM Integration", "AI-Price"),
            ("ManyChat & Make Automation", "MM-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "AI Calling, Make & CRM Automation": {
        "template": "AI Calling, Make & CRM Automation.docx",
        "pricing_fields": [
            ("AI Calling", "AI-Price"),
            ("Make Automation", "M-Price"),
            ("CRM Automations", "C-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "AI Calling(Basic) & CRM Automation": {
        "template": "AI Calling(Basic) & CRM Automation.docx",
        "pricing_fields": [
            ("AI Calling(Basic)", "AI-Price"),
            ("CRM Automation", "CC-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "AI Calling, Make & Manychat Automation": {
        "template": "Ai Calling, Make & Manychat Automation.docx",
        "pricing_fields": [
            ("AI Calling(Basic)", "AI-Price"),
            ("ManyChat Automation", "MC-Price"),
            ("Make Automation", "M-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "Ai Calling + CRM Intergration, Make & Manychat Automation, CRM Automation": {
        "template": "Ai Calling + CRM Intergration, Make & Manychat Automation, CRM Automation.docx",
        "pricing_fields": [
            ("AI Calling + CRM Integration", "AI-Price"),
            ("ManyChat & Make Automation", "MM-Price"),
            ("CRM Automation", "CC-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "AI Calling(Basic) & CRM Automation & Email Automation": {
        "template": "AI Calling(Basic) & CRM Automation & Email Automation.docx",
        "pricing_fields": [
            ("AI Calling(Basic)", "AI-Price"),
            ("CRM Automation", "CC-Price"),
            ("Email Automation", "E-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "Manychat & CRM Automation": {
        "template": "Manychat & CRM Automation.docx",
        "pricing_fields": [
            ("ManyChat Automation", "MC-Price"),
            ("CRM Automations", "C-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "Make & CRM Automation": {
        "template": "Make & CRM Automation.docx",
        "pricing_fields": [
            ("Make Automation", "M-Price"),
            ("CRM Automations", "C-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "Make, CRM Automation & AI Content Creation": {
        "template": "Make, CRM Automation & AI Content Creation.docx",
        "pricing_fields": [
            ("Make Automation", "M-Price"),
            ("CRM Automations", "C-Price"),
            ("AI Content Creation", "ACC-Price")
        ],
        "team_type": "general",
        "special_fields": [("VDate", "<<")]
    },
    "Digital Marketing Proposal": {
        "template": "DM Proposal_1.docx",
        "pricing_fields": [
            ("Service 1", "dm_discrip1_price"),
            ("Service 2", "dm_discrip2_price"),
            ("Monthly Maintenance", "monthly_main_price")
        ],
        "team_type": "marketing",
        "special_fields": [("VDate", "<<")]
    },
    "DM & Automation": {
        "template": "DM & Automations Proposal.docx",
        "pricing_fields": [
            ("AI Automation", "auto_price"),
            ("Marketing Strategy", "market_stra"),
            ("Social Media Channels", "social_med"),
            ("Creatives (10 Per Month)", "creatives"),
            ("Ad Account Setup", "ad_acc_set"),
            ("Paid Ads", "paid_ads"),
            ("Monthly Maintenance", "montly_mai")
        ],
        "team_type": "marketing",
        "special_fields": [("VDate", "<<")]
    },
    "Web Based AI Fintech": {
        "template": "Web based AI Fintech proposal.docx",
        "pricing_fields": [
            ("Design", "design"),
            ("Development", "development"),
            ("AI/ML Models", "ai_ml_model"),
            ("Annual Maintenance", "annual_main"),
            ("Additional Features", "additional_feat")
        ],
        "team_type": "technical",
        "special_fields": [("VDate", "<<")]
    },
    "AI Based Search Engine": {
        "template": "AI Based Search Engine Website Technical Consultation proposal.docx",
        "pricing_fields": [
            ("Design", "design"),
            ("Development", "development"),
            ("Testing & Deployment", "test_deploy"),
            ("Annual Maintenance", "annual_maintenance"),
            ("Additional Features", "ad_f")
        ],
        "team_type": "technical"
    },
    "Shopify Website": {
        "template": "Shopify website.docx",
        "pricing_fields": [
            ("Development", "development"),
            ("Design", "design"),
            ("Testing & Live", "testing"),
            ("Annual Maintenance", "annual_mai"),
            ("Additional Features", "add_feature")
        ],
        "team_type": "technical"
    }
}

def apply_formatting(new_run, original_run):
    """Copy formatting from original run to new run"""
    if original_run.font.name:
        new_run.font.name = original_run.font.name
        new_run._element.rPr.rFonts.set(qn('w:eastAsia'), original_run.font.name)
    if original_run.font.size:
        new_run.font.size = original_run.font.size
    if original_run.font.color.rgb:
        new_run.font.color.rgb = original_run.font.color.rgb
    new_run.bold = original_run.bold
    new_run.italic = original_run.italic

def replace_in_paragraph(para, placeholders):
    """Handle paragraph replacements preserving formatting"""
    original_runs = para.runs.copy()
    full_text = para.text
    for ph, value in placeholders.items():
        full_text = full_text.replace(ph, str(value))

    if full_text != para.text:
        para.clear()
        new_run = para.add_run(full_text)
        if original_runs:
            original_run = next((r for r in original_runs if r.text), None)
            if original_run:
                apply_formatting(new_run, original_run)

def replace_and_format(doc, placeholders):
    """Enhanced replacement with table cell handling"""
    # Process paragraphs
    for para in doc.paragraphs:
        replace_in_paragraph(para, placeholders)

    # Process tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.tables:
                    for nested_table in cell.tables:
                        for nested_row in nested_table.rows:
                            for nested_cell in nested_row.cells:
                                for para in nested_cell.paragraphs:
                                    replace_in_paragraph(para, placeholders)
                else:
                    for para in cell.paragraphs:
                        replace_in_paragraph(para, placeholders)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    return doc

def get_marketing_team_details():
    """Collect team composition details specifically for marketing proposals"""
    st.subheader("Marketing Team Composition")
    team_roles = {
        "Project Manager": "PM",
        "Content Writers": "CW",
        "Graphic Designer": "GD",
        "SEO Specialists": "SE",
        "Social Media Manager": "SM",
        "Ad Campaign Manager": "AC"
    }
    team_details = {}
    cols = st.columns(3)

    for idx, (role, placeholder) in enumerate(team_roles.items()):
        with cols[idx % 3]:
            count = st.number_input(
                f"{role} Count:",
                min_value=0,
                step=1,
                key=f"marketing_team_{placeholder}"
            )
            team_details[f"<<{placeholder}>>"] = str(count)
    return team_details

def get_general_team_details():
    """Collect team composition for non-marketing proposals"""
    st.subheader("Team Composition")
    team_roles = {
        "Project Manager": "P1",
        "Frontend Developers": "F1",
        "Business Analyst": "B1",
        "AI/ML Developers": "A1",
        "UI/UX Members": "U1",
        "System Architect": "S1",
        "Backend Developers": "BD1",
        "AWS Developer": "AD1"
    }
    team_details = {}
    cols = st.columns(2)

    for idx, (role, placeholder) in enumerate(team_roles.items()):
        with cols[idx % 2]:
            count = st.number_input(
                f"{role} Count:",
                min_value=0,
                step=1,
                key=f"team_{placeholder}"
            )
            team_details[f"<<{placeholder}>>"] = str(count)
    return team_details

def remove_empty_rows(table):
    """Remove rows from the table where the second cell is empty or has no value."""
    rows_to_remove = []
    for row in table.rows:
        if len(row.cells) > 1 and row.cells[1].text.strip() == "":
            rows_to_remove.append(row)
    # Remove rows in reverse order to avoid index issues
    for row in reversed(rows_to_remove):
        table._tbl.remove(row._element)

def validate_phone_number(country, phone_number):
    """Validate phone number based on country"""
    if country.lower() == "india":
        if not phone_number.startswith("+91"):
            return False
    else:
        if not phone_number.startswith("+1"):
            return False
    return True

def format_number_with_commas(number):
    """Format number with commas (e.g., 10000 -> 10,000)"""
    return f"{number:,}"

def generate_document():
    # Page configuration
    st.set_page_config(
        page_title="AI Automation Proposal Generator",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for modern styling
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 1rem;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f1f3f6;
        }
        
        /* Header styling */
        .main-header {
            text-align: center;
            padding: 1.5rem 0;
            margin-bottom: 2rem;
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border-radius: 10px;
        }
        
        /* Section styling */
        .section-header {
            color: #1e3c72;
            padding: 1rem 0;
            margin-bottom: 1rem;
            border-bottom: 2px solid #e0e0e0;
        }
        
        /* Input field styling */
        .stTextInput > div > div > input {
            border-radius: 5px;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Metrics styling */
        .metrics-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* Divider styling */
        .section-divider {
            margin: 2rem 0;
            border-top: 1px solid #e0e0e0;
        }

        /* Sub-section styling */
        .sub-section {
            margin: 1rem 0;
            padding-left: 1rem;
            border-left: 3px solid #1e3c72;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar for template selection
    with st.sidebar:
        st.title("📄 Template Selection")
        st.markdown("---")
        selected_proposal = st.selectbox(
            "Choose Your Proposal Type",
            list(PROPOSAL_CONFIG.keys()),
            format_func=lambda x: x.replace("_", " ").title()
        )
        st.markdown("---")
        st.markdown("### Selected Template:")
        st.info(selected_proposal.replace("_", " ").title())

    config = PROPOSAL_CONFIG[selected_proposal]
    base_dir = os.getcwd()
    template_path = os.path.join(base_dir, config["template"])

    # Main header
    st.markdown("""
        <div class="main-header">
            <h1>AI Automation Proposal Generator</h1>
            <p>Create professional proposals in minutes</p>
        </div>
    """, unsafe_allow_html=True)

    # Client Information
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("🏢 Company Information")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Basic Details")
        client_name = st.text_input("Client Name", placeholder="Enter client name")
        client_email = st.text_input("Email", placeholder="Enter email")
        date_field = st.date_input("Date", datetime.today())
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Contact Information")
        country = st.selectbox("Select Country", ["India", "United States", "Other"])
        client_number = st.text_input("Contact Number", placeholder="+91 for India, +1 for US")
        
        # Add location field for all proposals
        client_location = st.text_input("Location", placeholder="Enter client location")
        
        # Additional fields for specific proposals
        if selected_proposal in ["Digital Marketing Proposal", "DM & Automation"]:
            client_desig = st.text_input("Client Designation", placeholder="Enter client designation")
        
        if client_number and country:
            if not validate_phone_number(country, client_number):
                st.error(f"Invalid format. Use {'+91' if country.lower() == 'india' else '+1'} prefix")
        st.markdown('</div>', unsafe_allow_html=True)

    # Special Fields Handling
    special_data = {}
    if config.get("special_fields"):
        st.markdown('<div class="section-header">', unsafe_allow_html=True)
        st.header("📋 Additional Details")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        for field, wrapper in config["special_fields"]:
            if wrapper == "<<":
                placeholder = f"<<{field}>>"
                if field == "VDate":
                    vdate = st.date_input("Proposal Validity Until:", date_field + timedelta(days=7))
                    special_data[placeholder] = vdate.strftime("%d-%m-%Y")
                else:
                    special_data[placeholder] = st.text_input(f"{field.replace('_', ' ').title()}:")
        st.markdown('</div>', unsafe_allow_html=True)

    # Service Pricing Section
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("💰 Service Pricing")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get currency symbol based on country selection
    currency_symbol = "₹" if country == "India" else "$"

    # Service pricing
    pricing_data = {}
    numerical_values = {}
    
    if selected_proposal == "DM & Automation":
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Service Pricing")
        
        # Client Information
        pricing_data["<<client_name>>."] = client_name
        pricing_data["<<client_name>>"] = client_name  # For signature
        pricing_data["<<client_desig>>"] = client_desig if 'client_desig' in locals() else ""
        pricing_data["<<client_cont>>"] = client_number
        pricing_data["<<client_email>>"] = client_email
        
        # Dates
        today_date = date_field.strftime("%d-%m-%Y")
        pricing_data["<<date>>"] = today_date  # This will update all instances of <<date>>
        pricing_data["<<validity_date>>"] = (date_field + timedelta(days=7)).strftime("%d-%m-%Y")
        
        # Service Pricing - All as number inputs
        pricing_fields = [
            ("AI Automation", "auto_price"),
            ("Marketing Strategy", "market_stra"),
            ("Social Media Channels", "social_med"),
            ("Creatives (10 Per Month)", "creatives"),
            ("Ad Account Setup (Meta)", "ad_acc_set"),
            ("Paid Ads (Lead Generation)", "paid_ads"),
            ("Monthly Maintenance & Reporting", "montly_mai")
        ]
        
        for display_name, field_key in pricing_fields:
            price = st.number_input(
                f"{display_name} Price ({currency_symbol})",
                min_value=0,
                value=0,
                step=1000,
                key=f"dma_{field_key}"  # Prefix with dma_ to avoid conflicts
            )
            numerical_values[field_key] = price
            pricing_data[f"<<{field_key}>>"] = f"{currency_symbol}{format_number_with_commas(price)}"
        
        # Calculate totals
        amount_1_business = sum(numerical_values.values())
        amount_2_business = int(amount_1_business * 0.9)  # 10% discount
        total_amount = amount_1_business + amount_2_business
        
        # Update pricing data
        pricing_data["<<amount_for_1_buisness>>"] = f"{currency_symbol}{format_number_with_commas(amount_1_business)}"
        pricing_data["<<amount_2_buisness>>"] = f"{currency_symbol}{format_number_with_commas(amount_2_business)}"
        pricing_data["<< amount_2_buisness>>"] = f"{currency_symbol}{format_number_with_commas(amount_2_business)}"
        pricing_data["<<total_amount>>"] = f"{currency_symbol}{format_number_with_commas(total_amount)}"
        
        # Payment schedule calculations
        payment_30 = int(total_amount * 0.3)
        payment_40 = int(total_amount * 0.4)
        balance_payment = total_amount - payment_30 - payment_40
        
        pricing_data["<<30_payment>>"] = f"{currency_symbol}{format_number_with_commas(payment_30)}"
        pricing_data["<<40_payment>>"] = f"{currency_symbol}{format_number_with_commas(payment_40)}"
        pricing_data["<<blnc_payment>>"] = f"{currency_symbol}{format_number_with_commas(balance_payment)}"

    elif selected_proposal == "Digital Marketing Proposal":
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Service Descriptions")
        
        col1, col2 = st.columns(2)
        with col1:
            dm_description1 = st.text_input("Service 1 Description", 
                                          placeholder="e.g., Social Media Management",
                                          key="dm_desc1")
            pricing_data["<<dm_discprition1>>"] = dm_description1
            
            service1_price = st.number_input(
                f"Service 1 Price ({currency_symbol})",
                min_value=0,
                value=0,
                step=1000,
                key="price_dm_discrip1_price"
            )
            numerical_values["dm_discrip1_price"] = service1_price
            if service1_price > 0:
                pricing_data["<<dm_discrip1_price>>"] = f"{currency_symbol}{format_number_with_commas(service1_price)}"
            else:
                pricing_data["<<dm_discrip1_price>>"] = ""
                
        with col2:
            dm_description2 = st.text_input("Service 2 Description", 
                                          placeholder="e.g., Content Creation",
                                          key="dm_desc2")
            pricing_data["<<dm_discprition2>>"] = dm_description2
            
            service2_price = st.number_input(
                f"Service 2 Price ({currency_symbol})",
                min_value=0,
                value=0,
                step=1000,
                key="price_dm_discrip2_price"
            )
            numerical_values["dm_discrip2_price"] = service2_price
            if service2_price > 0:
                pricing_data["<<dm_discrip2_price>>"] = f"{currency_symbol}{format_number_with_commas(service2_price)}"
            else:
                pricing_data["<<dm_discrip2_price>>"] = ""
        
        # Monthly maintenance
        monthly_price = st.number_input(
            f"Monthly Maintenance Price ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="price_monthly_main_price"
        )
        numerical_values["monthly_main_price"] = monthly_price
        if monthly_price > 0:
            pricing_data["<<monthly_main_price>>"] = f"{currency_symbol}{format_number_with_commas(monthly_price)}"
        else:
            pricing_data["<<monthly_main_price>>"] = ""
            
        # Set GST text
        pricing_data["<<gst>>"] = "GST (18%)"
        
        st.markdown('</div>', unsafe_allow_html=True)
    elif selected_proposal == "Web Based AI Fintech":
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Service Pricing")
        
        # Update date fields
        today_date = date_field.strftime("%d-%m-%Y")
        validity_date = (date_field + timedelta(days=7)).strftime("%d-%m-%Y")
        
        pricing_data["<<date>>"] = today_date
        pricing_data["<<validity_date>>"] = validity_date
        
        # Use the existing client info variables
        pricing_data["<<client_name>>"] = client_name
        pricing_data["<<client_email>>"] = client_email
        pricing_data["<<client_phoneno>>"] = client_number
        pricing_data["<<client_location>>"] = client_location
        
        # Service Pricing (rest remains the same)
        design_price = st.number_input(
            f"Design Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="fintech_design"
        )
        numerical_values["design"] = design_price
        pricing_data["<<design>>"] = f"{currency_symbol}{format_number_with_commas(design_price)}"
        
        dev_price = st.number_input(
            f"Development Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="fintech_development"
        )
        numerical_values["development"] = dev_price
        pricing_data["<<development>>"] = f"{currency_symbol}{format_number_with_commas(dev_price)}"
        
        ai_ml_price = st.number_input(
            f"AI/ML Models Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="fintech_ai_ml"
        )
        numerical_values["ai_ml_model"] = ai_ml_price
        pricing_data["<<ai_ml_model>>"] = f"{currency_symbol}{format_number_with_commas(ai_ml_price)}"
        
        # Calculate total amount (excluding additional features)
        total_amount = design_price + dev_price + ai_ml_price
        
        # Annual Maintenance (10% of total)
        annual_maintenance = int(total_amount * 0.10)
        numerical_values["annual_main"] = annual_maintenance
        pricing_data["<<annual_main>>"] = f"{currency_symbol}{format_number_with_commas(annual_maintenance)}"
        
        # Additional Features (not included in total)
        additional_features = st.number_input(
            f"Additional Features Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="fintech_additional"
        )
        numerical_values["additional_feat"] = additional_features
        pricing_data["<<additional_feat>>"] = f"{currency_symbol}{format_number_with_commas(additional_features)}"
        
        # Display price summary
        st.subheader("Price Summary")
        st.write(f"Services Total: {currency_symbol}{format_number_with_commas(total_amount)}")
        st.write(f"Annual Maintenance (10%): {currency_symbol}{format_number_with_commas(annual_maintenance)}")
        st.write(f"Final Amount: {currency_symbol}{format_number_with_commas(total_amount + annual_maintenance)}")
    elif selected_proposal == "AI Based Search Engine":
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Service Pricing")
        
        # Use existing client info
        pricing_data["<<client_name>>"] = client_name
        pricing_data["<<client_email>>"] = client_email
        pricing_data["<<client_phoneno>>"] = client_number
        pricing_data["<<client_location>>"] = client_location
        
        # Update dates
        today_date = date_field.strftime("%d-%m-%Y")
        pricing_data["<<date>>"] = today_date
        pricing_data["<<validity_date>>"] = (date_field + timedelta(days=7)).strftime("%d-%m-%Y")
        
        # Get currency symbol based on country
        currency_symbol = "₹" if country == "India" else "$"
        
        # Service Pricing
        design_price = st.number_input(
            f"Design Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="search_design"
        )
        numerical_values["design"] = design_price
        pricing_data["<<design>>"] = f"{currency_symbol}{format_number_with_commas(design_price)}"
        
        dev_price = st.number_input(
            f"Development Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="search_development"
        )
        numerical_values["development"] = dev_price
        pricing_data["<<development>>"] = f"{currency_symbol}{format_number_with_commas(dev_price)}"
        
        test_deploy_price = st.number_input(
            f"Testing & Deployment Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="search_test_deploy"
        )
        numerical_values["test_deploy"] = test_deploy_price
        pricing_data["<<test_deploy>>"] = f"{currency_symbol}{format_number_with_commas(test_deploy_price)}"
        
        # Calculate total amount before maintenance
        subtotal = design_price + dev_price + test_deploy_price
        
        # Calculate annual maintenance (10% of subtotal)
        annual_maintenance = int(subtotal * 0.10)
        numerical_values["annual_maintenance"] = annual_maintenance
        pricing_data["<<annual_maintenance>>"] = f"{currency_symbol}{format_number_with_commas(annual_maintenance)}"
        
        # Calculate total amount including maintenance
        total_amount = subtotal + annual_maintenance
        pricing_data["<<total_amount>>"] = f"{currency_symbol}{format_number_with_commas(total_amount)}"
        
        # Additional Features (not included in total)
        additional_features = st.number_input(
            f"Additional Features Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="search_additional"
        )
        numerical_values["ad_f"] = additional_features
        pricing_data["<<ad_f>>"] = f"{currency_symbol}{format_number_with_commas(additional_features)}"
        
        # Display price summary
        st.subheader("Price Summary")
        st.write(f"Services Total: {currency_symbol}{format_number_with_commas(subtotal)}")
        st.write(f"Annual Maintenance (10%): {currency_symbol}{format_number_with_commas(annual_maintenance)}")
        st.write(f"Final Amount: {currency_symbol}{format_number_with_commas(total_amount)}")
    elif selected_proposal == "Shopify Website":
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Service Pricing")
        
        # Use existing client info
        pricing_data["<<client_name>>"] = client_name
        pricing_data["<<client_email>>"] = client_email
        pricing_data["<<client_phoneno>>"] = client_number
        pricing_data["<<location>>"] = country  # Note: Using country instead of client_location
        
        # Update dates
        today_date = date_field.strftime("%d-%m-%Y")
        pricing_data["<<date>>"] = today_date
        pricing_data["<<validity_date>>"] = (date_field + timedelta(days=7)).strftime("%d-%m-%Y")
        
        # Get currency symbol based on country
        currency_symbol = "₹" if country == "India" else "$"
        
        # Service Pricing
        development_price = st.number_input(
            f"Development Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="shopify_development"
        )
        numerical_values["development"] = development_price
        pricing_data["<<development>>"] = f"{currency_symbol}{format_number_with_commas(development_price)}"
        
        design_price = st.number_input(
            f"Design Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="shopify_design"
        )
        numerical_values["design"] = design_price
        pricing_data["<<design>>"] = f"{currency_symbol}{format_number_with_commas(design_price)}"
        
        testing_price = st.number_input(
            f"Testing & Live Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="shopify_testing"
        )
        numerical_values["testing"] = testing_price
        pricing_data["<<testing>>"] = f"{currency_symbol}{format_number_with_commas(testing_price)}"
        
        # Calculate subtotal
        subtotal = development_price + design_price + testing_price
        
        # Calculate annual maintenance (10% of subtotal)
        annual_maintenance = int(subtotal * 0.10)
        numerical_values["annual_mai"] = annual_maintenance
        pricing_data["<<annual_mai>>"] = f"{currency_symbol}{format_number_with_commas(annual_maintenance)}"
        
        # Calculate total amount
        total_amount = subtotal + annual_maintenance
        pricing_data["<<total_amount>>"] = f"{currency_symbol}{format_number_with_commas(total_amount)}"
        
        # Additional Features (not included in total)
        additional_features = st.number_input(
            f"Additional Features Cost ({currency_symbol})",
            min_value=0,
            value=0,
            step=1000,
            key="shopify_additional"
        )
        numerical_values["add_feature"] = additional_features
        pricing_data["<<add_feature>>"] = f"{currency_symbol}{format_number_with_commas(additional_features)}"
        
        # Display price summary
        st.subheader("Price Summary")
        st.write(f"Services Total: {currency_symbol}{format_number_with_commas(subtotal)}")
        st.write(f"Annual Maintenance (10%): {currency_symbol}{format_number_with_commas(annual_maintenance)}")
        st.write(f"Final Amount: {currency_symbol}{format_number_with_commas(total_amount)}")
    else:
        # Standard pricing fields for other proposals
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        cols = st.columns(len(config["pricing_fields"]))
        
        for idx, (label, key) in enumerate(config["pricing_fields"]):
            with cols[idx]:
                st.subheader(label)
                value = st.number_input(
                    f"Amount ({currency_symbol})",
                    min_value=0,
                    value=0,
                    step=100,
                    key=f"price_{key}"
                )
                numerical_values[key] = value
                if value > 0:
                    pricing_data[f"<<{key}>>"] = f"{currency_symbol}{format_number_with_commas(value)}"
                else:
                    pricing_data[f"<<{key}>>"] = ""
        st.markdown('</div>', unsafe_allow_html=True)

    # Calculate services sum based on selected proposal
    services_sum = sum(numerical_values.values())
    
    # Digital Marketing specific calculations
    if selected_proposal == "Digital Marketing Proposal":
        # GST calculation (18%)
        gst_amount = int(services_sum * 0.18)
        pricing_data["<<gst_price>>"] = f"{currency_symbol}{format_number_with_commas(gst_amount)}"
        
        # Total with GST
        total_with_gst = services_sum + gst_amount
        pricing_data["<<total_price>>"] = f"{currency_symbol}{format_number_with_commas(total_with_gst)}"
        
        # Advance payment (50%)
        advance_payment = int(total_with_gst * 0.5)
        pricing_data["<<advance>>"] = f"{currency_symbol}{format_number_with_commas(advance_payment)}"
        
        # Balance payment (50%)
        pricing_data["<<balance>>"] = f"{currency_symbol}{format_number_with_commas(advance_payment)}"
        
        # Set validity date
        pricing_data["<<validity_date>>"] = (date_field + timedelta(days=7)).strftime("%d-%m-%Y")
        
        # Update placeholders based on proposal type
        pricing_data["<<client_desig>>"] = client_desig if 'client_desig' in locals() else ""
    else:
        # Annual Maintenance (10% of Total Amount) for other proposals
        am_price = int(services_sum * 0.10)
        pricing_data["<<AM-Price>>"] = f"{currency_symbol}{format_number_with_commas(am_price)}"

        # Total Amount
        total = services_sum + am_price
        if currency_symbol == "₹":
            pricing_data["<<T-Price>>"] = f"{currency_symbol}{format_number_with_commas(total)} + 18% GST"
        else:
            pricing_data["<<T-Price>>"] = f"{currency_symbol}{format_number_with_commas(total)}"

        # Additional Features & Enhancements
        af_price = 250 if currency_symbol == "$" else 25000
        pricing_data["<<AF-Price>>"] = f"{currency_symbol}{format_number_with_commas(af_price)}"

    # Price Summary
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    st.subheader("Price Summary")
    
    if selected_proposal == "Digital Marketing Proposal":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Services Total", f"{currency_symbol}{format_number_with_commas(services_sum)}")
        with col2:
            st.metric("GST (18%)", f"{currency_symbol}{format_number_with_commas(gst_amount)}")
        with col3:
            st.metric("Final Amount", f"{currency_symbol}{format_number_with_commas(total_with_gst)}")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Services Total", f"{currency_symbol}{format_number_with_commas(services_sum)}")
        with col2:
            st.metric("Annual Maintenance (10%)", f"{currency_symbol}{format_number_with_commas(am_price)}")
        with col3:
            st.metric("Final Amount", 
                    f"{currency_symbol}{format_number_with_commas(total)}" + 
                    (" + 18% GST" if currency_symbol == "₹" else ""))
    st.markdown('</div>', unsafe_allow_html=True)

    # Team Configuration Section
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("👥 Team Configuration")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sub-section">', unsafe_allow_html=True)
    team_data = {}
    if config["team_type"] == "marketing" and selected_proposal != "Digital Marketing Proposal":
        team_data = get_marketing_team_details()
    elif config["team_type"] == "general":
        team_data = get_general_team_details()
    st.markdown('</div>', unsafe_allow_html=True)

    # Additional Tools Section
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("🛠️ Additional Tools")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sub-section">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        additional_tool_1 = st.text_input("Tool 1", placeholder="Enter tool name")
    with col2:
        additional_tool_2 = st.text_input("Tool 2", placeholder="Enter tool name")
    
    additional_tools_data = {}
    if additional_tool_1:
        additional_tools_data["<<T1>>"] = additional_tool_1
    else:
        additional_tools_data["<<T1>>"] = ""

    if additional_tool_2:
        additional_tools_data["<<T2>>"] = additional_tool_2
    else:
        additional_tools_data["<<T2>>"] = ""
    st.markdown('</div>', unsafe_allow_html=True)

    # Generate Proposal Button
    st.markdown('<div style="margin-top: 2rem;">', unsafe_allow_html=True)
    if st.button("🚀 Generate Proposal", type="primary", use_container_width=True):
        with st.spinner("Creating your proposal..."):
            try:
                # Combine all placeholders
                placeholders = {
                    "<<Client Name>>": client_name,
                    "<<Client Email>>": client_email,
                    "<<Client Number>>": client_number,
                    "<<Date>>": date_field.strftime("%d-%m-%Y"),
                    "<<Country>>": country
                }
                
                # Add Digital Marketing specific placeholders
                if selected_proposal == "Digital Marketing Proposal":
                    placeholders["<<client_name>>"] = client_name
                    placeholders["<<client_email>>"] = client_email
                    placeholders["<<client_contact>>"] = client_number
                    placeholders["<<client_desig>>"] = client_desig if 'client_desig' in locals() else ""
                    placeholders["<<date>>"] = date_field.strftime("%d-%m-%Y")
                    placeholders["<<validity_date>>"] = (date_field + timedelta(days=7)).strftime("%d-%m-%Y")
                
                placeholders.update(pricing_data)
                placeholders.update(team_data)
                placeholders.update(special_data)
                placeholders.update(additional_tools_data)
                
                # Format date for filename
                formatted_date = date_field.strftime("%d_%b_%Y")
                unique_id = str(uuid.uuid4())[:8]
                doc_filename = f"{selected_proposal}_{client_name}_{formatted_date}_{unique_id}.docx"
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        doc = Document(template_path)
                    except FileNotFoundError:
                        st.error(f"Template file not found: {template_path}")
                        return

                    doc = replace_and_format(doc, placeholders)

                    # Remove empty rows from the pricing table
                    for table in doc.tables:
                        remove_empty_rows(table)

                    doc_path = os.path.join(temp_dir, doc_filename)
                    doc.save(doc_path)

                    with open(doc_path, "rb") as f:
                        docx_bytes = f.read()
                    
                    st.success("Proposal generated successfully!")
                    
                    st.download_button(
                        label="📥 Download Proposal",
                        data=docx_bytes,
                        file_name=doc_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_docx"
                    )
                    
                    # PDF conversion if available
                    if PDF_CONVERSION_AVAILABLE:
                        try:
                            pdf_path = os.path.join(temp_dir, f"{selected_proposal}_{client_name}_{formatted_date}_{unique_id}.pdf")
                            convert(doc_path, pdf_path)
                            
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_bytes,
                                file_name=f"{selected_proposal}_{client_name}_{formatted_date}_{unique_id}.pdf",
                                mime="application/pdf",
                                key="download_pdf"
                            )
                        except Exception as e:
                            st.warning("PDF conversion failed. Please download the DOCX file.")
                    else:
                        st.info("PDF conversion is not available. Install docx2pdf for PDF support.")
                        st.code("pip install docx2pdf", language="bash")
            
            except Exception as e:
                st.error(f"Error generating proposal: {str(e)}")
                st.error("Please make sure all required fields are filled correctly.")
    st.markdown('</div>', unsafe_allow_html=True)

# Add this function for DM & Automation specific calculations
def calculate_dm_automation_pricing(pricing_data, numerical_values, currency_symbol):
    # Calculate amount for 1 business
    amount_1_business = sum(numerical_values.values())
    pricing_data["<<amount_for_1_buisness>>"] = f"{currency_symbol}{format_number_with_commas(amount_1_business)}"
    
    # Calculate 10% discount for 2nd business
    amount_2_business = int(amount_1_business * 0.9)  # 10% discount
    pricing_data["<<amount_2_buisness>>"] = f"{currency_symbol}{format_number_with_commas(amount_2_business)}"
    
    # Calculate total amount
    total_amount = amount_1_business + amount_2_business
    pricing_data["<<total_amount>>"] = f"{currency_symbol}{format_number_with_commas(total_amount)}"
    
    # Calculate payment schedule
    payment_30 = int(total_amount * 0.3)
    payment_40 = int(total_amount * 0.4)
    balance_payment = total_amount - payment_30 - payment_40
    
    pricing_data["<<30_payment>>"] = f"{currency_symbol}{format_number_with_commas(payment_30)}"
    pricing_data["<<40_payment>>"] = f"{currency_symbol}{format_number_with_commas(payment_40)}"
    pricing_data["<<blnc_payment>>"] = f"{currency_symbol}{format_number_with_commas(balance_payment)}"
    
    return pricing_data

if __name__ == "__main__":
    generate_document()

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

    # Company Information Section
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("🏢 Company Information")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Basic Details")
        client_name = st.text_input("Company Name", placeholder="Enter company name")
        client_email = st.text_input("Business Email", placeholder="Enter business email")
        date_field = st.date_input("Proposal Date", datetime.today())
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="sub-section">', unsafe_allow_html=True)
        st.subheader("Contact Information")
        country = st.selectbox("Select Country", ["India", "United States", "Other"])
        client_number = st.text_input("Contact Number", placeholder="+91 for India, +1 for US")
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
                    vdate = st.date_input("Proposal Validity Until:", date_field + timedelta(days=30))
                    special_data[placeholder] = vdate.strftime("%d-%m-%Y")
                else:
                    special_data[placeholder] = st.text_input(f"{field.replace('_', ' ').title()}:")
        st.markdown('</div>', unsafe_allow_html=True)

    # Service Pricing Section
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("💰 Service Pricing")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Currency selection
    currency = st.select_slider(
        "Select Currency",
        options=["USD", "INR"],
        value="USD"
    )
    currency_symbol = "$" if currency == "USD" else "₹"

    # Service pricing
    pricing_data = {}
    numerical_values = {}
    
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
    
    # Annual Maintenance (10% of Total Amount)
    am_price = int(services_sum * 0.10)
    pricing_data["<<AM-Price>>"] = f"{currency_symbol}{format_number_with_commas(am_price)}"

    # Total Amount
    total = services_sum + am_price
    if currency == "INR":
        pricing_data["<<T-Price>>"] = f"{currency_symbol}{format_number_with_commas(total)} + 18% GST"
    else:
        pricing_data["<<T-Price>>"] = f"{currency_symbol}{format_number_with_commas(total)}"

    # Additional Features & Enhancements
    af_price = 250 if currency == "USD" else 25000
    pricing_data["<<AF-Price>>"] = f"{currency_symbol}{format_number_with_commas(af_price)}"

    # Price Summary
    st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
    st.subheader("Price Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Services Total", f"{currency_symbol}{format_number_with_commas(services_sum)}")
    with col2:
        st.metric("Annual Maintenance (10%)", f"{currency_symbol}{format_number_with_commas(am_price)}")
    with col3:
        st.metric("Final Amount", 
                 f"{currency_symbol}{format_number_with_commas(total)}" + 
                 (" + 18% GST" if currency == "INR" else ""))
    st.markdown('</div>', unsafe_allow_html=True)

    # Team Configuration Section
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("👥 Team Configuration")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sub-section">', unsafe_allow_html=True)
    team_data = {}
    if config["team_type"] == "marketing":
        team_data = get_marketing_team_details()
    else:
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

if __name__ == "__main__":
    generate_document()
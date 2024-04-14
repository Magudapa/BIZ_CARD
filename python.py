import os
import re
import easyocr
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image
from sqlalchemy import create_engine, update, Table, MetaData, Column, String, Integer

engine = create_engine("postgresql+psycopg2://postgres:magu@localhost/bizcard_data")
conn = engine.connect()

metadata = MetaData()

# Define the table structure
business_card_table = Table(
    'bizcard_data', metadata,  
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('designation', String),
    Column('contact', String),
    Column('email', String),
    Column('website', String),
    Column('street', String),
    Column('city', String),
    Column('state', String),
    Column('pincode', String),
    Column('company', String)
)

# Create the table
metadata.create_all(engine)

def png_to_text(image_path):
    reader = easyocr.Reader(['en'], gpu=False)
    image = Image.open(image_path).convert('RGB')
    details = reader.readtext(image_path, detail=0)
    return details

def data_output(details):
    data = {
        "name": "",
        "designation": "",
        "contact": [],
        "email": "",
        "website": "",
        "street": "",
        "city": "",
        "state": "",
        "pincode": "",
        "company": []
    }

    for i in range(len(details)):
        match1 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+). ([a-zA-Z]+)', details[i])
        match2 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+)', details[i])
        match3 = re.findall('^[E].+[a-z]', details[i])
        match4 = re.findall('([A-Za-z]+) ([0-9]+)', details[i])
        match5 = re.findall('([0-9]+ [a-zA-z]+)', details[i])
        match6 = re.findall('.com$', details[i])
        match7 = re.findall('([0-9]+)', details[i])
        if i == 0:
            data["name"] = details[i]
        elif i == 1:
            data["designation"] = details[i]
        elif '-' in details[i]:
            data["contact"].append(details[i])
        elif '@' in details[i]:
            data["email"] = details[i]
        elif "www " in details[i].lower() or "www." in details[i].lower():
            data["website"] = details[i]
        elif "WWW" in details[i]:
            data["website"] = details[i] + "." + details[i+1]
        elif match6:
            pass
        elif match1:
            data["street"] = match1[0][0]
            data["city"] = match1[0][1]
            data["state"] = match1[0][2]
        elif match2:
            data["street"] = match2[0][0]
            data["city"] = match2[0][1]
        elif match3:
            data["city"] = match3[0]
        elif match4:
            data["state"] = match4[0][0]
            data["pincode"] = match4[0][1]
        elif match5:
            data["street"] = match5[0] + ' St,'
        elif match7:
            data["pincode"] = match7[0]
        else:
            data["company"].append(details[i])

    data["contact"] = " & ".join(data["contact"])
    data["company"] = " ".join(data["company"])
    return data

def data_insert(data):
    df = pd.DataFrame([data])
    df.to_sql("bizcard_data", conn, if_exists='append', index=False)

# Streamlit part
st.set_page_config(layout="wide")

st.title("BUSINESS CARD EXTRACTION USING 'EASYOCR'")

col1, col2 = st.columns([1, 4])
with col1:
    menu = option_menu("MAIN_MENU", ["HOME", "UPLOAD", "Database"])
    
    if menu == 'Database':
        Database_menu = option_menu("Database", ['Modify','Delete'])

with col2:
    if menu == 'HOME':
        st.header('WELCOME TO BIZCARDX :')
        home_text = "THIS PROJECT IS USED TO EXTRACT THE BUSINESS CARD INFORMATION FROM IMAGES USING 'EASYOCR' LIBRARY"
        st.markdown(f"<h4 text-align: left;'>{home_text} </h4>", unsafe_allow_html=True)
    
        st.subheader(':red[ABOUT THE PROJECT:]')
        above_text = '''BIZCARDX is a streamlit web application used for extracting information 
                        from business card images using easyocr (Optical Character Recognition) library. 
                        The extracted details are stored in the PostgreSQL database. Users can upload the image and retrieve the details easily.'''
        st.markdown(f"<h4 text-align: left;'>{above_text} </h4>", unsafe_allow_html=True)
    
        st.subheader(":green[TECHNOLOGIES USED:]")
        tech_text = '''The project is built using Python and libraries like Pandas, Streamlit, SQLAlchemy, and EasyOCR.'''
        st.markdown(f"<h4 text-align: left;'>{tech_text} </h4>", unsafe_allow_html=True)
    if menu == 'UPLOAD':
        path = False
        col3, col4 = st.columns([2, 2])
        with col3:
            uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                image_path = uploaded_file.name
                image = Image.open(image_path)
                col3.image(image)
                path = True

        with col4:
            if path:
                extract = st.button("EXTRACT", key="EXTRACT_BUTTON")
                upload = st.button("UPLOAD", key="UPLOAD_BUTTON")

                if upload:
                    if path:
                        extracted_data = png_to_text(image_path)
                        processed_details = data_output(extracted_data)
                        data_insert(processed_details)
                        st.success("FILE UPLOADED SUCCESSFULLY")

                if extract:
                    if path:
                        extracted_data = png_to_text(image_path)
                        processed_details = data_output(extracted_data)
                        st.write('**Name** :', processed_details['name'])
                        st.write('**Designation** :', processed_details['designation'])
                        st.write('**Company Name** :', processed_details['company'])
                        st.write('**Contact Number** :', processed_details['contact'])
                        st.write('**E-mail** :', processed_details['email'])
                        st.write('**Website** :', processed_details['website'])
                        st.write('**Street** :', processed_details['street'])
                        st.write('**City** :', processed_details['city'])
                        st.write('**State** :', processed_details['state'])
                        st.write('**Pincode** :', processed_details['pincode'])

    if menu == 'Database':
        df = pd.read_sql('bizcard_data', engine)
        st.header("Database")
        st.dataframe(df)
        st.button('Show Changes')
            
        if Database_menu == 'Modify':
            modify_col_1, modify_col_2 = st.columns(2)
            with modify_col_1:
                st.header('Choose where to modify the details.')
                names= ['Please select one','name','contact','email']
                selected = st.selectbox('**select Categories**',names)
                if selected != 'Please select one':
                        select = ['Please select one'] + list(df[selected])
                        select_detail = st.selectbox(f'**select the {selected}**', select)
                        
                        with modify_col_2:
                            if select_detail != 'Please select one':
                                st.header('Choose what details to modify.')
                                df1 = df[df[selected] == select_detail]
                                df1 = df1.reset_index()
                                select_modify = st.selectbox('**select categories**', ['Please select one'] + list(df.columns))
                                if select_modify != 'Please select one':
                                    a = df1[select_modify][0]            
                                    st.write(f'Do you want to change {select_modify}: **{a}** ?')
                                    modified = st.text_input(f'**Enter the {select_modify} to be modified.**')
                                    if modified:
                                        st.write(f'{select_modify} **{a}** will change as **{modified}**')
                                        with modify_col_1:
                                            if st.button("Commit Changes"):
                                                
                                                update_statement = (
                                                                    update(business_card_table)
                                                                    .where(business_card_table.c[selected] == select_detail)
                                                                    .values({select_modify: modified})
                                                                )
                                                
                                                conn.execute(update_statement)
                                                conn.commit()
                                                st.success("Changes committed successfully!")
            
        if Database_menu == 'Delete':
            names= ['Please select one','name','email']
            delete_selected = st.selectbox('**select where to delete the details**',names) 
            if delete_selected != 'Please select one':
                options_list = list(df[delete_selected].unique())
                delete_select_detail = st.selectbox(f'**select the {delete_selected} to remove**', ['Please select one'] + options_list)
                if delete_select_detail != 'Please select one':
                    st.write(f'Do you want to delete **{delete_select_detail}** card details ?')
                    col5,col6,col7 =st.columns([1,1,5])
                    delete = col5.button('Yes I do')
                    if delete:
                        delete_query = (
                                        business_card_table.delete()
                                        .where(business_card_table.c[delete_selected] == delete_select_detail)
                                        )

                        
                        conn.execute(delete_query)
                        conn.commit()
                        st.success("Data Deleted successfully", icon ='✅')


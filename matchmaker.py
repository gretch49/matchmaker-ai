# # streamlit run matchmaker.py
import streamlit as st
import os
from langchain_openai import ChatOpenAI


@st.cache_data(show_spinner=False)
def get_keywords(description):
    from langchain_openai import ChatOpenAI

    model = ChatOpenAI()
    prompt = f"""
    Return a list of key words: '{description}' 
    Separate the keywords with semi-colons. Keep each keyword short, 1-3 words max. Use a single line.
    """

    response = model.invoke(prompt)
    response_stripped = response.content.strip(' "')

    return response_stripped


@st.cache_data(show_spinner=False)
def get_resume_section(initial_prompt):
    model = ChatOpenAI()
    prompt = f"""
    {initial_prompt} Do not make up numbers. When you use a keyword from the list, wrap it like so: [[[keyword]]]
    """
    response = model.invoke(prompt)
    response_stripped = response.content.strip(' "')

    print(response_stripped)

    blueify = response_stripped.replace("[[[", ":blue[")
    blueify = blueify.replace("]]]", "]")

    return blueify



def clicked(button):
    st.session_state.clicked[button] = True



if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
    gretchen_key = os.environ.get('GRETCHEN_KEY')
    openai_api_key=""        
    keywords=""
    # relevant_keywords=""

    if 'clicked' not in st.session_state:
        st.session_state.clicked = {"key_button_get_keywords":False,"key_button_save_rele_keywords":False,"key_button_go":False}
    
    st.header("MatchMaker AI")
    st.write("Match your resume to the job application with ChatGPT")
    st.divider()

    with st.sidebar:
        sidebar_key = st.sidebar.text_input("OpenAI API Key")
        if sidebar_key == gretchen_key:
            st.success("You used Gretchen's key. :tada:")
            openai_api_key = os.environ.get('OPENAI_API_KEY')
        elif sidebar_key and not sidebar_key.startswith('sk-'):
            st.error("Double-check your OpenAI API key! If you try to use this, you'll get an error.", icon='⚠')
        elif sidebar_key:
            st.success('Key saved for the duration of this session.')
            st.info('Close the sidebar to hide your key.')
            openai_api_key = sidebar_key

    if not openai_api_key:
        st.info("Enter your OpenAI API key on the left to continue.")

    else:
        st.write(" ")
        st.subheader("The Job")
        st.write(" ")
        st.write(":red[Copy and paste the job description here.]")
        job_description = st.text_area("Copy and paste the job description here.",label_visibility="collapsed", placeholder="The job description", key="key_job_description", height=300)
        
        ################################################################################
        st.button('Get keywords', on_click=clicked, args=["key_button_get_keywords"],type="primary")
        ################################################################################

        if st.session_state.clicked["key_button_get_keywords"] and not job_description:
            st.warning("Enter the job description.", icon='⚠')

        if job_description and st.session_state.clicked["key_button_get_keywords"]:
            with st.spinner('Scanning job description for keywords . . .'):
                keywords = get_keywords(job_description)
                
                st.write(" ")
                st.subheader("Keywords")
                st.write(f"**The keywords for this job description are:**  \n{keywords}  \n")
                st.write(" ")

        if keywords:
            st.write(" ")
            ################################################################################
            ################################################################################
            ################################################################################





            st.markdown(":red[Check the keywords that are relevant to your experience.]")
            


            keywords_list = keywords.split('; ')
            keywords_list = [x.strip() for x in keywords_list]
            



            checked_keywords_list = []
            for x in keywords_list:
                checkbox_value = st.checkbox(x,key=f"key_{x}")
                if checkbox_value:
                    checked_keywords_list.append(x)
            
            wrapped_list = ["[[[" + x.strip() + "]]]" for x in checked_keywords_list]

            checked_keywords_string = "; ".join(checked_keywords_list)
            
            ########################################################################
            st.write(" ")
            st.button('Save keywords', on_click=clicked, args=["key_button_save_rele_keywords"], type="primary")
            ########################################################################
            
            if checked_keywords_string and st.session_state.clicked["key_button_save_rele_keywords"]:
                st.write(" ")
                st.write(" ")
                st.markdown(f"**Your relevant keywords are:**  \n:blue[{checked_keywords_string}]  \n")

                st.write(" ")
                st.divider()
                st.write(" ")
                st.subheader("Your Work History")
                column1, column2, column3 = st.columns([2,1,1])
                
                column1.write("Your position title: ")
                your_job_title = column1.text_input("Your position title: ", key = "key_your_title",label_visibility="collapsed").upper()
                
                column2.write("Years: ")
                years_job = column2.number_input("Years:", value="min", min_value=1,max_value=40, key="key_years_job", label_visibility="collapsed", step=1)

                column3.write("(Optional)  Notes: ")
                notes = column3.text_area("Notes",key="key_job_notes", label_visibility="collapsed",height=100, placeholder="Add in clients, specific projects, or anything else.")

                if your_job_title:
                    st.write(" ")
                    display_prompt = f"Write a resume section with 5 bullet points for {your_job_title} with {years_job} year(s) of experience with the following keywords:  \n  :blue[{checked_keywords_string}]"

                    if notes:
                        display_prompt += f"  \n  \nAdditional notes include: {notes}"
                    
                    with st.container(border=True):
                        st.markdown(f'**ChatGPT will receive this prompt:**  \n  \n{display_prompt}\n')
                    st.write(" ")

                    func_prompt = f"Write a resume section with 5 bullet points for a {your_job_title} with {years_job} year(s) of experience with the following keywords: {wrapped_list}"

                    if notes:
                        func_prompt += f" Additional notes about this job: {notes}"
                    
                    ########################################################################
                    st.button('Generate resume section', on_click=clicked, args=["key_button_go"], type="primary")
                    ########################################################################
                    
                    if st.session_state.clicked["key_button_go"]:
                        with st.spinner('Creating resume section . . .'):    
                            resume_result = get_resume_section(func_prompt)
                            
                            st.write(" ")
                            st.divider()
                            st.write(" ")

                            st.subheader("Your Result")
                            with st.container(border=True):
                                st.markdown(resume_result)
                            st.markdown("*NB: The highlight is for your benefit. It is recommended you* ***do not*** *highlight the keywords in your resume PDF.*")

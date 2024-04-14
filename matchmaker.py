import streamlit as st
import time
import os
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


@st.cache_data(show_spinner=False)
def get_keywords(description):
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=chatgpt_key)
    prompt = f"""
    Return a list of key words: '{description}' 
    Separate the keywords with semi-colons. Keep each keyword short, 1-3 words max. Use a single line.
    """

    response = llm.invoke(prompt)
    response_stripped = response.content.strip(' "')

    return response_stripped


@st.cache_data(show_spinner=False)
def get_resume_section(your_job_title,years_job, wrapped_list, final_keywords_list, company, notes):
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=chatgpt_key)
    
    wrapped_list = [item.lower() for item in wrapped_list]
    final_keywords_list = [item.lower() for item in final_keywords_list]
    
    if company:
        func_prompt = f"Write a resume section with 5 bullet points for a {your_job_title} with {years_job} year(s) of experience at '{company}' with the following keywords: {wrapped_list}"
    else:
        func_prompt = f"Write a resume section with 5 bullet points for a {your_job_title} with {years_job} year(s) of experience with the following keywords: {wrapped_list}"
    if notes:
        func_prompt += f" Additional notes about this job: {notes}"

    prompt = f"""
    {func_prompt} Only use the numbers given to you. Do not use a header.
    """

    response = llm.invoke(prompt)
    response_stripped = response.content.strip(' "')

    wrapped_response = wrap_keywords_in_description(response_stripped, final_keywords_list)

    return wrapped_response



@st.cache_data(show_spinner=False)
def get_resume_bio(your_job_title,years_job, wrapped_list, final_keywords_list, company, notes):
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=chatgpt_key)
    # wrapper = DuckDuckGoSearchAPIWrapper(max_results=1)
    
    # if company:
    #     search = DuckDuckGoSearchRun()
    #     print(company)
    #     company_description = search.run(f'Search for the homepage of the company {company}')

    #     print("\n\n\n"+"##$$$%"*10+"\n")
    #     print(company_description)
    #     print("\n"+"##$$$%"*10+"\n\n\n")

    for index, item in enumerate(wrapped_list):
        wrapped_list[index] = item.lower()

    for index, item in enumerate(final_keywords_list):
        final_keywords_list[index] = item.lower()

    func_prompt = f"Write a resume bio about 25 words for a {your_job_title} with {years_job} year(s) of experience with the following keywords:  \n {wrapped_list} \n"

    if notes:
        func_prompt += f" Additional notes about this job: {notes}"

    prompt = f"""
    {func_prompt}
    """

    response = llm.invoke(prompt)
    response_stripped = response.content.strip(' "')

    print(f"\n\n\n{response_stripped}\n\n\n")

    wrapped_response = wrap_job_details(response_stripped, your_job_title, years_job, company, notes)
    wrapped_response = wrap_keywords_in_description(wrapped_response, final_keywords_list)

    

    return wrapped_response



@st.cache_data(show_spinner=False)
def clicked(button):
    st.session_state.clicked[button] = True



@st.cache_data(show_spinner=False)
def wrap_keywords_in_description(description, keywords):

    for keyword in keywords:
        description = description.replace(keyword.lower(), ":blue[**" + keyword + "**]")

    return description



@st.cache_data(show_spinner=False)
def wrap_job_details(description, your_job_title, years_job, company, notes):
    years_job = str(years_job) + " years"
    keywords = [your_job_title, years_job]

    for keyword in keywords:
        description = description.replace(keyword.lower(), "**" + keyword + "**")

    return description







if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
    gretchen_key = os.environ.get('GRETCHEN_KEY')
    chatgpt_key = ""
    keywords = None

    if 'clicked' not in st.session_state:
        st.session_state.clicked = {"key_button_get_keywords":False,"key_button_save_rele_keywords":False,"key_button_go":False,"key_generate_prompt_button":False}
    
    st.header("MatchMaker AI")
    st.write("Match your resume to the job application with ChatGPT")
    st.subheader(" ", divider='blue')

    with st.sidebar:
        sidebar_key = st.sidebar.text_input("OpenAI API Key").strip()
        st.sidebar.button("Enter key")
        st.sidebar.write(" ")

        if sidebar_key == gretchen_key: 
            st.success("You're using Gretchen's key. :tada:")
            chatgpt_key = os.environ.get('OPENAI_API_KEY')
        elif sidebar_key and not sidebar_key.startswith('sk-'):
            st.error("Double-check your OpenAI API key! If you try to use this, you'll get an error.", icon='⚠')
        elif sidebar_key:
            st.success('Key saved for the duration of this session.')
            st.info('Close the sidebar to hide your key.')
            chatgpt_key = sidebar_key

    if not chatgpt_key:
        st.info("Enter your OpenAI API key on the left to continue.")

    else:
        st.write(" ")
        st.write(" ")
        st.write(" ")

        st.subheader("The Job")
        st.write(" ")
        
        st.write(":red[Copy and paste the job description:]")
        job_description = st.text_area("Copy and paste the job description here.",label_visibility="collapsed", placeholder="The job description", key="key_job_description", height=300)

        st.button('Get keywords', on_click=clicked, args=["key_button_get_keywords"],type="primary")

        if st.session_state.clicked["key_button_get_keywords"] and not job_description:
            st.warning("Enter the job description.", icon='⚠')

        if job_description and st.session_state.clicked["key_button_get_keywords"]:
            with st.spinner('Scanning job description for keywords . . .'):
                keywords = get_keywords(job_description)
                
                st.write(" ")
                st.write(" ")
                st.subheader("Keywords")

        if keywords:
            st.markdown(":red[Check the keywords that are relevant to your experience. You'll be able to edit them later.]")

            keywords_list = keywords.split('; ')
            keywords_list = [x.strip() for x in keywords_list]

            checked_keywords_list = []
            for x in keywords_list:
                checkbox_value = st.checkbox(x,key=f"key_{x}")
                if checkbox_value:
                    checked_keywords_list.append(x)
        

            checked_keywords_string = "; ".join(checked_keywords_list)

            st.write(" ")
            st.markdown(":red[Edit the keywords:]")
            edit_keywords_string = st.text_area("Edit", value=checked_keywords_string,key="key_relevant_keywords",label_visibility="collapsed")
            
            edit_keywords_list = edit_keywords_string.split('; ')
            edit_keywords_list = [x.strip() for x in edit_keywords_list]

            final_keywords_list = []
            for keyword_string in edit_keywords_list:
                keywords = keyword_string.split()
                final_keywords_list.extend(keywords)

            # wrapped_list = ["[[[" + x.strip() + "]]]" for x in edit_keywords_list]

            save_keywords_button = st.button('Save your relevant keywords', on_click=clicked, args=["key_button_save_rele_keywords"], type="primary")

            if checked_keywords_string and save_keywords_button:
                st.write(" ")
                container = st.empty()
                container.success("Keywords saved.") 
                time.sleep(1.5)
                container.empty()  

            if checked_keywords_string and st.session_state.clicked["key_button_save_rele_keywords"]:
                st.write(" ")
                st.write(" ")
                st.write(" ")
                st.subheader("Your Work History")
                column1, column2 = st.columns([1.5,1])
                
                column1.write(":red[Your position title: ]")
                your_job_title = column1.text_input("Your position title: ", key = "key_your_title",label_visibility="collapsed")
                
                column1.write(" ")

                column2.write(":red[Years: ]")
                years_job = column2.number_input("Years:", value="min", min_value=1,max_value=40, key="key_years_job", label_visibility="collapsed", step=1)

                column2.write(" ")
                
                column2.write("(Optional) Company: ")
                company = column2.text_input("Company: ", key = "key_company",label_visibility="collapsed")

                column1.write("(Optional)  Notes: ")
                notes = column1.text_area("Notes",key="key_job_notes", label_visibility="collapsed",height=120, placeholder="Add in clients, specific projects, or anything else.")

                generate_prompt = st.button("Generate prompt", type="primary",key="key_generate_prompt_button",on_click=clicked, args=["key_generate_prompt_button"])
                
                if your_job_title and st.session_state.clicked["key_generate_prompt_button"]:
                    st.write(" ")
                    if company:
                        display_prompt = f"Write a resume section with 5 bullet points for a **{your_job_title}** with **{years_job} year(s) of experience** at **{company}** with the following keywords:  \n  \n  :blue[**{edit_keywords_string}**]"
                    else:
                        display_prompt = f"Write a resume section with 5 bullet points for a **{your_job_title}** with **{years_job} year(s) of experience** with the following keywords:   \n  :blue[**{edit_keywords_string}**]"

                    if notes:
                        display_prompt += f"  \n  \nAdditional notes: **{notes}**"
                    
                    st.write(" ")
                    with st.container(border=True):
                        st.markdown(f'**ChatGPT will receive this prompt:**  \n  \n {display_prompt}\n')
                    st.write(" ")

                    button_go = st.button('Generate resume section', on_click=clicked, args=["key_button_go"], type="primary")
                    
                    if button_go:
                        with st.spinner('Creating resume section . . .'):    
                            resume_section_result = get_resume_section(your_job_title,years_job, edit_keywords_list,final_keywords_list, company, notes)
                            resume_bio_result = get_resume_bio(your_job_title,years_job, edit_keywords_list,final_keywords_list, company, notes)
                            
                            st.write(" ")
                            st.write(" ")
                            st.write(" ")
                            st.subheader("Your Result")

                            with st.container(border=True):
                                st.write("BIO")
                                st.markdown(resume_bio_result)
                                st.divider()

                                if company:
                                    st.write(f"EXPERIENCE at **{company}**")
                                else: 
                                    st.write("EXPERIENCE")

                                st.markdown(resume_section_result)
                            st.caption("Please note: The highlighted text is provided for your convenience. Not all keywords may be highlighted if the text was changed slightly. It is strongly advised that you refrain from highlighting keywords in your resume.")

                            st.caption("**Double check the results for accuracy.**")
                            print("\n\n\n"+"##$$$%"*10+"\n\n\n")

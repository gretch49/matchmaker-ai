import streamlit as st
import time
import random
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
    Separate the keywords with semi-colons. Keep each keyword short, 1-3 words max. Use a single line. Do not use any periods at the end.
    """

    response = llm.invoke(prompt)
    response_stripped = response.content.strip(' "')

    return response_stripped


@st.cache_data(show_spinner=False)
def get_resume_section(your_job_title,years_job, list_keywords, list_keywords_split, company, notes, include_checkbox):
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=chatgpt_key)
    company_description = ""

    list_keywords = [item.lower() for item in list_keywords]
    list_keywords_split = [item.lower() for item in list_keywords_split]
    short_company_bio = None
    
    if company and include_checkbox:
        company_description = ddg_search(company)

        func_prompt = f"Write a resume section with 5 bullet points for a {your_job_title} with {years_job} year(s) of experience at '{company}' with the following keywords: [{list_keywords}] The company is described here: [{company_description}] Add in relevant details about the company to the job description."

        short_company_bio = get_short_bio(company,company_description)

    else:
        func_prompt = f"Write a resume section with 5 bullet points for a {your_job_title} with {years_job} year(s) of experience with the following keywords: {list_keywords}"
    if notes:
        func_prompt += f" Additional notes about this job: {notes}"

    prompt = f"""
    {func_prompt} Do not use a header. Do not make up numbers. 
    """

    response = llm.invoke(prompt)
    response_stripped = response.content.strip(' "')

    wrapped_response = wrap_keywords_in_description(response_stripped, list_keywords)

    return wrapped_response, short_company_bio



@st.cache_data(show_spinner=False)
def get_resume_bio(your_job_title,years_job, list_keywords, list_keywords_split, company, notes, unique):
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=chatgpt_key)

    for index, item in enumerate(list_keywords):
        list_keywords[index] = item.lower()

    for index, item in enumerate(list_keywords_split):
        list_keywords_split[index] = item.lower()

    if company and include_checkbox:
        company_description = ddg_search(company)
        short_company_bio = get_short_bio(company,company_description)
        func_prompt = f"Write a 3-sentence, unique resume bio for a {your_job_title} with {years_job} year(s) of experience at {company}, {short_company_bio} with the following keywords:  \n {list_keywords} \n Don't use all the keywords. Keep the length to about 25 words."
    else:
        func_prompt = f"Write a unique resume bio about 25 words for a {your_job_title} with {years_job} year(s) of experience with the following keywords:  \n {list_keywords} \n Don't use all the keywords. Keep the length to about 25 words."

    if notes:
        func_prompt += f"\nAdditional notes about this job: {notes}"

    if unique:
        func_prompt += f"\nI'm unique as a {your_job_title} because: {unique}"

    prompt = f"""
    {func_prompt}
    """

    response = llm.invoke(prompt)
    response_stripped = response.content.strip(' "')

    wrapped_response = wrap_job_details(response_stripped, your_job_title, years_job)
    wrapped_response = wrap_keywords_in_description(wrapped_response, list_keywords)

    return wrapped_response



@st.cache_data(show_spinner=False)
def clicked(button):
    st.session_state.clicked[button] = True



@st.cache_data(show_spinner=False)
def wrap_keywords_in_description(description, keywords):

    for keyword in keywords:
        description = description.replace(keyword.lower(), ":blue[" + keyword + "]")

    return description



@st.cache_data(show_spinner=False)
def wrap_job_details(description, your_job_title, years_job):
    years_job = str(years_job) + " years"
    keywords = [your_job_title, years_job]

    for keyword in keywords:
        description = description.replace(keyword.lower(), "**" + keyword + "**")

    return description



@st.cache_data(show_spinner=False)
def ddg_search(company):
    wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)

    company_description = search.run(f'Search for a description of the company {company}')

    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
    prompt = f"""
    Summarize the description this company [{company}] with several possible descriptions scraped from the web: [{company_description}] 
    
    Use the relevant information and ignore the rest. If the descriptions do not seem to match, reply "No relevant description found."
    """

    response = llm.invoke(prompt)
    response_stripped = response.content.strip(' "')

    return(response_stripped)



@st.cache_data(show_spinner=False)
def get_short_bio(company,company_description):
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, api_key=chatgpt_key)

    short_company_bio = llm.invoke(f"Write a '5-10 word' summary about the company {company} based on the description: [{company_description}] Return in the format: {company}, description")

    short_company_bio = short_company_bio.content.strip(' "')

    return short_company_bio



if __name__ == "__main__":
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
    gretchen_key = os.environ.get('GRETCHEN_KEY')
    friends_key = os.environ.get('FRIENDS_KEY')
    chatgpt_key = ""
    keywords = None
    include_checkbox = False
    asterick = "\\*"

    if 'clicked' not in st.session_state:
        st.session_state.clicked = {
            "key_button_get_keywords": False,
            "key_button_save_rele_keywords": False,
            "key_button_go": False,
            "key_generate_prompt_button": False
        }

    st.header("MatchMaker AI")
    st.write("Match your résumé to the job application with ChatGPT")
    st.subheader(" ", divider='blue')

    with st.sidebar:
        sidebar_key = st.sidebar.text_input("OpenAI API Key:").strip()
        st.sidebar.button("Enter key")
        st.sidebar.write(" ")

        if sidebar_key == gretchen_key or sidebar_key == friends_key: 
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
        st.write(f":red[ **{asterick}** indicates a required field.]")
        st.write(" ")
        st.write(" ")


        st.subheader("The Job")
        st.write(" ")
        
        st.write(f"Copy and paste the job description: :red[**{asterick}**]")
        job_description = st.text_area("Copy and paste the job description here.",label_visibility="collapsed", placeholder="The job description", key="key_job_description", height=300)

        get_keywords_button = st.button('Get keywords', on_click=clicked, args=["key_button_get_keywords"],type="primary")
        
        if get_keywords_button:
            st.session_state.clicked["key_button_get_keywords"] = True

        if st.session_state.clicked["key_button_get_keywords"] and not job_description:
            st.warning("Enter the job description.", icon='⚠')

        if job_description and st.session_state.clicked["key_button_get_keywords"]:
            with st.spinner('Scanning job description for keywords . . .'):
                keywords = get_keywords(job_description)
                
                st.write(" ")
                st.write(" ")
                st.subheader("Keywords")

        if keywords:
            st.markdown(f"Check the keywords that are relevant to your experience. You'll be able to edit them later. :red[**{asterick}**]")

            keywords_list = keywords.split('; ')
            keywords_list = [x.strip() for x in keywords_list]

            keywords_list = list(set(keywords_list))

            checked_keywords_list = []
            for x in keywords_list:
                checkbox_value = st.checkbox(x,key=f"key_{x}")
                if checkbox_value:
                    checked_keywords_list.append(x)

            
            percentage_checked = round((len(checked_keywords_list) / len(keywords_list)) * 100, 1)
            st.caption(f"Percentage of keywords selected: {percentage_checked}%")

            checked_keywords_string = "; ".join(checked_keywords_list)

            st.write(" ")
            st.markdown("*(Optional)* Edit the keywords:")
            edit_keywords_string = st.text_area("Edit", value=checked_keywords_string,key="key_relevant_keywords",label_visibility="collapsed")
            
            edit_keywords_list = edit_keywords_string.split('; ')
            edit_keywords_list = [x.strip() for x in edit_keywords_list]

            list_keywords_split = []
            for keyword_string in edit_keywords_list:
                keywords = keyword_string.split()
                list_keywords_split.extend(keywords)

            save_keywords_button = st.button('Save your relevant keywords', on_click=clicked, args=["key_button_save_rele_keywords"], type="primary")

            if save_keywords_button:
                st.session_state.clicked["key_button_save_rele_keywords"] = True

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
                
                column1.write(f"Your position title: :red[**{asterick}**]")
                your_job_title = column1.text_input("Your position title: ", key = "key_your_title",label_visibility="collapsed").strip()
                
                column1.write(" ")

                column2.write(f"Years: :red[**{asterick}**]")
                years_job = column2.number_input("Years:", value="min", min_value=1,max_value=40, key="key_years_job", label_visibility="collapsed", step=1)

                column2.write(" ")
                
                column2.write("*(Optional)* Company: ")
                company = column2.text_input("Company: ", key = "key_company",label_visibility="collapsed").strip()

                column1.write("*(Optional)*  Notes: ")
                notes = column1.text_area("Notes",key="key_job_notes", label_visibility="collapsed",height=120, placeholder="Add in clients, specific projects, or anything else.").strip()
                
                st.write(" ")
                st.write(" ")
                st.write(" ")
                st.subheader("About You")

                st.write("*(Optional)* Add something unique about you to put in your bio: ")
                unique = st.text_area(f"What makes you unique as a {your_job_title}?",label_visibility="collapsed",placeholder=f"I'm unique as a(n) {your_job_title} because... ", key = "key_unique_job").strip()

                generate_prompt = st.button("Generate prompt", type="primary",key="key_generate_prompt_button",on_click=clicked, args=["key_generate_prompt_button"])

            if generate_prompt:
                st.session_state.clicked["key_generate_prompt_button"] = True

                
                if your_job_title and st.session_state.clicked["key_generate_prompt_button"]:
                    st.write(" ")
                    if company:
                        display_prompt = f"Write a résumé bio and a work section with 5 bullet points for a(n) **{your_job_title}** with **{years_job} year(s) of experience** at **{company}** with the following keywords:  \n  \n  :blue[**{edit_keywords_string}**]"
                    else:
                        display_prompt = f"Write a résumé bio and a work section with 5 bullet points for a(n) **{your_job_title}** with **{years_job} year(s) of experience** with the following keywords:   \n  :blue[**{edit_keywords_string}**]"

                    if notes:
                        display_prompt += f"  \n  \nAdditional notes: **{notes}**"

                    if unique:
                        display_prompt += f"  \n  \nAbout me: **{unique}**"
                    
                    st.write(" ")
                    with st.container(border=True):
                        st.markdown(f'**ChatGPT will receive this prompt:**  \n  \n {display_prompt}\n')
                    st.write(" ")

                    if company:
                        with st.spinner(f'Searching the web for {company} . . .'):
                            company_gpt_found = ddg_search(company)
                        with st.container(border=True):
                            company_gpt_found = company_gpt_found.replace("$", "\\$")
                            st.markdown(f"**ChatGPT searched for *{company}* and found this:**  \n  \n:blue[**{company_gpt_found}**]")
                            st.divider()
                            st.write(" ")
                            st.write(f"*(Optional)* Edit the description for *{company}* here:")
                            company_description = st.text_area("Edit company description", value = company_gpt_found,height=300, label_visibility="collapsed")

                            include_checkbox = st.checkbox(f"Include this description of *{company}* to assist ChatGPT in your résumé generation.",value=True,key="key_checkbox_include_company")
                            
                        st.write(" ")


                    button_go = st.button('Generate résumé section', on_click=clicked, args=["key_button_go"], type="primary")
                    
                    if button_go:
                        with st.spinner('Creating résumé section . . .'):    
                            resume_section_result,short_company_bio = get_resume_section(your_job_title,years_job, edit_keywords_list,list_keywords_split, company, notes, include_checkbox)
                            resume_bio_result = get_resume_bio(your_job_title,years_job, edit_keywords_list,list_keywords_split, company, notes, unique)

                            st.write(" ")
                            st.write(" ")
                            st.write(" ")

                            st.subheader("Your Result",divider="blue")
                            st.write(" ")

                            with st.container(border=True):
                                st.write("BIO")
                                st.markdown(resume_bio_result)
                                st.divider()

                                if short_company_bio:
                                    st.write(f"EXPERIENCE at **{short_company_bio}**")
                                elif company:
                                    st.write(f"EXPERIENCE at **{company}**")
                                else: 
                                    st.write("EXPERIENCE")

                                st.markdown(resume_section_result)

                            st.caption("Please note: The highlighted text is provided for your convenience. Not all keywords may be highlighted if the text was changed slightly. It is strongly advised that you refrain from highlighting keywords in your résumé.")

                            st.caption("**Double check the results for accuracy.**")
    st.write(" ")
    st.write(" ")
    st.divider()
    st.write(" ")
    st.caption("Created 2024 by Gretchen Vogt — gretchenvogt.com #OpentoWork")

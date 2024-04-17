import streamlit as st
import time
import re
import os
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

# Get keywords from the initial job description
@st.cache_data(show_spinner=False)
def get_keywords(description):
    llm = ChatOpenAI(model='gpt-3.5-turbo-0125', temperature=0, api_key=chatgpt_key)
    # ATS tracking
    prompt = f'''
    What are the most likely ATS (Applicant Tracking System) keywords for this job description? Give up to 19 of the most likely ATS keywords and list them in the order of most important to least important. The description is: '{description}' 
    
    
    Separate the keywords with semi-colons. Keep each keyword short, 1-3 words max. Use a single line. Do not use any periods at the end.'''
    response = llm.invoke(prompt)

    keywords = response.content.strip(' "')
    keywords = keywords.replace('.','')
    keywords = keywords.strip()
    keywords_list = keywords.split('; ')
    keywords_list = [x.strip() for x in keywords_list]
    keywords_list = list(set(keywords_list))
    return keywords_list

#If a button is clicked, change the session state to True for the remainder of the program
@st.cache_data(show_spinner=False)
def clicked(button):
    st.session_state.clicked[button] = True



@st.cache_data(show_spinner=False)
def ddg_search(company):
    wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)

    company_description = search.run(f'Search for a description of the company {company}')

    llm = ChatOpenAI(model='gpt-3.5-turbo-0125', temperature=0)
    prompt = f'''
    Summarize the description this company [{company}] with several possible descriptions scraped from the web: [{company_description}] 
    
    Use the relevant information and ignore the rest. If none of the descriptions do not seem to match, return only 'No relevant description found.'
    '''
    with st.spinner(f'Searching for the web for {company}...'):
        response = llm.invoke(prompt)
        response = response.content.strip(' "')
        response = response.replace('$', '\\$')

        short_company_bio = llm.invoke(f'''
                                       Write a '5-10 word' summary about the company {company} based on the description: [{company_description}] Return in the format with the company name and a comma before the description: 

                                       {company}, description
                                       ''')
        short_company_bio = short_company_bio.content.strip(' "')


    return(response, short_company_bio)


@st.cache_data(show_spinner=False)
def get_bio(unique,relevant_keywords_list,experience_1,experience_2,experience_3):
    llm = ChatOpenAI(model='gpt-3.5-turbo-0125', temperature=0, api_key=chatgpt_key)
    job_details = f"{experience_1['job_title']}, {experience_2['job_title']}, {experience_3['job_title']}"

    prompt = f'''
    Write a 3-sentence, unique resume bio for a {job_details} based on this information [{unique}] and using these keywords [{relevant_keywords_list}]
    '''

    response = llm.invoke(prompt)
    response = response.content.strip(' "')
    
    final_response = wrap_keywords_in_description(response,relevant_keywords_list)
    return final_response



def get_experience(i,keywords_string):
    experience = {'job_title': '',
                  'years_job': '',
                  'company': '',
                  'notes': '',
                  'company_description': '',
                  'include': False,
                  'short_company_bio': ''
                  }
    asterick = '\\*'
    
    st.write(f'Your position title: :red[**{asterick}**]')
    experience['job_title'] = st.text_input('Your position title: ', key = f'job_title_{i}',label_visibility='collapsed').strip()
    st.write(' ')

    column1, column2 = st.columns([1,1])
    with column1:
        st.write(f'Years: :red[**{asterick}**]')
        year_num = st.number_input('Years:', value='min', min_value=1,max_value=40, key=f'years_job_{i}', label_visibility='collapsed', step=1)
        if year_num ==1:
            experience['years_job'] = f'{year_num} year'
        else:
            experience['years_job'] = f'{year_num} years'
        
    with column2:
        st.write('*(Optional)* Company: ')
        experience['company'] = st.text_input('Company: ',key = f'company_{i}',label_visibility='collapsed',value='').strip()
    st.write(' ')
    st.write('*(Optional)*  Notes: ')
    experience['notes'] = st.text_area('Notes',key=f'job_notes_{i}', label_visibility='collapsed',height=120, placeholder='Add in clients, specific projects, or anything else.').strip()
    st.write(' ')

    with st.container(border = True):
        st.markdown(f'**ChatGPT will receive this prompt for Position {i}:**  \n  \n ')
        if not experience['job_title']:
            st.caption('This section will populate once you add your position title.')
        else:
            if experience['company']:
                display = f'Write a résumé work section with 5 bullet points for a(n) **{experience['job_title']}** with **{experience['years_job']} year(s) of experience** at **{experience['company']}** with the following keywords:  \n  \n  :blue[**{keywords_string}**]'
                # Search for the company
                experience['company_description'],experience['short_company_bio'] = ddg_search(experience['company'])
            else:
                display = f'Write a résumé work section with 5 bullet points for a(n) **{experience['job_title']}** with **{experience['years_job']} year(s) of experience** with the following keywords:  \n  \n  :blue[**{keywords_string}**]'
            if experience['notes']:
                display = (f"{display}  \n  \nAdditional notes: {experience['notes']}")
            st.markdown(display)
            st.write(' ')

    if experience['company']:
        with st.container(border=True):        
            st.markdown(f'**ChatGPT searched for {experience['company']} and found this:**  \n')
            display_description = f':blue[{experience['company_description']}]'
            st.markdown(display_description)
            st.write(' ')
            st.write(f'*(Optional)* Edit the description for {experience['company']} here:')
            experience['company_description'] = st.text_area('Edit company description', value = experience['company_description'],height=150, label_visibility='collapsed',key=f'company_description_{i}')

            experience['include'] = st.checkbox(f'Include this description of {experience['company']} to assist ChatGPT in your résumé generation.',value=True,key=f'key_checkbox_include_company_{i}')

    st.write(' ')

    return experience



@st.cache_data(show_spinner=False)
def ask_gpt(experience,keywords_list):
    llm = ChatOpenAI(model='gpt-3.5-turbo-0125', temperature=0, api_key=chatgpt_key)
    keywords_string = st.session_state['relevant keywords']
    
    if experience['include']:
        prompt = f'''
        Write a resume section with 5 bullet points for a {experience['job_title']} with {experience['years_job']} year(s) of experience at '{experience['short_company_bio']}' with the following keywords: [{keywords_string}] The company is described here: [{experience['company_description']}] Add in relevant details about the company to the job description.
        '''
    elif experience['company']:
        prompt = f'''
        Write a resume section with 5 bullet points for a {experience['job_title']} with {experience['years_job']} year(s) of experience at '{experience['company']}' with the following keywords: [{keywords_string}]        
        '''
    else:
        prompt = f'''
        Write a resume section with 5 bullet points for a {experience['job_title']} with {experience['years_job']} year(s) of experience with the following keywords: [{keywords_string}]        
        '''
    if experience['notes']:
        prompt += f' Additional notes about this {experience['job_title']}: {experience['notes']}'

    prompt += ' Just return the bullet points. Do not use a header. Do not make up numbers.'

    with st.spinner('Creating résumé section . . .'):
        response = llm.invoke(prompt)
        response_stripped = response.content.strip(' "')

    final_response = wrap_keywords_in_description(response_stripped,keywords_list)
    return final_response



@st.cache_data(show_spinner=False)
def wrap_keywords_in_description(description, relevant_keywords_list):
    patterns = [re.compile(re.escape(keyword), re.IGNORECASE) for keyword in relevant_keywords_list]
    for pattern, keyword in zip(patterns, relevant_keywords_list):
        description = pattern.sub(':blue[' + keyword + ']', description)

    return description



if __name__ == '__main__':
    
    # Initializations
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(), override=True)
    gretchen_key = os.environ.get('GRETCHEN_KEY')
    friends_key = os.environ.get('FRIENDS_KEY')
    chatgpt_key = ''
    asterick = '\\*'
    relevant_keywords_list = []
    experience_1 = {'job_title': '',
                  'years_job': 1,
                  'company': '',
                  'notes': '',
                  'company_description': '',
                  'include': False,
                  'short_company_bio': ''
                  }    
    experience_2 = {'job_title': '',
                  'years_job': 1,
                  'company': '',
                  'notes': '',
                  'company_description': '',
                  'include': False,
                  'short_company_bio': ''
                  }
    experience_3 = {'job_title': '',
                  'years_job': 1,
                  'company': '',
                  'notes': '',
                  'company_description': '',
                  'include': False,
                  'short_company_bio': ''
                  }

    # If the program just started, set all buttons to False
    if 'clicked' not in st.session_state:
        st.session_state.clicked = {
            'get_keywords_button': False,
            'save_relevant_keywords_button': False,
            'key_button_go': False,
            'key_generate_prompt_button': False,
            'add_another_1':False,
            'add_another_2':False,
            'generate_prompt':False
        }
    # If the program just started, only show 1 job accordion
    if 'number_of_jobs' not in st.session_state:
        st.session_state['number_of_jobs'] = 1

    # Sidebar and API key
    with st.sidebar:
        sidebar_key = st.sidebar.text_input('OpenAI API Key:').strip()
        st.sidebar.button('Enter key')
        st.sidebar.write(' ')

        if sidebar_key == gretchen_key or sidebar_key == friends_key: 
            st.success("You're using Gretchen's key. :tada:")
            chatgpt_key = os.environ.get('OPENAI_API_KEY')
        elif sidebar_key and not sidebar_key.startswith('sk-'):
            st.error("Double-check your OpenAI API key! If you try to use this, you'll get an error.", icon='⚠')
        elif sidebar_key:
            st.success('Key saved for the duration of this session.')
            st.info('Close the sidebar to hide your key.')
            chatgpt_key = sidebar_key

    # Main page
    st.header('MatchMakerAI')
    st.write(' ')
    st.write("**Boost your résumé with tailored keywords to beat ATS and match with your dream job.** Stand out from the crowd with MatchmakerAI's advanced keyword optimization tools. Take the next step towards your dream career.")
    

    st.subheader(' ', divider='blue')
    if not chatgpt_key:
        st.info('Enter your OpenAI API key on the left to continue.')

    else:
        st.write(' ')
        st.write(' ')
        st.write(' ')    
        st.subheader('The Job')
        col1,col2=st.columns(2)
        col1.write(f'Copy and paste a job description here: :red[**{asterick}**]')
        col2.markdown("<div style='text-align: right; color: red; '>* indicates a required field.</div>", unsafe_allow_html=True)

        job_description = st.text_area('Copy and paste the job description here.',label_visibility='collapsed', placeholder='Job description', key='job_description', height=300)
        get_keywords_button = st.button('Get most likely ATS keywords', on_click=clicked, args=['get_keywords_button'],type='primary')
        
        if get_keywords_button:
            st.session_state.clicked['get_keywords_button'] = True

        # Remind user to give job description before asking for the keywords
        if st.session_state.clicked['get_keywords_button'] and not job_description:
            st.warning('Enter the job description.', icon="⚠️")
        #Get the keywords
        elif st.session_state.clicked['get_keywords_button'] and job_description:
            with st.spinner('Scanning job description for the most likely ATS keywords . . .'):
                keywords_list = get_keywords(job_description)
                st.write(' ')
                st.write(' ')
                st.subheader('Keywords')
            st.markdown(f"Check the keywords that are relevant to your experience. You'll be able to edit them later. :red[**{asterick}**]")
            
            i = 1
            for x in keywords_list:
                if x.islower():
                    checkbox_value = st.checkbox(f"{i}\\. {x.capitalize()}",key=f'checkbox {x}')
                else:
                    checkbox_value = st.checkbox(f"{i}\\. {x}",key=f'checkbox {x}')
                i += 1
                if checkbox_value:
                    relevant_keywords_list.append(x)

            # Count the number of keywords selected
            percentage_checked = round((len(relevant_keywords_list) / len(keywords_list)) * 100, 1)
            st.caption(f'Percentage of keywords selected: {percentage_checked}%')
            # Change list to string separated by a semicolon
            relevant_keywords_string = '; '.join(relevant_keywords_list)
            # Let the user edit the string of relevant keywords
            st.write(' ')
            st.markdown('*(Optional)* Edit the keywords:')
            edited_keywords_string = st.text_area('Edit', value=relevant_keywords_string,key='relevant keywords',label_visibility='collapsed')

            if not edited_keywords_string:
                save_keywords_button = st.button('Save your relevant keywords', type='primary',disabled=True)
                st.caption('Add keywords to save.')
            else:
                save_keywords_button = st.button('Save your relevant keywords', on_click=clicked, args=['save_relevant_keywords_button'], type='primary')
                st.caption(' ')

            if save_keywords_button:
                st.session_state.clicked['save_relevant_keywords_button'] = True

            if save_keywords_button and not edited_keywords_string:
                st.warning('Select keywords from the list or add your own.',icon="⚠")
            elif save_keywords_button and edited_keywords_string:
            # Show success state for a moment when button is pressed
                st.write(' ')
                container = st.empty()
                container.success('Keywords saved.') 
                time.sleep(1.5)
                container.empty()  

            if edited_keywords_string and st.session_state.clicked['save_relevant_keywords_button']:
                st.write(' ')
                st.write(' ')
                st.write(' ')

                st.subheader('Your Work History')
                st.write(' ')                
                
                with st.expander('Position 1',expanded=True):
                    experience_1 = get_experience(1,edited_keywords_string)  
                if st.session_state['number_of_jobs'] == 1 and not experience_1['job_title']:
                    add_another_1 = st.button('Add another position', disabled=True)
                    st.caption('Fill out Position 1 before adding another position.')
                # Once the user has added job experience...
                elif experience_1['job_title'] and st.session_state['number_of_jobs'] == 1:
                    add_another_1 = st.button('Add another position', on_click=clicked, args=['add_another_1'])
                # ...give them the option to add another
                    if add_another_1:
                        st.session_state.clicked['add_another_1'] = True
                        st.session_state['number_of_jobs'] = 2
                        st.rerun()

                if st.session_state['number_of_jobs'] > 1:
                    with st.expander('Position 2',expanded=True):
                        experience_2 = get_experience(2,edited_keywords_string)
                    if not experience_2['job_title']:
                        add_another_2 = st.button('Add another position', disabled=True)
                        st.caption('Fill out Position 2 before adding another position or generate résumé sections now.')
                    elif experience_2['job_title']:
                        add_another_2 = st.button('Add another position', on_click=clicked, args=['add_another_2'])
                        if add_another_2:
                            st.session_state.clicked['add_another_2'] = True
                            st.session_state['number_of_jobs'] = 3
                            st.rerun()
                            
                if st.session_state['number_of_jobs'] == 3:
                    with st.expander('Position 3',expanded=True):
                        experience_3 = get_experience(3,edited_keywords_string)
                        st.caption('The maximum number of positions is 3.')


                st.write(' ')
                st.write(' ')
                st.write('*(Optional)* Add something unique about you to put in your bio: ')
                unique = st.text_area(f'What makes you unique',label_visibility='collapsed',placeholder=f"I'm unique as a(n) {experience_1['job_title']} because... ", key = 'key_unique_job').strip()
                st.write(' ')
                st.write(' ')

                if 'job_title_1' not in st.session_state:
                    generate_prompt = st.button('Generate résumé sections with ChatGPT', disabled=True)
                else:
                    generate_prompt = st.button('Generate résumé sections with ChatGPT', on_click=clicked, args=['generate_resume'], type='primary')

                    if generate_prompt:
                        st.write(' ')
                        st.write(' ')
                        with st.container(border=True):
                            st.write(' ')
                            st.subheader('Your Result',divider='blue')
                            st.write(' ')

                            with st.spinner('Generating bio...'):
                                bio = get_bio(unique,relevant_keywords_list,experience_1,experience_2,experience_3)
                                bio
                            if experience_1['job_title']:
                                if experience_1['company'] and experience_1['include']:
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.markdown(f'**{experience_1['job_title']}** at {experience_1['short_company_bio']} — {experience_1['years_job']}')
                                    st.write(ask_gpt(experience_1,relevant_keywords_list))
                                elif experience_1['company'] and not experience_1['include']: 
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.markdown(f'**{experience_1['job_title']}** at {experience_1['company']} — {experience_1['years_job']}')
                                    st.write(ask_gpt(experience_1,relevant_keywords_list))
                                else:
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(f'**{experience_1['job_title']}** — {experience_1['years_job']}')
                                    st.write(ask_gpt(experience_1,relevant_keywords_list))


                            if experience_2['job_title']:
                                if experience_2['company'] and experience_2['include']:
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.markdown(f'**{experience_2['job_title']}** at {experience_2['short_company_bio']} — {experience_2['years_job']}')
                                    st.write(ask_gpt(experience_2,relevant_keywords_list))
                                elif experience_2['company'] and not experience_2['include']: 
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.markdown(f'**{experience_2['job_title']}** at {experience_2['company']} — {experience_2['years_job']}')
                                    st.write(ask_gpt(experience_2,relevant_keywords_list))
                                else:
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.markdown(f'**{experience_2['job_title']}** — {experience_2['years_job']}')
                                    st.write(ask_gpt(experience_2,relevant_keywords_list))



                            if experience_3['job_title']:
                                if experience_3['company'] and experience_3['include']:
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.markdown(f'**{experience_3['job_title']}** at {experience_3['short_company_bio']} — {experience_3['years_job']}')
                                    st.write(ask_gpt(experience_3,relevant_keywords_list))

                                elif experience_3['company'] and not experience_3['include']: 
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.markdown(f'**{experience_3['job_title']}** at {experience_3['company']} — {experience_3['years_job']}')
                                    st.write(ask_gpt(experience_3,relevant_keywords_list))
                                else:
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(' ')
                                    st.write(f'**{experience_3['job_title']}**{experience_3['years_job']}')
                                    st.write(ask_gpt(experience_3,relevant_keywords_list))
                                

                            st.divider()
                            st.markdown(f'Relevant keywords: :blue[{relevant_keywords_string}]')
            
                            st.caption('Please note: The highlighted text is provided for your convenience. Not all keywords may be highlighted if the text was changed slightly. It is strongly advised that you refrain from highlighting keywords in your résumé.')

                            st.caption('**Double check the results for accuracy.**')
    st.write(' ')
    st.write(' ')
    st.divider()
    st.write(' ')
    st.caption('Created 2024 by Gretchen Vogt — gretchenvogt.com #OpentoWork')

#this script registers the UDFs in diffirent datasets 

def get_predicate_prompt(attr, op, operand, desp, entity, type, data):
    #filter: [attr] [op] [operand]
    #desp: natual language desp for attr
    #entity: natual language desp for an entity/a tuple in the table
    nl = desp[attr]
    prompt = ''
    if(data == 'paper'):
        if(attr == 'demographics'):
            return 'In the given paper, were ' + operand + ' the type of population being studied or designed for? Return "True" or "False" . '
        if(type =='bool'):
            if(op == '='):
                prompt = 'Is the ' + nl + ' of ' + entity + ' ' + operand + '?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '>'):
                prompt = 'Is the ' + nl + ' of ' + entity + ' larger than ' + operand + '?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '<'):
                prompt = 'Is the ' + nl + ' of ' + entity + ' smaller than ' + operand +  '?' + ' Return "True" or "False" . If answer is not found, return "None".'
        
    if(data == 'civic'):
        if(type =='bool'):
            if(op == '='):
                prompt = 'Is the ' + nl + ' of ' + entity + ' ' + operand + '?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '>'):
                prompt = 'Is the ' + nl + ' of ' + entity + ' later than ' + operand + '?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '<'):
                prompt = 'Is the ' + nl + ' of ' + entity + ' earlier than ' + operand +  '?' + ' Return "True" or "False" . If answer is not found, return "None".'
        elif(type == 'vals'):
            #'Return the names of all projects whose complete design time or completion time is earlier than 2023 January. Put answers in one line seperate by coma. '
            if(op == '='):
                prompt = 'Return the names of all projects whose ' + nl +  ' is ' + operand + '.' + ' Put answers in one line seperate by coma. '
            elif(op == '>'):
                prompt = 'Return the names of all projects whose ' + nl +  ' is later than ' + operand + '.' + ' Put answers in one line seperate by coma. '
            elif(op == '<'):
                prompt = 'Return the names of all projects whose ' + nl +  ' is earlier than ' + operand + '.' + ' Put answers in one line seperate by coma. '
    elif(data == 'notice'):
        if(type =='bool'):
            if(op == '='):
                prompt = 'Is the ' + nl  + ' ' + operand + ' in this violation document?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '>'):
                prompt = 'Is the ' + nl  + ' larger than ' + operand + ' in this violation document?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '<'):
                prompt = 'Is the ' + nl  + ' smaller than ' + operand +  '?' + ' Return "True" or "False" . If answer is not found, return "None".'
        elif(type == 'vals'):
            #'Return the names of all projects whose complete design time or completion time is earlier than 2023 January. Put answers in one line seperate by coma. '
            if(op == '='):
                prompt = 'Return the name of company in this violation document if ' + nl +  ' is ' + operand + '.' 
            elif(op == '>'):
                prompt = 'Return the name of company in this violation document if ' + nl +  ' is larger than ' + operand + '.' 
            elif(op == '<'):
                prompt = 'Return the name of company in this violation document if ' + nl +  ' is smaller than ' + operand + '.' 
        if(attr == 'type'):
            prompt = 'Is the type of violation items related with ' + operand + '? ' + ' Return "True" or "False" . If answer is not found, return "None".'
        if(attr == 'compliance_order'):
            prompt = 'Does the compliance order proposed in this document? ' + ' Return "True" or "False" . If answer is not found, return "None".'

    
    return prompt

def get_combined_prompt(sql, desp, data):
    filters = sql['filters']
    prompt_paper = 'Given the following paper, if this paper satisfys ALL the following conditions, return "True". If any condition is not satisfied, return "False". '
    i = 1
    if(data == 'paper'):
        for left, right in filters.items():
            attr = left
            op = right[0]
            operand = right[1]
            nl = desp[attr]
            prompt_paper += 'Condition ' + str(i) + ': the ' + nl + ' of paper '
            if(op == '='):
                prompt_paper += ' is ' + operand + '. ' 
            elif(op == '>'):
                prompt_paper += ' is larger than ' + operand + '. ' 
            elif(op == '<'):
                prompt_paper += ' is smaller than ' + operand + '. ' 
            i += 1

        return prompt_paper
    
    prompt_civic = 'Return the names of projects if they satisfy all the following conditions. Put answers in one line seperate by coma. If there are no projects satisfying all the conditions, return "None". '
    if(data == 'civic'):
        for left, right in filters.items():
            attr = left
            op = right[0]
            operand = right[1]
            nl = desp[attr]
            prompt_civic += 'Condition ' + str(i) + ': the ' + nl 
            if(op == '='):
                prompt_civic += ' is ' + operand + ' . ' 
            elif(op == '>'):
                prompt_civic += ' is later than ' + operand + ' . '
            elif(op == '<'):
                prompt_civic += ' is earlier than ' + operand + ' . '
            i += 1

        return prompt_civic
    
    if(data == 'NoticeViolation'):
        prompt = 'If all the following conditions are satisfied based on the violation document, return "True", otherwise, return "False". If there are no projects satisfying all the conditions, return "None". '
        for left, right in filters.items():
            attr = left
            op = right[0]
            operand = right[1]
            nl = desp[attr]
            if(attr == 'type'):
                prompt += 'Condition ' + str(i) + ': the type of violation items is related with ' + operand + '. '
            elif(attr == 'compliance_order'):
                prompt += 'Condition ' + str(i) + ': the compliance order is proposed in this document. '
            else:
                prompt += 'Condition ' + str(i) + ': the ' + nl 
                
                if(op == '='):
                    prompt += ' is ' + operand + '. ' 
                elif(op == '>'):
                    prompt += ' is larger than ' + operand + '. ' 
                elif(op == '<'):
                    prompt += ' is smaller than ' + operand + '. ' 
            i += 1
        return prompt 


def paper_udfs():
    udfs = {}
    tag_map = {}#map udf to a tag
    keywords = {}
    question_tag = ['venue','source','domain','health_wellness','li','motivation','lived_informatics','privacy&ethics','privacy_ethics_depth','contribution','study','artifact_kind','recruitment','participant_count','study_duration','involved','demographics','expert','expert_description','theory','theory_depth']

    udfs['publication_date'] = 'What is the publication year of this paper? Only return a single number. If cannot find, return "None" .'
    udfs['contribution_type_empirical'] = 'Is the contribution type of this paper empirical? Return "True" or "False" .  '
    udfs['domain_health_behavior'] = 'Is the health behavior a proper domain of this paper? Return "True" or "False" . '
    udfs['study_interview'] = 'Is interview a type of study conducted in this paper? Return "True" or "False" . '
    udfs['venue_CHI'] = 'Is the venue of this paper CHI? Return "True" or "False" . '
    udfs['artifact_website'] = 'Is website the kind of artifact created in this paper? Return "True" or "False" . '
    udfs['theory_schon'] = 'Does the approach proposed in this paper use schon theory? Return "True" or "False" . '
    udfs['demographics_students'] = 'In the given paper, were students the type of population being studied or designed for? Return "True" or "False" . '
    udfs['health_wellness'] = 'Does the domain of this paper relate with health or wellness? Return "True" or "False" . '
    udfs['privacy&ethics'] = 'Does this paper consider privacy and ethics in personal data management? Return "True" or "False" . '
    
    keywords['publication_date'] = 'publication date'
    keywords['contribution_type_empirical'] = 'empirical'
    keywords['domain_health_behavior'] = 'health behavior'
    keywords['study_interview'] = 'interview'
    keywords['artifact_website'] = 'website'
    keywords['venue_CHI'] = 'CHI'

    tag_map['publication_date'] = ('year','2015')
    tag_map['study_interview'] = ('study','interview')
    tag_map['venue_CHI'] = ('venue','CHI')
    tag_map['artifact_website'] = ('artifact_kind','website')
    tag_map['contribution_type_empirical'] = ('contribution','empirical')
    tag_map['domain_health_behavior'] = ('domain','health_behavior')
    

    
    tag_map['theory_schon'] = ('theory','schon')
    tag_map['health_wellness'] = ('health_wellness', 'yes')
    tag_map['demographics_students'] = ('demographics','students')
    tag_map['privacy&ethics'] = ('privacy&ethics','yes')

    keywords['theory_schon'] = 'schon'
    keywords['health_wellness'] = 'wellness'
    keywords['demographics_students'] = 'student'
    keywords['privacy&ethics'] = 'privacy'
    #udf set 3: combined udf 

    udfs['combined'] = 'Given the following paper, answer me the following questions. 1. What is the publication year of this paper? Only return a single number. 2. Is the contribution type of this paper empirical? Return true or false. 3. Is the health behavior a proper domain of this paper? Return true or false. 4.Is interview a type of study conducted in this paper? Return true or false. 5. Is the venue of this paper CHI? Return true or false. 6. Is website the kind of artifact created in this paper? Return true or false. 7. Does the approach proposed in this paper use schon theory? Return true or false. 8. Does the domain of this paper relate with health or wellness? Return true or false. 9. In the given paper, were students the type of population being studied or designed for? Return true or false. 10. Does this paper consider privacy and ethics in personal data management? Return true or false. Seperate the answers using comma. Example: 2017, False, False, True, True, False, False, True, True, False '

    cols = ['publication_date','contribution_type_empirical','domain_health_behavior','study_interview','venue_CHI','artifact_website','theory_schon','health_wellness','demographics_students','privacy&ethics']

    return udfs, tag_map, cols, keywords

def paper_attr_desp():
    desp = {}
    desp['year'] = 'publication year'
    desp['contribution'] = 'type of contribution'
    desp['domain'] = 'domain'
    desp['study'] = 'type of study'
    desp['venue'] = 'venue'
    desp['artifact'] = 'artifact'
    desp['theory'] = 'theory'
    desp['demographics'] = 'type of population being studied or designed'
    desp['author_number'] = 'number of authors'
    return desp 

def paper_SQLs():
    # desp['publication_year'] = 'publication year'
    # desp['contribution'] = 'type of contribution'
    # desp['domain'] = 'domain'
    # desp['study'] = 'type of study'
    # desp['venue'] = 'venue'
    # desp['artifact'] = 'artifact'
    # desp['theory'] = 'theory'
    # desp['demographics'] = 'the type of population being studied or designed for'
    sqls = []

    #one predicate sql 
    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['year'] = ('>', '2017')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['venue'] = ('=', 'CHI')
    sql['filters'] = filters

    sqls.append(sql)

    # sql = {}
    # sql['project'] = ['paper_name']
    # filters = {}
    # filters['domain'] = ('=', 'health_behavior')
    # sql['filters'] = filters

    # sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['author_number'] = ('>', '3')
    sql['filters'] = filters

    sqls.append(sql)

    #two predicates sql
    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['year'] = ('<', '2018')
    filters['author_number'] = ('<', '5')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['year'] = ('<', '2017')
    filters['venue'] = ('=', 'CHI')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['year'] = ('<', '2018')
    filters['study'] = ('=', 'surveys or interviews')
    sql['filters'] = filters

    sqls.append(sql)

    #three predicates sql
    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['author_number'] = ('<', '5')
    filters['venue'] = ('=', 'CHI')
    filters['year'] = ('>', '2012')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['study'] = ('=', 'surveys')
    filters['venue'] = ('=', 'CHI or Ubicomp')
    filters['year'] = ('>', '2012')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['venue'] = ('=', 'CHI or Ubicomp')
    filters['year'] = ('>', '2013')
    filters['author_number'] = ('>', '3')
    sql['filters'] = filters

    sqls.append(sql)

    return sqls

def civic_udfs():
    udfs = {}

    udfs['project_name'] = 'Return the name of this project?'
    udfs['st'] = 'Return the begin construction time of this project in the format of year-month or year-season. Example: 2021-04 or 2021-winter. If cannot find, return none.'
    udfs['et'] = 'Return the complete design time or completion of this project in the format of year-month or year-season. Example: 2021-04 or 2021-winter. If cannot find, return none.'
    udfs['ad'] = 'Return the advertise time of this project in the format of year-month or year-season. Example: 2021-04 or 2021-winter. If cannot find, return none.'
    udfs['topic'] = 'Return several words to describe the related topics of this project. Example: health, road, water, park, vehicle, storm. '
    udfs['type'] = 'Return the type of this project, either capital or disaster.'
    udfs['status'] = "Return the status of this project in the following choices:  design, construction, not started, completed"

    return udfs

def civic_attr_desp():
    desp = {}
    desp['project_name'] = 'the name of project'
    desp['st'] = 'begin construction time'
    desp['et'] = 'complete design time or completion'
    desp['ad'] = 'advertise time'
    desp['topic'] = 'topic'
    desp['type'] = 'type'
    desp['status'] = 'status'

    return desp

def civic_SQLs():
    sqls = []
    #1 predicate SQL 

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['type'] = ('=', 'capital')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['status'] = ('=', 'not started')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('<', '2022-03')
    sql['filters'] = filters

    sqls.append(sql)

    #2 predicate SQL 

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('<', '2022-01')
    filters['type'] = ('=', 'capital')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('>', '2021-03')
    filters['status'] = ('=', 'not started')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('<', '2023-01')
    filters['type'] = ('=', 'disaster')
    sql['filters'] = filters

    sqls.append(sql)

    #3 predicate SQL
    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('<', '2022-06')
    filters['type'] = ('=', 'capital')
    filters['status'] = ('=', 'not started')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('>', '2021-07')
    filters['type'] = ('=', 'disaster')
    filters['status'] = ('=', 'design')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('>', '2021-05')
    filters['type'] = ('=', 'capital')
    filters['topic'] = ('=', 'road')
    sql['filters'] = filters
    sqls.append(sql)

    # sql4 = {}
    # sql4['project'] = ['project_name']
    # filters = {}
    # filters['ad'] = ('>', '2021-01')
    # filters['type'] = ('=', 'capital')
    # filters['status'] = ('=', 'design')
    # sql4['filters'] = filters
    # sqls.append(sql4)

    # sql5 = {}
    # sql5['project'] = ['project_name']
    # filters = {}
    # filters['et'] = ('<', '2023-01')
    # filters['topic'] = ('=', 'road')
    # filters['status'] = ('=', 'design')
    # sql5['filters'] = filters
    # sqls.append(sql5)

    return sqls

def notice_attr_desp():
    desp = {}
    desp['company'] = 'name of company'
    desp['region'] = 'region of company'
    desp['state'] = 'state of company'
    desp['date'] = 'date of notice'
    desp['penalty'] = 'proposed civil penalty'
    desp['type'] = 'type of violaton item'
    desp['item_num'] = 'number of violation items'
    desp['compliance_order'] = 'compliance order'
    return desp

def notice_SQLs():
    sqls = []
    #1 predicate SQL 

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['region'] = ('=', 'western or central')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['penalty'] = ('>', '0')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['item_num'] = ('>', '3')
    sql['filters'] = filters
    sqls.append(sql)

    #2 predicate SQL 

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['region'] = ('=', 'western or central')
    filters['date'] = ('<', '01/01/2024')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['penalty'] = ('>', '10000')
    filters['item_num'] = ('>', '1')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['type'] = ('=', 'Corrosion Control')
    filters['penalty'] = ('<', '10000')
    sql['filters'] = filters
    sqls.append(sql)

    #3 predicate SQL 

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['region'] = ('=', 'western or central')
    filters['date'] = ('<', '06/01/2024')
    filters['penalty'] = ('>', '10000')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['penalty'] = ('>', '5000')
    filters['item_num'] = ('>', '1')
    filters['type'] = ('=', 'Control Room Management or Corrosion Control')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['penalty'] = ('>', '2000')
    filters['item_num'] = ('>', '2')
    filters['type'] = ('=', 'Corrosion Control')
    sql['filters'] = filters
    sqls.append(sql)

    return sqls 

def civic_SQLs_prompt():
    sqls = []

    # sql1 = {}
    # sql1['project'] = ['project_name']
    # filters = {}
    # filters['st'] = ('<', '2022-06')
    # filters['type'] = ('=', 'capital')
    # filters['status'] = ('=', 'not started')
    # sql1['filters'] = filters

    sql1 = {}
    sql1['project'] = ['project_name']
    filters = {}
    filters['st'] = 'Return the names of all projects whose begin construction or begin design time is earlier than 2022 June. Put answers in one line seperate by coma. '
    filters['type'] = 'Return the names of all projects whose type is capital. Put answers in one line seperate by coma. '
    filters['status'] = 'Return the names of all projects whose status is not started. Put answers in one line seperate by coma.'
    bool_filters = {}
    bool_filters['st'] = 'Is the begin construction or begin design time of this project earlier than 2022 June? return yes or no.'
    sql1['filters'] = filters
    sql1['bool_filters'] = bool_filters
    sqls.append(sql1)
    # sql2 = {}
    # sql2['project'] = ['project_name']
    # filters = {}
    # filters['et'] = ('>', '2021-07')
    # filters['type'] = ('=', 'disaster')
    # filters['status'] = ('=', 'design')
    # sql2['filters'] = filters
    # sqls.append(sql2)

    sql2 = {}
    sql2['project'] = ['project_name']
    filters = {}
    filters['et'] = 'Return the names of all projects whose complete design time or completion time is later than 2021 July. Put answers in one line seperate by coma. '
    filters['type'] = 'Return the names of all projects whose type is disaster. Put answers in one line seperate by coma. '
    filters['status'] = 'Return the names of all projects whose status is design. Put answers in one line seperate by coma.'
    bool_filters = {}
    bool_filters['et'] = 'Is the complete design time or completion time of this project later than 2021 July? return yes or no.'
    sql2['filters'] = filters
    sql2['bool_filters'] = bool_filters

    sqls.append(sql2)

    # sql3 = {}
    # sql3['project'] = ['project_name']
    # filters = {}
    # filters['st'] = ('>', '2021-05')
    # filters['type'] = ('=', 'capital')
    # filters['topic'] = ('=', 'road')
    # sql3['filters'] = filters
    # sqls.append(sql3)

    sql3 = {}
    sql3['project'] = ['project_name']
    filters = {}
    filters['st'] = 'Return the names of all projects whose begin construction or begin design time is later than 2021 May. Put answers in one line seperate by coma. '
    filters['type'] = 'Return the names of all projects whose type is capital. Put answers in one line seperate by coma. '
    filters['topic'] = 'Return the names of all projects whose topic is related with road improvement. Put answers in one line seperate by coma.'
    bool_filters = {}
    bool_filters['st'] = 'Is the begin construction or begin design time of this project later than 2021 May? return yes or no.'
    bool_filters['topic'] = 'Is the project about road improvement? return yes or no.'
    sql3['filters'] = filters
    sql3['bool_filters'] = bool_filters

    sqls.append(sql3)

    # sql4 = {}
    # sql4['project'] = ['project_name']
    # filters = {}
    # filters['ad'] = ('>', '2021-01')
    # filters['type'] = ('=', 'capital')
    # filters['status'] = ('=', 'design')
    # sql4['filters'] = filters
    # sqls.append(sql4)

    sql4 = {}
    sql4['project'] = ['project_name']
    filters = {}
    filters['ad'] = 'Return the names of all projects whose advertise time is later than 2021 January. Put answers in one line seperate by coma. '
    filters['type'] = 'Return the names of all projects whose type is capital. Put answers in one line seperate by coma. '
    filters['status'] = 'Return the names of all projects whose status is design. Put answers in one line seperate by coma.'
    bool_filters = {}
    bool_filters['st'] = 'Is the advertise time of this project later than 2021 January? return yes or no.'
    sql4['filters'] = filters
    sql4['bool_filters'] = bool_filters

    sqls.append(sql4)

    # sql5 = {}
    # sql5['project'] = ['project_name']
    # filters = {}
    # filters['et'] = ('<', '2023-01')
    # filters['topic'] = ('=', 'road repair')
    # filters['status'] = ('=', 'design')
    # sql5['filters'] = filters
    # sqls.append(sql5)

    sql5 = {}
    sql5['project'] = ['project_name']
    filters = {}
    filters['et'] = 'Return the names of all projects whose complete design time or completion time is earlier than 2023 January. Put answers in one line seperate by coma. '
    filters['topic'] = 'Return the names of all projects whose topic is related with road repair. Put answers in one line seperate by coma.'
    filters['status'] = 'Return the names of all projects whose status is design. Put answers in one line seperate by coma.'
    bool_filters = {}
    bool_filters['et'] = 'Is the complete design time or completion time of this project earlier than 2023 January? return yes or no.'
    bool_filters['topic'] = 'Is the project about road repair? return yes or no.'
    sql5['filters'] = filters
    sql5['bool_filters'] = bool_filters

    sqls.append(sql5)
    return sqls


if __name__ == "__main__":
    #test predicate prompt 
    sqls = paper_SQLs()
    desp = paper_attr_desp()
    i = 1
    for sql in sqls:
        
        print(i)
        for left, right in sql['filters'].items():
            print(left, right)
            print(get_predicate_prompt(left, right[0], right[1], desp, 'paper', 'bool', 'paper'))
        # prompt = get_combined_prompt(sql, desp, 'notice')
        # print(prompt)
        i+=1
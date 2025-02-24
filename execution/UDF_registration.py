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
                prompt = 'Is the ' + nl + ' of ' + entity + ' ' + operand + ' based on the provided document?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '>'):
                prompt = 'Is the ' + nl + ' of ' + entity + ' larger than ' + operand + ' based on the provided document?' + ' Return "True" or "False" . If answer is not found, return "None".'
            elif(op == '<'):
                prompt = 'Is the ' + nl + ' of ' + entity + ' smaller than ' + operand +  ' based on the provided document?' + ' Return "True" or "False" . If answer is not found, return "None".'
        
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
    elif(data == 'NoticeViolation'):
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

def paper_SQLs_small():
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

def civic_SQLs_small():
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

def notice_SQLs_small():
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

def paper_SQLs():
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

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['author_number'] = ('>', '3')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['contribution'] = ('=', 'empirical')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['demographics'] = ('=', 'patients')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['paper_name']
    filters = {}
    filters['venue'] = ('=', 'CHI')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'avg'
    sql['project'] = ['author_number']
    filters = {}
    filters['venue'] = ('=', 'CHI')
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

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['author_number'] = ('<', '5')
    filters['study'] = ('=', 'surveys or interviews')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['author_number'] = ('>', '3')
    filters['venue'] = ('=', 'CHI')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'avg'
    sql['project'] = ['author_number']
    filters = {}
    filters['year'] = ('<', '2018')
    filters['study'] = ('=', 'surveys or interviews')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['paper_name']
    filters = {}
    filters['author_number'] = ('<', '5')
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

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['study'] = ('=', 'surveys')
    filters['author_number'] = ('<', '4')
    filters['year'] = ('>', '2013')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['paper_name']
    filters = {}
    filters['author_number'] = ('<', '5')
    filters['venue'] = ('=', 'CHI')
    filters['year'] = ('<', '2017')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['paper_name']
    filters = {}
    filters['venue'] = ('=', 'CHI or Ubicomp')
    filters['year'] = ('>', '2013')
    filters['author_number'] = ('>', '3')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'max'
    sql['project'] = ['author_number']
    filters = {}
    filters['study'] = ('=', 'surveys')
    filters['venue'] = ('=', 'CHI or Ubicomp')
    filters['year'] = ('>', '2013')
    sql['filters'] = filters

    sqls.append(sql)

    return sqls


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

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('>', '2022-01')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['status'] = ('=', 'not started')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'max'
    sql['project'] = ['st']
    filters = {}
    filters['status'] = ('=', 'not started')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('>', '2022-01')
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

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('>', '2021-09')
    filters['type'] = ('=', 'capital')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('<', '2022-06')
    filters['status'] = ('=', 'design')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('>', '2021-03')
    filters['status'] = ('=', 'not started')
    sql['filters'] = filters

    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('>', '2021-09')
    filters['type'] = ('=', 'capital')
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

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['ad'] = ('>', '2021-01')
    filters['type'] = ('=', 'capital')
    filters['status'] = ('=', 'design')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['project_name']
    filters = {}
    filters['et'] = ('<', '2023-01')
    filters['topic'] = ('=', 'road')
    filters['status'] = ('=', 'design')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('>', '2021-05')
    filters['type'] = ('=', 'capital')
    filters['topic'] = ('=', 'road')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['project_name']
    filters = {}
    filters['st'] = ('<', '2022-06')
    filters['type'] = ('=', 'capital')
    filters['status'] = ('=', 'not started')
    sql['filters'] = filters

    sqls.append(sql)

    return sqls

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

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['compliance_order'] = ('=', 'true')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['date'] = ('<', '03/01/2024')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['company']
    filters = {}
    filters['compliance_order'] = ('=', 'true')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['company']
    filters = {}
    filters['date'] = ('<', '03/01/2024')
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

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['compliance_order'] = ('=', 'false')
    filters['penalty'] = ('<', '20000')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['state'] = ('=', 'California')
    filters['type'] = ('=', 'Corrosion Control')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['company']
    filters = {}
    filters['penalty'] = ('>', '10000')
    filters['item_num'] = ('>', '1')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'max'
    sql['project'] = ['penalty']
    filters = {}
    filters['state'] = ('=', 'California')
    filters['type'] = ('=', 'Corrosion Control')
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

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['state'] = ('=', 'California')
    filters['type'] = ('=', 'Corrosion Control')
    filters['item_num'] = ('>', '1')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['project'] = ['company']
    filters = {}
    filters['region'] = ('=', 'western or central')
    filters['penalty'] = ('>', '5000')
    filters['item_num'] = ('>', '1')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'count'
    sql['project'] = ['company']
    filters = {}
    filters['region'] = ('=', 'western or central')
    filters['date'] = ('<', '06/01/2024')
    filters['penalty'] = ('>', '10000')
    sql['filters'] = filters
    sqls.append(sql)

    sql = {}
    sql['agg'] = 'average'
    sql['project'] = ['penalty']
    filters = {}
    filters['state'] = ('=', 'California')
    filters['type'] = ('=', 'Corrosion Control')
    filters['item_num'] = ('>', '1')
    sql['filters'] = filters
    sqls.append(sql)

    return sqls 
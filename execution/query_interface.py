#this function parses a SQL query 
import json 
import UDF_registration
import random

def parse_SQL(level, query):
    selected_attrs = []
    from_tables = []
    predicates = []
    groupby = []
    orderby = {} #{attr, order}

    #parse selection 
    # Finding the substring between 'select' and 'from'
    select_start = query.lower().find('select') + len('select')
    from_end = query.lower().find('from')

    selections = query[select_start:from_end].strip()
    attrs = selections.split(',')
    for attr in attrs:
        selected_attrs.append(attr.strip())
    
    #parse from
    from_start = query.lower().find('from') + len('from')
    where_end = query.lower().find('where')

    tables = query[from_start:where_end].strip()
    if(',' in tables):
        tables = tables.split(',')
        for table in tables:
            from_tables.append(table.strip())
    else:
        from_tables.append(tables.strip())
    #print(from_tables)
        
    #parse predicates 
    if('where' in query.lower()):
        predicates_block = ''
        if('group by' in query.lower()):
            where_start = query.lower().find('where') + len('where')
            group_end = query.lower().find('group by')
            predicates_block = query[where_start:group_end].strip()
        else:
            where_start = query.lower().find('where') + len('where')
            predicates_block = query[where_start:].strip()
        #print(predicates_block)
        preds = []
        if('and' in query):
            preds = predicates_block.split('and')
        elif('AND' in query):
            preds = predicates_block.split('AND')
        elif('And' in query):
            preds = predicates_block.split('And')
        else:
            predicates.append(predicates_block.strip())
        if(len(predicates) == 0):
            for pred in preds:
                predicates.append(pred.strip())

    #print(predicates)
            
    #parse group by 
    
    if('group by' in query.lower()):
        groupby_block = ''
        if('order by' in query.lower()):
            group_start = query.lower().find('group by') + len('group by')
            order_end = query.lower().find('order by')
            groupby_block = query[group_start:order_end].strip()
        else:
            group_start = query.lower().find('group by') + len('group by')
            groupby_block = query[group_start:].strip()
        if(',' in groupby_block):
            groups = groupby_block.split(',')
            for group in groups:
                groupby.append(group.strip())
        else:
            groupby.append(groupby_block.strip())
        #print(groupby)
        
    #parse order 
        if('order by' in query.lower()):
            order_start = query.lower().find('order by') + len('order by')
            orderby_block = query[order_start:].strip()
            if(',' in orderby_block):
                orders = orderby_block.split(',')
                for order in orders:
                    order = order.strip()
                    str = order.split(' ')
                    attr = str[0]
                    ordermark = str[1]
                    orderby[attr] = ordermark
            else:
                order = orderby_block.strip()
                str = order.split(' ')
                attr = str[0]
                ordermark = str[1]
                orderby[attr] = ordermark
            #print(orderby)

    return selected_attrs, from_tables, predicates, groupby, orderby

def parse_predicates(predicates):
    #one predicate is: udf op oprand 
    ops = ['>','>=','<','<=','=','approx','!=','in']
    new_preds = []
    for pred in predicates: 
        for op in ops:
            if(op in pred):
                parts = pred.split(op)
                udf = parts[0].strip()
                operand = parts[1].strip()
                new_pred = (udf, op, operand)
                new_preds.append(new_pred)
                break
    return new_preds

def write_2_json(tree, dict_path):
    with open(dict_path, 'w') as file:
        json.dump(tree, file)

def read_json(dict_path):
    with open(dict_path, 'r') as file:
        loaded_dict = json.load(file)
    return loaded_dict

def UDF_registrate(udf_name, instruction, udf_path):
    #read json from local files 
    #add udf and write it back 
    udfs = read_json(udf_path)
    udfs[udf_name] = instruction
    write_2_json(udfs, udf_path)

def load_udfs(udf_path):
    return read_json(udf_path)

def generate_single_SQL(pred_num, udfs):
    size = len(udfs)
    SQL = []
    mp = {}
    for i in range(pred_num):
        udf_id = random.randint(0, size-1)
        if(udf_id not in mp):
            udf = udfs[udf_id]
            SQL.append(udf)
        else:#avoid duplicate predicates
            udf_id = random.randint(0, size-1)
            while(udf_id not in mp):
                udf = udfs[udf_id]
                SQL.append(udf)
                break
    return SQL


    
import pandas as pd

def read_csv(path):
    # Read the CSV file
        df = pd.read_csv(path) 
        return df

def merge_df():
    path1 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/answer_GPT4_single_udf1.csv'
    path2 = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/answer_GPT4_single_udf2.csv'
    result1 = read_csv(path1)
    result2 = read_csv(path2)

    selected_df = result2.iloc[:, -4:]

    result = result1.join(selected_df)

    result.iloc[:, 1:].to_csv('/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/answer_GPT4_single.csv')

def process_combined_df():
    path = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/answer_GPT4_combined_udf3.csv'
    folder = '/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/data/sys review/extracted_data/'
    results = read_csv(path)
    cols = ['publication_date', 'contribution_type_empirical', 'domain_health_behavior', 'study_interview', 'venue_CHI', 'artifact_website', 'theory_schon', 'health_wellness', 'demographics_students', 'privacy&ethics']

    mp = {}
    titles = []
    for i in range(len(results)):
            title = results['title'][i]
            titles.append(title)
    mp['title'] = titles

    for j in range(len(cols)):#scan each udf 
        col = cols[j]
        #print(col)
        accuracy = 0
        #scan each paper

        vals = []
        for i in range(len(results)):
            title = results['title'][i]
            title = title.replace(folder, '', 1)
            title = title.replace('.txt', '')

            #print(results['publication_date'][i])
            udf_value = str(results['combined'][i]).strip()
            udf_values = udf_value.split(',')

            udf_value = udf_values[j].strip()
            vals.append(udf_value)
        mp[col] = vals
    new_cols = ['title','publication_date', 'contribution_type_empirical', 'domain_health_behavior', 'study_interview', 'venue_CHI', 'artifact_website', 'theory_schon', 'health_wellness', 'demographics_students', 'privacy&ethics']
    df = pd.DataFrame(mp, columns=new_cols)
    df.to_csv('/Users/yiminglin/Documents/Codebase/TextDB/Text-DB/runtime/paper/answer_GPT4_combined.csv')

process_combined_df()
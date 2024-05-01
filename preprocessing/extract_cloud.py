from documentcloud import DocumentCloud

def write_file(name):
    path = '/Users/yiminglin/Documents/research/Text management system/data/docucloud/agenda-watch-11341/' + name + '.pdf'
    with open(path,'wb') as f:
        f.write(obj.pdf)
    f.close()


#+user:serdar-tumgoren-20993 +access:public
client = DocumentCloud('yiminglin@berkeley.edu','5980268Lym@')
obj_list = client.documents.search("+organization:agenda-watch-11341 ")

print(obj_list.count)
metadata = []

#write metadata 
with open('/Users/yiminglin/Documents/research/Text management system/data/docucloud/agenda-watch-11341_meta/meta.txt', "w") as fm:
    fm.write('id,title\n')

    for i in range(obj_list.count):
        obj = obj_list[i]
        print(i)
        metai = []
        metai.append(obj.id)
        #print(obj.id)
        metai.append(obj.title)
        #print(obj.title)
        # metai.append(obj.contributor_organization)
        # print(obj.contributor_organization)
        #metai.append(obj.canonical_url)
        name = obj.id + '_' + obj.title
        print(name)
        list_as_string = ','.join(map(str, metai))
        fm.write(list_as_string)
        fm.write('\n')
        write_file(name)

    fm.close()
    
#second run from 497


#https://www.documentcloud.org/documents/24117240-city-council-meeting


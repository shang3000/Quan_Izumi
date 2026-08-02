import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_ch3 = """{id:46,chapter:3,type:'single',question:'中国特色社会主义最本质的特征是（    ）。',options:['人民当家作主','中国共产党领导','依法治国','社会主义制度'],answer:[1],explanation:'中国特色社会主义最本质的特征是中国共产党领导。P56'},
{id:47,chapter:3,type:'single',question:'党的领导的最高原则是（    ）。',options:['坚持民主集中制','坚持党的全面领导','党中央集中统一领导','维护党中央权威'],answer:[2],explanation:'党中央集中统一领导是党的领导的最高原则。P66'},
{id:48,chapter:3,type:'single',question:'党的领导制度是我国的（    ）领导制度。',options:['基本','重要','根本','核心'],answer:[2],explanation:'党的领导制度是我国的根本领导制度。P69'},
{id:49,chapter:3,type:'single',question:'中国特色社会主义制度体系中具有统领地位的是（    ）。',options:['根本制度','基本制度','重要制度','党的领导制度'],answer:[3],explanation:'其中具有统领地位的是党的领导制度。P69'},
{id:50,chapter:3,type:'single',question:'（    ）是党的领导决策核心。',options:['全国人大、国务院、全国政协','中央委员会、中央政治局、中央政治局常委会','中央书记处、中央纪委、中央军委','省委、市委、县委'],answer:[1],explanation:'中央委员会，中央政治局，中央政治局常委会，是党的领导决策核心。P71'},
{id:51,chapter:3,type:'multiple',question:'中国共产党领导地位是在（    ）中形成的。',options:['历史奋斗','人民选择','制度设计','理论创新'],answer:[0,1],explanation:'中国共产党的领导地位是在历史奋斗中形成的。P57'},
{id:52,chapter:3,type:'multiple',question:'中国共产党作为最高政治领导力量（    ）。',options:['不是自封的，而是在历史发展中形成的','是由我国国家性质和政治制度体系决定的','是由中华民族伟大复兴事业决定的','是自封的'],answer:[0,1,2],explanation:'P63-64'},
{id:53,chapter:3,type:'multiple',question:'党的领导是（    ）的。',options:['全面的','系统的','整体的','局部的'],answer:[0,1,2],explanation:'党的领导是全面的、系统的、整体的。P65-66'},
{id:54,chapter:3,type:'multiple',question:'维护党中央权威和集中统一领导，必须（    ）。',options:['坚决贯彻党的理论、路线、方针政策和党中央的决策部署','坚决维护习近平同志党中央的核心、全党的核心地位','同坚持党的民主集中制完全一致','放弃党的民主集中制'],answer:[0,1,2],explanation:'P67-68'},
{id:55,chapter:3,type:'multiple',question:'坚持和加强党的全面领导，使（    ）。',options:['党的领导核心作用充分彰显','党的政治领导力、思想引领力、群众组织力、社会号召力显著增强','党成为风雨来袭时中国人民最可靠的主心骨','党的领导制度体系更加健全'],answer:[0,1,2,3],explanation:'P60-62'},
{id:56,chapter:3,type:'fill',question:'坚持党的全面领导是坚持和发展中国特色社会主义的______。',answer:'必由之路',explanation:'P56'},
{id:57,chapter:3,type:'fill',question:'中国最大的国情就是______的领导。',answer:'中国共产党',explanation:'P57'},
{id:58,chapter:3,type:'fill',question:'中国特色社会主义之所以是社会主义，究其根本就在于坚持科学社会主义基本原则，在于坚持______的领导。',answer:'中国共产党',explanation:'P58'},
{id:59,chapter:3,type:'fill',question:'中国共产党自身优势是中国特色社会主义______的主要来源。',answer:'制度优势',explanation:'P59'},
{id:60,chapter:3,type:'fill',question:'______，要在中央。党中央集中统一领导是党的领导的最高原则。',answer:'事在四方',explanation:'P66-67'}"""

lines = content.split('\n')
insert_line = None
for i, line in enumerate(lines):
    if '{id:45,' in line and 'chapter:2' in line:
        insert_line = i + 1
        break

if insert_line:
    new_lines = lines[:insert_line] + [new_ch3] + lines[insert_line:]
    with open('习思想期末复习/刷题题库.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print('OK')
else:
    print('ERROR')

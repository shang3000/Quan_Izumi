import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_ch1 = """{id:16,chapter:1,type:'single',question:'道路问题是关系党的事业兴衰成败（    ）的问题。',options:['最重要','第一位','最根本','最关键'],answer:[1],explanation:'道路问题是关系党的事业兴衰成败第一位的问题。P15'},
{id:17,chapter:1,type:'single',question:'中国特色社会主义是科学社会主义理论逻辑和中国社会发展历史逻辑的（    ）。',options:['有机统一','辩证统一','历史统一','逻辑统一'],answer:[1],explanation:'中国特色社会主义是科学社会主义理论逻辑和中国社会发展历史逻辑的辩证统一。P18'},
{id:18,chapter:1,type:'single',question:'我们说要坚定道路自信、理论自信、制度自信，说到底是要坚定（    ）。',options:['道路自信','理论自信','制度自信','文化自信'],answer:[3],explanation:'说到底是要坚定文化自信。P22'},
{id:19,chapter:1,type:'single',question:'党的十八大以来，我国社会主要矛盾已经转化为（    ）。',options:['人民日益增长的物质文化需要同落后的社会生产之间的矛盾','人民日益增长的美好生活需要和不平衡不充分的发展之间的矛盾','人民日益增长的经济文化需要同落后的社会生产之间的矛盾','人民日益增长的美好生活需要同落后的社会生产之间的矛盾'],answer:[1],explanation:'P25'},
{id:20,chapter:1,type:'single',question:'全面建设社会主义现代化国家是（    ），在"四个全面"中居于引领地位。',options:['战术目标','基本方略','战略目标','根本保证'],answer:[2],explanation:'全面建设社会主义现代化国家是战略目标，在"四个全面"中居于引领地位。P31'},
{id:21,chapter:1,type:'multiple',question:'改革开放以来我们取得一切成绩和进步的根本原因，归结起来就是（    ）。',options:['开辟了中国特色社会主义道路','形成了中国特色社会主义理论体系','确立了中国特色社会主义制度','发展了中国特色社会主义文化'],answer:[0,1,2,3],explanation:'P20'},
{id:22,chapter:1,type:'multiple',question:'中国特色社会主义进入新时代的三个"意味着"包括（    ）。',options:['意味着中华民族迎来了从站起来、富起来到强起来的伟大飞跃','意味着科学社会主义在21世纪的中国焕发出强大生机活力','意味着中国特色社会主义道路、理论、制度、文化不断发展','意味着我国社会主要矛盾发生了变化'],answer:[0,1,2],explanation:'P23'},
{id:23,chapter:1,type:'multiple',question:'道路、理论体系、制度、文化四者的关系是（    ）。',options:['道路是实现途径','理论体系是行动指南','制度是根本保障','文化是精神力量'],answer:[0,1,2,3],explanation:'P20'},
{id:24,chapter:1,type:'multiple',question:'新时代坚持和发展中国特色社会主义要一以贯之，必须（    ）。',options:['全面贯彻党的基本理论','全面贯彻党的基本路线','全面贯彻党的基本方略','统筹推进"五位一体"总体布局'],answer:[0,1,2,3],explanation:'P29-32'},
{id:25,chapter:1,type:'multiple',question:'新时代伟大变革在（    ）上具有里程碑意义。',options:['党史','新中国史','改革开放史','社会主义发展史','中华民族发展史'],answer:[0,1,2,3,4],explanation:'P28'},
{id:26,chapter:1,type:'fill',question:'中国特色社会主义是______和人民的选择。',answer:'历史',explanation:'P15'},
{id:27,chapter:1,type:'fill',question:'中国特色社会主义进入新时代，是我国发展新的______。',answer:'历史方位',explanation:'P14'},
{id:28,chapter:1,type:'fill',question:'我们既要看到我国社会主要矛盾发生的变化，也要看到我国仍处于并将长期处于社会主义______的基本国情没有变。',answer:'初级阶段',explanation:'P26'},
{id:29,chapter:1,type:'fill',question:'中国特色社会主义写出了科学社会主义的"______"。',answer:'新版本',explanation:'P19'},
{id:30,chapter:1,type:'fill',question:'"五位一体"总体布局和协调推进"______"战略布局。',answer:'四个全面',explanation:'P29-32'}"""

# 找id:15最后一行
lines = content.split('\n')
insert_line = None
for i, line in enumerate(lines):
    if '{id:15,' in line and 'chapter:0' in line:
        insert_line = i + 1
        break

if insert_line:
    new_lines = lines[:insert_line] + [new_ch1] + lines[insert_line:]
    new_content = '\n'.join(new_lines)
    with open('习思想期末复习/刷题题库.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('OK - 第一章15道题已插入到第' + str(insert_line+1) + '行之后')
else:
    print('ERROR - 找不到id:15')

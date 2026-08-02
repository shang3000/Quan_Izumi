import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_ch4 = """{id:61,chapter:4,type:'single',question:'马克思主义的本质属性和鲜明品格是（    ）。',options:['实践性','人民性','科学性','阶级性'],answer:[1],explanation:'人民性是马克思主义的本质属性和鲜明品格。P74'},
{id:62,chapter:4,type:'single',question:'我们党的最大政治优势是（    ）。',options:['理论联系实际','批评与自我批评','密切联系群众','民主集中制'],answer:[2],explanation:'我们党的最大政治优势是密切联系群众。P79'},
{id:63,chapter:4,type:'single',question:'人民立场是中国共产党的（    ）政治立场。',options:['根本','基本','重要','核心'],answer:[0],explanation:'人民立场是中国共产党的根本政治立场。P78'},
{id:64,chapter:4,type:'single',question:'（    ）是我们党的生命线和根本工作路线。',options:['实事求是','群众路线','独立自主','民主集中制'],answer:[1],explanation:'群众路线是我们党的生命线和根本工作路线。P84'},
{id:65,chapter:4,type:'single',question:'（    ）是获得真知灼见的源头活水，是贯彻群众路线的有效途径。',options:['理论学习','调查研究','实践锻炼','批评与自我批评'],answer:[1],explanation:'调查研究是获得真知灼见的源头活水，是贯彻群众路线的有效途径。P85'},
{id:66,chapter:4,type:'multiple',question:'坚持人民立场，就要（    ）。',options:['始终牢记党的初心和使命','始终保持党同人民群众的血肉联系','热爱人民、尊重人民、敬畏人民','始终坚持以经济建设为中心'],answer:[0,1,2],explanation:'P78-79'},
{id:67,chapter:4,type:'multiple',question:'人民群众是（    ）。',options:['社会物质财富的创造者','社会精神财富的创造者','社会变革的决定力量','历史发展的旁观者'],answer:[0,1,2],explanation:'P75'},
{id:68,chapter:4,type:'multiple',question:'依靠人民创造历史伟业，必须（    ）。',options:['尊重人民主体地位','尊重人民首创精神','坚持党的领导','坚持依法治国'],answer:[0,1],explanation:'依靠人民创造历史伟业，必须尊重人民主体地位。依靠人民创造历史伟业，必须尊重人民首创精神。P81'},
{id:69,chapter:4,type:'multiple',question:'为人民造福，要（    ）。',options:['着力解决人民群众最关心最直接最现实的利益问题','一件事情接着一件事情办','一年接着一年干','一蹴而就'],answer:[0,1,2],explanation:'P86'},
{id:70,chapter:4,type:'multiple',question:'促进共同富裕，要把握好的原则包括（    ）。',options:['鼓励勤劳创新致富','坚持基本经济制度','尽力而为量力而行','坚持循序渐进'],answer:[0,1,2,3],explanation:'P88'},
{id:71,chapter:4,type:'fill',question:'江山就是______，人民就是江山。',answer:'人民',explanation:'P75'},
{id:72,chapter:4,type:'fill',question:'民心是最大的______，决定事业兴衰成败。',answer:'政治',explanation:'P76'},
{id:73,chapter:4,type:'fill',question:'时代是出卷人，我们是答卷人，______是阅卷人。',answer:'人民',explanation:'P82'},
{id:74,chapter:4,type:'fill',question:'______是中国特色社会主义的本质要求，是中国式现代化的重要特征。',answer:'共同富裕',explanation:'P87'},
{id:75,chapter:4,type:'fill',question:'人民是我们党的______、执政之基、力量之源。',answer:'生命之根',explanation:'P81'}"""

lines = content.split('\n')
insert_line = None
for i, line in enumerate(lines):
    if '{id:60,' in line and 'chapter:3' in line:
        insert_line = i + 1
        break

if insert_line:
    new_lines = lines[:insert_line] + [new_ch4] + lines[insert_line:]
    with open('习思想期末复习/刷题题库.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print('OK')
else:
    print('ERROR')

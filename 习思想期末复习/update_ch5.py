import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_ch5 = """{id:76,chapter:5,type:'single',question:'全面深化改革总目标是（    ）。',options:['完善中国特色社会主义制度','推进国家治理体系和治理能力现代化','实现中华民族伟大复兴','建设社会主义现代化强国'],answer:[1],explanation:'全面深化改革总目标是：完善和发展中国特色社会主义制度、推进国家治理体系和治理能力现代化。P98'},
{id:77,chapter:5,type:'single',question:'改革发展稳定中，（    ）是解决一切经济社会问题的关键。',options:['改革','发展','稳定','创新'],answer:[1],explanation:'发展是解决一切经济社会问题的关键。P103'},
{id:78,chapter:5,type:'single',question:'全面深化改革开放的正确方向不包括（    ）。',options:['坚持和改善党的全面领导','坚持和完善中国特色社会主义制度','以资本为中心','以人民为中心'],answer:[2],explanation:'必须坚持和改善党的全面领导、坚持和完善中国特色社会主义制度。必须坚持以人民为中心。P96'},
{id:79,chapter:5,type:'single',question:'改革开放使中国创造了（    ）。',options:['经济快速发展和社会长期稳定两大奇迹','科技领先和军事强大两大奇迹','文化繁荣和教育普及两大奇迹','民主发展和法治进步两大奇迹'],answer:[0],explanation:'创造了经济快速发展和社会长期稳定两大奇迹。P92'},
{id:80,chapter:5,type:'single',question:'（    ）是经济社会发展的强大动力。',options:['改革','发展','稳定','开放'],answer:[0],explanation:'改革是经济社会发展的强大动力。P103'},
{id:81,chapter:5,type:'multiple',question:'改革开放是（    ）。',options:['决定当代中国命运的关键一招','决定实现"两个一百年"奋斗目标的关键一招','党和人民大踏步赶上时代的重要法宝','坚持和发展中国特色社会主义的必由之路'],answer:[0,1,2,3],explanation:'P91-92'},
{id:82,chapter:5,type:'multiple',question:'改革开放使中国面貌发生的变化包括（    ）。',options:['极大改变了中国的面貌','极大改变了中华民族的面貌','极大改变了中国人民的面貌','极大改变了中国共产党的面貌'],answer:[0,1,2,3],explanation:'P92'},
{id:83,chapter:5,type:'multiple',question:'全面深化改革开放的正确方向包括（    ）。',options:['必须坚持和改善党的全面领导','必须坚持和完善中国特色社会主义制度','必须坚持以人民为中心','必须有利于进一步解放思想、解放和发展社会生产力、解放和增强社会活力'],answer:[0,1,2,3],explanation:'P96'},
{id:84,chapter:5,type:'multiple',question:'推进国家治理体系和治理能力现代化，必须（    ）。',options:['坚定中国特色社会主义制度自信','更好发挥中国特色社会主义制度优势','把中国特色社会主义制度优势转化为国家治理效能','照搬西方治理模式'],answer:[0,1,2],explanation:'P100'},
{id:85,chapter:5,type:'multiple',question:'中国对外开放（    ）。',options:['不是要一家唱独角戏，而是要欢迎各方共同参与','不是要谋求势力范围，而是要支持各国共同发展','不是要营造自己的后花园，而是要建设各国共享的百花园','不是要关闭国门，而是要更大范围开放'],answer:[0,1,2],explanation:'P110'},
{id:86,chapter:5,type:'fill',question:'改革开放是决定当代中国命运的______，也是决定实现"两个一百年"奋斗目标、实现中华民族伟大复兴的关键一招。',answer:'关键一招',explanation:'P91'},
{id:87,chapter:5,type:'fill',question:'党的十一届三中全会是______的，开启了改革开放和社会主义现代化建设新时期。',answer:'划时代',explanation:'P93'},
{id:88,chapter:5,type:'fill',question:'凡属重大改革要于法有据，需要修改法律的可以先修改法律，先______后破，有序进行。',answer:'立',explanation:'P104'},
{id:89,chapter:5,type:'fill',question:'国家治理体系和治理能力现代化，是一个国家______的重要标志。',answer:'现代化',explanation:'P100'},
{id:90,chapter:5,type:'fill',question:'稳定是改革发展的______。',answer:'前提',explanation:'P103'}"""

lines = content.split('\n')
insert_line = None
for i, line in enumerate(lines):
    if '{id:75,' in line and 'chapter:4' in line:
        insert_line = i + 1
        break

if insert_line:
    new_lines = lines[:insert_line] + [new_ch5] + lines[insert_line:]
    with open('习思想期末复习/刷题题库.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print('OK')
else:
    print('ERROR')

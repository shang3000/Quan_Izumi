import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_ch2 = """{id:31,chapter:2,type:'single',question:'新时代新征程中国共产党的中心任务，就是以（    ）全面推进中华民族伟大复兴。',options:['改革开放','中国式现代化','高质量发展','共同富裕'],answer:[1],explanation:'P35'},
{id:32,chapter:2,type:'single',question:'中国式现代化是强国建设、民族复兴的（    ）。',options:['重要途径','唯一正确道路','必然选择','根本保证'],answer:[1],explanation:'中国式现代化是强国建设、民族复兴的唯一正确道路。P41'},
{id:33,chapter:2,type:'single',question:'中国式现代化是中国共产党领导的（    ）现代化。',options:['资本主义','社会主义','民主主义','科学主义'],answer:[1],explanation:'中国式现代化是中国共产党领导的社会主义现代化。P44'},
{id:34,chapter:2,type:'single',question:'团结奋斗是中国共产党和中国人民最显著的（    ）。',options:['优良传统','精神标识','政治优势','制度优势'],answer:[1],explanation:'团结奋斗是中国共产党和中国人民最显著的精神标识。P53'},
{id:35,chapter:2,type:'single',question:'实现中华民族伟大复兴的中国梦，本质是（    ）。',options:['经济发展、政治民主、文化繁荣','国家统一、民族团结、社会稳定','国家富强、民族振兴、人民幸福','科技进步、教育发展、民生改善'],answer:[2],explanation:'实现中华民族伟大复兴的中国梦，本质是国家富强、民族振兴、人民幸福。P37'},
{id:36,chapter:2,type:'multiple',question:'中国式现代化的中国特色包括（    ）。',options:['人口规模巨大的现代化','全体人民共同富裕的现代化','物质文明和精神文明相协调的现代化','人与自然和谐共生的现代化','走和平发展道路的现代化'],answer:[0,1,2,3,4],explanation:'P44-46'},
{id:37,chapter:2,type:'multiple',question:'推进中国式现代化需要牢牢把握的重大原则包括（    ）。',options:['坚持和加强党的全面领导','坚持中国特色社会主义道路','坚持以人民为中心的发展思想','坚持深化改革开放','坚持发扬斗争精神'],answer:[0,1,2,3,4],explanation:'P50-51'},
{id:38,chapter:2,type:'multiple',question:'中国式现代化打破了（    ）的迷思。',options:['现代化等于西方化','只有走资本主义道路才能实现现代化','现代化必须照搬西方模式','发展中国家无法实现现代化'],answer:[0,1],explanation:'P48-49'},
{id:39,chapter:2,type:'multiple',question:'推进中国式现代化需要正确处理的重大关系包括（    ）。',options:['顶层设计与实践探索','战略与策略','守正与创新','效率与公平'],answer:[0,1,2,3],explanation:'P51'},
{id:40,chapter:2,type:'multiple',question:'中国式现代化创造了人类文明新形态，（    ）。',options:['提供了一种全新的现代化模式','是对西方式现代化理论和实践的重大超越','为广大发展中国家提供了全新选择','摒弃了以资本为中心的西方现代化老路'],answer:[0,1,2,3],explanation:'P48-49'},
{id:41,chapter:2,type:'fill',question:'中国式现代化是中国共产党领导的______现代化。',answer:'社会主义',explanation:'P44'},
{id:42,chapter:2,type:'fill',question:'党的二十大明确，全面建成社会主义现代化强国总的战略安排是分______走。',answer:'两',explanation:'P40'},
{id:43,chapter:2,type:'fill',question:'中国式现代化作为科学社会主义的最新成果，坚持社会主义______和方向。',answer:'目标',explanation:'P49'},
{id:44,chapter:2,type:'fill',question:'中国式现代化蕴含的独特世界观、价值观、历史观、文明观、______观、生态观等及其伟大实践，是对世界现代化理论和实践的重大创新。',answer:'民主',explanation:'P49'},
{id:45,chapter:2,type:'fill',question:'团结奋斗是中国人民创造历史伟业的______。',answer:'必由之路',explanation:'P53'}"""

lines = content.split('\n')
insert_line = None
for i, line in enumerate(lines):
    if '{id:30,' in line and 'chapter:1' in line:
        insert_line = i + 1
        break

if insert_line:
    new_lines = lines[:insert_line] + [new_ch2] + lines[insert_line:]
    with open('习思想期末复习/刷题题库.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print('OK - 第二章已插入')
else:
    print('ERROR')

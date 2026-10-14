"""RMO monthly workplan and progress reporting portal."""
from datetime import date
from pathlib import Path
import base64
import hmac
import html
import json

import pandas as pd
import streamlit as st

from reporting import (ROOT, FIELDS, BASES, STATUSES, new_draft, loads_draft,
                       normalise_rows, validate, totals, sections, period,
                       export_docx, filename)

st.set_page_config(page_title='DM RMO Monthly Reporting', page_icon='📋', layout='wide')
st.markdown('''<style>
.block-container{max-width:1250px;padding-top:1.5rem}
div[data-testid="stMetric"]{background:#f4f7fa;border-radius:8px;padding:12px}
h1,h2,h3{color:#18394d}
div[data-testid="stTabs"] button{font-weight:600}
@media(max-width:650px){.block-container{padding:1rem}h1{font-size:1.7rem!important}}
</style>''', unsafe_allow_html=True)

def setting(name, default=''):
    try: return st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError): return default

def login():
    expected=setting('APP_PASSWORD')
    if not expected:return
    if st.session_state.get('authenticated'):return
    st.title('DM RMO Reporting')
    with st.form('login'):
        entered=st.text_input('App password',type='password')
        submit=st.form_submit_button('Sign in')
    if submit:
        if hmac.compare_digest(entered.encode(),str(expected).encode()):
            st.session_state.authenticated=True;st.rerun()
        else:st.error('Password is incorrect.')
    st.stop()

login()
if 'draft' not in st.session_state:
    st.session_state.draft=new_draft();st.session_state.epoch=0

def restore(d):
    st.session_state.draft=d
    st.session_state.epoch+=1
    st.session_state.pop('editor_source',None)

with st.sidebar:
    st.header('Monthly reporting')
    st.caption('One draft per sub-stream and reporting cycle.')
    upload=st.file_uploader('Restore a saved draft',type=['json'],key='restore_upload')
    if st.button('Restore draft',disabled=upload is None,width='stretch'):
        try:restore(loads_draft(upload.getvalue()));st.rerun()
        except (ValueError,TypeError,KeyError,OverflowError) as e:st.error(f'Cannot restore draft: {e}')
    if st.button('Load BBB example',width='stretch'):
        restore(loads_draft((ROOT/'examples/bbb_example.json').read_bytes()));st.rerun()
    st.caption('BBB is an editable example from your supplied report. Review dates, hours and evidence before reuse.')
    if st.checkbox('Confirm clearing the current draft',key='reset_confirm'):
        if st.button('Start a blank draft',width='stretch'):restore(new_draft());st.rerun()
    st.divider()
    st.caption('Save your draft JSON before closing. Sessions are temporary; this version has no shared database or automatic cloud storage.')
    if setting('APP_PASSWORD') and st.button('Sign out'):
        st.session_state.clear();st.rerun()

    variant=st.selectbox('Logo artwork',['Enhanced','Original template'],index=0 if st.session_state.draft['meta'].get('logo_variant')=='Enhanced' else 1,key=f'logo_{st.session_state.epoch}')
    st.session_state.draft['meta']['logo_variant']=variant
    st.caption('Enhanced artwork is a restored display version. The original embedded logos are also available for official document use.')

logo=ROOT/'assets/logos_enhanced.png' if variant=='Enhanced' else ROOT/'assets/image1.png'
if not logo.exists():logo=ROOT/'assets/image1.png'
left,right=st.columns([2,1])
with left:st.image(str(logo),width=600)
with right:
    st.caption('NATIONAL DISASTER MANAGEMENT CENTRE')
    st.markdown('**Disaster Management Results Management Office**')
st.title('Monthly workplans and progress reports')
st.write('Capture activities against your KRAs, review hours and evidence, and generate Word documents using the RMO template.')

d=st.session_state.draft;m=d['meta'];n=d['narratives'];epoch=st.session_state.epoch
def key(k):return f'{k}_{epoch}'

tabs=st.tabs(['1 · Reporting details','2 · Activities and hours','3 · Narratives','4 · Preview and downloads','5 · Stream overview'])
with tabs[0]:
    st.subheader('Reporting details')
    a,b=st.columns(2)
    with a:
        m['substream']=st.text_input('Sub-stream name',value=m['substream'],key=key('substream'),placeholder='Build Back Better, SEMS, Fire Services…')
        m['prepared_by']=st.text_input('Prepared by',value=m['prepared_by'],key=key('prepared_by'))
        m['role']=st.text_input('Role or designation',value=m['role'],key=key('role'))
    with b:
        m['monthly_limit']=st.number_input('Monthly planning ceiling (hours)',value=float(m['monthly_limit']),min_value=0.0,step=1.0,key=key('limit'),help='A planning ceiling, not approval of billable hours. Enter 0 if no ceiling is specified.')
        m['signoff_date']=st.date_input('Sign-off date',date.fromisoformat(m['signoff_date']),key=key('signoff')).isoformat()
    a,b=st.columns(2)
    with a:
        st.markdown('**Progress reporting window**')
        m['report_start']=st.date_input('Progress start',date.fromisoformat(m['report_start']),key=key('report_start')).isoformat()
        m['report_end']=st.date_input('Progress end',date.fromisoformat(m['report_end']),key=key('report_end')).isoformat()
    with b:
        st.markdown('**Forward workplan window**')
        m['plan_start']=st.date_input('Workplan start',date.fromisoformat(m['plan_start']),key=key('plan_start')).isoformat()
        m['plan_end']=st.date_input('Workplan end',date.fromisoformat(m['plan_end']),key=key('plan_end')).isoformat()
    m['hours_note']=st.text_area('Hours assumptions and verification notes',value=m['hours_note'],key=key('hours_note'),help='Record how estimates were derived and whether the ceiling is confirmed.')
    m['contract_note']=st.text_area('Contract gaps and excluded periods',value=m['contract_note'],key=key('contract_note'),help='If the report spans an interruption, identify the excluded dates here.')

with tabs[1]:
    st.subheader('Activity register')
    st.caption('Add and remove rows in the table. Progress contains reported work; Workplan contains forward activities. Scroll horizontally for deliverables, evidence and dependencies.')
    if 'editor_source' not in st.session_state:
        frame=pd.DataFrame(d['activities'],columns=FIELDS)
        for k in ['start','end']:
            frame[k]=frame[k].map(lambda x: date.fromisoformat(x) if isinstance(x,str) and x else None)
        frame['hours']=pd.to_numeric(frame['hours'])
        st.session_state.editor_source=frame
    configs={
        'phase':st.column_config.SelectboxColumn('Phase',options=['Progress','Workplan'],required=True,default='Progress'),
        'kra':st.column_config.TextColumn('KRA / objective'),
        'activity':st.column_config.TextColumn('Activity',required=True,width='large'),
        'start':st.column_config.DateColumn('Start',format='DD MMM YYYY',required=True),
        'end':st.column_config.DateColumn('End',format='DD MMM YYYY',required=True),
        'hours':st.column_config.NumberColumn('Hours',min_value=0.0,step=0.5,required=True,default=0.0),
        'basis':st.column_config.SelectboxColumn('Hours basis',options=BASES,required=True,default='Estimated'),
        'status':st.column_config.SelectboxColumn('Status',options=STATUSES,required=True,default='Planned'),
        'output':st.column_config.TextColumn('Deliverable',width='large'),
        'purpose':st.column_config.TextColumn('Purpose',width='large'),
        'alignment':st.column_config.TextColumn('Strategy / Matrix / APP alignment',width='large'),
        'evidence':st.column_config.TextColumn('PoE reference / link',width='large'),
        'owner':st.column_config.TextColumn('Responsible person'),
        'dependencies':st.column_config.TextColumn('Dependencies / approvals',width='large'),
        'notes':st.column_config.TextColumn('Activity detail',width='large')}
    edited=st.data_editor(st.session_state.editor_source,num_rows='dynamic',hide_index=True,
                          column_config=configs,key=key('activity_editor'),width='stretch')
    try:d['activities']=normalise_rows(edited.to_dict('records'))
    except (ValueError,TypeError) as e:st.error(f'Check activity values: {e}')
    st.markdown('**Progress hours by basis**')
    progress=[r for r in d['activities'] if r['phase']=='Progress']
    t=totals(progress)
    for col,basis in zip(st.columns(4),BASES):col.metric(basis,f'{t[basis]:g} h')
    planned=[r for r in d['activities'] if r['phase']=='Workplan']
    st.metric('Forward workplan hours',f"{sum(r['hours'] for r in planned):g} h")
    st.caption('These figures are separate. Scheduled meeting durations do not establish attendance or actual hours.')

with tabs[2]:
    st.subheader('Progress report narratives')
    labels={'summary':'Executive summary','objectives':'Objectives for the reporting period',
            'targets':'Performance targets','outputs':'Summary of key outputs (leave blank to use activity outputs)',
            'integration':'Cross-stream integration','lessons':'Key lessons, emerging issues and risks',
            'conclusion':'Conclusion','annexures':'Annexure references (one per line)'}
    for k,label in labels.items():
        n[k]=st.text_area(label,value=n[k],height=110,key=key(k))
    st.subheader('Forward workplan narratives')
    labels={'plan_summary':'Workplan executive summary','plan_objectives':'Workplan objectives',
            'plan_targets':'Workplan performance targets','plan_integration':'Planned cross-stream integration',
            'plan_risks':'Dependencies, approvals and delivery risks','plan_conclusion':'Workplan conclusion'}
    for k,label in labels.items():n[k]=st.text_area(label,value=n[k],height=100,key=key(k))

def preview(mode):
    rows,content=sections(d,mode)
    e=lambda s:html.escape(str(s)).replace('\n','<br>')
    image_data=base64.b64encode(logo.read_bytes()).decode()
    title='Monthly Workplan' if mode=='workplan' else 'Executive Summary of Portfolio of Evidence'
    body=f'<img class="logo" alt="CoGTA and NDMC logos" src="data:image/png;base64,{image_data}"><h1>{title}</h1><p><b>{e(m["substream"])}</b><br>Prepared by: {e(m["prepared_by"])}<br>{e(period(m,"plan" if mode=="workplan" else "report"))}</p>'
    for h,text in content:
        body+=f'<h2>{e(h)}</h2>'
        if h.startswith('5.'):
            for i,r in enumerate(rows,1):
                body+=f'<h3>5.{i} {e(r["activity"])}</h3><p>{e(r["start"])} to {e(r["end"])} · {e(r["kra"])}<br>{r["hours"]:g} hours ({e(r["basis"])}) · {e(r["status"])}</p>'
                for label,k in [('Owner','owner'),('Deliverable','output'),('Purpose','purpose'),('Strategy and APP alignment','alignment'),('Evidence','evidence'),('Dependencies','dependencies'),('Detail','notes')]:
                    if r[k]:body+=f'<p><b>{label}:</b> {e(r[k])}</p>'
        elif h.startswith('8.'):
            body+='<table><tr><th>Output</th><th>Purpose</th><th>Strategy / APP contribution</th><th>PoE and status</th></tr>'
            for r in rows:body+=f'<tr><td>{e(r["output"] or r["activity"])}</td><td>{e(r["purpose"])}</td><td>{e(r["kra"])}<br>{e(r["alignment"])}</td><td>{e(r["evidence"])}<br>{e(r["status"])}</td></tr>'
            body+='</table>'
        else:body+=f'<p>{e(text)}</p>'
        if h.startswith('10.'):body+=f'<p>Signature __________________<br>Name: {e(m["prepared_by"])}<br>Date: {e(m["signoff_date"])}</p>'
    body+=f'<h2>Annexures</h2><p>{e(n["annexures"])}</p>'
    return '''<!doctype html><html><head><meta charset="utf-8"><style>
    body{font:15px/1.5 Arial,sans-serif;color:#222;padding:28px;max-width:850px;margin:auto;background:white}
    .logo{width:min(100%,600px);display:block;margin:0 auto 20px}h1{font-size:22px;text-align:center}h2{font-size:18px;margin-top:25px}h3{font-size:16px}
    table{width:100%;border-collapse:collapse;font-size:13px}th,td{border:1px solid #ccc;padding:9px;vertical-align:top}th{background:#eef2f5}
    </style></head><body>'''+body+'</body></html>'

with tabs[3]:
    st.subheader('Review and download')
    errors,warnings=validate(d)
    for error in errors:st.error(error)
    if warnings:
        with st.expander(f'{len(warnings)} review notes',expanded=True):
            for warning in warnings:st.warning(warning)
    mode=st.radio('Document preview',['Progress report','Monthly workplan'],horizontal=True,key=key('preview_mode'))
    export_mode='workplan' if mode=='Monthly workplan' else 'progress'
    st.caption('Content preview below. Word downloads use the attached template; Word pagination may differ from this preview.')
    with st.expander('Show document preview',expanded=True):st.iframe(preview(export_mode),height=650,alt='RMO document content preview')
    c1,c2,c3=st.columns(3)
    for col,kind,label in [(c1,'progress','Download progress report · Word'),(c2,'workplan','Download monthly workplan · Word')]:
        with col:
            if errors:st.button(label,disabled=True,width='stretch',key=key(kind))
            else:
                try:st.download_button(label,export_docx(d,kind),filename(d,kind),mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',width='stretch',key=key(kind))
                except Exception:st.error('Document generation failed. Check the bundled template and logo assets.')
    with c3:st.download_button('Save draft · JSON',json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False),file_name='RMO_monthly_draft.json',mime='application/json',width='stretch')
    st.download_button('Download activity register · CSV',pd.DataFrame(d['activities'],columns=FIELDS).to_csv(index=False),file_name='RMO_activity_register.csv',mime='text/csv')
    st.download_button('Download supplied Word template',(ROOT/'templates/rmo_template.docx').read_bytes(),file_name='DM_RMO_Executive_Summary_Template.docx')

with tabs[4]:
    st.subheader('Overview across sub-streams')
    st.write('Upload saved drafts from participating sub-streams to compare reported progress and forward hours. This does not merge their underlying documents.')
    files=st.file_uploader('Sub-stream draft files',type=['json'],accept_multiple_files=True,key='overview_upload')
    records=[];seen=set()
    for f in files:
        try:
            item=loads_draft(f.getvalue());mm=item['meta'];errs,_=validate(item)
            identity=(mm['substream'],mm['report_start'],mm['report_end'],mm['prepared_by'])
            if identity in seen:st.warning(f'{f.name}: duplicate reporting cycle skipped.');continue
            seen.add(identity)
            tt=totals([r for r in item['activities'] if r['phase']=='Progress'])
            record={'Sub-stream':mm['substream'],'Prepared by':mm['prepared_by'],
                    'Report start':mm['report_start'],'Report end':mm['report_end'],
                    **{b+' hours':tt[b] for b in BASES},
                    'Workplan hours':sum(r['hours'] for r in item['activities'] if r['phase']=='Workplan'),
                    'Completed activities':sum(r['status']=='Completed' for r in item['activities'] if r['phase']=='Progress'),
                    'Validation issues':len(errs)}
            records.append(record)
        except (ValueError,TypeError,KeyError,OverflowError) as e:st.error(f'{f.name}: {e}')
    if records:
        df=pd.DataFrame(records);st.dataframe(df,hide_index=True,width='stretch')
        st.download_button('Download overview · CSV',df.to_csv(index=False),'RMO_substream_overview.csv','text/csv')
    else:st.info('Upload one or more saved draft files to see the overview.')

st.divider()
st.caption('DM RMO · Monthly planning, progress and portfolio of evidence. Generated reports remain subject to verification and signature.')

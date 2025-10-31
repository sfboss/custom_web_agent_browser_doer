"""Streamlit UI for reviewing web agent evidence packs."""
import streamlit as st
import json
import glob
from pathlib import Path


st.set_page_config(page_title='Web Agent Evidence Viewer', layout='wide')

# Session directory
root = 'runtime/sessions'

# Get all run directories
run_dirs = sorted(glob.glob(f"{root}/*/"), reverse=True)

st.title('🕵️ Web Agent Evidence Viewer')

if not run_dirs:
    st.warning('No runs found. Execute a task first to generate evidence.')
    st.info('Run: `python packages/web-agent-py/agent.py packages/web-agent-py/tasks/examples/find_salesforce_pricing.yaml`')
else:
    # Sidebar for run selection
    st.sidebar.header('📁 Session Runs')
    
    # Show run info in sidebar
    run_info = []
    for run_dir in run_dirs:
        run_path = Path(run_dir)
        run_name = run_path.name
        
        # Check if successful
        success = (run_path / 'success.flag').exists()
        status = '✅' if success else '❌'
        
        # Get task ID if available
        task_id = 'unknown'
        manifest_path = run_path / 'run.json'
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    task_id = manifest.get('task_id', 'unknown')
            except:
                pass
        
        run_info.append(f"{status} {run_name} ({task_id})")
    
    choice_idx = st.sidebar.selectbox('Select run', range(len(run_info)), 
                                       format_func=lambda i: run_info[i])
    choice = run_dirs[choice_idx]
    
    # Display selected run
    run_path = Path(choice)
    st.subheader(f"📊 {run_path.name}")
    
    # Load manifest
    manifest_path = run_path / 'run.json'
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Task ID', manifest.get('task_id', 'N/A'))
        with col2:
            duration = manifest.get('duration_seconds', 0)
            st.metric('Duration', f"{duration:.2f}s")
        with col3:
            success = (run_path / 'success.flag').exists()
            st.metric('Status', '✅ Success' if success else '❌ Failed')
        
        # Show git commit if available
        if manifest.get('git_commit'):
            st.code(f"Git commit: {manifest['git_commit']}", language='text')
    
    # Tabs for different evidence types
    tabs = st.tabs(['📸 Screenshots', '🔍 Selectors', '📝 Reasoning', '📄 Manifest', '🌐 DOM'])
    
    # Screenshots tab
    with tabs[0]:
        st.subheader('Screenshots')
        pngs = sorted(glob.glob(f"{choice}/evidence/*.png"))
        
        if pngs:
            for png in pngs:
                st.image(png, caption=Path(png).name, use_container_width=True)
        else:
            st.info('No screenshots available')
    
    # Selectors tab
    with tabs[1]:
        st.subheader('Selectors')
        selectors_path = run_path / 'evidence' / 'selectors.json'
        
        if selectors_path.exists():
            with open(selectors_path) as f:
                selectors = json.load(f)
            
            st.json(selectors)
            
            # Download button
            st.download_button(
                'Download selectors.json',
                data=open(selectors_path, 'rb').read(),
                file_name='selectors.json',
                mime='application/json'
            )
        else:
            st.info('No selectors data available')
    
    # Reasoning tab
    with tabs[2]:
        st.subheader('Reasoning Log')
        reasoning_path = run_path / 'reasoning.jsonl'
        
        if reasoning_path.exists():
            with open(reasoning_path) as f:
                lines = f.readlines()
            
            st.write(f"Total steps: {len(lines)}")
            
            for i, line in enumerate(lines, 1):
                try:
                    entry = json.loads(line)
                    with st.expander(f"Step {entry.get('step', i)}: {entry.get('action', 'N/A')}"):
                        st.json(entry)
                except:
                    st.text(line)
        else:
            st.info('No reasoning log available')
    
    # Manifest tab
    with tabs[3]:
        st.subheader('Run Manifest')
        
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            st.json(manifest)
        else:
            st.info('No manifest available')
    
    # DOM tab
    with tabs[4]:
        st.subheader('DOM Snapshots')
        dom_files = sorted(glob.glob(f"{choice}/evidence/*.html"))
        
        if dom_files:
            selected_dom = st.selectbox('Select DOM snapshot', dom_files, 
                                       format_func=lambda x: Path(x).name)
            
            with open(selected_dom) as f:
                dom_content = f.read()
            
            st.code(dom_content[:5000] + ('...' if len(dom_content) > 5000 else ''), 
                   language='html')
            
            st.download_button(
                'Download full DOM',
                data=dom_content,
                file_name=Path(selected_dom).name,
                mime='text/html'
            )
        else:
            st.info('No DOM snapshots available')
